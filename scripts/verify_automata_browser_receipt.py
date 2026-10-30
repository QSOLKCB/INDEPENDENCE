#!/usr/bin/env python3
"""Strict finite-vector browser receipt verifier; never authenticates browser execution."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from check_automata_formal import EXPECTED_VECTORS_SHA256, vectors, vectors_digest

PROTOCOL = "AUTOMATA4-BROWSER/1"
FORMAT = "AUTOMATA4-BROWSER-RECEIPT/1"
MAX_BYTES = 4096

class BrowserReceiptError(ValueError):
    pass

def unique(pairs):
    record = {}
    for key, value in pairs:
        if key in record:
            raise BrowserReceiptError("duplicate key: " + key)
        record[key] = value
    return record

def invalid_float(_):
    raise BrowserReceiptError("floating or nonfinite JSON number rejected")

def parse(raw: str):
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_float=invalid_float, parse_constant=invalid_float)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise BrowserReceiptError("invalid JSON: " + str(exc)) from exc

def verify(raw: str) -> dict:
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise BrowserReceiptError("oversized envelope")
    wrapper = parse(raw)
    if type(wrapper) is not dict or set(wrapper) != {"format", "sha256", "payload_text"}:
        raise BrowserReceiptError("invalid envelope schema")
    payload = wrapper["payload_text"]
    if type(payload) is not str or wrapper["format"] != FORMAT:
        raise BrowserReceiptError("wrong format or payload type")
    if type(wrapper["sha256"]) is not str or (
            hashlib.sha256(payload.encode("utf-8")).hexdigest() != wrapper["sha256"]):
        raise BrowserReceiptError("receipt SHA-256 mismatch")
    observed = parse(payload)
    expected = {
        "protocol": PROTOCOL, "status": "FINITE_JS_CONFORMANCE",
        "cases": 4096, "vectors_sha256": EXPECTED_VECTORS_SHA256,
        "proof_status": "NOT_A_FORMAL_PROOF"
    }
    if (type(observed) is not dict or set(observed) != set(expected)
            or any(type(observed[k]) is not type(v) or observed[k] != v
                   for k, v in expected.items())):
        raise BrowserReceiptError("wrong finite vector digest, count, schema or proof status")
    if vectors_digest(list(vectors())) != expected["vectors_sha256"]:
        raise BrowserReceiptError("reference corpus changed")
    return {"status": "INTERNALLY_CONSISTENT_UNATTESTED",
            "cases": expected["cases"], "vectors_sha256": expected["vectors_sha256"]}

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("receipt", type=Path)
    args = ap.parse_args(argv)
    try:
        record = verify(args.receipt.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError, TypeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(record, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
