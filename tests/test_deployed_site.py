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
        # Mirror the uploaded Pages observation: this control marker 404s,
        # even while ordinary HTTP assets can be fetched.
        if uri.endswith("/.nojekyll"):
            raise AssertionError(".nojekyll must never be fetched over HTTP")
        return (self.site / uri.removeprefix(remote.BASE)).read_bytes()

    def test_local_fake_cdn_verifies_consistency_not_authorship(self):
        with patch.object(remote, "fetch_bytes", side_effect=self.fake):
            report = remote.verify(self.site / bundle.MANIFEST)
        self.assertEqual(report["status"], "REMOTE_HTTP_ASSETS_MATCHED_MARKER_UNOBSERVED")
        self.assertEqual(report["files"], len(bundle.SITE_FILES) - 1)
        self.assertTrue(report["manifest_verified"])
        self.assertEqual(report["non_http_markers_unobserved"], [".nojekyll"])
        self.assertEqual(report["non_http_marker_staged_sha256"][".nojekyll"],
                         bundle.hash_bytes((self.site / ".nojekyll").read_bytes()))


    def test_dotfile_is_required_in_staging_but_not_fetched_remotely(self):
        manifest = json.loads((self.site / bundle.MANIFEST).read_text())
        self.assertIn(".nojekyll", bundle.SITE_FILES)
        self.assertIn(".nojekyll", manifest["files"])
        requested = []

        def fetch(uri):
            requested.append(uri)
            return self.fake(uri)

        with patch.object(remote, "fetch_bytes", side_effect=fetch):
            result = remote.verify_once(self.site / bundle.MANIFEST)
        self.assertNotIn(remote.BASE + ".nojekyll", requested)
        self.assertEqual(set(requested),
                         {remote.BASE + bundle.MANIFEST}
                         | {remote.BASE + name for name in remote.PUBLIC_HTTP_ASSETS})
        self.assertEqual(result["status"], "REMOTE_HTTP_ASSETS_MATCHED_MARKER_UNOBSERVED")

    def test_missing_or_wrong_real_remote_file_still_fails_closed(self):
        for mismatch in (False, True):
            with self.subTest(mismatch=mismatch):
                def observed(uri):
                    if uri.endswith("/index.html"):
                        if mismatch:
                            return b"<html>tampered</html>"
                        raise remote.DeploymentError("public asset HTTP 404 at " + uri)
                    return self.fake(uri)
                with patch.object(remote, "fetch_bytes", side_effect=observed):
                    with self.assertRaisesRegex(remote.DeploymentError, "index.html"):
                        remote.verify_once(self.site / bundle.MANIFEST)

    def test_remote_manifest_cannot_omit_or_rehash_control_marker(self):
        path = self.site / bundle.MANIFEST
        record = json.loads(path.read_text())
        for mode in ("missing", "rehashed"):
            with self.subTest(mode=mode):
                forged = json.loads(json.dumps(record))
                if mode == "missing":
                    forged["files"].pop(".nojekyll")
                else:
                    forged["files"][".nojekyll"] = "0" * 64
                path.write_text(json.dumps(forged))
                with patch.object(remote, "fetch_bytes") as fetch:
                    # Missing marker inventory fails in the existing strict
                    # bundle schema; changed marker digest fails in the
                    # observation's manifest-envelope check. Both fail closed.
                    with self.assertRaises((remote.DeploymentError,
                                            bundle.BundleError)):
                        remote.verify_once(path)
                    fetch.assert_not_called()
        path.write_text(json.dumps(record))

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
                remote.BASE + ".nojekyll",
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
        self.assertNotIn("REMOTE_HTTP_ASSETS_MATCHED_MARKER_UNOBSERVED", output.read_text())

    def test_workflows_separate_publish_from_remote_byte_observation(self):
        deploy = (ROOT / ".github/workflows/deploy-pages.yml").read_text()
        manual = (ROOT / ".github/workflows/verify-public-pages.yml").read_text()
        self.assertIn("id: deployment", deploy)
        self.assertIn("continue-on-error: true", deploy)
        self.assertIn("id: public-observation", deploy)
        self.assertIn("name: independence-pages-manifest", deploy)
        self.assertIn("id: deployment", deploy.split("id: public-observation")[0])
        self.assertIn("run-id:", manual)
        self.assertIn("name: independence-pages-manifest", manual)
        self.assertIn("name: github-pages", manual)
        self.assertLess(manual.index("name: independence-pages-manifest"),
                        manual.index("name: github-pages"))
        self.assertIn("id: preserved_manifest", manual)
        self.assertIn("if: steps.preserved_manifest.outcome != 'success'", manual)
        self.assertIn("continue-on-error: true", manual)
        self.assertIn("select_public_manifest.py", manual)
        self.assertIn("artifact.tar", manual)
        self.assertIn("verify_deployed_site.py", manual)

    def test_missing_remote_stays_not_verified(self):
        with patch.object(remote, "fetch_bytes", side_effect=OSError("offline")):
            with self.assertRaisesRegex(remote.DeploymentError, "failed after"):
                remote.verify(self.site / bundle.MANIFEST)
