"""v1.0 browser harness parser tests; these do not claim real browser execution."""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_browser_journeys as browser

class BrowserJourneysTests(unittest.TestCase):
    def test_script_is_standalone_actual_browser_module(self):
        text = (ROOT / "scripts/browser_harness.js").read_text()
        for snippet in ("frame.contentWindow", "'/#top'", "getElementById('run-tests')",
                        "getElementById('formal-lab-run')", "getElementById('property-run')",
                        "__independence_inline_probe", "getEntriesByType('resource')"):
            self.assertIn(snippet, text)

    def test_html_requires_real_completed_json(self):
        report = {"mode": "normal", "status": "PASS",
                  "user_agent": "Real Browser Test",
                  "viewport": {"width": 1000, "height": 800},
                  "resource_count": 10,
                  "checks": [{"name": name, "status": "PASS", "detail": "ok"}
                             for name in sorted(browser.NORMAL_CHECKS)]}
        raw = ('<pre id="verification-result" data-complete="yes">' +
               json.dumps(report).replace("&", "&amp;") + "</pre>")
        self.assertEqual(browser.parse_html(raw, "normal"), report)
        with self.assertRaisesRegex(browser.BrowserError, "did not complete"):
            browser.parse_html(raw.replace('data-complete="yes"', ''), "normal")

    def test_forged_pass_with_missing_assertions_is_rejected(self):
        fake = {"mode": "normal", "status": "PASS", "user_agent": "fake",
                "viewport": {"width": 1000}, "resource_count": 10,
                "checks": [{"name": "real CSP blocks inline code", "status": "PASS", "detail": ""}]}
        raw = '<pre id="verification-result" data-complete="yes">' + json.dumps(fake) + '</pre>'
        with self.assertRaisesRegex(browser.BrowserError, "contradicts"):
            browser.parse_html(raw, "normal")
        fake["checks"] = [{"name": name, "status": "PASS", "detail": ""}
                          for name in sorted(browser.NORMAL_CHECKS)]
        fake["checks"][0]["status"] = "FAIL"
        raw = '<pre id="verification-result" data-complete="yes">' + json.dumps(fake) + '</pre>'
        with self.assertRaisesRegex(browser.BrowserError, "contradicts"):
            browser.parse_html(raw, "normal")

    def test_fake_browsers_cannot_produce_a_pass(self):
        with self.assertRaises(browser.BrowserError):
            browser.parse_html('<pre id="verification-result" data-complete="yes">{}</pre>', "normal")
        with self.assertRaises(browser.BrowserError):
            browser.parse_html('<pre id="verification-result" data-complete="yes">invalid</pre>', "normal")

    def test_harness_is_development_only_not_staged(self):
        from site_bundle import SITE_FILES
        self.assertNotIn("scripts/browser_harness.js", SITE_FILES)
        self.assertNotIn("scripts/run_browser_journeys.py", SITE_FILES)
        self.assertNotIn("scripts/browser_harness.js", (ROOT / "index.html").read_text())
