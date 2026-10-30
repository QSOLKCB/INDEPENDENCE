"""Offline fake-CDN fixture tests; explicitly NOT real public network evidence."""
import json
from pathlib import Path
from urllib.error import HTTPError
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


    def test_public_404_identifies_exact_asset_and_never_passes(self):
        url = remote.BASE + "deployment-manifest.json"
        error = HTTPError(url, 404, "Not Found", {}, None)
        opener = Mock()
        opener.open.side_effect = error
        with patch.object(remote, "build_opener", return_value=opener):
            with self.assertRaisesRegex(remote.DeploymentError,
                                        "public asset HTTP 404 at .*deployment-manifest.json"):
                remote.fetch_bytes(url)

    def test_failed_public_observation_writes_explicit_not_verified_receipt(self):
        output = self.root / "failed-observation.json"
        with patch.object(remote, "verify", side_effect=remote.DeploymentError(
                "public asset HTTP 404 at " + remote.BASE + "deployment-manifest.json")):
            exit_code = remote.main([
                "--manifest", str(self.site / bundle.MANIFEST),
                "--output", str(output)
            ])
        self.assertEqual(exit_code, 1)
        result = json.loads(output.read_text())
        self.assertEqual(result["protocol"], remote.PROTOCOL)
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertIn("deployment-manifest.json", result["reason"])
        self.assertNotIn("REMOTE_BYTES_MATCHED_UNATTESTED", output.read_text())

    def test_workflows_separate_publish_from_remote_byte_observation(self):
        deploy = (ROOT / ".github/workflows/deploy-pages.yml").read_text()
        manual = (ROOT / ".github/workflows/verify-public-pages.yml").read_text()
        self.assertIn("id: deployment", deploy)
        self.assertIn("continue-on-error: true", deploy)
        self.assertIn("id: public-observation", deploy)
        self.assertIn("name: independence-pages-manifest", deploy)
        self.assertIn("id: deployment", deploy.split("id: public-observation")[0])
        self.assertIn("run-id:", manual)
        self.assertIn("name: github-pages", manual)
        self.assertIn("tar -xOf", manual)
        self.assertIn("./deployment-manifest.json", manual)
        self.assertIn("verify_deployed_site.py", manual)

    def test_missing_remote_stays_not_verified(self):
        with patch.object(remote, "fetch_bytes", side_effect=OSError("offline")):
            with self.assertRaisesRegex(remote.DeploymentError, "failed after"):
                remote.verify(self.site / bundle.MANIFEST)
