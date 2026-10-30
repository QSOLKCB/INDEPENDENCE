#!/usr/bin/env python3
"""Offline integrity checks for v0.9 proof/runtime tool reports; no remote attestation."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from check_automata_formal import (
    ROOT, PROTOCOL, THEOREMS, PIN, ALLOWED_AXIOMS, inspect, NEGATIVES,
    vectors_digest, vectors,
)

MAX_SIZE = 250_000
LEAN_CMD = ["lean", "--trust=0", "formal/lean/AutomataReference.lean"]
SPARK_CMD = ["gnatprove", "-P", "automata.gpr", "-u",
             "automata_reference.adb", "--mode=all", "--checks-as-errors=on",
             "--warnings=error", "--report=all", "--level=2"]
ADA_CMD = ["gprbuild", "-P", "automata_cli.gpr", "-p", "-f"]
JS_CMD = ["node", "--experimental-default-type=module", "scripts/check_automata_js.mjs"]


class ReceiptError(ValueError):
    pass


def reject_pairs(pairs):
    obj = {}
    for k, v in pairs:
        if k in obj:
            raise ReceiptError("duplicate JSON key: " + k)
        obj[k] = v
    return obj


def reject_float(value):
    raise ReceiptError("floating/nonfinite JSON number not allowed")


def strict_json(payload: str):
    try:
        return json.loads(payload, object_pairs_hook=reject_pairs,
                          parse_float=reject_float, parse_constant=reject_float)
    except (ValueError, RecursionError, UnicodeError) as e:
        raise ReceiptError("invalid evidence JSON: " + str(e)) from e


def exact(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def validate_log(raw, checksum):
    if (type(raw) is not str or type(checksum) is not str
        or hashlib.sha256(raw.encode("utf-8")).hexdigest() != checksum):
        raise ReceiptError("tool output SHA-256 inconsistent")


def verify(report: dict, root: Path = ROOT):
    expected = inspect(root)
    if type(report) is not dict or set(report) != set(expected):
        raise ReceiptError("unexpected report schema")
    for field in expected:
        if field not in ("lean", "spark", "ada", "javascript") and not exact(report[field], expected[field]):
            raise ReceiptError("reported specification, corpus or evidence limits differ: " + field)
    for field in ("lean", "spark", "ada", "javascript"):
        if type(report[field]) is not dict or "status" not in report[field]:
            raise ReceiptError("missing optional stage status: " + field)
        status = report[field]["status"]
        if status == "NOT_RUN":
            if not isinstance(report[field].get("reason", ""), str) or set(report[field]) - {"status", "reason"}:
                raise ReceiptError("NOT_RUN stage fabricates execution information")
            continue
        if field == "lean":
            if status != "KERNEL_CHECKED" or set(report[field]) != {
                    "status", "tool_version", "command", "exit_code",
                    "axiom_audit", "raw_output", "raw_output_sha256"}:
                raise ReceiptError("unapproved Lean status/schema")
            x = report[field]
            if (type(x["tool_version"]) is not str
                or re.search(r"\bLean\s+\(version\s+4\.35\.0[,)]", x["tool_version"]) is None
                or x["command"] != LEAN_CMD or type(x["exit_code"]) is not int
                or x["exit_code"] != 0 or type(x["axiom_audit"]) is not dict
                or set(x["axiom_audit"]) != set(THEOREMS)
                or any(type(a) is not list or any(y not in ALLOWED_AXIOMS for y in a)
                       for a in x["axiom_audit"].values())):
                raise ReceiptError("Lean proof audit or toolchain mismatch")
            validate_log(x["raw_output"], x["raw_output_sha256"])
            for theorem, axioms in x["axiom_audit"].items():
                key = "IndependenceAutomata." + theorem
                if axioms:
                    snippet = "'" + key + "' depends on axioms:"
                    if snippet not in x["raw_output"]:
                        raise ReceiptError("Lean axiom report missing")
                elif "'" + key + "' does not depend on any axioms" not in x["raw_output"]:
                    raise ReceiptError("Lean empty axiom report missing")
        elif field == "spark":
            x = report[field]
            if status != "GNATPROVE_REPORTED_DISCHARGED" or set(x) != {
                "status", "tool_version", "command", "exit_code", "checks",
                "raw_output", "raw_output_sha256"
            } or x["command"] != SPARK_CMD or type(x["exit_code"]) is not int or x["exit_code"] != 0:
                raise ReceiptError("unapproved GNATprove status/schema")
            if (type(x["checks"]) is not int or x["checks"] < 1
                or type(x["tool_version"]) is not str or not x["tool_version"]):
                raise ReceiptError("invalid GNATprove check count or version")
            validate_log(x["raw_output"], x["raw_output_sha256"])
            match = re.search(r"Success:\s+all checks proved\s+\(([1-9][0-9]*) checks\)\.", x["raw_output"])
            if (not match or int(match.group(1)) != x["checks"]
                or re.search(r"\b(unproved|not proved|skipped|assumed)\b", x["raw_output"], re.I)):
                raise ReceiptError("GNATprove raw output does not discharge claimed checks")
        elif field == "ada":
            x = report[field]
            if status != "LOCAL_ADA_FINITE_EXECUTED_UNATTESTED" or set(x) != {
                "status", "command", "build_exit_code", "build_output",
                "build_output_sha256", "binary_sha256", "cases",
                "invalid_cases", "vectors_sha256"
            } or x["command"] != ADA_CMD or type(x["build_exit_code"]) is not int or x["build_exit_code"] != 0:
                raise ReceiptError("unapproved compiled Ada evidence")
            if (type(x["cases"]) is not int or x["cases"] != 4096
                or type(x["invalid_cases"]) is not int or x["invalid_cases"] != len(NEGATIVES)
                or x["vectors_sha256"] != expected["vectors_sha256"]
                or type(x["binary_sha256"]) is not str
                or re.fullmatch("[0-9a-f]{64}", x["binary_sha256"]) is None):
                raise ReceiptError("Ada corpus count or hashes contradict reference")
            validate_log(x["build_output"], x["build_output_sha256"])
        elif field == "javascript":
            x = report[field]
            if status != "LOCAL_JS_FINITE_EXECUTED" or set(x) != {
                "status", "protocol", "cases", "vectors_sha256",
                "limitation", "command", "tool_version", "independent_execution_attestation"
            } or x["command"] != JS_CMD:
                raise ReceiptError("unapproved JavaScript evidence")
            if (x["protocol"] != "AUTOMATA4-JS-EVIDENCE/1"
                or type(x["cases"]) is not int or x["cases"] != 4096
                or x["vectors_sha256"] != expected["vectors_sha256"]
                or x["independent_execution_attestation"] is not False
                or x["limitation"] != "Developer Node runtime executed production evolve; no Lean/Ada proof or browser attestation."):
                raise ReceiptError("JavaScript corpus or provenance differs")
    return {
        "archive_integrity": "PASS",
        "reference_cases": 4096,
        "lean_status": report["lean"]["status"],
        "spark_status": report["spark"]["status"],
        "ada_status": report["ada"]["status"],
        "javascript_status": report["javascript"]["status"],
        "execution_attestation": "NOT_INDEPENDENTLY_ESTABLISHED",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.evidence.stat().st_size > MAX_SIZE:
            raise ReceiptError("evidence report exceeds size cap")
        result = verify(strict_json(args.evidence.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as e:
        print("FAIL: " + str(e), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
