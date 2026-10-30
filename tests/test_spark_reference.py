"""SPARK source contracts only; compiler/prover availability is never assumed."""
import json
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

    def test_cli_validates_modular_input_before_conversion(self):
        code = (ROOT / "formal/spark/reference_cli.adb").read_text()
        for snippet in ("N (2) > 1", "N (2) > 2", "C >= W",
                        "not K.Valid_Edge"):
            self.assertIn(snippet, code)

    def test_missing_tool_reports_not_run(self):
        result = run_gnatprove(ROOT, executable="/missing/gnatprove")
        self.assertEqual(result["ada_contracts"], "NOT_RUN")

    def test_no_synthetic_proof_success(self):
        result = run_gnatprove(ROOT, executable="/missing/gnatprove")
        self.assertNotEqual(result["ada_contracts"], "GNATPROVE_REPORTED_DISCHARGED")

    def test_static_gate_without_compiler(self):
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
