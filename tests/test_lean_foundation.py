"""Lean math source gate and honest kernel evidence statuses — Python stdlib only."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_lean_foundation as lean  # noqa: E402


class LeanFoundationTests(unittest.TestCase):
    def test_manifest_pins_expected_release_and_inventory(self):
        report = lean.inspect(ROOT)
        self.assertEqual(report["toolchain"], "leanprover/lean4:v4.35.0")
        self.assertEqual(len(report["theorems_declared"]), 13)
        self.assertEqual(report["kernel_check"], "NOT_RUN")

    def test_source_has_no_unapproved_escape_and_all_axiom_audits(self):
        self.assertEqual(lean.inspect(ROOT)["source_audit"], "PASSED")

    @staticmethod
    def copy_scope():
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "formal/lean").mkdir(parents=True)
        shutil.copy2(ROOT / "lean-toolchain", root / "lean-toolchain")
        shutil.copy2(ROOT / lean.SOURCE, root / lean.SOURCE)
        return tmp, root

    def test_rejects_sorry_and_custom_axioms(self):
        for injection in ("theorem bad : True := by sorry", "axiom made_up : False",
                          "theorem bad : True := by native_decide"):
            with self.subTest(injection=injection):
                temp, root = self.copy_scope()
                with temp:
                    path = root / lean.SOURCE
                    path.write_text(path.read_text() + "\n" + injection + "\n")
                    with self.assertRaises(lean.LeanAuditError):
                        lean.inspect(root)

    def test_rejects_unapproved_new_theorem(self):
        temp, root = self.copy_scope()
        with temp:
            path = root / lean.SOURCE
            path.write_text(path.read_text() + "\ntheorem extra : True := by trivial\n")
            with self.assertRaisesRegex(lean.LeanAuditError, "theorem inventory"):
                lean.inspect(root)

    def test_rejects_missing_axiom_inspection(self):
        temp, root = self.copy_scope()
        with temp:
            path = root / lean.SOURCE
            path.write_text(path.read_text().replace(
                "#print axioms IndependenceLean.monomial_translate", ""))
            with self.assertRaisesRegex(lean.LeanAuditError, "transitive-axiom"):
                lean.inspect(root)

    def test_rejects_unpinned_toolchain(self):
        temp, root = self.copy_scope()
        with temp:
            (root / "lean-toolchain").write_text("leanprover/lean4:stable\n")
            with self.assertRaisesRegex(lean.LeanAuditError, "pinned"):
                lean.inspect(root)

    def test_missing_lean_toolchain_is_not_a_proof(self):
        with patch.object(lean.shutil, "which", return_value=None), \
             patch.object(lean.subprocess, "run") as execute:
            result = lean.check(ROOT, require_checked=True)
            self.assertEqual(result["kernel_check"], "NOT_RUN")
            execute.assert_not_called()

    def test_empty_output_cannot_be_proof(self):
        valid, summary = lean.parse_axiom_audit("")
        self.assertFalse(valid)
        self.assertEqual(summary, {})

    def test_prohibited_axioms_cannot_pass(self):
        log = "\n".join(f"'{lean.PREFIX}{name}' does not depend on any axioms"
                        for name in lean.THEOREMS[:-1])
        log += "\n'IndependenceLean.monomial_translate' depends on axioms: [sorryAx]"
        passed, summary = lean.parse_axiom_audit(log)
        self.assertFalse(passed)
        self.assertIn("sorryAx", summary["monomial_translate"])

    def test_all_no_axioms_logs_can_pass_parse_only(self):
        log = "\n".join(f"'{lean.PREFIX}{name}' does not depend on any axioms"
                        for name in lean.THEOREMS)
        passed, summary = lean.parse_axiom_audit(log)
        self.assertTrue(passed)
        self.assertEqual(len(summary), 13)
        # A fabricated log does NOT independently prove that Lean actually ran.

    def test_require_checked_fails_without_toolchain(self):
        with patch.object(lean.shutil, "which", return_value=None):
            self.assertEqual(lean.main(["--require-checked"]), 1)

    def test_static_check_must_not_mark_kernel_checked(self):
        self.assertEqual(lean.check(ROOT)["kernel_check"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
