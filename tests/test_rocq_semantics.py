"""v1.0.2 independent model / Rocq gate adversarial stdlib tests."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_rocq_semantics as rocq


class RocqSemanticsTests(unittest.TestCase):
    def source_fixture(self):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        target = root / rocq.SOURCE
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / rocq.SOURCE, target)
        return td, root, target

    def test_sources_unmodified_static_is_not_proved(self):
        report = rocq.inspect()
        self.assertEqual(report["rocq"]["status"], "NOT_RUN")
        self.assertFalse(report["independent_execution_attestation"])
        self.assertEqual(report["finite_bridge"]["automata4_cases"], 4096)
        self.assertEqual(report["finite_bridge"]["status"], "FINITE_BRIDGE_CHECKED")
        self.assertEqual(report["finite_bridge"]["canonical_vectors_sha256"],
                         "f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635")
        self.assertEqual(len(report["theorems"]), 15)

    def test_explicit_model_all_patterns_independent(self):
        for pattern, index in rocq.PATTERN_TABLE.items():
            self.assertEqual(index, 4 * pattern[0] + 2 * pattern[1] + pattern[2])
        self.assertEqual(rocq.explicit_step(90, (0, 0, 1, 0)), (0, 1, 0, 1))
        self.assertEqual(rocq.explicit_step(90, (1, 0, 0, 0)), (0, 1, 0, 0))
        self.assertEqual(rocq.explicit_step(255, ()), ())
        self.assertEqual(rocq.explicit_step(0, (1,)), (0,))

    def test_bad_input_rejected(self):
        for rule, row in (
            (-1, (0,)), (256, (1,)), (True, (0,)),
            (0, (2,)), (0, [0]), (0, (False,)),
        ):
            with self.subTest(rule=rule, row=row), self.assertRaises(rocq.RocqEvidenceError):
                rocq.explicit_step(rule, row)

    def test_source_drift_fails_closed(self):
        td, root, target = self.source_fixture()
        with td:
            target.write_bytes(target.read_bytes() + b"\nTheorem fake : True. Proof. exact I. Qed.\n")
            with self.assertRaisesRegex(rocq.RocqEvidenceError, "reviewed blob"):
                rocq.inspect_source(root)

    def test_holes_do_not_claim_proof(self):
        td, root, target = self.source_fixture()
        with td:
            target.write_text(target.read_text().replace(
                "Proof. reflexivity. Qed.", "Proof. Admitted.", 1))
            with self.assertRaises(rocq.RocqEvidenceError):
                rocq.inspect_source(root)

    def test_missing_rocq_reports_not_run(self):
        with patch.object(rocq.shutil, "which", return_value=None):
            self.assertEqual(rocq.run_rocq()["status"], "NOT_RUN")

    def test_real_rocq_920_version_banner_is_accepted(self):
        actual = "The Rocq Prover, version 9.2\ncompiled with OCaml 4.14.2"
        self.assertTrue(rocq.pinned_version_display(actual))
        self.assertTrue(rocq.pinned_version_display("The Rocq Prover, version 9.2.0"))
        for invalid in ("The Rocq Prover, version 9.2.1",
                        "The Rocq Prover, version 9.3",
                        "The Rocq Prover, version 9.20",
                        "The Rocq Prover, version 9.2.0-rc1",
                        "Different compiler version 9.2.0",
                        "not a version\nThe Rocq Prover, version 9.2",
                        ""):
            with self.subTest(version=invalid):
                self.assertFalse(rocq.pinned_version_display(invalid))

    def test_real_rocq_920_banner_reaches_compiler_instead_of_mismatch(self):
        version = subprocess.CompletedProcess(
            [], 0, "The Rocq Prover, version 9.2\ncompiled with OCaml 4.14.2", ""
        )
        fail = subprocess.CompletedProcess([], 1, "", "Error: proof not discharged")
        with patch.object(rocq.shutil, "which", return_value="/usr/bin/rocq"), \
             patch.object(rocq, "invoke", side_effect=(version, fail)) as invoked:
            result = rocq.run_rocq()
        self.assertEqual(result["status"], "FAILED_OR_UNRESOLVED")
        self.assertEqual(invoked.call_args_list[0].args[0], ["rocq", "--version"])
        self.assertEqual(invoked.call_args_list[1].args[0][:2], ["rocq", "compile"])
        self.assertEqual(result["exit_code"], 1)

    def test_wrong_version_reports_mismatch(self):
        fake = subprocess.CompletedProcess([], 0, "The Rocq Prover, version 9.3.0", "")
        with patch.object(rocq.shutil, "which", return_value="/usr/bin/rocq"), \
             patch.object(rocq, "invoke", return_value=fake):
            self.assertEqual(rocq.run_rocq()["status"], "VERSION_MISMATCH")

    def test_compiler_failure_never_becomes_success(self):
        version = subprocess.CompletedProcess([], 0, "The Rocq Prover, version 9.2.0", "")
        fail = subprocess.CompletedProcess([], 1, "", "Error: unproved lemma")
        with patch.object(rocq.shutil, "which", return_value="/usr/bin/rocq"), \
             patch.object(rocq, "invoke", side_effect=(version, fail)):
            self.assertEqual(rocq.run_rocq()["status"], "FAILED_OR_UNRESOLVED")

    def test_fake_stdout_without_compiled_vo_not_counted(self):
        version = subprocess.CompletedProcess([], 0, "The Rocq Prover, version 9.2.0", "")
        fake = subprocess.CompletedProcess([], 0,
            ("Closed under the global context\n" * len(rocq.THEOREMS)), "")
        with patch.object(rocq.shutil, "which", return_value="/usr/bin/rocq"), \
             patch.object(rocq, "invoke", side_effect=(version, fake)):
            self.assertEqual(rocq.run_rocq()["status"], "FAILED_OR_UNRESOLVED")

    def test_require_tool_failure_sets_nonzero_and_retains_not_run(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(rocq.shutil, "which", return_value=None):
            output = Path(td) / "receipt.json"
            self.assertEqual(rocq.main(["--require-rocq", "--output", str(output)]), 1)
            self.assertEqual(json.loads(output.read_text())["rocq"]["status"], "NOT_RUN")

    def test_static_output_is_truthful_not_run(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "receipt.json"
            self.assertEqual(rocq.main(["--output", str(output)]), 0)
            data = json.loads(output.read_text())
            self.assertEqual(data["rocq"]["status"], "NOT_RUN")
            self.assertFalse(data["independent_execution_attestation"])


if __name__ == "__main__":
    unittest.main()
