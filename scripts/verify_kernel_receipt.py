#!/usr/bin/env python3
"""Validate v0.7.2 receipt bytes and fixture-consistency, NOT external attestation."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from run_kernel_conformance import (BRIDGE, RECEIPT, build_report,
    finite_cases, rejected_cases, lexical_cases, oracle, sample_ada_cases)


class InvalidReceipt(ValueError):
    pass


def unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InvalidReceipt("duplicate property: " + key)
        obj[key] = value
    return obj


def finite_float(value):
    v = float(value)
    if not math.isfinite(v):
        raise InvalidReceipt("numeric overflow")
    return v


def constant(value):
    raise InvalidReceipt("nonfinite JSON constant")


def strict_json(text):
    try:
        return json.loads(text, object_pairs_hook=unique_pairs,
                          parse_float=finite_float, parse_constant=constant)
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise InvalidReceipt("invalid JSON: " + str(error)) from error


def strict_equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return a.keys() == b.keys() and all(strict_equal(a[k], v) for k, v in b.items())
    if type(a) is list:
        return len(a) == len(b) and all(strict_equal(x, y) for x, y in zip(a, b))
    return a == b


def verify(document):
    if type(document) is not dict or set(document) != {
            "format", "algorithm", "sha256", "payload_text"}:
        raise InvalidReceipt("unexpected envelope")
    if document["format"] != RECEIPT or document["algorithm"] != "SHA-256/UTF-8":
        raise InvalidReceipt("unsupported receipt type")
    payload, sha = document["payload_text"], document["sha256"]
    if type(payload) is not str or len(payload.encode()) > 200_000:
        raise InvalidReceipt("payload length/type invalid")
    if type(sha) is not str or re.fullmatch("[0-9a-f]{64}", sha) is None:
        raise InvalidReceipt("invalid SHA-256")
    if hashlib.sha256(payload.encode("utf-8")).hexdigest() != sha:
        raise InvalidReceipt("payload SHA mismatch")
    report = strict_json(payload)
    if type(report) is not dict or report.get("protocol") != BRIDGE or type(report.get("seed")) is not int:
        raise InvalidReceipt("unexpected report identity or seed")
    if type(report.get("evidence")) is not dict:
        raise InvalidReceipt("missing evidence classes")
    ada = report["evidence"].get("ada_cli_conformance")
    if type(ada) is not dict or ada.get("status") not in ("NOT_RUN", "ADA_CLI_TESTED_UNATTESTED"):
        raise InvalidReceipt("unsupported Ada result status")
    expected = build_report(seed=report["seed"])
    if ada.get("status") == "ADA_CLI_TESTED_UNATTESTED":
        count = ada.get("cases")
        if type(count) is not int or count < len(rejected_cases()) + len(lexical_cases()) + 7 or count > len(list(finite_cases())) + len(rejected_cases()) + len(lexical_cases()):
            raise InvalidReceipt("invalid Ada case count")
        number = count - len(rejected_cases()) - len(lexical_cases())
        cases = sample_ada_cases(list(finite_cases()), number, report["seed"]) + rejected_cases() + lexical_cases()
        records = [[op, list(args), oracle(op, args)] for op, args in cases]
        reference_sha = hashlib.sha256(json.dumps(
            records, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        if type(ada.get("binary_sha256")) is not str or re.fullmatch("[0-9a-f]{64}", ada["binary_sha256"]) is None or ada.get("vectors_sha256") != reference_sha:
            raise InvalidReceipt("Ada CLI evidence metadata inconsistent")
        expected["evidence"]["ada_cli_conformance"] = ada
        expected["unresolved"][3] = "Ada CLI execution matches selected inputs but provenance not attested"
    if not strict_equal(report, expected):
        raise InvalidReceipt("fixed spec, source hash, classification or unresolved-obligation mismatch")
    return {"valid": True, "sha256": sha,
            "python_cases": report["evidence"]["python_conformance"]["finite_cases"],
            "ada_status": ada["status"], "mathematical_proof": "NOT_RUN",
            "ada_contracts": "NOT_RUN",
            "scope": "self-consistent fixture receipt only; no execution or proof attestation"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.receipt.stat().st_size > 400_000:
            raise InvalidReceipt("receipt file too large")
        result = verify(strict_json(args.receipt.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, InvalidReceipt) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
