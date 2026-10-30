#!/usr/bin/env python3
"""Offline consistency check for local Ada/Python build-and-run evidence.

Self-consistency and source/binary hashes are not external attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from build_and_compare_ada import (
    ROOT, HISTORICAL_SHA, LIMITATIONS, PROTOCOL, BUILD_COMMAND,
    SOURCES, SNAPSHOT,
)
from run_kernel_conformance import (
    SEED, RECEIPT, finite_cases, lexical_cases, rejected_cases,
)
from verify_kernel_receipt import InvalidReceipt, verify as verify_bridge
from verify_spark_evidence_archive import SOURCE_SHA, verify as verify_archive


class EvidenceError(ValueError):
    pass


def duplicate_safe(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_float(value):
    raise EvidenceError("non-integer or non-finite JSON literal")


def load_json(path: Path):
    if path.stat().st_size > 500_000:
        raise EvidenceError("runtime evidence file too large")
    try:
        return json.loads(path.read_text(encoding="utf-8"),
                          object_pairs_hook=duplicate_safe,
                          parse_constant=reject_float, parse_float=reject_float)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise EvidenceError("invalid runtime evidence JSON: " + str(error)) from error


def verify(document, root: Path = ROOT):
    fields = {
        "protocol", "status", "historical_source_commit", "source_sha256",
        "tool_versions", "build_command", "build_exit_code", "build_output",
        "build_output_sha256", "binary_sha256", "seed", "mode",
        "finite_cases_checked", "rejected_fixture_checked",
        "lexical_invalid_checked", "ada_processes_checked", "vectors_sha256",
        "python_bridge_receipt", "bridge_receipt_verification",
        "independent_execution_attestation", "limitations",
    }
    if type(document) is not dict or set(document) != fields:
        raise EvidenceError("unexpected local execution evidence schema")
    if (document["protocol"] != PROTOCOL
        or document["status"] != "LOCAL_BUILD_AND_DIFFERENTIAL_PASSED_UNATTESTED"
        or document["historical_source_commit"] != HISTORICAL_SHA
        or document["independent_execution_attestation"] is not False
        or document["limitations"] != LIMITATIONS):
        raise EvidenceError("runtime status or provenance inflated")
    if verify_archive(root)["archive_integrity"] != "PASS":
        raise EvidenceError("historical SPARK archive inconsistent")
    expected_hashes = {n: SOURCE_SHA[n] for n in SOURCES}
    if document["source_sha256"] != expected_hashes:
        raise EvidenceError("reported Ada build input digest mismatch")
    for name, expected in expected_hashes.items():
        path = root / SNAPSHOT / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise EvidenceError("historical Ada build input bytes differ: " + name)
    versions = document["tool_versions"]
    if (type(versions) is not dict or set(versions) != {"gprbuild", "gnatmake"}
        or any(type(x) is not str or len(x) < 5 or len(x) > 1000
               for x in versions.values())
        or not versions["gprbuild"].startswith("GPRBUILD ")
        or not versions["gnatmake"].startswith("GNATMAKE ")):
        raise EvidenceError("compiler version metadata inconsistent")
    if (document["build_command"] != BUILD_COMMAND
        or type(document["build_exit_code"]) is not int
        or document["build_exit_code"] != 0):
        raise EvidenceError("compiler build command or status mismatch")
    output = document["build_output"]
    if (type(output) is not str
        or len(output.encode("utf-8")) > 100_000
        or hashlib.sha256(output.encode("utf-8")).hexdigest()
           != document["build_output_sha256"]):
        raise EvidenceError("build log fingerprint mismatch")
    if type(document["seed"]) is not int or not 0 <= document["seed"] <= 0xffffffff:
        raise EvidenceError("runtime seed invalid")
    finite = len(list(finite_cases()))
    checked = document["finite_cases_checked"]
    if (type(checked) is not int or not 7 <= checked <= finite
        or document["mode"] not in ("SEEDED_SAMPLE", "FULL_FINITE_SET")
        or (document["mode"] == "FULL_FINITE_SET") != (checked == finite)):
        raise EvidenceError("finite-case mode or count inconsistent")
    neg, lex = len(rejected_cases()), len(lexical_cases())
    if (type(document["rejected_fixture_checked"]) is not int
        or document["rejected_fixture_checked"] != neg
        or type(document["lexical_invalid_checked"]) is not int
        or document["lexical_invalid_checked"] != lex
        or type(document["ada_processes_checked"]) is not int
        or document["ada_processes_checked"] != checked + neg + lex):
        raise EvidenceError("Ada invocation count inconsistent")
    for field in ("binary_sha256", "vectors_sha256"):
        if (type(document[field]) is not str
            or re.fullmatch("[0-9a-f]{64}", document[field]) is None):
            raise EvidenceError("missing binary/vector SHA-256: " + field)
    bridge = document["python_bridge_receipt"]
    if type(bridge) is not dict or set(bridge) != {
        "format", "algorithm", "sha256", "payload_text",
    } or bridge.get("format") != RECEIPT:
        raise EvidenceError("missing expected bridge receipt")
    try:
        result = verify_bridge(bridge)
    except InvalidReceipt as error:
        raise EvidenceError("underlying Python/Ada bridge receipt invalid: " + str(error)) from error
    if result["valid"] is not True or result["ada_status"] != "ADA_CLI_TESTED_UNATTESTED":
        raise EvidenceError("bridge receipt does not report Ada comparison")
    report = json.loads(bridge["payload_text"], object_pairs_hook=duplicate_safe)
    ada = report["evidence"]["ada_cli_conformance"]
    if (report["seed"] != document["seed"]
        or ada["cases"] != document["ada_processes_checked"]
        or ada["binary_sha256"] != document["binary_sha256"]
        or ada["vectors_sha256"] != document["vectors_sha256"]
        or report["evidence"]["python_conformance"]["finite_cases"] != finite
        or document["bridge_receipt_verification"] != "SELF_CONSISTENT_ONLY"):
        raise EvidenceError("bridge metadata contradicts build/run summary")
    return {
        "integrity": "PASS",
        "runtime_status": document["status"],
        "historical_source_commit": HISTORICAL_SHA,
        "cases": checked + neg + lex,
        "binary_sha256": document["binary_sha256"],
        "execution_attestation": "NOT_INDEPENDENTLY_ESTABLISHED",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify(load_json(args.record))
    except (OSError, UnicodeError, TypeError, EvidenceError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
