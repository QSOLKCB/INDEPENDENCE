#!/usr/bin/env python3
"""Verify recovered Lean evidence archive integrity, not independent execution.

Requires only the Python standard library. This does not invoke Lean.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
FOLDER = Path("formal/evidence/lean/v0.7.3")
SOURCE_COMMIT = "68351489e8bbbb879efdcac19d02869124fcf724"
SOURCE_SHA256 = "0a71bba7fa1d8e81a73051c9c5e508126ba97242bf88537d2e55779019e2756d"
EVIDENCE_SHA256 = "ef3edf6cbfb7ac0b02ca6c30e3c9bfd3b21e89382f3ec0436f31093c5e4355a7"
PIN = "leanprover/lean4:v4.35.0"
THEOREMS = (
    "crt_left_inverse", "crt_right_inverse",
    "gf2_add_comm", "gf2_add_assoc", "gf2_add_self",
    "gf2_mul_comm", "gf2_left_distrib",
    "phase_add_comm", "phase_add_assoc", "phase_zero",
    "monomial_irrefl", "monomial_trans", "monomial_translate",
)
ALLOWED = {"propext", "Quot.sound", "Classical.choice"}


class ArchiveError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ArchiveError("duplicate JSON key: " + key)
        obj[key] = value
    return obj


def reject_float(text):
    raise ArchiveError("noninteger numeric literal")


def reject_constant(text):
    raise ArchiveError("nonfinite JSON number")


def load_json(data: bytes):
    if len(data) > 100_000:
        raise ArchiveError("oversized JSON")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs,
                          parse_float=reject_float, parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ArchiveError("invalid JSON: " + str(error)) from error


def verify(root: Path = ROOT) -> dict:
    folder = root / FOLDER
    manifest = load_json((folder / "manifest.json").read_bytes())
    report_bytes = (folder / "lean-evidence.json").read_bytes()
    report = load_json(report_bytes)
    source_bytes = (folder / "FiniteFoundation.lean").read_bytes()
    toolchain = (folder / "lean-toolchain").read_bytes()

    if manifest.get("protocol") != "INDEPENDENCE-LEAN-EVIDENCE-ARCHIVE/1":
        raise ArchiveError("archive protocol mismatch")
    if manifest.get("evidence_origin") != "USER_SHARED_TERMINAL_TRANSCRIPT" or (
        manifest.get("independently_attested_execution") is not False
    ):
        raise ArchiveError("unsupported provenance claim")
    if manifest.get("evidence_provenance") != "RECOVERED_COMPLETE_JSON_FROM_TERMINAL_OUTPUT_NOT_ORIGINAL_FILE_UPLOAD":
        raise ArchiveError("original-file provenance claim mismatch")

    src = manifest.get("source", {})
    if src.get("repository") != "QSOLKCB/INDEPENDENCE" or (
        src.get("git_commit") != SOURCE_COMMIT or
        src.get("file") != "formal/lean/FiniteFoundation.lean" or
        src.get("sha256") != SOURCE_SHA256
    ):
        raise ArchiveError("source Git revision or digest mismatch")
    artifact = manifest.get("artifact", {})
    if (artifact.get("path") != (FOLDER / "lean-evidence.json").as_posix() or
        artifact.get("sha256") != EVIDENCE_SHA256 or
        artifact.get("original_file_byte_identity") != "NOT_INDEPENDENTLY_CONFIRMED"):
        raise ArchiveError("evidence provenance/hash metadata mismatch")
    if sha(report_bytes) != EVIDENCE_SHA256:
        raise ArchiveError("recovered evidence bytes changed")
    snapshot = manifest.get("source_snapshot", {})
    if (snapshot.get("path") != (FOLDER / "FiniteFoundation.lean").as_posix()
        or snapshot.get("sha256") != SOURCE_SHA256
        or sha(source_bytes) != SOURCE_SHA256):
        raise ArchiveError("historical Lean source changed")
    tc = manifest.get("toolchain", {})
    tool_snapshot = manifest.get("toolchain_snapshot", {})
    if (toolchain != (PIN + "\n").encode("ascii")
        or tc.get("pinned_value") != PIN
        or tc.get("file") != "lean-toolchain"
        or tool_snapshot.get("path") != (FOLDER / "lean-toolchain").as_posix()
        or tool_snapshot.get("sha256") != sha(toolchain)):
        raise ArchiveError("toolchain pin mismatch")
    if (report.get("source") != "formal/lean/FiniteFoundation.lean"
        or report.get("source_sha256") != SOURCE_SHA256
        or report.get("toolchain") != PIN
        or report.get("tool_version") != tc.get("reported_version")
        or not str(report.get("tool_version", "")).startswith("Lean (version 4.35.0,")
        or report.get("command") != ["lean", "--trust=0", "formal/lean/FiniteFoundation.lean"]
        or report.get("kernel_check") != "KERNEL_CHECKED"
        or type(report.get("exit_code")) is not int or report["exit_code"] != 0):
        raise ArchiveError("reported kernel evidence inconsistent")
    if report.get("theorems_declared") != list(THEOREMS):
        raise ArchiveError("theorem inventory mismatch")
    audit = report.get("axiom_audit")
    if (type(audit) is not dict or set(audit) != set(THEOREMS)
        or any(type(v) is not list or any(type(a) is not str or a not in ALLOWED for a in v)
               for v in audit.values())):
        raise ArchiveError("disallowed or missing axioms")
    output = report.get("raw_output")
    if type(output) is not str or (
        sha(output.encode("utf-8")) != report.get("raw_output_sha256")
        or report["raw_output_sha256"] != artifact.get("raw_lean_output_sha256")
    ):
        raise ArchiveError("raw Lean output hash mismatch")
    for theorem in THEOREMS:
        name = "IndependenceLean." + theorem
        if audit[theorem]:
            expected_line = "'" + name + "' depends on axioms: [" + ", ".join(audit[theorem]) + "]"
        else:
            expected_line = "'" + name + "' does not depend on any axioms"
        if output.splitlines().count(expected_line) != 1:
            raise ArchiveError("axiom audit log differs from JSON: " + theorem)
    # A publication manifest must not contradict the pinned evidence it
    # summarizes. Enforce every check field, the exact schema, and exact types:
    # Python bool compares equal to 0/1 unless checked explicitly.
    checks = manifest.get("checks")
    expected_keys = {
        "python_unittest_reported", "lean_kernel_reported",
        "lean_exit_code_reported", "theorems_declared", "axiom_audits",
        "unapproved_axioms_reported",
    }
    if type(checks) is not dict or set(checks) != expected_keys:
        raise ArchiveError("manifest checks schema mismatch")
    tests = checks["python_unittest_reported"]
    if (type(tests) is not dict or set(tests) != {"ran", "failed"}
        or type(tests["ran"]) is not int or tests["ran"] != 169
        or type(tests["failed"]) is not int or tests["failed"] != 0):
        raise ArchiveError("reported unittest metadata changed")
    lean_expected = {
        "lean_kernel_reported": report["kernel_check"],
        "lean_exit_code_reported": report["exit_code"],
        "theorems_declared": len(report["theorems_declared"]),
        "axiom_audits": len(audit),
        "unapproved_axioms_reported": sum(
            axiom not in ALLOWED for values in audit.values() for axiom in values
        ),
    }
    for name, expected in lean_expected.items():
        actual = checks[name]
        if type(actual) is not type(expected) or actual != expected:
            raise ArchiveError("manifest Lean result mismatch: " + name)
    return {
        "archive_integrity": "PASS",
        "source_commit": SOURCE_COMMIT,
        "source_sha256": SOURCE_SHA256,
        "evidence_sha256": EVIDENCE_SHA256,
        "theorem_audits": len(THEOREMS),
        "reported_kernel_check": "KERNEL_CHECKED",
        "execution_attestation": "NOT_INDEPENDENTLY_VERIFIED",
        "original_file_byte_identity": "NOT_INDEPENDENTLY_CONFIRMED",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    try:
        result = verify(args.root)
    except (OSError, ArchiveError, UnicodeError, TypeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
