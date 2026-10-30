"""Original uploaded proof evidence must remain byte-identical and scoped."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import verify_original_ada_evidence as archived  # noqa: E402


class OriginalAdaEvidenceTests(unittest.TestCase):
    @staticmethod
    def fixture():
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        shutil.copytree(ROOT / "formal/evidence", root / "formal/evidence")
        return tmp, root

    def test_baseline_preserves_both_original_byte_sequences(self):
        result = archived.validate(ROOT)
        self.assertEqual(result["archive_integrity"], "PASS")
        self.assertEqual(result["original_receipts"], "EXACT_BYTE_MATCH")
        self.assertEqual((result["sample_ada_cases"], result["full_ada_cases"]),
                         (150, 8903))
        self.assertEqual(result["independent_execution_attestation"], "NOT_ESTABLISHED")

    def test_package_checksum_is_fixed_and_not_remote_attestation(self):
        self.assertEqual(archived.ZIP_SHA,
                         "429b946d083c2b0562450704f924eb3370e5c9a9c62eb81ef5ac90d41a5e2256")
        self.assertEqual(archived.BIN_SHA,
                         "9d74484857e3937586003a0dea2a648704c58e039ad6812b8a75167b1169fddf")

    def test_original_runtime_bytes_tampered_rejected(self):
        for filename in archived.RECORDS:
            with self.subTest(filename=filename):
                tmp, root = self.fixture()
                with tmp:
                    path = root / archived.FOLDER / filename
                    path.write_bytes(path.read_bytes() + b"\n")
                    with self.assertRaisesRegex(archived.OriginalEvidenceError,
                                                "original runtime receipt bytes changed"):
                        archived.validate(root)

    def test_manifest_digest_and_checkout_forgery_rejected(self):
        for field, replacement in (("sha256", "0"*64), ("reported_checkout", "0"*40)):
            with self.subTest(field=field):
                tmp, root = self.fixture()
                with tmp:
                    path = root / archived.FOLDER / "manifest.json"
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    obj["files"][0][field] = replacement
                    path.write_text(json.dumps(obj), encoding="utf-8")
                    with self.assertRaisesRegex(archived.OriginalEvidenceError,
                                                "manifest contradicts"):
                        archived.validate(root)

    def test_comparison_build_and_spec_digests_must_match_receipts(self):
        # Codex P2 reproduction: mutating either publication-summary hash
        # cannot pass when the original runtime JSONs remain unchanged.
        for field in ("compiler_build_output_sha256", "source_spec_sha256"):
            with self.subTest(field=field):
                tmp, root = self.fixture()
                with tmp:
                    path = root / archived.FOLDER / "manifest.json"
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    obj["comparison"][field] = "0" * 64
                    path.write_text(json.dumps(obj), encoding="utf-8")
                    with self.assertRaisesRegex(
                        archived.OriginalEvidenceError, "cross-record comparison"
                    ):
                        archived.validate(root)

    def test_both_comparison_hashes_corrupted_together_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            path = root / archived.FOLDER / "manifest.json"
            obj = json.loads(path.read_text(encoding="utf-8"))
            for field in ("compiler_build_output_sha256", "source_spec_sha256"):
                obj["comparison"][field] = "0" * 64
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(
                archived.OriginalEvidenceError, "cross-record comparison"
            ):
                archived.validate(root)

    def test_comparison_summary_schema_rejects_missing_and_extra_hashes(self):
        for mode in ("missing", "extra"):
            with self.subTest(mode=mode):
                tmp, root = self.fixture()
                with tmp:
                    path = root / archived.FOLDER / "manifest.json"
                    obj = json.loads(path.read_text(encoding="utf-8"))
                    if mode == "missing":
                        del obj["comparison"]["source_spec_sha256"]
                    else:
                        obj["comparison"]["unproven_extra_certification"] = True
                    path.write_text(json.dumps(obj), encoding="utf-8")
                    with self.assertRaisesRegex(
                        archived.OriginalEvidenceError, "cross-record comparison"
                    ):
                        archived.validate(root)

    def test_comparison_test_count_rejects_boolean(self):
        # bool is an int subclass in Python; false must not impersonate 0.
        tmp, root = self.fixture()
        with tmp:
            path = root / archived.FOLDER / "manifest.json"
            obj = json.loads(path.read_text(encoding="utf-8"))
            obj["comparison"]["reported_python_unit_tests"] = True
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(
                archived.OriginalEvidenceError, "cross-record comparison"
            ):
                archived.validate(root)

    def test_relabel_old_lean_as_original_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            path = root / archived.FOLDER / "manifest.json"
            obj = json.loads(path.read_text(encoding="utf-8"))
            obj["existing_records"][1]["original_file_provenance"] = "ORIGINAL_LEAN_EXECUTION"
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(archived.OriginalEvidenceError, "Lean reconstructed"):
                archived.validate(root)

    def test_claim_independent_execution_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            path = root / archived.FOLDER / "manifest.json"
            obj = json.loads(path.read_text(encoding="utf-8"))
            obj["provenance"]["independently_attested_execution"] = True
            path.write_text(json.dumps(obj), encoding="utf-8")
            with self.assertRaisesRegex(archived.OriginalEvidenceError, "provenance"):
                archived.validate(root)

    def test_spark_reference_bytes_tampered_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            path = root / "formal/evidence/spark/pr13/spark-evidence.json"
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(archived.OriginalEvidenceError, "older proof source bytes changed"):
                archived.validate(root)


if __name__ == "__main__":
    unittest.main()
