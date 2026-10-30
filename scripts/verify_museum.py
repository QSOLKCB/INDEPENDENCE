#!/usr/bin/env python3
"""Verify deterministic GREMLIN-MUSEUM/1 receipts offline, using stdlib only.

The verifier checks exact payload integrity AND fixed, independently encoded
expected observations. It does not authenticate who produced a receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

MAX_BYTES = 120_000
PROTOCOL = "GREMLIN-MUSEUM/1"
FORMAT = "GREMLIN-MUSEUM-RECEIPT/1"

EXPECTED = (
    ("side-effect-import", "Static-audit bypass",
     "import 'https://example.invalid/museum-only.js';",
     "Original static rule missed the remote side-effect import: true",
     "Corrected rule detects the side-effect import: true", 3),
    ("checkout-ancestry", "Audit false positive",
     "Repository /workspace/.venv/repo; file app.js",
     "Absolute-ancestor scan reports a vendored directory: true",
     "Repository-relative scan reports a vendored directory: false", 3),
    ("sha-identity", "Evidence integrity / validation",
     "Synthetic receipt: " + "a" * 64,
     "Reused 40-hex validator rejects this 64-hex receipt: true",
     "Dedicated 64-hex validator accepts it: true", 4),
    ("json-overflow", "JSON numeric correctness",
     '{"budget":1e999}',
     'Native parse creates Infinity; stringification yields: {"budget":null}',
     "Deep finite-number check rejects the parsed value: true", 4),
    ("html-encoding", "HTML output encoding",
     "<img src=x onerror=alert(1)>",
     "Unsafe HTML construction contains unescaped input: <p><img src=x onerror=alert(1)></p>",
     "Encoded HTML string (displayed as TEXT, never rendered): <p>&lt;img src=x onerror=alert(1)&gt;</p>", 4),
)


class InvalidReceipt(ValueError):
    pass


def _pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            raise InvalidReceipt("duplicate JSON property")
        obj[key] = value
    return obj


def _constant(value):
    raise InvalidReceipt("nonfinite JSON constant")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise InvalidReceipt("nonfinite JSON number")
    return result


def strict_json(data):
    try:
        return json.loads(data, object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)
    except (TypeError, ValueError, OverflowError, RecursionError) as error:
        raise InvalidReceipt("invalid JSON: " + str(error)) from error


def verify(envelope):
    if not isinstance(envelope, dict) or set(envelope) != {"format", "algorithm", "sha256", "payload_text"}:
        raise InvalidReceipt("invalid receipt envelope")
    if envelope["format"] != FORMAT or envelope["algorithm"] != "SHA-256/UTF-8":
        raise InvalidReceipt("unsupported receipt format")
    text = envelope["payload_text"]
    digest = envelope["sha256"]
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise InvalidReceipt("invalid payload length")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise InvalidReceipt("invalid SHA-256 digest")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
        raise InvalidReceipt("payload SHA-256 mismatch")
    data = strict_json(text)
    if not isinstance(data, dict) or data.get("protocol") != PROTOCOL or data.get("schema_version") != 1:
        raise InvalidReceipt("unknown experiment protocol")
    if data.get("scope") != "isolated deterministic examples, no external exploitation":
        raise InvalidReceipt("invalid scope")
    rows = data.get("exhibits")
    provenance = data.get("provenance")
    if not isinstance(rows, list) or not isinstance(provenance, list) or len(rows) != len(EXPECTED) or len(provenance) != len(EXPECTED):
        raise InvalidReceipt("incomplete exhibit sequence")
    for index, (id_, kind, input_text, legacy, hardened, assertions) in enumerate(EXPECTED):
        row = rows[index]
        if not isinstance(row, dict) or set(row) != {
            "id", "kind", "input", "legacy", "hardened", "assertions", "passed"
        }:
            raise InvalidReceipt("invalid exhibit record")
        if (row["id"], row["kind"], row["input"], row["legacy"], row["hardened"]) != (
            id_, kind, input_text, legacy, hardened
        ):
            raise InvalidReceipt("unexpected specimen observation: " + id_)
        if row["passed"] is not True or row["assertions"] != {"passed": assertions, "total": assertions}:
            raise InvalidReceipt("specimen assertions failed: " + id_)
        src = provenance[index]
        if not isinstance(src, dict) or set(src) != {"id", "provenance", "source"} or src["id"] != id_:
            raise InvalidReceipt("invalid provenance for " + id_)
        if not isinstance(src["provenance"], str) or not isinstance(src["source"], str) or not src["source"].startswith(
            "https://github.com/QSOLKCB/INDEPENDENCE"
        ):
            raise InvalidReceipt("unrecognised exhibit origin")
    limitations = data.get("limitations")
    if not isinstance(limitations, list) or len(limitations) != 3 or any(not isinstance(x, str) or not x for x in limitations):
        raise InvalidReceipt("missing explicit limitations")
    return {"valid": True, "sha256": digest, "exhibits": len(EXPECTED),
            "assertions": sum(row[-1] for row in EXPECTED),
            "scope": "offline fixed-fixture consistency; not proof of absence of vulnerabilities"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.receipt.stat().st_size > MAX_BYTES * 2:
            raise InvalidReceipt("file exceeds maximum size")
        doc = strict_json(args.receipt.read_text(encoding="utf-8"))
        outcome = verify(doc)
    except (OSError, UnicodeError, InvalidReceipt) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(outcome, sort_keys=True) if args.json else
          "PASS — fixed-fixture receipt integrity and consistency, not real-world security certification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
