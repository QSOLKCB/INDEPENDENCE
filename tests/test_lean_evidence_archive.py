"""Offline verification of recovered Lean evidence, not independent execution."""
import copy
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
