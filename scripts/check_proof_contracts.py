#!/usr/bin/env python3
"""Offline PROOF-CONTRACT-REGISTRY/1 gate; stdlib only, no formal proof claims."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

EXPECTED = {
    "AUTOMATA-TRANSITION": ("lab/core.js", "evolve", "BOUNDED_EXHAUSTIVE"),
    "DEPENDENCY-SUM": ("lab/core.js", "dependencyExposure", "FINITE_CASES"),
    "AUTOMATA-REPLAY": ("lab/core.js", "buildAutomaton", "FINITE_CASES"),
    "SHA-FORMAT": ("ledger/ledger.js", "validReceiptSha", "FINITE_CASES"),
    "FINGERPRINT-IMMUTABILITY": ("lab/core.js", "buildAutomaton", "COUNTEREXAMPLE"),
    "RECEIPT-AUTHENTICITY": ("scripts/verify_museum.py", "verify", "PENDING"),
    "LEAN-TRANSITION": ("lab/core.js", "evolve", "PENDING"),
    "SPARK-TRANSITION": ("lab/core.js", "evolve", "PENDING"),
}
RELEASE_BASELINE = "cb1d8686cc7e11997fd7608d2ce52e032d7c0056"


class ContractError(ValueError):
    pass


def no_dupes(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("duplicate JSON property: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ContractError("nonfinite JSON value")


def strict_json(data):
    try:
        return json.loads(data, object_pairs_hook=no_dupes, parse_constant=reject_constant)
    except (ValueError, TypeError, RecursionError) as error:
        raise ContractError("invalid JSON: " + str(error)) from error


def check_registry(root: Path):
    root = root.resolve()
    raw = (root / "proof/contracts.json").read_bytes()
    if len(raw) > 100_000:
        raise ContractError("registry too large")
    document = strict_json(raw.decode("utf-8"))
    if not isinstance(document, dict) or set(document) != {
        "protocol", "schema_version", "release", "source_baseline", "formal_status",
        "source", "obligations", "limitations"
    }:
        raise ContractError("registry envelope invalid")
    if (document["protocol"], document["schema_version"], document["release"]) != (
        "PROOF-CONTRACT-REGISTRY/1", 1, "v0.7.0"
    ) or type(document["schema_version"]) is not int:
        raise ContractError("unexpected contract registry identity")
    if document["source_baseline"] != {"tag": "v0.6.0", "commit": RELEASE_BASELINE}:
        raise ContractError("unexpected source baseline")
    if document["formal_status"] != "NOT_PROVED":
        raise ContractError("unjustified formal proof status")
    if not isinstance(document["source"], str) or not document["source"]:
        raise ContractError("missing provenance scope")
    rows = document["obligations"]
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ContractError("incomplete proof obligations")
    for position, (name, (path, symbol, kind)) in enumerate(EXPECTED.items()):
        row = rows[position]
        if not isinstance(row, dict) or set(row) != {
            "id", "target", "priority", "expected_evidence", "formal_status",
            "claim", "domain"
        }:
            raise ContractError("invalid obligation shape")
        if row["id"] != name or row["target"] != {"path": path, "symbol": symbol}:
            raise ContractError("incorrect obligation target/order: " + name)
        if row["expected_evidence"] != kind or row["formal_status"] != "NOT_PROVED":
            raise ContractError("unproved obligation mislabelled: " + name)
        if row["priority"] not in ("P0", "P1", "P2", "P3"):
            raise ContractError("invalid risk priority")
        if any(not isinstance(row[k], str) or not row[k] for k in ("claim", "domain")):
            raise ContractError("missing contract rationale")
        source = (root / path)
        if not source.is_file() or not re.search(r"\b" + re.escape(symbol) + r"\b", source.read_text(encoding="utf-8")):
            raise ContractError("missing referenced target symbol: " + name)
    if not isinstance(document["limitations"], list) or len(document["limitations"]) != 4 or any(
        not isinstance(value, str) or not value for value in document["limitations"]
    ):
        raise ContractError("missing proof boundaries")
    return {
        "valid": True, "protocol": document["protocol"], "obligations": len(rows),
        "formally_proved": 0, "source_baseline": RELEASE_BASELINE,
        "registry_sha256": hashlib.sha256(raw).hexdigest(),
        "scope": "registry identity and target presence; not a formal proof of production code",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true")
    options = parser.parse_args(argv)
    try:
        output = check_registry(options.root)
    except (OSError, UnicodeError, ContractError, RecursionError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(output, sort_keys=True) if options.json else
          "PASS — 8 declarations validated; 0 formal proofs claimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
