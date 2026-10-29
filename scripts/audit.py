#!/usr/bin/env python3
"""Deterministic stdlib-only audit for this repository's web deployment.

Scope: first-party web files and dependency-manifest detection within this repo.
Not a vulnerability scanner, GitHub organisation-wide audit, or proof of zero risk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

WEB_FILES = ("index.html", "styles.css", "app.js", "lab/core.js", "lab/tests.js")
FORBIDDEN_MANIFESTS = frozenset({
    "package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
    "pnpm-lock.yaml", "bun.lock", "bun.lockb", "requirements.txt",
    "requirements-dev.txt", "Pipfile", "Pipfile.lock", "poetry.lock",
    "uv.lock", "pyproject.toml", "setup.py", "composer.json", "composer.lock",
    "Gemfile", "Gemfile.lock", "Cargo.toml", "Cargo.lock",
})
IGNORED_DIRS = frozenset({".git", "__pycache__", ".mypy_cache", ".pytest_cache"})
REMOTE_LOADS = (
    ("remote_script", re.compile(r'<script\b[^>]*\bsrc\s*=\s*["\x27]https?://', re.I)),
    ("remote_stylesheet", re.compile(r'<link\b(?=[^>]*\brel\s*=\s*["\x27]stylesheet)(?=[^>]*\bhref\s*=\s*["\x27]https?://)[^>]*>', re.I)),
    ("css_import", re.compile(r'@import\s+(?:url\s*\(\s*)?["\x27]?https?://', re.I)),
    ("remote_css_url", re.compile(r'url\s*\(\s*["\x27]?https?://', re.I)),
    ("remote_js_import", re.compile(r'\bimport\s*(?:\(\s*|[^;\n]*?\bfrom\s*)?["\x27]https?://', re.I)),
    ("remote_js_fetch", re.compile(r'\bfetch\s*\(\s*["\x27]https?://', re.I)),
)
SCHEMA_VERSION = 1


def audit(root: Path) -> dict:
    root = root.resolve()
    findings = []
    hashes = {}
    inspected = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(p in IGNORED_DIRS for p in path.relative_to(root).parts):
            continue
        inspected += 1
        relative = path.relative_to(root).as_posix()
        if path.name in FORBIDDEN_MANIFESTS:
            findings.append({"path": relative, "kind": "third_party_manifest"})
        if "node_modules" in path.relative_to(root).parts or ".venv" in path.relative_to(root).parts:
            findings.append({"path": relative, "kind": "vendored_dependency_directory"})
    for relative in WEB_FILES:
        path = root / relative
        if not path.is_file():
            findings.append({"path": relative, "kind": "missing_web_asset"})
            continue
        content = path.read_bytes()
        hashes[relative] = hashlib.sha256(content).hexdigest()
        source = content.decode("utf-8")
        for kind, pattern in REMOTE_LOADS:
            if pattern.search(source):
                findings.append({"path": relative, "kind": kind})
    return {
        "schema_version": SCHEMA_VERSION,
        "scope": "this repository; selected deployed browser assets; manifest filenames",
        "policy": "no third-party package manifests or remotely loaded executable web assets",
        "web_assets_sha256": dict(sorted(hashes.items())),
        "files_inspected": inspected,
        "findings": sorted(findings, key=lambda row: (row["path"], row["kind"])),
        "passed": not findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true", help="machine-readable deterministic JSON")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root)
    except (OSError, UnicodeError) as error:
        print("Audit could not complete: " + str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print("PASS" if report["passed"] else "FAIL", "-", report["files_inspected"], "files scanned")
        for finding in report["findings"]:
            print(finding["kind"] + ": " + finding["path"])
        print("Scope:", report["scope"])
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
