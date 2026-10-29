"""Offline, deterministic tests using only the Python standard library."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit import WEB_FILES, audit, main  # noqa: E402


class AuditTests(unittest.TestCase):
    def test_repo_audit_passes(self):
        report = audit(ROOT)
        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(list(report["web_assets_sha256"]), sorted(WEB_FILES))

    def test_hashes_match_file_bytes(self):
        report = audit(ROOT)
        for name, checksum in report["web_assets_sha256"].items():
            self.assertEqual(checksum, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_report_is_stable(self):
        self.assertEqual(audit(ROOT), audit(ROOT))

    def test_missing_asset_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            report = audit(Path(directory))
            self.assertFalse(report["passed"])
            self.assertIn({"path": "index.html", "kind": "missing_web_asset"}, report["findings"])

    def test_package_manifest_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "package.json").write_text("{}", encoding="utf-8")
            report = audit(root)
            self.assertIn({"path": "package.json", "kind": "third_party_manifest"}, report["findings"])

    def test_remote_script_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text(
                '<script src="https://untrusted.example/x.js"></script>', encoding="utf-8"
            )
            report = audit(root)
            self.assertIn({"path": "index.html", "kind": "remote_script"}, report["findings"])

    def test_relative_module_imports_are_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.js").write_text("import {a} from './lab/core.js';", encoding="utf-8")
            report = audit(root)
            self.assertNotIn({"path": "app.js", "kind": "remote_js_import"}, report["findings"])

    def test_remote_css_urls_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "styles.css").write_text(
                "body{background:url(https://example.com/image.png)}", encoding="utf-8"
            )
            report = audit(root)
            self.assertIn({"path": "styles.css", "kind": "remote_css_url"}, report["findings"])

    def test_cli_failure_for_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(main(["--root", directory]), 1)


if __name__ == "__main__":
    unittest.main()
