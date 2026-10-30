"""Offline verification of recovered Lean evidence, not independent execution."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_lean_evidence_archive import (  # noqa: E402
    ArchiveError, FOLDER, verify,
)


class LeanEvidenceArchiveTests(unittest.TestCase):
    @staticmethod
    def fixture():
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / FOLDER, root / FOLDER)
        return temp, root

    def test_valid_archive_integrity(self):
        report = verify(ROOT)
        self.assertEqual(report["archive_integrity"], "PASS")
        self.assertEqual(report["theorem_audits"], 13)
        self.assertEqual(report["execution_attestation"], "NOT_INDEPENDENTLY_VERIFIED")

    def test_recovered_report_has_no_original_byte_attestation(self):
        report = verify(ROOT)
        self.assertEqual(report["original_file_byte_identity"],
                         "NOT_INDEPENDENTLY_CONFIRMED")

    def test_modified_proof_report_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "lean-evidence.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ArchiveError, "evidence bytes changed"):
                verify(root)

    def test_modified_lean_source_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "FiniteFoundation.lean"
            path.write_bytes(path.read_bytes() + b"-- modified\n")
            with self.assertRaisesRegex(ArchiveError, "historical Lean source changed"):
                verify(root)

    def test_falsified_source_git_commit_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["source"]["git_commit"] = "0" * 40
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ArchiveError, "Git revision"):
                verify(root)

    def test_falsified_execution_attestation_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["independently_attested_execution"] = True
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ArchiveError, "provenance claim"):
                verify(root)

    def test_modified_toolchain_rejected(self):
        temp, root = self.fixture()
        with temp:
            (root / FOLDER / "lean-toolchain").write_text("leanprover/lean4:stable\n")
            with self.assertRaisesRegex(ArchiveError, "toolchain pin"):
                verify(root)

    def test_contradictory_lean_manifest_results_rejected(self):
        cases = (
            ("lean_kernel_reported", "FAILED_OR_UNRESOLVED"),
            ("lean_exit_code_reported", 1),
            ("theorems_declared", 0),
            ("axiom_audits", 0),
            ("unapproved_axioms_reported", 1),
        )
        for field, value in cases:
            with self.subTest(field=field):
                temp, root = self.fixture()
                with temp:
                    path = root / FOLDER / "manifest.json"
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    manifest["checks"][field] = value
                    path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(
                        ArchiveError, "manifest Lean result mismatch: " + field
                    ):
                        verify(root)

    def test_boolean_values_cannot_impersonate_integer_results(self):
        # False == 0 and True == 1 in Python; checks must be type strict.
        for field in ("lean_exit_code_reported", "unapproved_axioms_reported"):
            with self.subTest(field=field):
                temp, root = self.fixture()
                with temp:
                    path = root / FOLDER / "manifest.json"
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    manifest["checks"][field] = False
                    path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(ArchiveError, "manifest Lean result mismatch"):
                        verify(root)

    def test_missing_or_extra_lean_check_fields_rejected(self):
        for mode in ("missing", "extra"):
            with self.subTest(mode=mode):
                temp, root = self.fixture()
                with temp:
                    path = root / FOLDER / "manifest.json"
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    if mode == "missing":
                        del manifest["checks"]["axiom_audits"]
                    else:
                        manifest["checks"]["lean_proven_application_wide"] = True
                    path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(ArchiveError, "manifest checks schema mismatch"):
                        verify(root)

    def test_boolean_unittest_count_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["checks"]["python_unittest_reported"]["failed"] = False
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ArchiveError, "reported unittest metadata changed"):
                verify(root)

    def test_modified_raw_lean_output_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "lean-evidence.json"
            report = json.loads(path.read_text(encoding="utf-8"))
            report["raw_output"] = report["raw_output"].replace(
                "crt_right_inverse' does not depend on any axioms",
                "crt_right_inverse' depends on axioms: [sorryAx]",
            )
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaises(ArchiveError):
                verify(root)


if __name__ == "__main__":
    unittest.main()
