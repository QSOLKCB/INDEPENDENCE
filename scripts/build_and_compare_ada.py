#!/usr/bin/env python3
"""Build archived Ada reference sources in isolation, then execute Python/Ada comparisons.

This is a local executable conformance experiment, not independent execution
attestation and not a proof of the CLI or Python implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from run_kernel_conformance import (
    ROOT, SEED, build_report, finite_cases, make_receipt, rejected_cases,
    lexical_cases,
)
from verify_kernel_receipt import verify as verify_bridge_receipt
from verify_spark_evidence_archive import verify as verify_spark_archive

PROTOCOL = "ADA-PYTHON-EXECUTION/1"
HISTORICAL_SHA = "9900e57f2283c534815657dd6c079d0e966715f4"
SNAPSHOT = Path("formal/evidence/spark/pr13/source")
SOURCES = ("cli.gpr", "reference_cli.adb", "reference_kernel.ads",
           "reference_kernel.adb")
BUILD_COMMAND = ["gprbuild", "-P", "cli.gpr", "-p", "-f"]
VERSION_COMMANDS = (("gprbuild", "--version"), ("gnatmake", "--version"))
LIMITATIONS = [
    "Local CLI execution and binary hashing do not independently attest the compiler, host, or run.",
    "The archived GNATprove result covers the SPARK kernel only; CLI input handling is unproved.",
    "Differential agreement covers the specified finite vectors, not arbitrary inputs or production JS.",
    "Lean mathematical results and SPARK contracts are separate from Python/Ada runtime equivalence.",
]


class ExecutionError(RuntimeError):
    def __init__(self, stage: str, description: str):
        super().__init__(description)
        self.stage = stage


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_process(argv: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    # Trusted developer PATH is the executable boundary. No shell or user-
    # supplied executable paths are interpreted here.
    try:
        return subprocess.run(argv, cwd=cwd, shell=False, check=False,
                              text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ExecutionError("COMPILER", f"{argv[0]} could not execute: {error}") from error


def tool_versions(working_directory: Path) -> dict[str, str]:
    versions = {}
    for command in VERSION_COMMANDS:
        if shutil.which(command[0]) is None:
            raise ExecutionError("TOOLCHAIN", command[0] + " not found on PATH")
        result = checked_process(list(command), working_directory, 25)
        if result.returncode != 0:
            raise ExecutionError("TOOLCHAIN", command[0] + " version command failed")
        version = (result.stdout + result.stderr).strip()
        if not version:
            raise ExecutionError("TOOLCHAIN", command[0] + " returned no version")
        versions[command[0]] = version[:1000]
    return versions


def copy_verified_sources(destination: Path, root: Path = ROOT) -> dict[str, str]:
    """Use the archived PR #13 source, never cached object files or moving main."""
    try:
        archive = verify_spark_archive(root)
    except (ValueError, OSError, TypeError) as error:
        raise ExecutionError("SOURCE", "SPARK source archive integrity failed: " + str(error)) from error
    if archive["archive_integrity"] != "PASS" or archive["historical_checkout"] != HISTORICAL_SHA:
        raise ExecutionError("SOURCE", "archived SPARK checkout identity mismatch")
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in SOURCES:
        source = root / SNAPSHOT / name
        # The archive verifier already binds these file bytes to pinned hashes.
        payload = source.read_bytes()
        target = destination / name
        target.write_bytes(payload)
        hashes[name] = sha(target)
        if hashes[name] != sha(source):
            raise ExecutionError("SOURCE", "Ada source changed while copying: " + name)
    return hashes


