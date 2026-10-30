"""Browser AUTOMATA4 receipt and first-party deployment regression tests."""
from pathlib import Path
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import verify_automata_browser_receipt as bridge

def valid_envelope():
    payload = json.dumps({
        "protocol": bridge.PROTOCOL,
        "status": "FINITE_JS_CONFORMANCE",
        "cases": 4096, "vectors_sha256": bridge.EXPECTED_VECTORS_SHA256,
        "proof_status": "NOT_A_FORMAL_PROOF"
    }, separators=(",", ":"))
    return {"format": bridge.FORMAT, "payload_text": payload,
            "sha256": hashlib.sha256(payload.encode()).hexdigest()}

class AutomataBrowserReceiptTests(unittest.TestCase):
    def test_valid_bytes_are_internally_consistent_not_attested(self):
        self.assertEqual(bridge.verify(json.dumps(valid_envelope()))["status"],
                         "INTERNALLY_CONSISTENT_UNATTESTED")

    def test_reject_rehashed_forged_proof_status(self):
        record = valid_envelope()
        fake = json.loads(record["payload_text"])
        fake["proof_status"] = "KERNEL_CHECKED"
        record["payload_text"] = json.dumps(fake)
        record["sha256"] = hashlib.sha256(record["payload_text"].encode()).hexdigest()
        with self.assertRaises(bridge.BrowserReceiptError):
            bridge.verify(json.dumps(record))

    def test_reject_rehashed_wrong_vector_digest(self):
        record = valid_envelope()
        fake = json.loads(record["payload_text"])
        fake["vectors_sha256"] = "0" * 64
        record["payload_text"] = json.dumps(fake)
        record["sha256"] = hashlib.sha256(record["payload_text"].encode()).hexdigest()
        with self.assertRaises(bridge.BrowserReceiptError):
            bridge.verify(json.dumps(record))

    def test_reject_duplicate_keys_and_nonfinite(self):
        with self.assertRaises(bridge.BrowserReceiptError):
            bridge.verify('{"format":"x","format":"y"}')
        with self.assertRaises(bridge.BrowserReceiptError):
            bridge.verify('{"format":1e999}')
        with self.assertRaises(bridge.BrowserReceiptError):
            bridge.verify('{"format":NaN}')

    def test_reject_oversized_envelopes(self):
        with self.assertRaisesRegex(bridge.BrowserReceiptError, "oversized"):
            bridge.verify(" " * 4097)

    def test_html_script_and_stylesheet_are_separate_elements(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<link rel="stylesheet" href="./formal-lab/formal-lab.css">', html)
        self.assertIn('<script type="module" src="./app.js"></script>', html)
        self.assertNotIn('href="./formal-lab/formal-lab.css"\n', html)

    def test_browser_lab_is_staged_by_pages_deployment(self):
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text()
        from site_bundle import SITE_FILES
        self.assertIn("formal-lab/core.js", SITE_FILES)
        self.assertIn("formal-lab/ui.js", SITE_FILES)
        self.assertIn('python3 scripts/site_bundle.py stage --source .', workflow)

    def test_browser_and_node_use_real_production_evolve(self):
        source = (ROOT / "formal-lab/core.js").read_text()
        self.assertIn("import {evolve} from '../lab/core.js';", source)
        self.assertIn("const actual = transition(source, rule);", source)
        self.assertIn("source[i] === bit", source)
        self.assertIn("vectors.push([rule, ...bits, expected.join('')])", source)
        self.assertIn(bridge.EXPECTED_VECTORS_SHA256, source)

if __name__ == "__main__":
    unittest.main()
