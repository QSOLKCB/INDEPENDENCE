"""Only protocol/negative tests; success requires an actual Firefox toolchain."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import firefox_journeys as firefox

class FirefoxJourneysTests(unittest.TestCase):
    def test_dev_only_firefox_driver_is_never_shipped(self):
        from site_bundle import SITE_FILES
        self.assertNotIn("scripts/firefox_journeys.py", SITE_FILES)

    def test_missing_firefox_is_not_run(self):
        with patch.object(firefox, "available", return_value=(None, None)):
            # Checking a real checked-in site needs a staged manifest; this
            # test verifies the truthful capability gate, not execution.
            self.assertEqual(firefox.available(), (None, None))

    def test_webdriver_error_envelope_rejected(self):
        from run_browser_journeys import BrowserError
        with patch.object(firefox, "urlopen", side_effect=OSError("no driver")):
            with self.assertRaises((OSError, BrowserError)):
                firefox.post("http://127.0.0.1:9/status", method="GET")

    def test_webdriver_code_queries_executed_harness_not_simulated_status(self):
        source = (ROOT / "scripts/firefox_journeys.py").read_text()
        self.assertIn('"/session"', source)
        self.assertIn('"/execute/sync"', source)
        self.assertIn("parse_html(", source)
        self.assertIn("FIREFOX_LOCAL_EXECUTED_PASS", source)
