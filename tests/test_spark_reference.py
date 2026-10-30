"""SPARK source contracts only; compiler/prover availability is never assumed."""
import json
import subprocess
from unittest.mock import patch
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from check_spark_reference import inspect_sources, run_gnatprove, main  # noqa: E402


class SparkReferenceTests(unittest.TestCase):
    def test_source_contracts_present_and_not_proved(self):
        result = inspect_sources(ROOT)
        self.assertEqual(result["ada_contracts"], "NOT_RUN")
        self.assertEqual(len(result["files_sha256"]), 5)

    def test_shared_semantics_spec_explicit(self):
        spec = json.loads((ROOT / "formal/spec/kernel-v1.json").read_text())
        self.assertIn("edge_valid", spec["semantics"])
        self.assertIn("phase_add", spec["semantics"])
        self.assertIn("not CRT bijection", " ".join(spec["assumptions"]))

    @staticmethod
    def fixture_dir():
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / "formal", root / "formal")
        return temp, root

    def test_missing_source_rejected(self):
        temp, root = self.fixture_dir()
        with temp:
            (root / "formal/spark/reference_kernel.ads").unlink()
            with self.assertRaises(FileNotFoundError):
                inspect_sources(root)

    def test_fabricated_success_rejected(self):
        temp, root = self.fixture_dir()
        with temp:
            path = root / "formal/spec/kernel-v1.json"
            value = json.loads(path.read_text())
            value["proof_status"] = "PROVED"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "proof success"):
                inspect_sources(root)

    def test_unapproved_assumption_rejected(self):
        temp, root = self.fixture_dir()
        with temp:
            path = root / "formal/spark/reference_kernel.adb"
            path.write_text(path.read_text() + "\npragma Assume (True);\n")
            with self.assertRaisesRegex(ValueError, "proof exemption"):
                inspect_sources(root)

    def test_gpr_directory_attributes_are_scalar_strings(self):
        projects = {
            "kernel.gpr": ("Object_Dir",),
            "cli.gpr": ("Object_Dir", "Exec_Dir"),
        }
        for name, attributes in projects.items():
            with self.subTest(project=name):
                source = (ROOT / "formal/spark" / name).read_text(encoding="utf-8")
                for attr in attributes:
                    directory = "bin" if attr == "Exec_Dir" else "obj"
                    self.assertIn(f'for {attr} use "{directory}";', source)
                    self.assertNotIn(f'for {attr} use ("{directory}");', source)
                self.assertIn('for Create_Missing_Dirs use "True";', source)

    def test_static_gate_rejects_old_object_dir_list_syntax(self):
        temp, root = self.fixture_dir()
        with temp:
            path = root / "formal/spark/kernel.gpr"
            path.write_text(path.read_text().replace(
                'for Object_Dir use "obj";', 'for Object_Dir use ("obj");'
            ), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "GPR single-valued directory"):
                inspect_sources(root)

    def test_static_gate_rejects_old_exec_dir_list_syntax(self):
        temp, root = self.fixture_dir()
        with temp:
            path = root / "formal/spark/cli.gpr"
            path.write_text(path.read_text().replace(
                'for Exec_Dir use "bin";', 'for Exec_Dir use ("bin");'
            ), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "GPR single-valued directory"):
                inspect_sources(root)

    def test_static_gate_rejects_missing_directory_creation_policy(self):
        temp, root = self.fixture_dir()
        with temp:
            path = root / "formal/spark/kernel.gpr"
            path.write_text(path.read_text().replace(
                'for Create_Missing_Dirs use "True";', ''
            ), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing-directory creation"):
                inspect_sources(root)

    def test_cli_validates_modular_input_before_conversion(self):
        code = (ROOT / "formal/spark/reference_cli.adb").read_text()
        for snippet in ("N (2) > 1", "N (2) > 2", "C >= W",
                        "not K.Valid_Edge"):
            self.assertIn(snippet, code)

    def test_cli_restricts_numeric_grammar_to_ascii_decimal(self):
        source = (ROOT / "formal/spark/reference_cli.adb").read_text()
        self.assertIn("Text : constant String := CLI.Argument (Index)", source)
        self.assertIn("Text'Length = 0", source)
        self.assertIn("for C of Text loop", source)
        self.assertIn("C not in '0' .. '9'", source)
        self.assertIn("return Natural'Value (Text)", source)
        self.assertNotIn("Natural'Value (CLI.Argument", source)

    def test_missing_tool_reports_not_run(self):
        with patch("check_spark_reference.shutil.which", return_value=None), \
             patch("check_spark_reference.subprocess.run") as runner:
            result = run_gnatprove(ROOT)
            self.assertEqual(result["ada_contracts"], "NOT_RUN")
            runner.assert_not_called()

    def test_no_synthetic_proof_success(self):
        with patch("check_spark_reference.shutil.which", return_value=None):
            result = run_gnatprove(ROOT)
            self.assertNotEqual(result["ada_contracts"], "GNATPROVE_REPORTED_DISCHARGED")

    def test_fixed_shell_free_gnatprove_commands(self):
        version = subprocess.CompletedProcess(["gnatprove", "--version"], 0,
                                              stdout="GNATprove fixture", stderr="")
        proof = subprocess.CompletedProcess(["gnatprove"], 0,
                                            stdout="3 checks proved", stderr="")
        with patch("check_spark_reference.shutil.which", return_value="/trusted/bin/gnatprove"), \
             patch("check_spark_reference.subprocess.run", side_effect=[version, proof]) as runner:
            result = run_gnatprove(ROOT)
        self.assertEqual(result["ada_contracts"], "GNATPROVE_REPORTED_DISCHARGED")
        self.assertEqual(runner.call_count, 2)
        self.assertEqual(runner.call_args_list[0].args[0], ["gnatprove", "--version"])
        self.assertEqual(runner.call_args_list[1].args[0], [
            "gnatprove", "-P", "kernel.gpr", "-u", "reference_kernel.adb",
            "--mode=all", "--checks-as-errors=on", "--warnings=error",
            "--report=all", "--level=2"
        ])
        for call in runner.call_args_list:
            self.assertIs(call.kwargs["shell"], False)
            self.assertEqual(call.kwargs["cwd"], ROOT / "formal" / "spark")
        self.assertNotIn("/trusted/bin/gnatprove", repr(runner.call_args_list))

    def test_version_check_failure_does_not_run_prover(self):
        version = subprocess.CompletedProcess(["gnatprove", "--version"], 1,
                                              stdout="", stderr="failed")
        with patch("check_spark_reference.shutil.which", return_value="/trusted/bin/gnatprove"), \
             patch("check_spark_reference.subprocess.run", return_value=version) as runner:
            result = run_gnatprove(ROOT)
        self.assertEqual(result["ada_contracts"], "FAILED_OR_UNPROVED")
        self.assertEqual(runner.call_count, 1)

    def test_proof_runner_argument_vectors_are_literal(self):
        source = (ROOT / "scripts/check_spark_reference.py").read_text(encoding="utf-8")
        self.assertIn('subprocess.run(["gnatprove", "--version"]', source)
        self.assertIn('["gnatprove", "-P", "kernel.gpr", "-u", "reference_kernel.adb"', source)
        self.assertNotIn("subprocess.run(command", source)
        self.assertNotIn("executable: str | None", source)

    def test_static_gate_without_compiler(self):
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
