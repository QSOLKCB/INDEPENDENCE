#!/usr/bin/env python3
"""AUTOMATA-ROCQ/1: independent arbitrary-width semantics, optional real Rocq 9.2.

Only real Rocq compilation yields KERNEL_CHECKED. Static source/finite
crosschecks alone remain NOT_RUN; receipt verification is not execution
attestation. Python standard library, no network/runtime dependencies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import check_automata_formal as automata

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("formal/rocq/Automata.v")
PIN = "9.2.0"
SOURCE_BLOB = "15dfdf5925492c5647477d8f2970664bdd827d93"
PROTOCOL = "AUTOMATA-ROCQ/1"
THEOREMS = (
    "neighborhood_bounded",
    "arithmetic_table_cell",
    "arbitrary_width_length",
    "arbitrary_width_table_length",
    "independent_models_equivalent",
    "rule_zero_cell",
    "rule_255_cell",
    "rule_zero_all_widths",
    "rule_255_all_widths",
    "rule90_cell_xor",
    "rule90_all_widths",
    "automata4_model_bridge",
    "zero_boundary_empty",
    "zero_boundary_singleton",
    "rule90_known_four",
)
# Independent explicit table (left,center,right). Do NOT obtain this table
# from the arithmetic reference or reuse its source.
PATTERN_TABLE = {
    (0, 0, 0): 0, (0, 0, 1): 1,
    (0, 1, 0): 2, (0, 1, 1): 3,
    (1, 0, 0): 4, (1, 0, 1): 5,
    (1, 1, 0): 6, (1, 1, 1): 7,
}


class RocqEvidenceError(ValueError):
    pass


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def inspect_source(root: Path = ROOT) -> bytes:
    path = root / SOURCE
    if path.is_symlink() or not path.is_file():
        raise RocqEvidenceError("missing or symlinked Rocq proof source")
    raw = path.read_bytes()
    if git_blob(raw) != SOURCE_BLOB:
        raise RocqEvidenceError("Rocq proof source differs from reviewed blob")
    try:
        source = raw.decode("utf-8")
    except UnicodeError as error:
        raise RocqEvidenceError("Rocq source not UTF-8") from error
    # Comments are stripped for structural inspection; only real Rocq execution
    # can validate theorem bodies and dependency closure.
    clean = re.sub(r"\(\*.*?\*\)", "", source, flags=re.S)
    bad = (
        r"\b(?:Admitted|admit|Axiom|Axioms|Parameter|Parameters|Hypothesis|Hypotheses|"
        r"Conjecture|Abort|Opaque|Declare|Set\s+Universe\s+Polymorphism)\b",
        r"^\s*Load\b", r"^\s*Require\s+Import\b",
        r"^\s*From\s+(?!Stdlib\b)",
        r"\b(?:native_compute|vm_cast_no_check|unsafe)\b",
    )
    if any(re.search(p, clean, flags=re.I | re.M) for p in bad):
        raise RocqEvidenceError("unreviewed proof escape or import detected")
    inventory = re.findall(r"^(?:Theorem|Example)\s+([A-Za-z_]\w*)\b", clean, flags=re.M)
    audits = re.findall(r"^Print Assumptions\s+([A-Za-z_]\w*)\s*\.", clean, flags=re.M)
    if inventory != list(THEOREMS) or audits != list(THEOREMS):
        raise RocqEvidenceError("Rocq theorem or assumption audit inventory changed")
    if len(re.findall(r"\bQed\s*\.", clean)) != len(THEOREMS):
        raise RocqEvidenceError("Rocq proof completion inventory changed")
    return raw


def explicit_step(rule: int, row: tuple[int, ...]) -> tuple[int, ...]:
    if type(rule) is not int or not (0 <= rule <= 255) or (
        type(row) is not tuple or any(type(x) is not int or x not in (0, 1) for x in row)
    ):
        raise RocqEvidenceError("invalid explicit model input")
    out = []
    for pos, center in enumerate(row):
        left = row[pos - 1] if pos else 0
        right = row[pos + 1] if pos + 1 < len(row) else 0
        out.append((rule >> PATTERN_TABLE[left, center, right]) & 1)
    return tuple(out)


def finite_bridge() -> dict:
    count = 0
    for rule in range(256):
        for mask in range(16):
            row = tuple((mask >> (3 - i)) & 1 for i in range(4))
            if explicit_step(rule, row) != automata.reference_step(rule, row):
                raise RocqEvidenceError("explicit pattern model differs from canonical width-four corpus")
            count += 1
    if count != 4096 or automata.vectors_digest(automata.vectors()) != automata.EXPECTED_VECTORS_SHA256:
        raise RocqEvidenceError("canonical width-four corpus digest/count drift")
    for width in range(9):
        for mask in range(1 << width):
            row = tuple((mask >> (width - 1 - i)) & 1 for i in range(width))
            for rule in (0, 90, 255):
                out = explicit_step(rule, row)
                if len(out) != width:
                    raise RocqEvidenceError("variable-width finite model length drift")
                if rule == 0 and any(out):
                    raise RocqEvidenceError("rule 0 drift")
                if rule == 255 and any(x != 1 for x in out):
                    raise RocqEvidenceError("rule 255 drift")
                if rule == 90 and out != tuple(
                    (row[i - 1] if i else 0) ^ (row[i + 1] if i + 1 < width else 0)
                    for i in range(width)
                ):
                    raise RocqEvidenceError("rule 90 finite boundary drift")
    return {
        "status": "FINITE_BRIDGE_CHECKED",
        "automata4_cases": count,
        "canonical_vectors_sha256": automata.EXPECTED_VECTORS_SHA256,
        "finite_extra_widths": list(range(9)),
        "extra_rules": [0, 90, 255],
    }


def invoke(argv, cwd, timeout=120):
    return subprocess.run(argv, cwd=cwd, shell=False, check=False,
                          text=True, capture_output=True, timeout=timeout)


def run_rocq(root: Path = ROOT) -> dict:
    if shutil.which("rocq") is None:
        return {"status": "NOT_RUN", "reason": "Rocq 9.2.0 executable unavailable"}
    try:
        version = invoke(["rocq", "--version"], root, timeout=15)
        version_text = (version.stdout + version.stderr).strip()
        if version.returncode or not re.search(r"(?<!\d)9\.2\.0(?!\d)", version_text):
            return {"status": "VERSION_MISMATCH", "tool_version": version_text[:1000]}
        with tempfile.TemporaryDirectory(prefix="independence-rocq-") as tmp:
            copied = Path(tmp) / "Automata.v"
            copied.write_bytes(inspect_source(root))
            command = ["rocq", "compile", "-q", "-Q", ".", "IndependenceRocq", "Automata.v"]
            result = invoke(command, Path(tmp), timeout=180)
            raw_output = result.stdout + "\n" + result.stderr
            compiled = Path(tmp) / "Automata.vo"
            # Print Assumptions emits a separate "Closed under the global context"
            # response per named theorem when there are no additional axioms.
            closed = raw_output.count("Closed under the global context")
            clean = result.returncode == 0 and compiled.is_file() and (
                compiled.stat().st_size > 0) and closed == len(THEOREMS) and (
                "Axioms:" not in raw_output)
            return {
                "status": "KERNEL_CHECKED" if clean else "FAILED_OR_UNRESOLVED",
                "version": version_text,
                "command": command,
                "exit_code": result.returncode,
                "compiled_vo_sha256": sha(compiled.read_bytes()) if compiled.is_file() else None,
                "assumption_audit": {
                    "no_extra_axioms_reported": clean,
                    "closed_theorems": closed,
                    "expected_theorems": len(THEOREMS),
                },
                "raw_output": raw_output[:30000],
                "raw_output_sha256": sha(raw_output.encode("utf-8")),
            }
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        return {"status": "FAILED_OR_UNRESOLVED", "reason": str(error)}


def inspect(root: Path = ROOT, execute: bool = False) -> dict:
    source_bytes = inspect_source(root)
    bridge = finite_bridge()
    result = {
        "protocol": PROTOCOL,
        "rocq_version_pin": PIN,
        "source_sha256": sha(source_bytes),
        "source_git_blob_sha1": SOURCE_BLOB,
        "model": "binary elementary automaton; fixed-zero exterior; simultaneous update; finite rows of arbitrary length",
        "theorems": list(THEOREMS),
        "finite_bridge": bridge,
        "rocq": {"status": "NOT_RUN"},
        "independent_execution_attestation": False,
        "limitations": [
            "Only a genuine Rocq compile with each assumption audit closed is a kernel-checked result.",
            "Rocq mathematical equivalence does not prove implementation-level JavaScript/Ada refinement.",
            "The finite Python bridge is not an arbitrary-width theorem.",
            "Tool output and source hashes do not independently authenticate who executed a compiler.",
        ],
    }
    if execute:
        result["rocq"] = run_rocq(root)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-rocq", action="store_true")
    ap.add_argument("--require-rocq", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args(argv)
    try:
        record = inspect(execute=args.run_rocq or args.require_rocq)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2, sort_keys=True))
        if args.require_rocq and record["rocq"]["status"] != "KERNEL_CHECKED":
            return 1
        if args.run_rocq and record["rocq"]["status"] != "KERNEL_CHECKED":
            return 1
        return 0
    except (OSError, ValueError, UnicodeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
