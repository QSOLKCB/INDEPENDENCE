"""Strict offline tests for preferred manifest and historical archive fallback."""
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
import select_public_manifest as selector
import site_bundle as bundle


class PublicManifestSelectionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        source = self.tmp / "source"
        staged = self.tmp / "staged"
        for filename in bundle.SITE_FILES:
            dst = source / filename
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / filename, dst)
        bundle.stage(source, staged, "c" * 40)
        self.valid = (staged / bundle.MANIFEST).read_bytes()
        self.primary = self.tmp / "preferred" / bundle.MANIFEST
        self.legacy = self.tmp / "historical" / "artifact.tar"
        self.out = self.tmp / "output" / bundle.MANIFEST

    def archive(self, entries=None):
        self.legacy.parent.mkdir(parents=True, exist_ok=True)
        entries = entries or [("./deployment-manifest.json", self.valid)]
        with tarfile.open(self.legacy, "w") as tar:
            for name, data in entries:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

    def test_prefer_separate_manifest_even_if_archive_invalid(self):
        self.primary.parent.mkdir(parents=True)
        self.primary.write_bytes(self.valid)
        self.archive([("./deployment-manifest.json", b"{}")])
        self.assertEqual(selector.select(self.primary, self.legacy, self.out),
                         "independence-pages-manifest")
        self.assertEqual(self.out.read_bytes(), self.valid)

    def test_historical_tar_fallback_preserves_original_bytes(self):
        self.archive()
        self.assertEqual(selector.select(self.primary, self.legacy, self.out),
                         "historical-github-pages-artifact")
        self.assertEqual(self.out.read_bytes(), self.valid)

    def test_primary_corruption_fails_closed_without_archive_fallback(self):
        self.primary.parent.mkdir(parents=True)
        self.primary.write_text("{}")
        self.archive()
        with self.assertRaises(ValueError):
            selector.select(self.primary, self.legacy, self.out)
        self.assertFalse(self.out.exists())

    def test_reject_duplicate_archive_members_and_symlink(self):
        self.archive([("./deployment-manifest.json", self.valid),
                      ("deployment-manifest.json", self.valid)])
        with self.assertRaisesRegex(selector.SelectionError, "duplicating"):
            selector.select(self.primary, self.legacy, self.out)
        self.legacy.unlink()
        self.legacy.symlink_to(self.tmp / "missing")
        with self.assertRaisesRegex(selector.SelectionError, "unavailable"):
            selector.select(self.primary, self.legacy, self.out)

    def test_missing_both_sources_writes_not_verified_receipt(self):
        failure = self.tmp / "manual-observation.json"
        rc = selector.main(["--preferred", str(self.primary),
                            "--legacy-tar", str(self.legacy),
                            "--output", str(self.out),
                            "--failure-output", str(failure)])
        self.assertEqual(rc, 1)
        record = json.loads(failure.read_text())
        self.assertEqual(record["status"], "NOT_VERIFIED")
        self.assertEqual(record["stage"], "MANIFEST_SELECTION")
        self.assertEqual(record["verified_public_assets"], 0)
        self.assertFalse(self.out.exists())

    def test_rejects_resealed_wrong_checksum(self):
        self.primary.parent.mkdir(parents=True)
        manifest = json.loads(self.valid)
        manifest["files"]["app.js"] = "0" * 64
        self.primary.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(selector.SelectionError, "checksum"):
            selector.select(self.primary, self.legacy, self.out)
