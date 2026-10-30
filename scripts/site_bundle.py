#!/usr/bin/env python3
"""PAGES-ARTIFACT/1: build and verify exactly the shipped static bytes.

No package installs, GitHub REST, timestamps, network calls or runtime framework.
The checksum manifest proves byte consistency, NOT independent deployment provenance.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

from audit import WEB_FILES, audit

PROTOCOL = "PAGES-ARTIFACT/1"
MANIFEST = "deployment-manifest.json"
SITE_FILES = tuple(sorted((*WEB_FILES, ".nojekyll")))
SHA = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")
SCRIPT = "./app.js"
CSS = "./formal-lab/formal-lab.css"


class BundleError(ValueError):
    pass


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


class IndexParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.modules: list[str] = []
        self.styles: list[str] = []
        self.ids: list[str] = []
        self.csp: list[str] = []
        self.remote: list[str] = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if "id" in fields:
            self.ids.append(fields["id"])
        if tag == "script":
            if fields.get("type") == "module":
                self.modules.append(fields.get("src", ""))
            if fields.get("src", "").startswith(("http:", "https:", "//")):
                self.remote.append(fields["src"])
        if tag == "link" and fields.get("rel") == "stylesheet":
            self.styles.append(fields.get("href", ""))
        if tag == "meta" and fields.get("http-equiv", "").lower() == "content-security-policy":
            self.csp.append(fields.get("content", ""))


def check_html(raw: bytes) -> None:
    parser = IndexParser()
    parser.feed(raw.decode("utf-8"))
    parser.close()
    if parser.modules != [SCRIPT]:
        raise BundleError("missing, duplicate or malformed application module script")
    if CSS not in parser.styles or len(parser.styles) != len(set(parser.styles)):
        raise BundleError("malformed or duplicated first-party stylesheet")
    if len(parser.csp) != 1:
        raise BundleError("exactly one CSP meta policy required")
    policy = parser.csp[0]
    for clause in ("default-src 'self'", "script-src 'self'", "style-src 'self'",
                   "connect-src 'self'", "object-src 'none'", "base-uri 'self'"):
        if clause not in policy:
            raise BundleError("CSP missing required restriction: " + clause)
    if "unsafe-inline" in policy or "unsafe-eval" in policy or parser.remote:
        raise BundleError("remote/unsafe executable content present")
    if len(parser.ids) != len(set(parser.ids)):
        raise BundleError("duplicate HTML IDs")
    for expected in ("main", "automaton", "run-tests", "ledger", "formal-lab", "formal-lab-run"):
        if expected not in parser.ids:
            raise BundleError("missing public browser journey anchor: " + expected)
    for link in parser.styles + parser.modules:
        if not link.startswith("./") or link[2:] not in SITE_FILES:
            raise BundleError("unpackaged or remote stylesheet/module reference: " + link)


def safe_file(root: Path, name: str) -> Path:
    # Every path originates in the source-reviewed allowlist, not user input.
    path = root / name
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise BundleError("missing, escaping or symlink asset: " + name)
    return path


def inventory(root: Path) -> dict[str, str]:
    hashes = {}
    for name in SITE_FILES:
        hashes[name] = hash_bytes(safe_file(root, name).read_bytes())
    check_html(safe_file(root, "index.html").read_bytes())
    return hashes


def envelope(hashes: dict[str, str], revision: str) -> dict:
    if revision != "UNVERSIONED" and not REVISION.fullmatch(revision):
        raise BundleError("revision must be exact Git commit SHA or UNVERSIONED")
    if set(hashes) != set(SITE_FILES):
        raise BundleError("incomplete or unexpected staged file inventory")
    return {
        "protocol": PROTOCOL,
        "revision": revision,
        "files": dict(sorted(hashes.items())),
        "tree_sha256": hash_bytes(canonical(dict(sorted(hashes.items())))),
        "limitations": [
            "Checksums establish reproducible site bytes, not deployment authorship or browser correctness.",
            "A GitHub Pages deployment must be separately observed; local artifact checking is not remote deployment evidence."
        ],
    }


def strict_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise BundleError("duplicate JSON key: " + k)
        result[k] = v
    return result


def reject_number(_):
    raise BundleError("non-integer or nonfinite JSON value")


def parse_manifest(raw: bytes) -> dict:
    if len(raw) > 20000:
        raise BundleError("oversized deployment manifest")
    try:
        record = json.loads(raw.decode("utf-8"), object_pairs_hook=strict_pairs,
                            parse_float=reject_number, parse_constant=reject_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as e:
        raise BundleError("malformed deployment manifest: " + str(e)) from e
    if type(record) is not dict or set(record) != {
            "protocol", "revision", "files", "tree_sha256", "limitations"}:
        raise BundleError("unexpected deployment manifest schema")
    return record


def verify(site: Path, *, revision: str | None = None, source: Path | None = None) -> dict:
    site = site.resolve()
    if not site.is_dir():
        raise BundleError("staged site directory missing")
    if any(p.is_symlink() for p in site.rglob("*")):
        raise BundleError("symlink in site artifact")
    observed = {p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    if observed != set(SITE_FILES) | {MANIFEST}:
        raise BundleError("site has missing or unexpected files: " +
                          str(sorted(observed ^ (set(SITE_FILES) | {MANIFEST}))))
    manifest = parse_manifest((site / MANIFEST).read_bytes())
    hashes = inventory(site)
    if manifest != envelope(hashes, manifest["revision"]):
        raise BundleError("manifest content or asset hashes disagree with bytes")
    if revision is not None and manifest["revision"] != revision:
        raise BundleError("revision mismatch")
    if source is not None and hashes != inventory(source.resolve()):
        raise BundleError("artifact differs from source checkout")
    return {"status": "BYTE_EXACT_VERIFIED_UNATTESTED", "revision": manifest["revision"],
            "files": len(hashes), "tree_sha256": manifest["tree_sha256"]}


def stage(source: Path, site: Path, revision: str) -> dict:
    source, site = source.resolve(), site.absolute()
    if site.exists() and (not site.is_dir() or any(site.iterdir())):
        raise BundleError("destination must be absent or an empty directory")
    if site.resolve() == source or source.is_relative_to(site.resolve()) or site.resolve().is_relative_to(source):
        raise BundleError("source and destination cannot overlap")
    source_hashes = inventory(source)
    result = audit(source)
    if not result["passed"]:
        raise BundleError("source no-package audit failed: " + str(result["findings"]))
    for name in SITE_FILES:
        destination = site / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe_file(source, name), destination)
    record = envelope(source_hashes, revision)
    (site / MANIFEST).write_bytes(json.dumps(record, sort_keys=True, indent=2).encode() + b"\n")
    return verify(site, revision=revision, source=source)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "verify"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--revision")
    args = parser.parse_args(argv)
    try:
        if args.action == "stage":
            record = stage(args.source or Path(__file__).resolve().parent.parent,
                           args.site, args.revision or "UNVERSIONED")
        else:
            record = verify(args.site, revision=args.revision, source=args.source)
        print(json.dumps(record, sort_keys=True))
        return 0
    except (OSError, ValueError, UnicodeError) as e:
        print("FAIL: " + str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
