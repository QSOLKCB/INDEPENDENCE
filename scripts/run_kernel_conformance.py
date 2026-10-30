#!/usr/bin/env python3
"""Bounded finite Python oracle and OPTIONAL external Ada CLI differential evidence.

Conformance with a reference model is NOT a formal mathematical proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "formal/python"))
from kernel import evaluate  # noqa: E402

SPEC = ROOT / "formal/spec/kernel-v1.json"
BRIDGE = "PROOF-CONFORMANCE-BRIDGE/1"
RECEIPT = "PROOF-CONFORMANCE-RECEIPT/1"
SEED = 314159


def oracle(operation: str, args: tuple[int, ...]) -> str:
    """An independently coded arithmetic interpretation of kernel-v1.json."""
    if type(operation) is not str or type(args) is not tuple or any(type(v) is not int for v in args):
        return "ERR:INVALID"
    if any(v < 0 for v in args):
        return "ERR:INVALID"
    if operation == "ADDR" and len(args) == 3:
        row, col, width = args
        if 0 <= row < 16 and 1 <= width < 17 and col < width:
            return "OK:" + str(sum(width for _ in range(row)) + col)
    if operation == "DECODE" and len(args) == 2:
        pos, width = args
        if 0 <= pos < 256 and 1 <= width <= 16 and pos < width * 16:
            row = 0
            remainder = pos
            while remainder >= width:
                remainder -= width
                row += 1
            return f"OK:{row},{remainder}"
    if operation in ("PARITY_ADD", "PARITY_MUL") and len(args) == 2:
        a, b = args
        if a in (0, 1) and b in (0, 1):
            n = a + b if operation == "PARITY_ADD" else a * b
            return "OK:" + str(n % 2)
    if operation == "PHASE_ADD" and len(args) == 2:
        a, b = args
        if a in (0, 1, 2) and b in (0, 1, 2):
            result = a + b
            while result >= 3:
                result -= 3
            return "OK:" + str(result)
    if operation in ("EDGE_VALID", "EDGE_STEP") and len(args) in (3, 5):
        source, target, count = args[:3]
        if 0 <= source <= 255 and 0 <= target <= 255 and 2 <= count <= 256:
            valid = source < count and target < count and source != target
            if operation == "EDGE_VALID" and len(args) == 3:
                return "OK:" + ("1" if valid else "0")
            if operation == "EDGE_STEP" and len(args) == 5:
                current, influence = args[3:]
                if valid and current in (0, 1) and influence in (0, 1):
                    return "OK:" + str((current + influence) % 2)
    return "ERR:INVALID"


def finite_cases():
    for width in range(1, 17):
        for row in range(16):
            for col in range(width):
                yield "ADDR", (row, col, width)
        for pos in range(16 * width):
            yield "DECODE", (pos, width)
    for a in range(2):
        for b in range(2):
            yield "PARITY_ADD", (a, b)
            yield "PARITY_MUL", (a, b)
    for a in range(3):
        for b in range(3):
            yield "PHASE_ADD", (a, b)
    for count in range(2, 17):
        for source in range(16):
            for target in range(16):
                yield "EDGE_VALID", (source, target, count)
    for count in range(2, 9):
        for source in range(count):
            for target in range(count):
                if source == target:
                    continue
                for current in range(2):
                    for influence in range(2):
                        yield "EDGE_STEP", (source, target, count, current, influence)


def rejected_cases():
    return [
        ("ADDR", (0, 2, 2)), ("ADDR", (0, 0, 0)), ("ADDR", (16, 0, 1)),
        ("DECODE", (256, 16)), ("DECODE", (16, 1)),
        ("PARITY_ADD", (2, 0)), ("PARITY_MUL", (0, 2)),
        ("PHASE_ADD", (0, 3)), ("EDGE_VALID", (0, 1, 1)),
        ("EDGE_STEP", (0, 0, 4, 1, 1)), ("EDGE_STEP", (0, 4, 4, 1, 1)),
        ("EDGE_STEP", (0, 1, 4, 2, 0)), ("EDGE_STEP", (0, 1, 4, 0, 2)),
        ("ADDR", (-1, 0, 2)), ("PARITY_ADD", (True, 1)),
        ("UNKNOWN", (0, 0)),
    ]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_ada_cases(cases, amount: int, seed: int = SEED):
    if amount < 1 or amount > len(cases):
        raise ValueError("Ada sample count outside test domain")
    groups = {}
    for i, (op, _) in enumerate(cases):
        groups.setdefault(op, []).append(i)
    chosen = {members[0] for members in groups.values()}
    if amount < len(chosen):
        raise ValueError("Ada sample too small to cover every operation")
    indices = [i for i in range(len(cases)) if i not in chosen]
    randomizer = random.Random(seed)
    chosen.update(randomizer.sample(indices, amount - len(chosen)))
    return [cases[i] for i in sorted(chosen)]


def run_ada(binary: Path, cases):
    records = []
    for operation, args in cases:
        expected = oracle(operation, args)
        try:
            proc = subprocess.run([str(binary), operation, *map(str, args)],
                                  capture_output=True, text=True, timeout=3, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError("Ada CLI unavailable/timeout: " + str(error)) from error
        actual = proc.stdout.strip()
        if proc.returncode != 0 or actual != expected or proc.stderr.strip():
            raise RuntimeError("Ada mismatch: " + repr((operation, args, expected, actual,
                                                       proc.stderr[:160], proc.returncode)))
        records.append([operation, list(args), expected])
    serialized = json.dumps(records, separators=(",", ":"), ensure_ascii=False)
    return {"status": "ADA_CLI_TESTED_UNATTESTED", "cases": len(records),
            "vectors_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
            "binary_sha256": digest(binary),
            "note": "CLI output matched oracle; binary provenance and SPARK compilation not independently attested"}


def build_report(ada_binary: Path | None = None, ada_cases: int = 128, seed: int = SEED):
    if type(seed) is not int or not 0 <= seed <= 0xffffffff:
        raise ValueError("invalid seed")
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec.get("protocol") != "INDEPENDENCE-KERNEL-SPEC/1":
        raise ValueError("shared specification mismatch")
    finite = list(finite_cases())
    negative = rejected_cases()
    grouped = {}
    for op, args in finite + negative:
        expected = oracle(op, args)
        actual = evaluate(op, args)
        if actual != expected:
            raise RuntimeError("Python oracle mismatch: " + repr((op, args, expected, actual)))
        grouped[op] = grouped.get(op, 0) + 1
    ada = {"status": "NOT_RUN", "cases": 0,
           "reason": "No executable Ada CLI provided; no Ada/Python differential claim"}
    if ada_binary is not None:
        binary = Path(ada_binary).resolve()
        if not binary.is_file():
            raise FileNotFoundError("Ada executable not found: " + str(binary))
        ada = run_ada(binary, sample_ada_cases(finite, ada_cases, seed) + negative)
    unresolved = ["Lean mathematical theorems NOT_RUN", "GNATprove Ada contracts NOT_RUN",
                  "Existing application Python/JavaScript conformance NOT_ESTABLISHED",
                  "Actual Ada compiler/CLI execution NOT_RUN" if ada["status"] == "NOT_RUN" else
                  "Ada CLI execution matches selected inputs but provenance not attested"]
    return {
        "protocol": BRIDGE, "schema_version": 1,
        "spec_protocol": spec["protocol"], "spec_sha256": digest(SPEC),
        "sources_sha256": {
            "python": digest(ROOT / "formal/python/kernel.py"),
            "ada_spec": digest(ROOT / "formal/spark/reference_kernel.ads"),
            "ada_body": digest(ROOT / "formal/spark/reference_kernel.adb"),
        },
        "seed": seed,
        "evidence": {
            "mathematical_proof": {"status": "NOT_RUN", "tool": "Lean 4"},
            "ada_contracts": {"status": "NOT_RUN", "tool": "GNATprove"},
            "python_conformance": {"status": "FINITE_EXHAUSTIVE_TESTED",
                                   "finite_cases": len(finite), "rejected_cases": len(negative),
                                   "operations": dict(sorted(grouped.items()))},
            "ada_cli_conformance": ada,
        },
        "unresolved": unresolved,
        "limitations": [
            "Finite Python results compare a new independent kernel, not all existing Python application logic.",
            "No checked Lean theorem or discharged GNATprove contract is asserted.",
            "A self-hashed receipt proves bytes match reported data, not external execution authenticity.",
            "Endpoint validity does not prove Penrose tile adjacency or CRT address bijection.",
        ],
    }


def make_receipt(report):
    text = json.dumps(report, indent=2, ensure_ascii=False)
    return {"format": RECEIPT, "algorithm": "SHA-256/UTF-8",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "payload_text": text}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ada-cli", type=Path, default=None)
    parser.add_argument("--ada-cases", type=int, default=128)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.ada_cli, args.ada_cases, args.seed)
        if args.receipt:
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(make_receipt(report), indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
