#!/usr/bin/env python3
"""Offline Lean source audit and opt-in *real* kernel checker (stdlib only).

No Lean toolchain present => NOT_RUN. A static inspection is never a proof.
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

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path("formal/lean/FiniteFoundation.lean")
PIN = "leanprover/lean4:v4.35.0"
VERSION = "4.35.0"
THEOREMS = (
    "crt_left_inverse", "crt_right_inverse",
    "gf2_add_comm", "gf2_add_assoc", "gf2_add_self",
    "gf2_mul_comm", "gf2_left_distrib",
    "phase_add_comm", "phase_add_assoc", "phase_zero",
    "monomial_irrefl", "monomial_trans", "monomial_translate",
)
PREFIX = "IndependenceLean."
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
FORBIDDEN = (
    r"\bsorry\b", r"\badmit\b", r"\bnative_decide\b",
    r"\brun_tac\b", r"\bunsafe\b", r"\bpartial\b",
    r"^\s*(?:axiom|constant|opaque|elab|macro|syntax)\b",
    r"^\s*#eval\b", r"trustCompiler", r"set_option\s+kernelChecking",
)


class LeanAuditError(ValueError):
    pass


def inspect(root: Path = ROOT) -> dict:
    toolchain = (root / "lean-toolchain").read_text(encoding="utf-8")
    if toolchain != PIN + "\n":
        raise LeanAuditError("Lean toolchain is not exactly pinned")
    raw = (root / SOURCE).read_bytes()
    if len(raw) > 100_000:
        raise LeanAuditError("Lean source too large")
    text = raw.decode("utf-8")
    lines = "\n".join(line.split("--", 1)[0] for line in text.splitlines())
    for pattern in FORBIDDEN:
        if re.search(pattern, lines, re.M | re.I):
            raise LeanAuditError("forbidden proof escape or meta construct: " + pattern)
    definitions = re.findall(r"^theorem\s+(\w+)\b", lines, re.M)
    if definitions != list(THEOREMS):
        raise LeanAuditError("theorem inventory differs from audited manifest")
    axioms = re.findall(r"^#print axioms\s+([\w.]+)\s*$", lines, re.M)
    if axioms != [PREFIX + theorem for theorem in THEOREMS]:
        raise LeanAuditError("missing or unexpected transitive-axiom audits")
    if "decide +kernel" not in text or "import Lean" not in lines:
        raise LeanAuditError("explicit kernel reduction and bundled Lean import missing")
    return {
        "protocol": "LEAN-FOUNDATION-EVIDENCE/1",
        "toolchain": PIN,
        "source": SOURCE.as_posix(),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "theorems_declared": list(THEOREMS),
        "source_audit": "PASSED",
        "kernel_check": "NOT_RUN",
        "scope": "Finite CRT (2,3), Boolean GF(2), cyclic Z/3Z and degree-lex order properties",
        "limitations": [
            "Formal proof execution is separately required; source inspection is not proof.",
            "CRT is restricted to moduli 2 and 3, not general coprime moduli.",
            "Monomial well-foundedness and totality remain unproved in this phase.",
            "This does not verify Ada, Python, JavaScript or Penrose graph geometry.",
        ],
    }


def parse_axiom_audit(log: str) -> tuple[bool, dict[str, list[str]]]:
    """Accept only explicitly printed and allowlisted transitive axiom lists."""
    result = {}
    for theorem in THEOREMS:
        name = PREFIX + theorem
        if f"'{name}' does not depend on any axioms" in log:
            result[theorem] = []
            continue
        match = re.search(
            r"'" + re.escape(name) + r"' depends on axioms:\s*\[([^\]\n]*)\]",
            log,
        )
        if not match:
            return False, result
        axioms = [s.strip() for s in match.group(1).split(",") if s.strip()]
        if any(a not in ALLOWED_AXIOMS for a in axioms):
            return False, {**result, theorem: axioms}
        result[theorem] = axioms
    return len(result) == len(THEOREMS), result


def check(root: Path = ROOT, require_checked: bool = False) -> dict:
    report = inspect(root)
    if not require_checked:
        return report
    if shutil.which("lean") is None:
        return {**report, "kernel_check": "NOT_RUN",
                "reason": "Lean executable not installed; no proof execution claimed"}
    try:
        version = subprocess.run(["lean", "--version"], cwd=root, shell=False,
                                 text=True, capture_output=True, timeout=20, check=False)
        version_text = (version.stdout + version.stderr).strip()
        if version.returncode != 0 or not re.search(
            r"\bLean\s+\(version\s+" + re.escape(VERSION) + r"[,)]", version_text
        ):
            return {**report, "kernel_check": "VERSION_MISMATCH",
                    "version_output": version_text[:500]}
        command = ["lean", "--trust=0", SOURCE.as_posix()]
        run = subprocess.run(command, cwd=root, shell=False,
                             text=True, capture_output=True, timeout=180, check=False)
        output = run.stdout + "\n" + run.stderr
        clean, audit = parse_axiom_audit(output)
        result = ("KERNEL_CHECKED" if run.returncode == 0 and clean
                  else "FAILED_OR_UNRESOLVED")
        return {
            **report,
            "kernel_check": result,
            "tool_version": version_text,
            "command": command,
            "exit_code": run.returncode,
            "axiom_audit": audit,
            "raw_output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
            "raw_output": output[:30000],
            "note": "Checking this Lean model does NOT establish Ada/Python/JS conformance.",
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {**report, "kernel_check": "NOT_RUN", "reason": str(error)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true",
                        help="invoke pinned Lean kernel when installed")
    parser.add_argument("--require-checked", action="store_true",
                        help="fail unless the actual pinned Lean kernel and axiom audit pass")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = check(require_checked=args.run or args.require_checked)
    except (OSError, UnicodeError, LeanAuditError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    content = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    return 1 if args.require_checked and result["kernel_check"] != "KERNEL_CHECKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
