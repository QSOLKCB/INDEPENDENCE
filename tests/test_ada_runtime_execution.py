"""Orchestration security and fail-closed Ada compilation tests — mock compiler is not proof."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_and_compare_ada as runner  # noqa: E402
from run_kernel_conformance import run_ada, finite_cases


class AdaRuntimeExecutionTests(unittest.TestCase):
    def test_historical_sources_integrity_and_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            dest = Path(temporary) / "spark"
            hashes = runner.copy_verified_sources(dest)
            self.assertEqual(set(hashes), set(runner.SOURCES))
            for name in runner.SOURCES:
                self.assertEqual((dest / name).read_bytes(),
                                 (ROOT / runner.SNAPSHOT / name).read_bytes())
            self.assertFalse((dest / "bin/reference_cli").exists())

    def test_missing_compiler_is_fail_closed(self):
        with patch.object(runner.shutil, "which", return_value=None):
            with self.assertRaisesRegex(runner.ExecutionError, "not found on PATH") as failure:
                runner.execute()
        self.assertEqual(failure.exception.stage, "TOOLCHAIN")

    def test_invalid_case_counts_rejected_before_tool_execution(self):
        for count in (0, 6, 8882, -1, True):
            with self.subTest(count=count), patch.object(runner, "copy_verified_sources") as copy:
                with self.assertRaises(runner.ExecutionError) as failure:
                    runner.execute(sample_count=count)
                self.assertEqual(failure.exception.stage, "INPUT")
                copy.assert_not_called()

    def test_invalid_seed_and_timeouts_fail_closed(self):
        for options in ({"seed": -1}, {"seed": True},
                        {"build_timeout": 0}, {"build_timeout": 1000}):
            with self.subTest(options=options):
                with self.assertRaises(runner.ExecutionError) as failure:
                    runner.execute(**options)
                self.assertEqual(failure.exception.stage, "INPUT")

    def test_command_has_no_shell_or_untrusted_args(self):
        self.assertEqual(runner.BUILD_COMMAND,
                         ["gprbuild", "-P", "cli.gpr", "-p", "-f"])
        self.assertEqual(runner.VERSION_COMMANDS,
                         (("gprbuild", "--version"), ("gnatmake", "--version")))
        with patch.object(runner.subprocess, "run",
                          return_value=subprocess.CompletedProcess([], 0, "ok", "")) as call:
            runner.checked_process(["gprbuild", "--version"], ROOT, 20)
            self.assertIs(call.call_args.kwargs["shell"], False)
            self.assertIs(call.call_args.kwargs["check"], False)
            self.assertEqual(call.call_args.kwargs["cwd"], ROOT)

    @staticmethod
    def simulated_compiler(command, cwd, timeout):
        # Test fixture: synthetic shell output, never represented as Ada.
        out = cwd / "bin" / "reference_cli"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("#!/bin/sh\nprintf 'OK:999\\n'\n", encoding="utf-8")
        out.chmod(0o755)
        return subprocess.CompletedProcess(command, 0, stdout="synthetic build", stderr="")

    def test_fake_compiled_binary_does_not_pass_real_comparison(self):
        with patch.object(runner, "tool_versions",
                          return_value={"gprbuild": "fake", "gnatmake": "fake"}), \
             patch.object(runner, "checked_process",
                          side_effect=self.simulated_compiler):
            with self.assertRaisesRegex(runner.ExecutionError, "Ada mismatch") as failure:
                runner.execute(sample_count=7)
        self.assertEqual(failure.exception.stage, "DIFFERENTIAL")

    def test_nonzero_compilation_never_invokes_python_bridge(self):
        failed = subprocess.CompletedProcess([], 2, stdout="", stderr="mock compile error")
        with patch.object(runner, "tool_versions",
                          return_value={"gprbuild": "fake", "gnatmake": "fake"}), \
             patch.object(runner, "checked_process", return_value=failed), \
             patch.object(runner, "build_report") as bridge:
            with self.assertRaisesRegex(runner.ExecutionError, "gprbuild exited 2") as failure:
                runner.execute()
            self.assertEqual(failure.exception.stage, "BUILD")
            bridge.assert_not_called()

    def test_success_without_actual_binary_is_rejected(self):
        result = subprocess.CompletedProcess([], 0, stdout="mock output", stderr="")
        with patch.object(runner, "tool_versions",
                          return_value={"gprbuild": "fake", "gnatmake": "fake"}), \
             patch.object(runner, "checked_process", return_value=result), \
             patch.object(runner, "build_report") as bridge:
            with self.assertRaisesRegex(runner.ExecutionError, "executable missing") as failure:
                runner.execute()
            self.assertEqual(failure.exception.stage, "BUILD")
            bridge.assert_not_called()

    def test_raw_stdout_rejects_carriage_return_and_crlf(self):
        # Python text=True normalizes both malformed byte sequences to LF.
        # These subprocesses must be rejected at the byte-level boundary.
        for suffix in (r"\r", r"\r\n", r"\n\r"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temporary:
                stub = Path(temporary) / "wrong_newline"
                stub.write_text(
                    "#!/bin/sh\nprintf 'OK:0" + suffix + "'\n",
                    encoding="utf-8",
                )
                stub.chmod(0o755)
                with self.assertRaisesRegex(RuntimeError, "Ada mismatch"):
                    run_ada(stub, [("PARITY_ADD", (0, 0))])

    def test_raw_stdout_accepts_exact_lf(self):
        with tempfile.TemporaryDirectory() as temporary:
            stub = Path(temporary) / "good_line"
            stub.write_text("#!/bin/sh\nprintf 'OK:0\\n'\n", encoding="utf-8")
            stub.chmod(0o755)
            result = run_ada(stub, [("PARITY_ADD", (0, 0))])
            self.assertEqual(result["cases"], 1)
            self.assertEqual(result["status"], "ADA_CLI_TESTED_UNATTESTED")

    def test_cli_stdout_is_captured_in_binary_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            stub = Path(temporary) / "dummy"
            stub.write_bytes(b"fake binary fixture")
            fake = subprocess.CompletedProcess(
                ["fake"], 0, stdout=b"OK:0\n", stderr=b""
            )
            with patch("run_kernel_conformance.subprocess.run", return_value=fake) as call:
                result = run_ada(stub, [("PARITY_ADD", (0, 0))])
            self.assertEqual(result["cases"], 1)
            self.assertIs(call.call_args.kwargs["text"], False)
            self.assertIs(call.call_args.kwargs["capture_output"], True)

    def test_samples_full_domain_is_labelled_full_without_full_switch(self):
        # Mocked compiler and comparison isolate the mode selection without
        # impersonating 8,903 genuine Ada process executions.
        valid = len(list(finite_cases()))
        def fake_compiler(command, cwd, timeout):
            binary = cwd / "bin" / "reference_cli"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b"synthetic, not actual Ada")
            binary.chmod(0o755)
            return subprocess.CompletedProcess(command, 0, stdout="synthetic", stderr="")

        def fake_bridge(ada_binary, ada_cases, seed):
            self.assertEqual(ada_cases, valid)
            return {"evidence": {"ada_cli_conformance": {
                "status": "ADA_CLI_TESTED_UNATTESTED",
                "cases": valid + 22,
                "binary_sha256": runner.sha(ada_binary),
                "vectors_sha256": "a" * 64,
            }}}

        with patch.object(runner, "tool_versions", return_value={
                "gprbuild": "mock", "gnatmake": "mock",
             }), patch.object(runner, "checked_process", side_effect=fake_compiler), \
             patch.object(runner, "build_report", side_effect=fake_bridge) as compare, \
             patch.object(runner, "make_receipt", return_value={"synthetic": True}), \
             patch.object(runner, "verify_bridge_receipt", return_value={"valid": True}):
            output = runner.execute(sample_count=valid, full=False)
        self.assertEqual(output["mode"], "FULL_FINITE_SET")
        self.assertEqual(output["finite_cases_checked"], valid)
        self.assertEqual(output["ada_processes_checked"], valid + 22)
        self.assertEqual(compare.call_count, 1)

    def test_exact_stdout_rejects_extra_ada_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            stub = Path(temporary) / "fake"
            stub.write_text("#!/bin/sh\nprintf 'OK:0\\n\\n'\n", encoding="utf-8")
            stub.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError, "Ada mismatch"):
                run_ada(stub, [("PARITY_ADD", (0, 0))])

    def test_exact_stdout_rejects_trailing_spaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            stub = Path(temporary) / "fake"
            stub.write_text("#!/bin/sh\nprintf 'OK:0  \\n'\n", encoding="utf-8")
            stub.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError, "Ada mismatch"):
                run_ada(stub, [("PARITY_ADD", (0, 0))])

    def test_failed_run_writes_error_not_green_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "result.json"
            with patch.object(runner.shutil, "which", return_value=None):
                rc = runner.main(["--output", str(output)])
            self.assertEqual(rc, 1)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "FAILED_OR_NOT_RUN")
            self.assertEqual(record["stage"], "TOOLCHAIN")
            self.assertIs(record["independent_execution_attestation"], False)
            self.assertNotIn("python_bridge_receipt", record)

    def test_full_mode_enumerates_complete_finite_sweep(self):
        self.assertEqual(len(list(finite_cases())), 8881)
        self.assertEqual(runner.HISTORICAL_SHA,
                         "9900e57f2283c534815657dd6c079d0e966715f4")

    def test_archive_digest_does_not_claim_independent_proof(self):
        self.assertIn("not independently attest", " ".join(runner.LIMITATIONS))
        self.assertEqual(runner.PROTOCOL, "ADA-PYTHON-EXECUTION/1")


if __name__ == "__main__":
    unittest.main()
