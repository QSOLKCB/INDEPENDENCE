#!/usr/bin/env python3
"""Select the exact published manifest with independent-artifact precedence.

No network calls. The separately preserved manifest is authoritative when
present; a Pages artifact.tar serves only as a historical fallback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tarfile

from site_bundle import MANIFEST, envelope, parse_manifest

PROTOCOL = "GITHUB-PAGES-OBSERVATION/1"
MAX_MANIFEST = 20_000


class SelectionError(ValueError):
    pass


def checked(raw: bytes) -> bytes:
    manifest = parse_manifest(raw)
    try:
        expected = envelope(manifest["files"], manifest["revision"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SelectionError("invalid published manifest fields") from exc
    if manifest != expected:
        raise SelectionError("published manifest failed exact schema/checksum validation")
    return raw


def from_archive(archive: Path) -> bytes:
    if archive.is_symlink() or not archive.is_file():
        raise SelectionError("legacy Pages archive unavailable")
    try:
        with tarfile.open(archive, "r:*") as container:
            matches = [m for m in container.getmembers()
                       if m.name in (MANIFEST, "./" + MANIFEST)]
            if len(matches) != 1:
                raise SelectionError("historical archive missing or duplicating manifest")
            member = matches[0]
            if not member.isfile() or member.size <= 0 or member.size > MAX_MANIFEST:
                raise SelectionError("invalid or unsafe manifest member")
            stream = container.extractfile(member)
            if stream is None:
                raise SelectionError("could not read manifest member")
            with stream:
                raw = stream.read(MAX_MANIFEST + 1)
            if len(raw) != member.size:
                raise SelectionError("truncated manifest member")
            return checked(raw)
    except (OSError, tarfile.TarError, EOFError) as exc:
        raise SelectionError("unreadable historical Pages archive") from exc


def select(preferred: Path, legacy_tar: Path, output: Path) -> str:
    if preferred.is_symlink():
        raise SelectionError("symlink preferred manifest refused")
    if preferred.exists():
        # Never fall back from a corrupt downloaded primary manifest.
        if not preferred.is_file() or preferred.stat().st_size > MAX_MANIFEST:
            raise SelectionError("preferred manifest invalid or oversized")
        raw = checked(preferred.read_bytes())
        source = "independence-pages-manifest"
    else:
        raw = from_archive(legacy_tar)
        source = "historical-github-pages-artifact"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    if output.read_bytes() != raw:
        raise SelectionError("selected output did not preserve exact bytes")
    return source


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preferred", required=True, type=Path)
    p.add_argument("--legacy-tar", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--failure-output", required=True, type=Path)
    args = p.parse_args(argv)
    try:
        source = select(args.preferred, args.legacy_tar, args.output)
        print(json.dumps({"source": source, "status": "MANIFEST_INTEGRITY_VERIFIED_UNATTESTED"},
                         sort_keys=True))
        return 0
    except (OSError, ValueError, UnicodeError, tarfile.TarError) as exc:
        report = {
            "protocol": PROTOCOL, "stage": "MANIFEST_SELECTION",
            "status": "NOT_VERIFIED",
            "reason": str(exc),
            "verified_public_assets": 0,
            "limitations": ["No public byte match or execution attestation is claimed."]
        }
        try:
            args.failure_output.parent.mkdir(parents=True, exist_ok=True)
            args.failure_output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                           encoding="utf-8")
        except OSError as output_exc:
            print("Unable to save NOT_VERIFIED evidence: " + str(output_exc), file=sys.stderr)
        print("NOT_VERIFIED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
