#!/usr/bin/env python3
"""Source/spec integrity and optional GNATprove runner. NOT a substitute for proof."""
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
FILES = ("reference_kernel.ads", "reference_kernel.adb", "kernel.gpr",
         "reference_cli.adb", "cli.gpr")
FORBIDDEN = (r"\bpragma\s+Assume\b", r"\bSkip_Proof\b",
             r"\bSkip_Flow_And_Proof\b", r"\bpragma\s+Annotate\b")


def inspect_sources(root: Path = ROOT):
    folder = root / "formal" / "spark"
    data = json.loads((root / "formal/spec/kernel-v1.json").read_text(encoding="utf-8"))
    if data.get("protocol") != "INDEPENDENCE-KERNEL-SPEC/1" or data.get("schema_version") != 1:
        raise ValueError("incorrect kernel specification identity")
    if data.get("proof_status") != "NOT_RUN":
        raise ValueError("static specification may not assert proof success")
    if set(data.get("semantics", {})) != {
        "address", "decode", "parity_add", "parity_mul",
        "phase_add", "edge_valid", "edge_step"
    }:
        raise ValueError("incomplete kernel semantics")
    src = {}
    for name in FILES:
        src[name] = (folder / name).read_bytes()
        if not src[name]:
            raise ValueError("empty Ada source: " + name)
    for name in ("reference_kernel.ads", "reference_kernel.adb"):
        value = src[name].decode("utf-8")
        if "SPARK_Mode => On" not in value:
            raise ValueError("Ada kernel must be declared in SPARK mode")
        for expr in FORBIDDEN:
            if re.search(expr, value, flags=re.I):
                raise ValueError("unreviewed proof exemption in " + name)
    if "Pre => Valid_Edge" not in src["reference_kernel.ads"].decode():
        raise ValueError("edge step must require validated endpoints")
    # GPR single-valued attributes must use a quoted scalar, never ("list").
    # Reject this project grammar error before optionally invoking GNATprove.
    for project, attributes in (
        ("kernel.gpr", {"Object_Dir": "obj"}),
        ("cli.gpr", {"Object_Dir": "obj", "Exec_Dir": "bin"}),
    ):
        project_text = src[project].decode("utf-8")
        for attribute, directory in attributes.items():
            clause = f'for {attribute} use "{directory}";'
            if project_text.count(clause) != 1:
                raise ValueError("GPR single-valued directory attribute invalid: " +
                                 project + ": " + attribute)
        if project_text.count('for Create_Missing_Dirs use "True";') != 1:
            raise ValueError("GPR missing-directory creation flag absent: " + project)
    return {"spec": data["protocol"], "files_sha256": {
        key: hashlib.sha256(value).hexdigest() for key, value in sorted(src.items())
    }, "static_contracts": "INSPECTED_ONLY", "ada_contracts": "NOT_RUN"}


def run_gnatprove(root: Path = ROOT):
    record = inspect_sources(root)
    # Optional, local developer toolchain only; do not accept an arbitrary
    # executable path from caller input or source-controlled data.
    if shutil.which("gnatprove") is None:
        return {**record, "ada_contracts": "NOT_RUN", "reason": "gnatprove unavailable",
                "unproved_obligations": "UNKNOWN_UNTIL_EXECUTED"}
    command = ["gnatprove", "-P", "kernel.gpr", "-u", "reference_kernel.adb",
               "--mode=all", "--checks-as-errors=on", "--warnings=error",
               "--report=all", "--level=2"]
    try:
        # Static command/argument vectors and explicit shell=False prevent
        # shell interpretation; PATH remains a trusted local toolchain boundary.
        version = subprocess.run(["gnatprove", "--version"],
                                 cwd=root / "formal" / "spark", shell=False,
                                 capture_output=True, text=True, timeout=20, check=False)
        if version.returncode != 0:
            return {**record, "ada_contracts": "FAILED_OR_UNPROVED",
                    "reason": "gnatprove version check failed",
                    "tool_version": (version.stdout + version.stderr).strip()[:400],
                    "unproved_obligations": "UNKNOWN_UNTIL_EXECUTED"}
        result = subprocess.run(
            ["gnatprove", "-P", "kernel.gpr", "-u", "reference_kernel.adb",
             "--mode=all", "--checks-as-errors=on", "--warnings=error",
             "--report=all", "--level=2"],
            cwd=root / "formal" / "spark", shell=False,
            capture_output=True, text=True, timeout=120, check=False)
        output = result.stdout + "\n" + result.stderr
        lowered = output.lower()
        unresolved = bool(re.search(
            r"\b(unproved|not proved|no checks generated|skipped|assumed)\b", lowered
        ))
        has_evidence = bool(re.search(r"\b(proved|verified)\b", lowered))
        if result.returncode != 0 or unresolved:
            status = "FAILED_OR_UNPROVED"
        elif not has_evidence:
            status = "INCONCLUSIVE_NO_PROOF_EVIDENCE"
        else:
            status = "GNATPROVE_REPORTED_DISCHARGED"
        return {**record, "ada_contracts": status,
                "tool_version": (version.stdout + version.stderr).strip()[:400],
                "command": command, "exit_code": result.returncode,
                "proof_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "proof_output": output[:16000],
                "note": "Only the analyzed kernel and stated assumptions are in scope"}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {**record, "ada_contracts": "NOT_RUN", "reason": str(error),
                "unproved_obligations": "UNKNOWN_UNTIL_EXECUTED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prove", action="store_true")
    parser.add_argument("--require-proved", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_gnatprove() if (args.prove or args.require_proved) else inspect_sources()
    except (OSError, UnicodeError, ValueError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    content = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    print(content, end="")
    if args.require_proved and report["ada_contracts"] != "GNATPROVE_REPORTED_DISCHARGED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
