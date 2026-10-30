"""Adversarial tests for user-reported GNATprove archive evidence. Stdlib only."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_spark_evidence_archive import EvidenceError, FOLDER, verify  # noqa: E402


class SparkEvidenceArchiveTests(unittest.TestCase):
    @staticmethod
    def fixture():
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copytree(ROOT / FOLDER, root / FOLDER)
        return temp, root

    @staticmethod
    def change_json(root, name, edit):
        path = root / FOLDER / name
        value = json.loads(path.read_text(encoding="utf-8"))
        edit(value)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_original_archive_integrity(self):
        result = verify(ROOT)
        self.assertEqual(result["archive_integrity"], "PASS")
        self.assertEqual(result["reported_spark_checks_proved"], 21)
        self.assertEqual(result["reported_python_tests"], 186)
        self.assertEqual(result["independent_execution_attestation"], "NOT_ESTABLISHED")

    def test_missing_source_or_changed_gpr_fails(self):
        for name in ("kernel.gpr", "reference_kernel.ads"):
            with self.subTest(name=name):
                tmp, root = self.fixture()
                with tmp:
                    source = root / FOLDER / "source" / name
                    source.write_bytes(source.read_bytes() + b"\n-- altered\n")
                    with self.assertRaisesRegex(EvidenceError, "SPARK source bytes differ"):
                        verify(root)

    def test_spec_snapshot_tampering_rejected(self):
        temp, root = self.fixture()
        with temp:
            path = root / FOLDER / "source" / "kernel-v1.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(EvidenceError, "specification Git blob"):
                verify(root)

    def test_historical_snapshot_metadata_rejected_if_retarged(self):
        temp, root = self.fixture()
        with temp:
            self.change_json(root, "manifest.json",
                             lambda m: m["historical_source_snapshot"].update(
                                 source_checkout_git_sha="0"*40))
            with self.assertRaisesRegex(EvidenceError, "snapshot metadata"):
                verify(root)

    def test_archive_is_not_coupled_to_future_main_sources(self):
        # Fixture intentionally does not copy live formal/spark sources.
        temp, root = self.fixture()
        with temp:
            self.assertFalse((root / "formal/spark/reference_kernel.adb").exists())
            self.assertEqual(verify(root)["archive_integrity"], "PASS")

    def test_false_proved_count_rejected(self):
        for count in (0, 22, False):
            with self.subTest(count=count):
                tmp, root = self.fixture()
                with tmp:
                    self.change_json(root, "manifest.json",
                                     lambda m: m["gnatprove"].update(reported_checks_proved=count))
                    with self.assertRaisesRegex(EvidenceError, "manifest contradicts"):
                        verify(root)

    def test_fake_failed_or_success_status_rejected(self):
        for field, value in (
            ("status", "FAILED_OR_UNPROVED"),
            ("exit_code", 1),
            ("exit_code", False),
        ):
            tmp, root = self.fixture()
            with tmp:
                self.change_json(root, "manifest.json",
                                 lambda m: m["gnatprove"].update({field: value}))
                with self.assertRaisesRegex(EvidenceError, "manifest contradicts"):
                    verify(root)

    def test_modified_proof_output_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "spark-evidence.json",
                             lambda r: r.update(proof_output=r["proof_output"].replace(
                                 "21 checks", "22 checks")))
            with self.assertRaisesRegex(EvidenceError, "proof-output"):
                verify(root)

    def test_forged_attestation_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "manifest.json",
                             lambda m: m.update(execution_attested_independently=True))
            with self.assertRaisesRegex(EvidenceError, "provenance"):
                verify(root)

    def test_source_checkout_confusion_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "manifest.json",
                             lambda m: m["reported_checkout"].update(git_sha="0"*40))
            with self.assertRaisesRegex(EvidenceError, "merge-commit provenance"):
                verify(root)

    def test_fake_python_summary_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "manifest.json",
                             lambda m: m["reported_python_unittest"].update(failed=True))
            with self.assertRaisesRegex(EvidenceError, "Python test summary"):
                verify(root)

    def test_manifest_limitations_cannot_inflate_provenance(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "manifest.json",
                             lambda m: m["limitations"].__setitem__(
                                 0, "Independent tool execution was authenticated"))
            with self.assertRaisesRegex(EvidenceError, "limitations mismatch"):
                verify(root)

    def test_toolchain_version_must_be_exact(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "spark-evidence.json",
                             lambda r: r.update(tool_version=r["tool_version"] +
                                              "\\nIndependently certified SPARK verifier"))
            with self.assertRaisesRegex(EvidenceError, "toolchain version mismatch"):
                verify(root)

    def test_unknown_evidence_field_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            self.change_json(root, "spark-evidence.json",
                             lambda r: r.update(python_is_formally_proved=True))
            with self.assertRaisesRegex(EvidenceError, "proof report schema"):
                verify(root)

    def test_public_page_discloses_scope_and_new_declaration(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.assertIn('class="pest-control-declaration"', page)
        self.assertIn("This Isn't War, <strong>This Is Pest Control</strong>", page)
        self.assertLess(page.index('class="divorce-declaration"'),
                        page.index('class="pest-control-declaration"'))
        self.assertIn("GNATprove FSF 16.1.0 reported all 21 checks proved", page)
        self.assertIn("user-reported results", page)
        self.assertIn(".pest-control-declaration", css)


if __name__ == "__main__":
    unittest.main()
