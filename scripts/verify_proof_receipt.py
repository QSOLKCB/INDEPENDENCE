#!/usr/bin/env python3
"""Verify PROOF-CONTRACT-RECEIPT/1 payload integrity and fixed-fixture consistency.

This is NOT proof of execution, source authenticity, or formal verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

FORMAT = "PROOF-CONTRACT-RECEIPT/1"
MAX_BYTES = 100_000
LIMITATIONS = [
    "Bounded exhaustive and finite tests are not formal proofs of all JavaScript inputs.",
    "Receipt SHA-256 checks payload bytes, not authorship or actual browser execution.",
    "No Lean or SPARK theorem has been discharged for INDEPENDENCE in v0.7.0.",
]


class InvalidProofReceipt(ValueError):
    pass


def no_dupes(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidProofReceipt("duplicate JSON property: " + key)
        result[key] = value
    return result


def finite_float(raw):
    value = float(raw)
    if not math.isfinite(value):
        raise InvalidProofReceipt("nonfinite JSON value")
    return value


def reject_constant(value):
    raise InvalidProofReceipt("nonfinite JSON constant")


def strict_json(text):
    try:
        return json.loads(text, object_pairs_hook=no_dupes,
                          parse_float=finite_float, parse_constant=reject_constant)
    except (TypeError, ValueError, OverflowError, RecursionError) as error:
        raise InvalidProofReceipt("invalid JSON: " + str(error)) from error


def expected_report():
    return {
        "protocol": "PROOF-CONTRACTS/1",
        "schema_version": 1,
        "scope": "bounded first-party behaviour; no formal proofs",
        "checks": [
            {"id": "AUTOMATA-TRANSITION", "status": "BOUNDED_EXHAUSTIVE",
             "cases": 130560, "assertions": 918016},
            {"id": "DEPENDENCY-SUM", "status": "FINITE_CASES",
             "cases": 463, "assertions": 463},
            {"id": "AUTOMATA-REPLAY", "status": "FINITE_CASES",
             "cases": 36, "assertions": 36},
            {"id": "SHA-FORMAT", "status": "FINITE_CASES",
             "cases": 12, "assertions": 12},
            {"id": "FINGERPRINT-IMMUTABILITY", "status": "COUNTEREXAMPLE",
             "cases": 1, "assertions": 1,
             "stored_fingerprint": "6d8aa545",
             "recomputed_fingerprint": "eb95c744",
             "implication": "Object.freeze does not make the returned Uint8Array immutable."}
        ],
        "formal_proofs": {"lean": "NOT_RUN", "spark": "NOT_RUN"},
        "limitations": list(LIMITATIONS),
    }


def exact(a, b):
    """Avoid Python's bool == 1 and other cross-type equality surprises."""
    if type(a) is not type(b):
        return False
    if isinstance(b, dict):
        return a.keys() == b.keys() and all(exact(a[k], v) for k, v in b.items())
    if isinstance(b, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def verify(envelope):
    if type(envelope) is not dict or envelope.keys() != {
        "format", "algorithm", "sha256", "payload_text"
    }:
        raise InvalidProofReceipt("unexpected proof receipt envelope")
    if envelope["format"] != FORMAT or envelope["algorithm"] != "SHA-256/UTF-8":
        raise InvalidProofReceipt("wrong proof receipt format")
    text = envelope["payload_text"]
    digest = envelope["sha256"]
    if type(text) is not str or len(text.encode("utf-8")) > MAX_BYTES:
        raise InvalidProofReceipt("invalid payload text")
    if type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise InvalidProofReceipt("invalid digest format")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
        raise InvalidProofReceipt("SHA-256 mismatch")
    report = strict_json(text)
    if not exact(report, expected_report()):
        raise InvalidProofReceipt("fixed bounded results / counterexample / proof-status mismatch")
    return {"valid": True, "sha256": digest, "contracts_checked": 5,
            "counterexamples": 1, "formally_proved": 0,
            "scope": "payload integrity and published fixture consistency, not execution attestation"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.receipt.stat().st_size > 2 * MAX_BYTES:
            raise InvalidProofReceipt("receipt too large")
        envelope = strict_json(args.receipt.read_text(encoding="utf-8"))
        result = verify(envelope)
    except (InvalidProofReceipt, OSError, UnicodeError, RecursionError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True) if args.json else
          "PASS — receipt integrity and known results; NOT a formal proof or execution attestation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