def execute(root: Path = ROOT, sample_count: int = 128, full: bool = False,
            seed: int = SEED, build_timeout: int = 180) -> dict:
    count = len(list(finite_cases())) if full else sample_count
    if (type(count) is not int or count < 7 or count > len(list(finite_cases()))
            or type(seed) is not int or not 0 <= seed <= 0xffffffff):
        raise ExecutionError("INPUT", "invalid Ada sample count or seed")
    if type(build_timeout) is not int or not 10 <= build_timeout <= 900:
        raise ExecutionError("INPUT", "invalid build timeout")
    with tempfile.TemporaryDirectory(prefix="independence-ada-") as temporary:
        directory = Path(temporary)
        source = directory / "spark"
        hashes = copy_verified_sources(source, root)
        versions = tool_versions(directory)
        result = checked_process(BUILD_COMMAND, source, build_timeout)
        if result.returncode != 0:
            log = (result.stdout + "\n" + result.stderr)[-12000:]
            raise ExecutionError("BUILD", f"gprbuild exited {result.returncode}:\n{log}")
        binary = source / "bin" / "reference_cli"
        if not binary.is_file() or not os.access(binary, os.X_OK):
            raise ExecutionError("BUILD", "compiled Ada CLI executable missing or not executable")
        binary_sha = sha(binary)
        try:
            # Reuses the independent Python oracle and the verified report format.
            report = build_report(ada_binary=binary, ada_cases=count, seed=seed)
            receipt = make_receipt(report)
            receipt_verification = verify_bridge_receipt(receipt)
        except (RuntimeError, ValueError, OSError) as error:
            raise ExecutionError("DIFFERENTIAL", str(error)) from error
        ada = report["evidence"]["ada_cli_conformance"]
        expected_total = count + len(rejected_cases()) + len(lexical_cases())
        if (ada["status"] != "ADA_CLI_TESTED_UNATTESTED"
                or ada["cases"] != expected_total
                or ada["binary_sha256"] != binary_sha
                or receipt_verification["valid"] is not True):
            raise ExecutionError("DIFFERENTIAL", "test record or bridge receipt inconsistent")
        return {
            "protocol": PROTOCOL,
            "status": "LOCAL_BUILD_AND_DIFFERENTIAL_PASSED_UNATTESTED",
            "historical_source_commit": HISTORICAL_SHA,
            "source_sha256": hashes,
            "tool_versions": versions,
            "build_command": BUILD_COMMAND,
            "build_exit_code": result.returncode,
            "build_output_sha256": hashlib.sha256(
                (result.stdout + "\n" + result.stderr).encode("utf-8")).hexdigest(),
            "binary_sha256": binary_sha,
            "seed": seed,
            "mode": "FULL_FINITE_SET" if full else "SEEDED_SAMPLE",
            "finite_cases_checked": count,
            "numeric_invalid_checked": len(rejected_cases()),
            "lexical_invalid_checked": len(lexical_cases()),
            "ada_processes_checked": ada["cases"],
            "vectors_sha256": ada["vectors_sha256"],
            "python_bridge_receipt": receipt,
            "bridge_receipt_verification": "SELF_CONSISTENT_ONLY",
            "independent_execution_attestation": False,
            "limitations": LIMITATIONS,
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="run all 8,881 finite vectors plus 22 invalid inputs")
    parser.add_argument("--samples", type=int, default=128,
                        help="seeded valid-input sample (default 128)")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--build-timeout", type=int, default=180)
    parser.add_argument("--output", type=Path, default=Path("ada-runtime-evidence.json"))
    args = parser.parse_args(argv)
    try:
        record = execute(ROOT, args.samples, args.full, args.seed, args.build_timeout)
    except ExecutionError as error:
        record = {
            "protocol": PROTOCOL,
            "status": "FAILED_OR_NOT_RUN",
            "stage": error.stage,
            "reason": str(error)[:12000],
            "historical_source_commit": HISTORICAL_SHA,
            "independent_execution_attestation": False,
            "note": "Do not claim compilation or Ada/Python agreement from this failure.",
        }
        code = 1
    except (OSError, ValueError, RuntimeError) as error:
        record = {
            "protocol": PROTOCOL,
            "status": "FAILED_OR_NOT_RUN",
            "stage": "UNEXPECTED",
            "reason": str(error)[:12000],
            "historical_source_commit": HISTORICAL_SHA,
            "independent_execution_attestation": False,
        }
        code = 1
    else:
        code = 0
    serialized = json.dumps(record, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        except OSError as error:
            print("FAIL: evidence output could not be written: " + str(error), file=sys.stderr)
            return 1
    print(serialized, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
