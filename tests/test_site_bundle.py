"""v1.0 deploy-stage tests: bytes, symlinks, CSP and HTML entry point."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import site_bundle as bundle

REV = "e" * 40

class SiteBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / "dist"
        self.src = self.root / "src"
        for name in bundle.SITE_FILES:
            dst = self.src / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dst)

    def stage(self):
        # audit() scans first-party allowlist only; source-copy has no forbidden package manifests.
        return bundle.stage(self.src, self.site, REV)

    def test_checkout_html_has_real_script_and_csp(self):
        bundle.check_html((ROOT / "index.html").read_bytes())

    def test_stage_and_verify_all_first_party_bytes(self):
        self.assertEqual(self.stage()["status"], "BYTE_EXACT_VERIFIED_UNATTESTED")
        checked = bundle.verify(self.site, revision=REV, source=self.src)
        self.assertEqual(checked["files"], len(bundle.SITE_FILES))
        self.assertEqual(len(checked["tree_sha256"]), 64)

    def test_rejects_stray_or_missing_site_assets(self):
        self.stage()
        (self.site / "injected.js").write_text("evil")
        with self.assertRaisesRegex(bundle.BundleError, "unexpected"):
            bundle.verify(self.site)
        (self.site / "injected.js").unlink()
        (self.site / "app.js").unlink()
        with self.assertRaisesRegex(bundle.BundleError, "missing"):
            bundle.verify(self.site)

    def test_rejects_modified_file_even_if_manifest_remains(self):
        self.stage()
        (self.site / "app.js").write_bytes(b"// tampered")
        with self.assertRaises(bundle.BundleError):
            bundle.verify(self.site)

    def test_rejects_self_consistent_manifest_with_wrong_revision(self):
        self.stage()
        with self.assertRaisesRegex(bundle.BundleError, "revision mismatch"):
            bundle.verify(self.site, revision="a" * 40)

    def test_rejects_rehashed_manifest_drift_from_checkout(self):
        self.stage()
        (self.site / "styles.css").write_bytes(b"/* different */")
        raw = json.loads((self.site / bundle.MANIFEST).read_text())
        raw["files"]["styles.css"] = hashlib.sha256(b"/* different */").hexdigest()
        raw["tree_sha256"] = bundle.hash_bytes(bundle.canonical(raw["files"]))
        (self.site / bundle.MANIFEST).write_text(json.dumps(raw))
        self.assertEqual(bundle.verify(self.site)["status"], "BYTE_EXACT_VERIFIED_UNATTESTED")
        with self.assertRaisesRegex(bundle.BundleError, "differs from source"):
            bundle.verify(self.site, source=self.src)

    def test_broken_css_link_blocks_script_entry(self):
        bad = (ROOT / "index.html").read_bytes().replace(
            b'<link rel="stylesheet" href="./formal-lab/formal-lab.css">',
            b'<link rel="stylesheet" href="./formal-lab/formal-lab.css"')
        with self.assertRaisesRegex(bundle.BundleError, "script|stylesheet"):
            bundle.check_html(bad)

    def test_unsafe_csp_and_duplicate_html_ids_rejected(self):
        original = (ROOT / "index.html").read_bytes()
        for bad in (
            original.replace(b"script-src 'self'", b"script-src 'self' 'unsafe-inline'"),
            original.replace(b'<main id="main">', b'<main id="main"><div id="main">'),
        ):
            with self.subTest(bad=bad[:50]), self.assertRaises(bundle.BundleError):
                bundle.check_html(bad)

    def test_rejects_symlink_and_duplicate_manifest(self):
        self.stage()
        (self.site / "app.js").unlink()
        (self.site / "app.js").symlink_to(self.src / "app.js")
        with self.assertRaisesRegex(bundle.BundleError, "symlink"):
            bundle.verify(self.site)
        (self.site / "app.js").unlink()
        shutil.copyfile(self.src / "app.js", self.site / "app.js")
        data = (self.site / bundle.MANIFEST).read_text()
        data = data.replace('"protocol":', '"protocol": "WRONG", "protocol":', 1)
        (self.site / bundle.MANIFEST).write_text(data)
        with self.assertRaisesRegex(bundle.BundleError, "duplicate"):
            bundle.verify(self.site)

    def test_no_overwrite_or_reentrant_source_root(self):
        self.stage()
        with self.assertRaisesRegex(bundle.BundleError, "destination"):
            self.stage()
        with self.assertRaisesRegex(bundle.BundleError, "overlap"):
            bundle.stage(self.src, self.src, REV)

    def test_sha_revision_only(self):
        with self.assertRaisesRegex(bundle.BundleError, "revision"):
            bundle.envelope({k:"0"*64 for k in bundle.SITE_FILES}, "a" * 39)
