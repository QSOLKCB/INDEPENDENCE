#!/usr/bin/env python3
"""Verify locally exported DOM-TRIBUNAL/1 receipts with Python stdlib only.

This proves exact payload-text integrity and internal consistency, NOT authorship,
measurement authenticity, a controlled OS/hardware environment, or framework superiority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

PHASES = ("initial", "update", "reorder")
MAX_BYTES = 3_000_000


class ReceiptError(ValueError):
    """Malformed, inconsistent, or tampered receipt."""


def no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ReceiptError("duplicate JSON property: " + key)
        obj[key] = value
    return obj


def strict_json(text):
    def reject_constant(value):
        raise ReceiptError("non-finite JSON constant: " + value)
    try:
        data = json.loads(text, object_pairs_hook=no_duplicates, parse_constant=reject_constant)
    except (ValueError, TypeError) as error:
        raise ReceiptError("invalid JSON: " + str(error)) from error
    return data


def valid_number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def checked_median(values):
    if not values or any(not math.isfinite(v) for v in values):
        raise ReceiptError("nonfinite or empty samples")
    return statistics.median(values)



MASK = 0xffffffff


def _next_xorshift(state):
    state ^= (state << 13) & MASK
    state ^= state >> 17
    state ^= (state << 5) & MASK
    return state & MASK


def phase_fingerprints(seed, count):
    """Independent stdlib reimplementation of the fixed first-party JS fixture."""
    state = seed
    initial = []
    for index in range(count):
        state = _next_xorshift(state)
        initial.append(("r" + str(index),
                        "ITEM " + str(index) + " · " + str(state % 100000).zfill(5)))
    update = [(name, label + " *" if index % 2 == 0 else label)
              for index, (name, label) in enumerate(initial)]
    reorder = list(reversed([value for index, value in enumerate(update) if index % 3 != 0]))
    def fnv(rows):
        digest = 0x811c9dc5
        for name, label in rows:
            for char in name + "\x00" + label + "\n":
                digest = ((digest ^ ord(char)) * 0x01000193) & MASK
        return format(digest, "08x")
    return {"initial": fnv(initial), "update": fnv(update), "reorder": fnv(reorder)}


def bootstrap_interval(differences, resamples=512):
    """Cross-language match to the JavaScript xorshift32 resampling algorithm."""
    state = 0x1a2b3c4d
    medians = []
    for _ in range(resamples):
        draw = []
        for _ in differences:
            state = _next_xorshift(state)
            draw.append(differences[state % len(differences)])
        medians.append(statistics.median(draw))
    medians.sort()
    return [medians[math.floor((resamples - 1) * 0.025)],
            medians[math.ceil((resamples - 1) * 0.975)]]

def verify_receipt(envelope: dict) -> dict:
    if not isinstance(envelope, dict) or set(envelope) != {
        "format", "algorithm", "sha256", "payload_text"
    }:
        raise ReceiptError("unsupported receipt envelope")
    if envelope["format"] != "DOM-TRIBUNAL-RECEIPT/1" or envelope["algorithm"] != "SHA-256/UTF-8":
        raise ReceiptError("wrong receipt format")
    text = envelope["payload_text"]
    digest = envelope["sha256"]
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise ReceiptError("payload must be UTF-8 text smaller than limit")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ReceiptError("invalid SHA-256 format")
    actual = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if actual != digest:
        raise ReceiptError("SHA-256 mismatch: payload has changed")
    report = strict_json(text)
    if not isinstance(report, dict) or report.get("protocol") != "DOM-TRIBUNAL/1" or report.get("schema_version") != 1:
        raise ReceiptError("unexpected protocol")
    config = report.get("config")
    if not isinstance(config, dict):
        raise ReceiptError("config missing")
    for key, low, high in (("seed", 1, 0xffffffff), ("count", 20, 400),
                           ("trials", 8, 60), ("warmups", 2, 12)):
        value = config.get(key)
        if type(value) is not int or not (low <= value <= high):
            raise ReceiptError("invalid config: " + key)
    if report.get("candidates") != [
        {"id": "direct", "label": "Direct DOM", "kind": "native"},
        {"id": "keyed", "label": "Local keyed adapter", "kind": "illustrative"},
    ]:
        raise ReceiptError("unexpected candidates")
    if report.get("phase_fingerprints") != phase_fingerprints(config["seed"], config["count"]):
        raise ReceiptError("fixture fingerprint mismatch")
    times = report.get("samples_ms")
    if not isinstance(times, list) or len(times) != config["trials"]:
        raise ReceiptError("incorrect paired trial count")
    if not isinstance(report.get("statistics"), dict) or set(report["statistics"]) != set(PHASES):
        raise ReceiptError("missing phase statistics")
    for pair in times:
        if not isinstance(pair, dict) or set(pair) != {"direct", "keyed"}:
            raise ReceiptError("unmatched pair")
        for candidate in ("direct", "keyed"):
            values = pair[candidate]
            if not isinstance(values, dict) or set(values) != set(PHASES):
                raise ReceiptError("incomplete phase sample")
            if any(not valid_number(x) for x in values.values()):
                raise ReceiptError("invalid or negative timing")
    for phase in PHASES:
        rows = [pair["direct"][phase] for pair in times]
        keys = [pair["keyed"][phase] for pair in times]
        differences = [b - a for a, b in zip(rows, keys)]
        summary = report["statistics"][phase]
        if not isinstance(summary, dict) or summary.get("trials") != len(times):
            raise ReceiptError("wrong statistics sample count")
        for key, expected in (
            ("direct_median_ms", checked_median(rows)),
            ("keyed_median_ms", checked_median(keys)),
            ("paired_delta_median_ms", checked_median(differences)),
        ):
            actual = summary.get(key)
            if type(actual) not in (int, float) or not math.isfinite(actual) or not math.isclose(
                actual, expected, rel_tol=1e-12, abs_tol=1e-10
            ):
                raise ReceiptError("statistics mismatch: " + phase + "/" + key)
        interval = summary.get("paired_delta_bootstrap_95_ms")
        if not isinstance(interval, list) or len(interval) != 2 or any(
            type(v) not in (int, float) or not math.isfinite(v) for v in interval
        ) or interval[0] > interval[1]:
            raise ReceiptError("invalid bootstrap interval")
        for actual, expected in zip(interval, bootstrap_interval(differences)):
            if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-10):
                raise ReceiptError("bootstrap interval mismatch: " + phase)
    size = report.get("adapter_source_bytes")
    if not isinstance(size, dict) or set(size) != {"direct", "keyed"} or any(
        type(v) is not int or v <= 0 for v in size.values()
    ):
        raise ReceiptError("invalid adapter source byte lengths")
    correctness = report.get("correctness")
    if correctness != {"passed": True, "trials_verified": (
        config["warmups"] + config["trials"]) * 2 * len(PHASES)}:
        raise ReceiptError("correctness-gate claim inconsistent")
    lowres = report.get("low_clock_resolution_observed")
    if type(lowres) is not bool or lowres != any(
        pair[side][phase] == 0 for pair in times for side in ("direct", "keyed") for phase in PHASES
    ):
        raise ReceiptError("low-resolution warning mismatch")
    methodology = report.get("methodology")
    if not isinstance(methodology, dict) or methodology.get("attribution") != (
        "local keyed adapter is illustrative; NOT a React/Vue/Svelte benchmark"
    ):
        raise ReceiptError("missing evidence attribution")
    return {"valid": True, "sha256": actual, "paired_trials": len(times),
            "scope": "integrity and internal arithmetic only; not trusted measurement provenance"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    try:
        if args.receipt.stat().st_size > MAX_BYTES * 2:
            raise ReceiptError("receipt file exceeds size limit")
        envelope = strict_json(args.receipt.read_text(encoding="utf-8"))
        output = verify_receipt(envelope)
    except (OSError, UnicodeError, ReceiptError, AttributeError, RecursionError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(output, sort_keys=True) if args.json else
          "PASS — receipt integrity and internal statistics; NOT measurement authenticity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
