"""Offline fake-CDN fixture tests; explicitly NOT real public network evidence."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import site_bundle as bundle
import verify_deployed_site as remote

class DeployObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "src"
        self.site = self.root / "site"
        for name in bundle.SITE_FILES:
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        bundle.stage(self.source, self.site, "f" * 40)

    def fake(self, uri):
        return (self.site / uri.removeprefix(remote.BASE)).read_bytes()

    def test_local_fake_cdn_verifies_consistency_not_authorship(self):
        with patch.object(remote, "fetch_bytes", side_effect=self.fake):
            report = remote.verify(self.site / bundle.MANIFEST)
        self.assertEqual(report["status"], "REMOTE_BYTES_MATCHED_UNATTESTED")
        self.assertEqual(report["files"], len(bundle.SITE_FILES))

    def test_rejects_wrong_remote_public_asset(self):
        def bad(uri):
            if uri.endswith("/app.js"):
                return b"malicious or stale bytes"
            return self.fake(uri)
        with patch.object(remote, "fetch_bytes", side_effect=bad):
            with self.assertRaisesRegex(remote.DeploymentError, "app.js"):
                remote.verify(self.site / bundle.MANIFEST)

    def test_rejects_remote_manifest_mismatch(self):
        with patch.object(remote, "fetch_bytes", return_value=b"{}"):
            with self.assertRaisesRegex(remote.DeploymentError, "manifest"):
                remote.verify(self.site / bundle.MANIFEST)

    def test_redirect_handler_blocks_every_redirect_before_followup(self):
        from urllib.request import Request
        original = Request(remote.BASE + "app.js")
        for status, destination in (
            (301, "https://evil.example/steal"),
            (302, "http://qsolkcb.github.io/INDEPENDENCE/app.js"),
            (303, remote.BASE + "app.js"),
            (307, "https://evil.example/bounce"),
            (308, remote.BASE + "index.html"),
        ):
            with self.subTest(status=status), self.assertRaisesRegex(
                    remote.DeploymentError, "before follow-up"):
                remote.RejectRedirects().redirect_request(
                    original, None, status, "Redirect", {}, destination)

    def test_fetch_uses_redirect_rejecting_opener(self):
        fake = Mock()
        fake.__enter__ = Mock(return_value=fake)
        fake.__exit__ = Mock(return_value=False)
        fake.geturl.return_value = remote.BASE + "app.js"
        fake.status = 200
        fake.read.return_value = b"ok"
        opener = Mock()
        opener.open.return_value = fake
        with patch.object(remote, "build_opener", return_value=opener) as build:
            self.assertEqual(remote.fetch_bytes(remote.BASE + "app.js"), b"ok")
        self.assertEqual(len(build.call_args.args), 1)
        self.assertIsInstance(build.call_args.args[0], remote.RejectRedirects)

    def test_fetch_rejects_out_of_scope_url_without_network(self):
        with patch.object(remote, "build_opener") as build:
            for url in (
                "https://evil.example/INDEPENDENCE/app.js",
                "http://qsolkcb.github.io/INDEPENDENCE/app.js",
                remote.BASE + "../private",
                remote.BASE + "app.js?leak=1",
                remote.BASE + "unlisted.js",
            ):
                with self.subTest(url=url), self.assertRaises(remote.DeploymentError):
                    remote.fetch_bytes(url)
            build.assert_not_called()

    def test_outside_network_hosts_are_rejected(self):
        for value in ("http://qsolkcb.github.io/INDEPENDENCE/",
                      "https://example.org/INDEPENDENCE/",
                      "https://qsolkcb.github.io/ANOTHER/",
                      "https://qsolkcb.github.io.evil/INDEPENDENCE/"):
            with self.subTest(value=value), self.assertRaises(remote.DeploymentError):
                remote.validate_base(value)

    def test_forged_local_manifest_is_rejected_without_network(self):
        path = self.site / bundle.MANIFEST
        record = json.loads(path.read_text())
        record["files"]["app.js"] = "0"*64
        path.write_text(json.dumps(record))
        with patch.object(remote, "fetch_bytes") as fetch:
            with self.assertRaises(remote.DeploymentError):
                remote.verify_once(path)
            fetch.assert_not_called()

    def test_missing_remote_stays_not_verified(self):
        with patch.object(remote, "fetch_bytes", side_effect=OSError("offline")):
            with self.assertRaisesRegex(remote.DeploymentError, "failed after"):
                remote.verify(self.site / bundle.MANIFEST)
