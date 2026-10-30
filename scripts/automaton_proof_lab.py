#!/usr/bin/env python3
"""AUTOMATON-PROOF-LAB/1: finite independent vectors and optional real proof tools.

A source audit, vector comparison or self-hashed receipt does NOT attest execution
or establish production-program refinement. No packages or network access needed.
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
SPEC = "formal/spec/automaton-v1.json"
LEAN = "formal/lean/AutomatonFinite.lean"
ADA = ("formal/spark/automaton_kernel.ads", "formal/spark/automaton_kernel.adb",
       "formal/spark/automaton_cli.adb", "formal/spark/automaton.gpr")
THEOREMS = ("index_lt_eight", "zero_rule", "full_rule", "rule90_xor",
            "left_boundary_rule90")
ADA_RULES = (0, 1, 4, 15, 30, 45, 60, 75, 90, 105, 110, 120, 135, 150, 200, 255)
INVALID = (("256", "0", "0", "0"), ("90", "2", "0", "0"),
           ("90", "0", "2", "0"), ("90", "0", "0", "2"),
           ("+90", "0", "0", "0"), ("-1", "0", "0", "0"),
           ("2#90#", "0", "0", "0"), ("", "0", "0", "0"))
LIMITATIONS = (
    "Lean theorems concern the finite model, not browser JavaScript.",
    "GNATprove checks only Ada kernel contracts, not the CLI input boundary.",
    "Passing bounded vectors is not a universal refinement proof.",
    "Local evidence and SHA-256 hashes do not authenticate tool execution.",
)


class LabError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_gate(root: Path = ROOT) -> dict:
    spec_raw = (root / SPEC).read_bytes()
    spec = json.loads(spec_raw)
    if (spec.get("protocol"), spec.get("version"), spec.get("rule_range"),
            spec.get("bit_range"), spec.get("fixed_zero_boundary")) != (
            "AUTOMATON-SEMANTICS/1", 1, [0, 255], [0, 1], True):
        raise LabError("automaton specification changed without a version bump")
    if spec.get("neighbourhood_index") != "4*left + 2*center + right" or (
            spec.get("next_bit") != "floor(rule / (2 ** neighbourhood_index)) % 2"):
        raise LabError("automaton arithmetic semantics changed")
    if (root / "lean-toolchain").read_text() != "leanprover/lean4:v4.35.0\n":
        raise LabError("Lean toolchain not pinned")
    lean = (root / LEAN).read_text()
    stripped = "\n".join(line.split("--", 1)[0] for line in lean.splitlines())
    if re.search(r"\b(sorry|admit|unsafe|native_decide|run_tac|partial|axiom|opaque)\b",
                 stripped):
        raise LabError("Lean proof escape in source")
    if "import Lean" not in stripped:
        raise LabError("Lean source missing standard import")
    if re.findall(r"^theorem\s+(\w+)\b", stripped, re.M) != list(THEOREMS):
        raise LabError("Lean theorem inventory changed")
    audits = re.findall(r"^#print axioms\s+([\w.]+)", stripped, re.M)
    if audits != ["IndependenceAutomaton." + name for name in THEOREMS]:
        raise LabError("Lean transitive axiom audit inventory changed")
    for name in ADA[:2]:
        body = (root / name).read_text()
        if "SPARK_Mode => On" not in body or re.search(
                r"\bpragma\s+(Assume|Annotate)\b|\bSkip_Proof\b", body, re.I):
            raise LabError("Ada SPARK boundary or proof escape invalid")
    gpr = (root / ADA[3]).read_text()
    for clause in ('for Object_Dir use "obj";', 'for Exec_Dir use "bin";',
                   'for Create_Missing_Dirs use "True";'):
        if gpr.count(clause) != 1:
            raise LabError("invalid Ada project directory policy")
    return {"spec_sha256": sha(spec_raw), "lean_sha256": sha((root / LEAN).read_bytes()),
            "ada_sha256": {name: sha((root / name).read_bytes()) for name in ADA},
            "source_status": "INSPECTED_NOT_PROVED"}


def oracle(rule: int, left: int, center: int, right: int) -> int:
    if (any(type(v) is not int for v in (rule, left, center, right))
            or not 0 <= rule <= 255
            or any(v not in (0, 1) for v in (left, center, right))):
        raise LabError("invalid automaton operands")
    index = 4 * left + 2 * center + right
    return (rule // (2 ** index)) % 2


def independent_bit(rule: int, left: int, center: int, right: int) -> int:
    index = (left << 2) | (center << 1) | right
    return (rule >> index) & 1


def vectors():
    for rule in range(256):
        for left in (0, 1):
            for center in (0, 1):
                for right in (0, 1):
                    yield rule, left, center, right


def vector_bytes() -> bytes:
    return "".join("%d,%d,%d,%d:%d\n" % (*args, oracle(*args))
                   for args in vectors()).encode("ascii")


def finite_check() -> dict:
    cases = 0
    for args in vectors():
        if oracle(*args) != independent_bit(*args):
            raise LabError("independent arithmetic oracle mismatch")
        cases += 1
    for rule in range(256):
        for bit in (0, 1):
            # The one-cell row has two fixed-zero neighbours.
            if oracle(rule, 0, bit, 0) != (rule >> (2 * bit)) & 1:
                raise LabError("fixed-zero boundary mismatch")
    return {"status": "FINITE_ORACLE_AGREEMENT", "neighbourhood_cases": cases,
            "single_cell_boundary_cases": 512, "vector_sha256": sha(vector_bytes())}


def _run(cmd: list[str], root: Path, timeout: int = 120):
    return subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                          shell=False, check=False, timeout=timeout)


def check_lean(root: Path = ROOT) -> dict:
    if shutil.which("lean") is None:
        return {"status": "NOT_RUN", "reason": "Lean 4 executable unavailable"}
    try:
        version = _run(["lean", "--version"], root, 20)
        version_text = (version.stdout + version.stderr).strip()
        if version.returncode or not re.search(r"\bLean\s+\(version\s+4\.35\.0[,)]",
                                               version_text):
            return {"status": "VERSION_MISMATCH", "tool_version": version_text[:400]}
        command = ["lean", "--trust=0", LEAN]
        run = _run(command, root, 180)
        log = run.stdout + "\n" + run.stderr
        audits = {}
        for theorem in THEOREMS:
            name = "IndependenceAutomaton." + theorem
            if ("'" + name + "' does not depend on any axioms") in log:
                audits[theorem] = []
            else:
                match = re.search("'" + re.escape(name) +
                                  r"' depends on axioms:\s*\[([^\]\n]*)\]", log)
                if not match:
                    break
                found = [part.strip() for part in match.group(1).split(",") if part.strip()]
                if any(part not in {"propext", "Quot.sound", "Classical.choice"}
                       for part in found):
                    break
                audits[theorem] = found
        checked = run.returncode == 0 and len(audits) == len(THEOREMS)
        return {"status": "KERNEL_CHECKED" if checked else "FAILED_OR_UNRESOLVED",
                "tool_version": version_text, "command": command,
                "exit_code": run.returncode, "axiom_audit": audits,
                "raw_output_sha256": sha(log.encode()), "raw_output": log[:30000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "NOT_RUN", "reason": str(exc)}


def check_spark(root: Path = ROOT) -> dict:
    if shutil.which("gnatprove") is None:
        return {"status": "NOT_RUN", "reason": "GNATprove unavailable"}
    cwd = root / "formal/spark"
    cmd = ["gnatprove", "-P", "automaton.gpr", "-u", "automaton_kernel.adb",
           "--mode=all", "--checks-as-errors=on", "--warnings=error",
           "--report=all", "--level=2"]
    try:
        ver = _run(["gnatprove", "--version"], cwd, 20)
        if ver.returncode:
            return {"status": "FAILED_OR_UNRESOLVED", "reason": "version query failed"}
        run = _run(cmd, cwd, 180)
        log = run.stdout + "\n" + run.stderr
        problematic = re.search(r"\b(unproved|not proved|skipped|assumed|no checks generated)\b",
                                log, re.I)
        checked = (run.returncode == 0 and not problematic
                   and bool(re.search(r"\bproved\b", log, re.I)))
        return {"status": "GNATPROVE_REPORTED_DISCHARGED" if checked
                else "FAILED_OR_UNRESOLVED", "tool_version": (ver.stdout + ver.stderr).strip(),
                "command": cmd, "exit_code": run.returncode,
                "raw_output_sha256": sha(log.encode()), "raw_output": log[:16000]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "NOT_RUN", "reason": str(exc)}


def compare_ada(executable: Path | None, root: Path = ROOT) -> dict:
    if executable is None:
        return {"status": "NOT_RUN", "reason": "no compiled Ada CLI supplied"}
    candidate = executable.resolve()
    if not candidate.is_file():
        return {"status": "NOT_RUN", "reason": "Ada CLI path unavailable"}
    checked = 0
    try:
        for rule in ADA_RULES:
            for left in (0, 1):
                for center in (0, 1):
                    for right in (0, 1):
                        args = (rule, left, center, right)
                        run = _run([str(candidate), *map(str, args)], root, 5)
                        expected = "OK:" + str(oracle(*args)) + "\n"
                        if run.returncode or run.stdout != expected or run.stderr:
                            return {"status": "FAILED_OR_MISMATCH", "case": list(args),
                                    "checked": checked}
                        checked += 1
        for args in INVALID:
            run = _run([str(candidate), *args], root, 5)
            if run.returncode or run.stdout != "ERR:INVALID\n" or run.stderr:
                return {"status": "FAILED_OR_MISMATCH", "invalid_case": list(args),
                        "checked": checked}
        return {"status": "FINITE_ADA_AGREEMENT_UNATTESTED", "checked": checked,
                "rejected": len(INVALID), "binary_sha256": sha(candidate.read_bytes()),
                "note": "Supplied executable not independently authenticated."}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED_OR_MISMATCH", "reason": str(exc), "checked": checked}


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise LabError("duplicate JSON key")
        out[key] = value
    return out


def verify_browser_receipt(path: Path) -> dict:
    def bad_float(_):
        raise LabError("non-integer JSON number")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique,
                              parse_float=bad_float, parse_constant=bad_float)
        if type(envelope) is not dict or set(envelope) != {
                "format", "sha256", "payload_text"}:
            raise LabError("wrong receipt envelope")
        payload = envelope["payload_text"]
        if type(payload) is not str or len(payload) > 10000:
            raise LabError("unbounded receipt payload")
        if envelope["format"] != "AUTOMATON-BROWSER-RECEIPT/1" or (
                envelope["sha256"] != sha(payload.encode())):
            raise LabError("bad receipt digest or format")
        data = json.loads(payload, object_pairs_hook=_unique,
                          parse_float=bad_float, parse_constant=bad_float)
        expected = {"protocol": "AUTOMATON-BROWSER/1", "status": "FINITE_JS_CONFORMANCE",
                    "neighbourhood_cases": 2048, "boundary_cases": 512,
                    "vector_sha256": sha(vector_bytes()),
                    "proof_status": "NOT_A_FORMAL_PROOF"}
        if data != expected:
            raise LabError("reported browser vectors or status do not match reference")
        return {"status": "INTERNALLY_CONSISTENT_UNATTESTED", "vector_sha256":
                expected["vector_sha256"]}
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise LabError("invalid browser receipt: " + str(exc)) from exc


def run(root: Path = ROOT, *, prove: bool = False,
        ada_cli: Path | None = None, browser_receipt: Path | None = None) -> dict:
    sources = source_gate(root)
    report = {"protocol": "AUTOMATON-PROOF-LAB/1", "sources": sources,
              "finite": finite_check(),
              "lean": check_lean(root) if prove else {"status": "NOT_RUN"},
              "spark": check_spark(root) if prove else {"status": "NOT_RUN"},
              "ada_cli": compare_ada(ada_cli, root),
              "browser": verify_browser_receipt(browser_receipt) if browser_receipt
                         else {"status": "NOT_RUN"},
              "limitations": list(LIMITATIONS)}
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prove", action="store_true",
                        help="run REAL pinned Lean and GNATprove (optional developer tools)")
    parser.add_argument("--require-proofs", action="store_true",
                        help="exit nonzero unless both actual proof tool runs pass")
    parser.add_argument("--ada-cli", type=Path,
                        help="optional precompiled automaton_cli executable")
    parser.add_argument("--require-ada", action="store_true",
                        help="exit nonzero unless a real Ada comparison passes")
    parser.add_argument("--browser-receipt", type=Path,
                        help="verify locally exported browser vector receipt")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run(prove=args.prove or args.require_proofs,
                     ada_cli=args.ada_cli, browser_receipt=args.browser_receipt)
        data = json.dumps(report, sort_keys=True, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(data, encoding="utf-8")
        print(data, end="")
        if args.require_proofs and (
                report["lean"]["status"] != "KERNEL_CHECKED" or
                report["spark"]["status"] != "GNATPROVE_REPORTED_DISCHARGED"):
            return 1
        if args.require_ada and (
                report["ada_cli"]["status"] != "FINITE_ADA_AGREEMENT_UNATTESTED"):
            return 1
        return 0
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
