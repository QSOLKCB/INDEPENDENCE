#!/usr/bin/env python3
"""v0.9 bounded automata proof lab: separate finite, Lean, GNATprove, Ada, JS evidence.

All executable tools are optional; missing tools never produce a success claim.
The code is Python stdlib-only. Source inspection is NOT a formal proof.
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

ROOT = Path(__file__).resolve().parent.parent
SPEC = Path("formal/spec/automata4-v1.json")
LEAN = Path("formal/lean/AutomataReference.lean")
SPARK = Path("formal/spark")
ADA_FILES = ("automata_reference.ads", "automata_reference.adb",
             "automata_cli.adb", "automata.gpr", "automata_cli.gpr")
PIN = "leanprover/lean4:v4.35.0"
SPEC_BLOB = "2bd84f210260a61dc8c7541516a5b4a02cb26089"
THEOREMS = ("pattern_bounded", "rule_zero_cell", "rule_all_cell",
            "rule_zero_row", "rule_all_row", "rule90_known_row")
PREFIX = "IndependenceAutomata."
ALLOWED_AXIOMS = {"propext", "Quot.sound", "Classical.choice"}
PROTOCOL = "AUTOMATA4-FORMAL-LAB/1"
EXPECTED_VECTORS_SHA256 = "f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635"
FORBIDDEN_LEAN = (r"\bsorry\b", r"\badmit\b", r"\bnative_decide\b",
                  r"\bunsafe\b", r"\bpartial\b", r"\brun_tac\b",
                  r"^\s*(?:axiom|constant|opaque|elab|macro|syntax)\b",
                  r"^\s*#eval\b", r"trustCompiler", r"set_option\s+kernelChecking")
FORBIDDEN_SPARK = (r"\bpragma\s+Assume\b", r"\bSkip_Proof\b",
                   r"\bSkip_Flow_And_Proof\b", r"\bpragma\s+Annotate\b")
NEGATIVES = ((256, 0, 0, 0, 0), (0, 2, 0, 0, 0), (0, 0, 0, 0, 2),
             (0, 0, 0, 0), (0, 0, 0, 0, 0, 0),
             ("2#90#", "0", "0", "0", "0"), ("+90", "0", "0", "0", "0"),
             ("90", "0", "0", "0", "1_0"), ("-1", "0", "0", "0", "0"),
             ("", "0", "0", "0", "0"))


class FormalLabError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_hash(path: Path) -> str:
    return sha(path.read_bytes())


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def reference_step(rule: int, bits: tuple[int, int, int, int]) -> tuple[int, ...]:
    if type(rule) is not int or not 0 <= rule <= 255 or type(bits) is not tuple or len(bits) != 4 or any(type(x) is not int or x not in (0, 1) for x in bits):
        raise FormalLabError("invalid reference vector")
    padded = (0,) + bits + (0,)
    return tuple((rule // (2 ** (4 * padded[i] + 2 * padded[i+1] + padded[i+2]))) % 2 for i in range(4))


def vectors():
    for rule in range(256):
        for mask in range(16):
            bits = tuple((mask >> (3 - i)) & 1 for i in range(4))
            expected = reference_step(rule, bits)
            yield [rule, *bits, "".join(map(str, expected))]


def vectors_digest(rows) -> str:
    return sha(json.dumps(rows, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def inspect(root: Path = ROOT):
    raw = (root / SPEC).read_bytes()
    if git_blob(raw) != SPEC_BLOB:
        raise FormalLabError("unreviewed AUTOMATA4 specification change")
    spec = json.loads(raw)
    if (spec["protocol"] != "INDEPENDENCE-AUTOMATA4-SPEC/1"
        or spec["formal_status"] != "NOT_RUN"
        or spec["execution_status"] != "NOT_RUN"
        or spec["domain"] != {"width": 4, "rule_min": 0, "rule_max": 255,
                              "cell_values": [0, 1], "row_count": 16, "cases": 4096}):
        raise FormalLabError("incorrect automata specification identity/status/domain")
    if (root / "lean-toolchain").read_text() != PIN + "\n":
        raise FormalLabError("Lean pin changed")
    lean = (root / LEAN).read_text()
    if not lean.startswith("import Lean\n") or "decide +kernel" not in lean:
        raise FormalLabError("Lean source is not kernel-audited")
    uncommented = "\n".join(line.split("--", 1)[0] for line in lean.splitlines())
    for pattern in FORBIDDEN_LEAN:
        if re.search(pattern, uncommented, flags=re.M | re.I):
            raise FormalLabError("unapproved Lean proof escape")
    if re.findall(r"^theorem\s+(\w+)\b", uncommented, re.M) != list(THEOREMS):
        raise FormalLabError("automata Lean theorem inventory differs")
    if re.findall(r"^#print axioms\s+([\w.]+)", uncommented, re.M) != [PREFIX + n for n in THEOREMS]:
        raise FormalLabError("missing or unexpected Lean axiom audit")
    files = {}
    for name in ADA_FILES:
        src = (root / SPARK / name).read_bytes()
        if not src:
            raise FormalLabError("empty Ada source: " + name)
        files[name] = sha(src)
        if name.endswith((".ads", ".adb")) and name != "automata_cli.adb":
            value = src.decode("utf-8")
            if "SPARK_Mode => On" not in value:
                raise FormalLabError("Ada kernel lacks SPARK mode")
            for pattern in FORBIDDEN_SPARK:
                if re.search(pattern, value, flags=re.I):
                    raise FormalLabError("unreviewed SPARK assumption/escape")
    for name, object_dir in (("automata.gpr", "automata_obj"),
                             ("automata_cli.gpr", "automata_cli_obj")):
        value = (root / SPARK / name).read_text()
        if f'for Object_Dir use "{object_dir}";' not in value or 'for Create_Missing_Dirs use "True";' not in value:
            raise FormalLabError("invalid GPR scalar directory")
    rows = list(vectors())
    if len(rows) != 4096 or vectors_digest(rows) != EXPECTED_VECTORS_SHA256:
        raise FormalLabError("finite corpus count/digest drift")
    for known in spec["expected_vectors"]:
        if list(reference_step(known["rule"], tuple(known["bits"]))) != known["output"]:
            raise FormalLabError("known vector disagrees with reference")
    js_hashes = {name: source_hash(root / name)
                 for name in ("lab/core.js", "scripts/check_automata_js.mjs")}
    return {
        "protocol": PROTOCOL,
        "spec_sha256": sha(raw),
        "javascript_files_sha256": js_hashes,
        "lean_source_sha256": source_hash(root / LEAN),
        "ada_files_sha256": dict(sorted(files.items())),
        "theorem_inventory": list(THEOREMS),
        "finite_cases": len(rows),
        "vectors_sha256": vectors_digest(rows),
        "reference_status": "FINITE_ENUMERATION_CHECKED",
        "lean": {"status": "NOT_RUN"},
        "spark": {"status": "NOT_RUN"},
        "ada": {"status": "NOT_RUN"},
        "javascript": {"status": "NOT_RUN"},
        "independent_execution_attestation": False,
        "limitations": [
            "Finite enumeration of 4096 width-four cases is not universal correctness.",
            "Lean, SPARK, Ada and JavaScript evidence classes are independent.",
            "An absent compiler or executable cannot be counted as proof.",
            "Tool output and SHA-256 receipts are not independent provenance attestation."
        ],
    }


def invoke(argv: list[str], cwd: Path, timeout: int):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          shell=False, timeout=timeout, check=False)


def check_lean(root: Path):
    if shutil.which("lean") is None:
        return {"status": "NOT_RUN", "reason": "Lean executable not found"}
    try:
        version = invoke(["lean", "--version"], root, 20)
        ver = (version.stdout + version.stderr).strip()
        if version.returncode or not re.search(r"\bLean\s+\(version\s+4\.35\.0[,)]", ver):
            return {"status": "VERSION_MISMATCH", "tool_version": ver[:500]}
        command = ["lean", "--trust=0", LEAN.as_posix()]
        result = invoke(command, root, 180)
        output = result.stdout + "\n" + result.stderr
        audits = {}
        for name in THEOREMS:
            key = PREFIX + name
            if f"'{key}' does not depend on any axioms" in output:
                audits[name] = []
                continue
            match = re.search(r"'" + re.escape(key) + r"' depends on axioms:\s*\[([^\]\n]*)\]", output)
            if match is None:
                audits[name] = ["MISSING_AXIOM_AUDIT"]
                continue
            axioms = [x.strip() for x in match.group(1).split(",") if x.strip()]
            audits[name] = axioms
        clean = result.returncode == 0 and all(all(a in ALLOWED_AXIOMS for a in xs) for xs in audits.values())
        return {"status": "KERNEL_CHECKED" if clean else "FAILED_OR_UNRESOLVED",
                "tool_version": ver, "command": command, "exit_code": result.returncode,
                "axiom_audit": audits, "raw_output": output[:30000],
                "raw_output_sha256": sha(output.encode("utf-8"))}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED_OR_UNRESOLVED", "reason": str(exc)}


def check_spark(root: Path):
    if shutil.which("gnatprove") is None:
        return {"status": "NOT_RUN", "reason": "GNATprove unavailable"}
    command = ["gnatprove", "-P", "automata.gpr", "-u", "automata_reference.adb",
               "--mode=all", "--checks-as-errors=on", "--warnings=error",
               "--report=all", "--level=2"]
    try:
        v = invoke(["gnatprove", "--version"], root / SPARK, 25)
        if v.returncode:
            return {"status": "FAILED_OR_UNPROVED", "reason": "GNATprove version failed"}
        x = invoke(command, root / SPARK, 180)
        output = x.stdout + "\n" + x.stderr
        match = re.search(r"Success:\s+all checks proved\s+\(([1-9][0-9]*) checks\)\.", output)
        bad = re.search(r"\b(?:unproved|not proved|skipped|assumed|no checks generated)\b", output, re.I)
        ok = x.returncode == 0 and match is not None and bad is None
        return {"status": "GNATPROVE_REPORTED_DISCHARGED" if ok else "FAILED_OR_UNPROVED",
                "tool_version": (v.stdout + v.stderr).strip()[:2000], "command": command,
                "exit_code": x.returncode, "checks": int(match.group(1)) if ok else 0,
                "raw_output": output[:30000], "raw_output_sha256": sha(output.encode("utf-8"))}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED_OR_UNPROVED", "reason": str(exc)}


def check_ada(root: Path, rows: list):
    if shutil.which("gprbuild") is None:
        return {"status": "NOT_RUN", "reason": "GPRbuild unavailable"}
    try:
        with tempfile.TemporaryDirectory(prefix="independence-automata-") as dirname:
            temp = Path(dirname)
            for name in ADA_FILES:
                (temp / name).write_bytes((root / SPARK / name).read_bytes())
            command = ["gprbuild", "-P", "automata_cli.gpr", "-p", "-f"]
            build = invoke(command, temp, 120)
            output = build.stdout + "\n" + build.stderr
            if build.returncode:
                return {"status": "FAILED_OR_MISMATCH", "stage": "BUILD", "exit_code": build.returncode, "build_output": output[-12000:]}
            binary = temp / "automata_bin" / "automata_cli"
            if not binary.is_file():
                return {"status": "FAILED_OR_MISMATCH", "stage": "MISSING_BINARY"}
            for index, row in enumerate(rows):
                proc = subprocess.run([str(binary), *map(str, row[:5])],
                                      cwd=temp, capture_output=True, timeout=3,
                                      shell=False, check=False)
                if proc.returncode != 0 or proc.stdout != ("OK:" + row[5] + "\n").encode("ascii") or proc.stderr:
                    return {"status": "FAILED_OR_MISMATCH", "stage": "VECTOR", "index": index,
                            "expected": row[5], "actual_bytes": repr(proc.stdout[:100])}
            for args in NEGATIVES:
                proc = subprocess.run([str(binary), *map(str, args)],
                                      cwd=temp, capture_output=True, timeout=3,
                                      shell=False, check=False)
                if proc.returncode != 0 or proc.stdout != b"ERR:INVALID\n" or proc.stderr:
                    return {"status": "FAILED_OR_MISMATCH", "stage": "INVALID_INPUT",
                            "args": list(args), "actual_bytes": repr(proc.stdout[:100])}
            return {"status": "LOCAL_ADA_FINITE_EXECUTED_UNATTESTED",
                    "command": command, "build_exit_code": build.returncode,
                    "build_output": output[:30000], "build_output_sha256": sha(output.encode()),
                    "binary_sha256": source_hash(binary),
                    "cases": len(rows), "invalid_cases": len(NEGATIVES),
                    "vectors_sha256": vectors_digest(rows)}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED_OR_MISMATCH", "reason": str(exc)}


def check_js(root: Path, expected_sha: str):
    if shutil.which("node") is None:
        return {"status": "NOT_RUN", "reason": "Node developer tool unavailable"}
    cmd = ["node", "scripts/check_automata_js.mjs"]
    try:
        proc = invoke(cmd, root, 120)
        if proc.returncode:
            return {"status": "FAILED_OR_MISMATCH", "exit_code": proc.returncode, "raw_output": proc.stderr[:4000]}
        obj = json.loads(proc.stdout)
        if set(obj) != {"protocol", "status", "cases", "vectors_sha256", "limitation"} or (
            obj["protocol"] != "AUTOMATA4-JS-EVIDENCE/1"
            or obj["status"] != "LOCAL_JS_FINITE_EXECUTED"
            or type(obj["cases"]) is not int or obj["cases"] != 4096
            or obj["vectors_sha256"] != expected_sha
        ):
            return {"status": "FAILED_OR_MISMATCH", "reason": "JS result differs from independent corpus"}
        return {**obj, "command": cmd, "tool_version": "node developer tool", "independent_execution_attestation": False}
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED_OR_MISMATCH", "reason": str(exc)}


def check(root=ROOT, run_lean=False, run_spark=False, run_ada=False, run_js=False):
    record = inspect(root)
    if run_lean:
        record["lean"] = check_lean(root)
    if run_spark:
        record["spark"] = check_spark(root)
    rows = list(vectors())
    if run_ada:
        record["ada"] = check_ada(root, rows)
    if run_js:
        record["javascript"] = check_js(root, record["vectors_sha256"])
    return record


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-lean", action="store_true")
    ap.add_argument("--run-spark", action="store_true")
    ap.add_argument("--run-ada", action="store_true")
    ap.add_argument("--run-js", action="store_true")
    ap.add_argument("--require-all", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args(argv)
    try:
        r = check(run_lean=args.run_lean or args.require_all,
                  run_spark=args.run_spark or args.require_all,
                  run_ada=args.run_ada or args.require_all,
                  run_js=args.run_js or args.require_all)
    except (OSError, ValueError, UnicodeError, TypeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    encoded = json.dumps(r, sort_keys=True, indent=2) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        except OSError as error:
            print("FAIL: unable to write evidence: " + str(error), file=sys.stderr)
            return 1
    print(encoded, end="")
    failed = (
        ((args.run_lean or args.require_all) and r["lean"]["status"] != "KERNEL_CHECKED")
        or ((args.run_spark or args.require_all) and r["spark"]["status"] != "GNATPROVE_REPORTED_DISCHARGED")
        or ((args.run_ada or args.require_all) and r["ada"]["status"] != "LOCAL_ADA_FINITE_EXECUTED_UNATTESTED")
        or ((args.run_js or args.require_all) and r["javascript"]["status"] != "LOCAL_JS_FINITE_EXECUTED")
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
