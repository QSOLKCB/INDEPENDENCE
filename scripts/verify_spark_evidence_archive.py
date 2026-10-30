#!/usr/bin/env python3
"""Offline integrity check for user-reported SPARK results, NOT independent proof execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
FOLDER = Path("formal/evidence/spark/pr13")
PROTOCOL = "INDEPENDENCE-SPARK-EVIDENCE-ARCHIVE/1"
BASE_SHA = "9900e57f2283c534815657dd6c079d0e966715f4"
MERGE_SHA = "e52578ee630d619b7c0aa54b47ef05f997f80741"
OUTPUT_SHA = "834ff4418b98e36e011900c7c5a6897776d2db5f12d7874011a64a474a268fab"
SOURCE_SHA = {
    "cli.gpr": "b92a85e592d792c740e1b16d9a01c3b441a83cdb5d6420e240c993f1a97e8309",
    "kernel.gpr": "bd71f6edab8d5f2ff97c686f3c72600e532d28c25c8c07f982879f2b2ca7f312",
    "reference_cli.adb": "937c51b184e8173f90dd71d0df80797c25f3a88b20ea86910f1ee179c483d83a",
    "reference_kernel.adb": "22cb09b6df9e0b5a93406e6746b895205e7b465381ebcd4d61d267b6cf289334",
    "reference_kernel.ads": "a1569a35c2e924243f8d9cc2a3c83a83391e263f1c38a5a280f1b056984408fe",
}
COMMAND = [
    "gnatprove", "-P", "kernel.gpr", "-u", "reference_kernel.adb",
    "--mode=all", "--checks-as-errors=on", "--warnings=error",
    "--report=all", "--level=2",
]
TOOL_VERSION = """FSF 16.1.0
Why3 for gnatprove version 1.8.2+git
/home/trent/opt/edgewalk-spark-toolchain/libexec/spark/bin/alt-ergo: Alt-Ergo version 2.6.1
/home/trent/opt/edgewalk-spark-toolchain/libexec/spark/bin/cvc5: This is cvc5 version 1.3.2 [git 86cecd8 on branch HEAD]
/home/trent/opt/edgewalk-spark-toolchain/libexec/spark/bin/z3: Z3 version 4.15.4 - 64 bit"""
LIMITATIONS = [
    "The JSON is reconstructed from a user-provided terminal transcript; byte-identical provenance to the original local spark-evidence.json is not independently established.",
    "The 21 discharged checks are GNATprove's reported Ada reference-kernel result; the CLI boundary and production Python/JavaScript remain outside the proof.",
    "The transcript reports 186 Python unittests passed; it is not a separately signed or independently authenticated CI run.",
    "The evidence receipt hashes confirm consistency with reported bytes, not independent execution attestation.",
]
REPORT_KEYS = {
    "ada_contracts", "command", "exit_code", "files_sha256", "note",
    "proof_output", "proof_output_sha256", "spec", "static_contracts", "tool_version",
}
MANIFEST_KEYS = {
    "protocol", "evidence_origin", "evidence_provenance", "original_file_byte_identity",
    "execution_attested_independently", "reported_execution_local_date",
    "reported_checkout", "corresponding_merge_commit", "reported_python_unittest",
    "gnatprove", "source_hashes_sha256", "evidence_file", "limitations",
    "historical_source_snapshot",
}


class EvidenceError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError("duplicate JSON key: " + key)
        value[key] = item
    return value


def reject_number(value):
    raise EvidenceError("noninteger/overflow numeric field: " + value)


def read_json(path: Path):
    raw = path.read_bytes()
    if len(raw) > 100_000:
        raise EvidenceError("oversized archive JSON")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=strict_pairs,
                          parse_float=reject_number, parse_constant=reject_number)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise EvidenceError("invalid archive JSON: " + str(error)) from error


def verify(root: Path = ROOT):
    directory = root / FOLDER
    report = read_json(directory / "spark-evidence.json")
    manifest = read_json(directory / "manifest.json")
    if type(report) is not dict or set(report) != REPORT_KEYS:
        raise EvidenceError("unexpected proof report schema")
    if type(manifest) is not dict or set(manifest) != MANIFEST_KEYS:
        raise EvidenceError("unexpected manifest schema")
    if (manifest["protocol"] != PROTOCOL
        or manifest["evidence_origin"] != "USER_SUPPLIED_TERMINAL_TRANSCRIPT"
        or manifest["evidence_provenance"] != "JSON_RECONSTRUCTED_FROM_PASTED_TERMINAL_REPORT"
        or manifest["original_file_byte_identity"] != "NOT_INDEPENDENTLY_CONFIRMED"
        or manifest["execution_attested_independently"] is not False):
        raise EvidenceError("unsupported evidence provenance claim")
    if manifest["reported_checkout"] != {
        "repository": "QSOLKCB/INDEPENDENCE", "git_sha": BASE_SHA,
        "ref": "refs/pull/13/head",
    } or manifest["corresponding_merge_commit"] != MERGE_SHA:
        raise EvidenceError("incorrect PR-head or merge-commit provenance")
    tests = manifest["reported_python_unittest"]
    if (type(tests) is not dict or set(tests) != {"total", "passed", "failed"}
        or any(type(tests[key]) is not int for key in tests)
        or tests != {"total": 186, "passed": 186, "failed": 0}):
        raise EvidenceError("reported Python test summary mismatch")
    if (report["ada_contracts"] != "GNATPROVE_REPORTED_DISCHARGED"
        or type(report["exit_code"]) is not int or report["exit_code"] != 0
        or report["command"] != COMMAND
        or report["spec"] != "INDEPENDENCE-KERNEL-SPEC/1"
        or report["static_contracts"] != "INSPECTED_ONLY"
        or report["note"] != "Only the analyzed kernel and stated assumptions are in scope"):
        raise EvidenceError("GNATprove result status, command or scope mismatch")
    output = report["proof_output"]
    if (type(output) is not str
        or digest(output.encode("utf-8")) != OUTPUT_SHA
        or report["proof_output_sha256"] != OUTPUT_SHA
        or "Success: all checks proved (21 checks)." not in output
        or len(re.findall(r"^ info:", output, flags=re.M)) != 21):
        raise EvidenceError("reported proof-output digest or 21-check summary mismatch")
    version = report["tool_version"]
    if type(version) is not str or version != TOOL_VERSION:
        raise EvidenceError("GNATprove toolchain version mismatch")
    if type(report["files_sha256"]) is not dict or report["files_sha256"] != SOURCE_SHA:
        raise EvidenceError("reported source hash inventory mismatch")
    snapshot = manifest["historical_source_snapshot"]
    expected_source_dir = (FOLDER / "source").as_posix()
    if (type(snapshot) is not dict or set(snapshot) != {
        "path", "files", "hashes_sha256", "spec_snapshot_path",
        "spec_git_blob_sha1", "source_checkout_git_sha",
    } or snapshot["path"] != expected_source_dir
        or snapshot["files"] != list(SOURCE_SHA)
        or snapshot["hashes_sha256"] != SOURCE_SHA
        or snapshot["source_checkout_git_sha"] != BASE_SHA
        or snapshot["spec_snapshot_path"] != (FOLDER / "source/kernel-v1.json").as_posix()
        or snapshot["spec_git_blob_sha1"] != "aebdb9ca058b27adb71264b74a87cfafac0b8310"):
        raise EvidenceError("historical SPARK source snapshot metadata mismatch")
    for relative, expected in SOURCE_SHA.items():
        path = directory / "source" / relative
        if digest(path.read_bytes()) != expected:
            raise EvidenceError("historical SPARK source bytes differ from reported proof checkout: " + relative)
    spec_bytes = (directory / "source" / "kernel-v1.json").read_bytes()
    git_blob = b"blob " + str(len(spec_bytes)).encode("ascii") + b"\0" + spec_bytes
    if hashlib.sha1(git_blob).hexdigest() != snapshot["spec_git_blob_sha1"]:
        raise EvidenceError("historical kernel specification Git blob mismatch")
    tool = manifest["gnatprove"]
    if (type(tool) is not dict or set(tool) != {
        "status", "reported_checks_proved", "exit_code", "tool_version", "command",
        "proof_output_sha256",
    } or tool["status"] != report["ada_contracts"]
        or type(tool["reported_checks_proved"]) is not int or tool["reported_checks_proved"] != 21
        or type(tool["exit_code"]) is not int or tool["exit_code"] != report["exit_code"]
        or tool["tool_version"] != version or tool["command"] != COMMAND
        or tool["proof_output_sha256"] != OUTPUT_SHA
        or manifest["source_hashes_sha256"] != SOURCE_SHA
        or manifest["evidence_file"] != (FOLDER / "spark-evidence.json").as_posix()):
        raise EvidenceError("GNATprove manifest contradicts reported proof result")
    if (manifest["reported_execution_local_date"] != "2026-10-31"
        or type(manifest["limitations"]) is not list
        or manifest["limitations"] != LIMITATIONS):
        raise EvidenceError("manifest date or limitations mismatch")
    return {
        "archive_integrity": "PASS",
        "reported_python_tests": 186,
        "reported_spark_checks_proved": 21,
        "reported_gnatprove_status": report["ada_contracts"],
        "historical_checkout": BASE_SHA,
        "proof_output_sha256": OUTPUT_SHA,
        "independent_execution_attestation": "NOT_ESTABLISHED",
        "original_json_byte_identity": "NOT_INDEPENDENTLY_CONFIRMED",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = verify(args.root)
    except (OSError, UnicodeError, TypeError, EvidenceError, RecursionError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
