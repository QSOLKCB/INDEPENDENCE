"""v1.1.0 fail-closed research archive verification; no independent execution claims."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import verify_formalisation_archive as research


class FormalisationArchiveTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        source = ROOT / research.DIR
        dest = self.root / research.DIR
        dest.mkdir(parents=True)
        for filename in ("evidence-manifest.json", *research.PINNED):
            shutil.copyfile(source / filename, dest / filename)

    def test_original_archives_and_scope_are_verified(self):
        result = research.verify(self.root)
        self.assertEqual(result["status"],
                         "ORIGINAL_ARCHIVES_AND_RECEIPTS_INTERNALLY_VERIFIED_UNATTESTED")
        self.assertEqual(result["original_internal_sha256_entries_checked"], 13)
        self.assertEqual(result["lean_model_theorems_recorded"], 6)
        self.assertEqual(result["spark_checks_recorded"], 10)
        self.assertEqual(result["rocq_model_obligations_recorded"], 15)
        self.assertEqual(result["ada_valid_vectors_recorded"], 4096)
        self.assertFalse(result["independent_execution_attestation"])
        self.assertEqual(result["zenodo_publication"], "NOT_VERIFIED")

    def test_original_gzip_byte_tampering_fails(self):
        path = self.root / research.DIR / "automata4-proof-archive.tar.gz"
        data = bytearray(path.read_bytes())
        data[39] ^= 1
        path.write_bytes(data)
        with self.assertRaises(research.EvidenceError):
            research.verify(self.root)

    def test_remanifesting_changed_archive_cannot_bypass_hardcoded_pins(self):
        name = "INDEPENDENCE-rocq-proof-evidence.tar.gz"
        path = self.root / research.DIR / name
        path.write_bytes(path.read_bytes() + b"forged")
        manifest_path = self.root / research.DIR / "evidence-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["evidence_archives"][name]["bytes"] = path.stat().st_size
        manifest["evidence_archives"][name]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(research.EvidenceError, "original archive digest"):
            research.verify(self.root)

    def test_manifest_claim_inflation_fails(self):
        path = self.root / research.DIR / "evidence-manifest.json"
        manifest = json.loads(path.read_text())
        manifest["scope_policy"]["independent_execution_attestation"] = True
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(research.EvidenceError, "unsupported"):
            research.verify(self.root)

    def test_zenodo_publication_not_assumed(self):
        path = self.root / research.DIR / "evidence-manifest.json"
        manifest = json.loads(path.read_text())
        manifest["zenodo"]["do_not_claim_report_published"] = False
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(research.EvidenceError, "Zenodo"):
            research.verify(self.root)

    def test_duplicate_nonfinite_and_float_json_rejected(self):
        for value in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1.5}', b'{"a":Infinity}'):
            with self.subTest(value=value), self.assertRaises(research.EvidenceError):
                research.json_strict(value)

    def test_forged_rocq_closed_count_fails(self):
        manifest = json.loads((self.root / research.DIR / "evidence-manifest.json").read_text())
        archives = manifest["evidence_archives"]
        originals = {}
        for name in research.PINNED:
            originals[name] = research.original_members(
                (self.root / research.DIR / name).read_bytes(), archives[name], name)
        rocq = originals["INDEPENDENCE-rocq-proof-evidence.tar.gz"]
        key = "INDEPENDENCE-rocq-proof-evidence/rocq-executed-evidence.json"
        altered = json.loads(rocq[key])
        altered["rocq"]["assumption_audit"]["closed_theorems"] = 14
        rocq[key] = json.dumps(altered).encode()
        with self.assertRaisesRegex(research.EvidenceError, "Rocq proof"):
            research.verify_receipts(originals["automata4-proof-archive.tar.gz"], rocq)

    def test_archive_missing_or_symlink_rejected(self):
        path = self.root / research.DIR / "automata4-proof-archive.tar.gz"
        path.unlink()
        with self.assertRaisesRegex(research.EvidenceError, "missing"):
            research.verify(self.root)
        path.symlink_to(ROOT / research.DIR / "automata4-proof-archive.tar.gz")
        with self.assertRaisesRegex(research.EvidenceError, "symlink"):
            research.verify(self.root)

    def test_original_tar_member_allowlist_exact(self):
        name = "automata4-proof-archive.tar.gz"
        data = (self.root / research.DIR / name).read_bytes()
        manifest = json.loads((self.root / research.DIR / "evidence-manifest.json").read_text())
        expected = manifest["evidence_archives"][name]
        members = research.original_members(data, expected, name)
        self.assertEqual(set(members), set(expected["members"]))
        self.assertEqual(research.verify_sums(members, "automata4-proof-archive"), 8)

    def test_cli_writes_truthful_receipt(self):
        output = self.root / "evidence.json"
        self.assertEqual(research.main(["--root", str(self.root),
                                        "--output", str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())["zenodo_publication"],
                         "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
