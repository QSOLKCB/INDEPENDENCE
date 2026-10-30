#!/usr/bin/env python3
"""Validate original uploaded runtime receipt bytes and their archive manifest.

Hashes and receipt integrity are not independent execution attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from verify_ada_runtime_evidence import verify as verify_runtime, load_json
from verify_spark_evidence_archive import verify as verify_spark
from verify_lean_evidence_archive import verify as verify_lean

ROOT = Path(__file__).resolve().parent.parent
FOLDER = Path("formal/evidence/ada-runtime/v0.7.4")
ZIP_SHA = "429b946d083c2b0562450704f924eb3370e5c9a9c62eb81ef5ac90d41a5e2256"
RECORDS = {
    "ada-runtime-evidence.json": (
        "78ce9e40d221634391a9cf6a982848521369efa0bd9926459ec028a649e87aa6",
        "7baab24fc65a12655288666272257cf655d5b9a6", 5118, 150, 128, "SEEDED_SAMPLE",
        "24155e14fd2727781648bcd43aff8f13f33b0753f9c2a0a07ecbdc19b28a5ea5",
        "554627bdd8813b6106624f5e435659fbabb5f9c5",
    ),
    "ada-runtime-evidence-full.json": (
        "3dff931e123f55f0b3e7e8f3a8247d381d06cfbbb1135dc3fb637b03eba80b0a",
        "242503aef78c6e73558a16a487abf80e098eadb5", 5123, 8903, 8881, "FULL_FINITE_SET",
        "2d0c6fb5763d637b7ce7ef6750ff68f9dac7e954b87ee6e49015bbabf5f256bf",
        "765e00d7f6a361b0ee3744157c2a35c9dfc7ae59",
    ),
}
SPARK_SHA = "cd3c4ec7986e391ab9627d69069142b86bdf60bc6f4e4aced1d8622093cd1eba"
LEAN_SHA = "ef3edf6cbfb7ac0b02ca6c30e3c9bfd3b21e89382f3ec0436f31093c5e4355a7"
BIN_SHA = "9d74484857e3937586003a0dea2a648704c58e039ad6812b8a75167b1169fddf"


class OriginalEvidenceError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def validate(root: Path = ROOT) -> dict:
    base = root / FOLDER
    manifest = load_json(base / "manifest.json")
    if type(manifest) is not dict or manifest.get("protocol") != "INDEPENDENCE-ORIGINAL-ADA-EVIDENCE/1":
        raise OriginalEvidenceError("original evidence protocol mismatch")
    package = manifest.get("package")
    if (type(package) is not dict or package.get("uploaded_name") != "INDEPENDENCE-proof-evidence.zip"
        or package.get("sha256") != ZIP_SHA or package.get("provided_checksum_file_match") is not True
        or package.get("zip_crc_validation") != "PASS"
        or package.get("zip_retained_in_git") is not False):
        raise OriginalEvidenceError("uploaded ZIP identity/claims mismatch")
    origin = manifest.get("provenance")
    if (type(origin) is not dict or origin.get("acquisition") != "DIRECT_USER_UPLOADED_ORIGINAL_ZIP"
        or origin.get("original_runtime_json_bytes") != "GIT_BLOBS_EXACTLY_MATCH_ZIP_ENTRIES"
        or origin.get("independently_attested_execution") is not False
        or origin.get("historical_gnatprove_source_commit") !=
            "9900e57f2283c534815657dd6c079d0e966715f4"):
        raise OriginalEvidenceError("uploaded receipt provenance mismatch")
    items = manifest.get("files")
    if type(items) is not list or len(items) != len(RECORDS):
        raise OriginalEvidenceError("runtime receipt inventory mismatch")
    seen = set()
    statuses = {}
    build_output_digests = set()
    specification_digests = set()
    for item in items:
        if type(item) is not dict or set(item) != {
            "path", "original_zip_member", "sha256", "git_blob_sha1",
            "size_bytes", "mode", "reported_ada_processes", "valid_finite_cases",
            "invalid_fixtures", "lexical_invalid", "vector_sha256", "reported_checkout"
        }:
            raise OriginalEvidenceError("unexpected evidence inventory entry")
        name = item["original_zip_member"]
        if name not in RECORDS or name in seen or item["path"] != (FOLDER / name).as_posix():
            raise OriginalEvidenceError("unexpected or duplicate runtime receipt")
        seen.add(name)
        checksum, blob, size, processes, valid, mode, vectors, checkout = RECORDS[name]
        expected_meta = (checksum, blob, size, processes, valid, mode, vectors, checkout)
        observed = tuple(item[k] for k in (
            "sha256", "git_blob_sha1", "size_bytes", "reported_ada_processes",
            "valid_finite_cases", "mode", "vector_sha256", "reported_checkout"
        ))
        if (observed != expected_meta or any(type(item[k]) is not int for k in
            ("size_bytes", "reported_ada_processes", "valid_finite_cases",
             "invalid_fixtures", "lexical_invalid"))
            or item["invalid_fixtures"] != 16 or item["lexical_invalid"] != 6):
            raise OriginalEvidenceError("runtime receipt manifest contradicts pinned bytes")
        raw = (base / name).read_bytes()
        if len(raw) != size or sha256(raw) != checksum or git_blob(raw) != blob:
            raise OriginalEvidenceError("original runtime receipt bytes changed: " + name)
        document = load_json(base / name)
        receipt = verify_runtime(document, root)
        if (receipt["integrity"] != "PASS" or receipt["cases"] != processes
            or receipt["binary_sha256"] != BIN_SHA
            or document["mode"] != mode or document["vectors_sha256"] != vectors
            or document["independent_execution_attestation"] is not False):
            raise OriginalEvidenceError("runtime receipt result contradiction: " + name)
        # The original receipts have already passed their strict runtime
        # integrity check. Keep the two independently recorded digest types
        # for comparison with the publication manifest below.
        build_output_digests.add(document["build_output_sha256"])
        bridge_payload = json.loads(document["python_bridge_receipt"]["payload_text"])
        specification_digests.add(bridge_payload["spec_sha256"])
        statuses[name] = processes
    if set(RECORDS) != seen:
        raise OriginalEvidenceError("runtime receipt missing")
    old = manifest.get("existing_records")
    if type(old) is not list or len(old) != 2:
        raise OriginalEvidenceError("referenced old proof inventory mismatch")
    for record in old:
        if type(record) is not dict or "path" not in record or "sha256" not in record:
            raise OriginalEvidenceError("invalid older proof reference")
        path = record["path"]
        if path == "formal/evidence/spark/pr13/spark-evidence.json":
            if record["sha256"] != SPARK_SHA or record.get("original_zip_bytes_match_existing_git") is not True:
                raise OriginalEvidenceError("SPARK original bytes claim mismatched")
        elif path == "formal/evidence/lean/v0.7.3/lean-evidence.json":
            if record["sha256"] != LEAN_SHA or record.get("original_file_provenance") != "ALREADY_ARCHIVED_TRANSCRIPT_RECONSTRUCTION":
                raise OriginalEvidenceError("Lean reconstructed-file provenance modified")
        else:
            raise OriginalEvidenceError("unexpected older proof source")
        if sha256((root / path).read_bytes()) != record["sha256"]:
            raise OriginalEvidenceError("older proof source bytes changed")
    if (verify_spark(root)["archive_integrity"] != "PASS"
        or verify_lean(root)["archive_integrity"] != "PASS"):
        raise OriginalEvidenceError("historical proof archive check failed")
    checks = manifest.get("comparison")
    if (type(checks) is not dict or set(checks) != {
            "compiled_binary_sha256_in_both", "compiler_build_output_sha256",
            "source_spec_sha256", "reported_python_unit_tests"
        } or checks["compiled_binary_sha256_in_both"] != BIN_SHA
        or type(checks["reported_python_unit_tests"]) is not int
        or checks["reported_python_unit_tests"] != 233
        # Require agreement across BOTH separately preserved source receipts;
        # a single matching receipt must not conceal a contradictory peer.
        or len(build_output_digests) != 1
        or checks["compiler_build_output_sha256"] not in build_output_digests
        or len(specification_digests) != 1
        or checks["source_spec_sha256"] not in specification_digests):
        raise OriginalEvidenceError("cross-record comparison claims mismatch")
    if (type(manifest.get("limitations")) is not list
        or not any("not independently attested" in x.lower() for x in manifest["limitations"])):
        raise OriginalEvidenceError("missing provenance limitation")
    return {
        "archive_integrity": "PASS",
        "original_receipts": "EXACT_BYTE_MATCH",
        "sample_ada_cases": statuses["ada-runtime-evidence.json"],
        "full_ada_cases": statuses["ada-runtime-evidence-full.json"],
        "original_zip_sha256": ZIP_SHA,
        "binary_sha256": BIN_SHA,
        "independent_execution_attestation": "NOT_ESTABLISHED",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
