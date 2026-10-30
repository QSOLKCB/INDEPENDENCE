#!/usr/bin/env python3
"""Verify GREMLIN-BREEDING/1 fixed-fixture receipts with Python stdlib.

Checks byte integrity, independently encoded catalog/witness expectations,
seeded xorshift order, and exact kill/survive classifications. It cannot
authenticate execution, author identity, or repository-wide mutation coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

PROTOCOL = "GREMLIN-BREEDING/1"
FORMAT = "GREMLIN-BREEDING-RECEIPT/1"
MAX_BYTES = 200_000
MASK = 0xffffffff
CASES = {
    "receipt": ("valid64", "reject40", "rejectNonHex", "rejectUpper", "validOther"),
    "encoding": ("tag", "plain", "ampersand", "quotes", "combined"),
    "finite": ("finiteObject", "finiteList", "directInfinite", "nestedInfinite", "nullAllowed", "negativeInfinite"),
    "scope": ("localVendor", "clean", "ancestorVenv", "localVenv", "partialFolder"),
    "imports": ("named", "local", "sideEffect", "dynamic", "urlAsData"),
}
SMOKE = {
    "receipt": {"valid64", "reject40"},
    "encoding": {"tag", "plain"},
    "finite": {"finiteObject", "finiteList"},
    "scope": {"localVendor", "clean"},
    "imports": {"named", "local"},
}
# Independently recorded expectations of which fixed cases each curated mutant fails.
MUTANTS = (
    ("receipt", "accept40or64", "Boundary widened", ("reject40",)),
    ("receipt", "acceptUppercase", "Case restriction removed", ("rejectUpper",)),
    ("receipt", "lengthOnly", "Hex check removed", ("rejectNonHex", "rejectUpper")),
    ("encoding", "noEncoding", "Encoding removed", ("tag", "ampersand", "quotes", "combined")),
    ("encoding", "missAmp", "Ampersand escape removed", ("ampersand", "combined")),
    ("encoding", "missQuotes", "Quote escapes removed", ("quotes",)),
    ("finite", "alwaysTrue", "Finite check removed", ("directInfinite", "nestedInfinite", "negativeInfinite")),
    ("finite", "shallow", "Recursive validation removed", ("nestedInfinite",)),
    ("finite", "rejectNull", "Null handling inverted", ("nullAllowed",)),
    ("scope", "absoluteAncestry", "Scope widened to checkout ancestors", ("ancestorVenv",)),
    ("scope", "ignoreVenv", "One vendored directory omitted", ("localVenv",)),
    ("scope", "substringFolder", "Exact directory boundary removed", ("partialFolder",)),
    ("imports", "fromOnly", "Side-effect import form omitted", ("sideEffect",)),
    ("imports", "staticOnly", "Dynamic import form omitted", ("dynamic",)),
    ("imports", "anyURL", "Import context ignored", ("urlAsData",)),
)
LIMITATIONS = [
    "Fixed first-party mutation catalogue; not arbitrary mutation of application source files.",
    "Survival means selected tests missed a known divergent fixture, not that the defect is safe.",
    "Mutation score is scoped to these curated cases and cannot certify repository-wide test quality.",
]


class InvalidReceipt(ValueError):
    pass


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidReceipt("duplicate JSON property: " + key)
        result[key] = value
    return result


def finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise InvalidReceipt("nonfinite JSON float")
    return result


def reject_constant(value):
    raise InvalidReceipt("nonfinite JSON constant")


def strict_json(text):
    try:
        return json.loads(text, object_pairs_hook=no_duplicates,
                          parse_float=finite_float, parse_constant=reject_constant)
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise InvalidReceipt("invalid JSON: " + str(error)) from error


def shuffled(seed):
    pairs = list(MUTANTS)
    state = seed
    for index in range(len(pairs) - 1, 0, -1):
        state ^= (state << 13) & MASK
        state ^= state >> 17
        state ^= (state << 5) & MASK
        state &= MASK
        swap = state % (index + 1)
        pairs[index], pairs[swap] = pairs[swap], pairs[index]
    return pairs


def expected_report(seed, suite):
    if type(seed) is not int or not 1 <= seed <= MASK or suite not in ("smoke", "full"):
        raise InvalidReceipt("invalid seed or suite")
    results = []
    for target, mutant, operator, witnesses in shuffled(seed):
        if any(case not in CASES[target] for case in witnesses):
            raise InvalidReceipt("internal witness catalogue inconsistent")
        failures = [case for case in witnesses if suite == "full" or case in SMOKE[target]]
        results.append({
            "id": target + "/" + mutant, "target": target, "mutant": mutant,
            "operator": operator, "status": "killed" if failures else "survived",
            "failing_tests": failures, "witness_tests": list(witnesses)
        })
    killed = sum(row["status"] == "killed" for row in results)
    return {
        "schema_version": 1, "protocol": PROTOCOL, "config": {"seed": seed, "suite": suite},
        "targets": len(CASES), "baseline_assertions": sum(map(len, CASES.values())),
        "mutants": len(MUTANTS), "results": results,
        "summary": {"killed": killed, "survived": len(MUTANTS) - killed,
                    "mutation_score": {"numerator": killed, "denominator": len(MUTANTS)}},
        "limitations": list(LIMITATIONS),
    }


def verify(envelope):
    if not isinstance(envelope, dict) or set(envelope) != {
        "format", "algorithm", "sha256", "payload_text"
    }:
        raise InvalidReceipt("unexpected receipt envelope")
    if envelope["format"] != FORMAT or envelope["algorithm"] != "SHA-256/UTF-8":
        raise InvalidReceipt("unexpected receipt format")
    text, digest = envelope["payload_text"], envelope["sha256"]
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise InvalidReceipt("invalid UTF-8 payload length")
    if not isinstance(digest, str) or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest
    ):
        raise InvalidReceipt("invalid SHA-256 digest")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
        raise InvalidReceipt("SHA-256 mismatch")
    report = strict_json(text)
    if not isinstance(report, dict) or not isinstance(report.get("config"), dict):
        raise InvalidReceipt("missing report config")
    config = report["config"]
    if set(config) != {"seed", "suite"}:
        raise InvalidReceipt("unexpected config fields")
    expected = expected_report(config["seed"], config["suite"])
    if report != expected:
        raise InvalidReceipt("fixed catalogue, seeded order or classification mismatch")
    return {
        "valid": True, "sha256": digest, "mutants": expected["mutants"],
        "killed": expected["summary"]["killed"], "survived": expected["summary"]["survived"],
        "scope": "fixed-fixture integrity and expected outcomes; not independent execution attestation"
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.receipt.stat().st_size > MAX_BYTES * 2:
            raise InvalidReceipt("receipt file too large")
        envelope = strict_json(args.receipt.read_text(encoding="utf-8"))
        result = verify(envelope)
    except (OSError, UnicodeError, InvalidReceipt, RecursionError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True) if args.json else
          "PASS — curated fixture evidence, not security or execution certification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
