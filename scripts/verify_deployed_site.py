#!/usr/bin/env python3
"""GITHUB-PAGES-OBSERVATION/1: exact public CDN bytes after manual deployment.

Only the fixed official INDEPENDENCE Pages origin/path is permitted.
Network access is developer/deployer-side only. This is NOT a browser runtime
service and does not prove availability over time or the owner's identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from site_bundle import MANIFEST, SITE_FILES, BundleError, envelope, parse_manifest

BASE = "https://qsolkcb.github.io/INDEPENDENCE/"
MAX_BYTES = 2_000_000
PROTOCOL = "GITHUB-PAGES-OBSERVATION/1"
# .nojekyll is a packaging/deployment-control marker. The original staged
# artifact and complete manifest MUST contain it, but GitHub Pages can
# return 404 when fetching the dotfile over public HTTP. Its remote
# content cannot be attested by this public HTTP byte comparison.
NON_HTTP_MARKERS = (".nojekyll",)
PUBLIC_HTTP_ASSETS = tuple(name for name in SITE_FILES if name not in NON_HTTP_MARKERS)
if set(NON_HTTP_MARKERS) != {".nojekyll"} or set(PUBLIC_HTTP_ASSETS) != set(SITE_FILES) - set(NON_HTTP_MARKERS):
    raise ValueError("unexpected public HTTP vs packaging marker inventory")



class DeploymentError(ValueError):
    pass


def validate_base(url: str) -> None:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "qsolkcb.github.io" or
            parsed.netloc != "qsolkcb.github.io" or parsed.path != "/INDEPENDENCE/" or
            parsed.query or parsed.fragment):
        raise DeploymentError("only the official HTTPS Pages deployment path is permitted")


class RejectRedirects(HTTPRedirectHandler):
    """Fail closed before any redirect target is requested, even same-origin."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise DeploymentError("public Pages redirect denied before follow-up request")


def fetch_bytes(url: str) -> bytes:
    validate_base(BASE)
    requested = urlsplit(url)
    permitted = {MANIFEST, *PUBLIC_HTTP_ASSETS}
    # Check the whole URI, not merely a string prefix or a final redirect URL.
    if (requested.scheme != "https" or requested.netloc != "qsolkcb.github.io"
            or requested.path != "/INDEPENDENCE/" + requested.path.removeprefix("/INDEPENDENCE/")
            or requested.path.removeprefix("/INDEPENDENCE/") not in permitted
            or requested.query or requested.fragment):
        raise DeploymentError("out-of-scope public Pages asset")
    # The dedicated opener prevents urllib's default automatic redirect
    # handling. No external or downgraded HTTP URL can be fetched first.
    opener = build_opener(RejectRedirects())
    try:
        with opener.open(Request(url, headers={"User-Agent": "INDEPENDENCE-v1-deployment-check"}),
                         timeout=15) as response:
            if response.geturl() != url:
                raise DeploymentError("unexpected final public Pages URL")
            if getattr(response, "status", 200) != 200:
                raise DeploymentError("non-200 CDN response: " + url)
            data = response.read(MAX_BYTES + 1)
    except HTTPError as exc:
        raise DeploymentError("public asset HTTP " + str(exc.code) + " at " + url) from exc
    if len(data) > MAX_BYTES:
        raise DeploymentError("oversized public asset: " + url)
    return data


def verify_once(manifest_path: Path, *, base: str = BASE) -> dict:
    validate_base(base)
    raw = manifest_path.read_bytes()
    local = parse_manifest(raw)
    if local != envelope(local["files"], local["revision"]):
        raise DeploymentError("local manifest fields are internally inconsistent")
    remote_manifest = fetch_bytes(base + MANIFEST)
    if raw != remote_manifest:
        raise DeploymentError("public deployment manifest differs from staged bytes")
    matched = 0
    for name in PUBLIC_HTTP_ASSETS:
        observed = fetch_bytes(base + name)
        if hashlib.sha256(observed).hexdigest() != local["files"][name]:
            raise DeploymentError("public deployment asset differs from staging: " + name)
        matched += 1
    # The public manifest is byte-identical to the staged manifest and includes
    # the original SHA-256 of .nojekyll. That establishes only the marker's
    # *declared* staging identity, NOT a successful remote marker fetch.
    return {
        "protocol": PROTOCOL,
        "status": "REMOTE_HTTP_ASSETS_MATCHED_MARKER_UNOBSERVED",
        "revision": local["revision"],
        "files": matched,
        "manifest_verified": True,
        "non_http_markers_unobserved": list(NON_HTTP_MARKERS),
        "non_http_marker_staged_sha256": {
            name: local["files"][name] for name in NON_HTTP_MARKERS
        },
        "tree_sha256": local["tree_sha256"],
        "limitations": [
            "Only public HTTP assets and the manifest were fetched and matched at this instant.",
            "The .nojekyll deployment-control marker is locally packaged and named in the verified manifest but not remotely byte-observed.",
            "HTTPS and SHA-256 checks are not independent proof of authorship or security.",
            "JavaScript execution is verified separately using actual local browser journeys."
        ]
    }


def verify(manifest_path: Path, *, base: str = BASE, attempts: int = 1,
           delay: float = 3) -> dict:
    if type(attempts) is not int or not 1 <= attempts <= 8 or delay < 0 or delay > 30:
        raise DeploymentError("retry bounds invalid")
    last = None
    for attempt in range(1, attempts + 1):
        try:
            record = verify_once(manifest_path, base=base)
            record["attempts_used"] = attempt
            return record
        except (OSError, ValueError) as err:
            last = str(err)
            if attempt < attempts:
                time.sleep(delay)
    raise DeploymentError("public deployment check failed after " + str(attempts) +
                          " attempt(s): " + str(last))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--base-url", default=BASE)
    ap.add_argument("--attempts", type=int, default=1)
    ap.add_argument("--delay", type=float, default=3)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args(argv)
    try:
        record = verify(args.manifest, base=args.base_url,
                        attempts=args.attempts, delay=args.delay)
        encoded = json.dumps(record, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded)
        print(encoded, end="")
        return 0
    except (OSError, ValueError) as err:
        # The initial Pages publication may have succeeded even if public CDN
        # propagation or an individual asset did not. Write a truthful,
        # machine-readable failure receipt instead of losing all evidence.
        failure = {
            "protocol": PROTOCOL,
            "status": "NOT_VERIFIED",
            "public_site": BASE,
            "reason": str(err),
            "limitations": [
                "A failed public-byte observation does not reverse or establish Pages deployment.",
                "No public asset match or independent execution attestation is claimed."
            ],
        }
        if args.output:
            try:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(failure, sort_keys=True, indent=2) + "\n",
                                       encoding="utf-8")
            except OSError as output_error:
                print("FAILED_TO_SAVE_OBSERVATION: " + str(output_error), file=sys.stderr)
        print("NOT_VERIFIED: " + str(err), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
