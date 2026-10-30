"""Offline standard-library regression tests for exported Tribunal evidence receipts."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_tribunal import (  # noqa: E402
    ReceiptError, main, strict_json, verify_receipt, phase_fingerprints, bootstrap_interval
)

PHASES = ("initial", "update", "reorder")
ATTRIBUTION = "local keyed adapter is illustrative; NOT a React/Vue/Svelte benchmark"


def fixture():
    pairs = []
    for index in range(8):
        direct = {phase: float(index + 1) for phase in PHASES}
        keyed = {phase: float(index + 2) for phase in PHASES}
        pairs.append({"direct": direct, "keyed": keyed})
    summary = {}
    for phase in PHASES:
        summary[phase] = {
            "trials": 8, "direct_median_ms": 4.5, "keyed_median_ms": 5.5,
            "paired_delta_median_ms": 1.0, "paired_delta_bootstrap_95_ms": [1.0, 1.0]
        }
    report = {
        "protocol": "DOM-TRIBUNAL/1", "schema_version": 1, "observed_at": "2026-10-30T00:00:00.000Z",
        "config": {"seed": 1, "count": 100, "warmups": 2, "trials": 8},
        "candidates": [
            {"id": "direct", "label": "Direct DOM", "kind": "native"},
            {"id": "keyed", "label": "Local keyed adapter", "kind": "illustrative"}
        ],
        "samples_ms": pairs, "statistics": summary,
        "phase_fingerprints": phase_fingerprints(1, 100),
        "methodology": {"attribution": ATTRIBUTION},
        "adapter_source_bytes": {"direct": 500, "keyed": 900},
        "low_clock_resolution_observed": False,
        "correctness": {"passed": True, "trials_verified": 60},
    }
    return seal(report)


def seal(report):
    text = json.dumps(report, separators=(",", ":"), ensure_ascii=False)
    return {"format": "DOM-TRIBUNAL-RECEIPT/1", "algorithm": "SHA-256/UTF-8",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "payload_text": text}


class TribunalReceiptTests(unittest.TestCase):
    def test_valid_fixture(self):
        self.assertEqual(verify_receipt(fixture())["paired_trials"], 8)

    def test_payload_edit_detected(self):
        receipt = fixture()
        receipt["payload_text"] += " "
        with self.assertRaisesRegex(ReceiptError, "mismatch"):
            verify_receipt(receipt)

    def test_hash_wont_certify_false_statistics(self):
        record = json.loads(fixture()["payload_text"])
        record["statistics"]["initial"]["direct_median_ms"] = -999
        with self.assertRaisesRegex(ReceiptError, "statistics mismatch"):
            verify_receipt(seal(record))

    def test_missing_or_extra_samples_rejected(self):
        for samples in ([], [None]):
            record = json.loads(fixture()["payload_text"])
            record["samples_ms"] = samples
            with self.subTest(samples=samples), self.assertRaises(ReceiptError):
                verify_receipt(seal(record))

    def test_nonfinite_and_negative_measurements_rejected(self):
        for value in (-1, 1e999):
            record = json.loads(fixture()["payload_text"])
            record["samples_ms"][0]["direct"]["initial"] = value
            with self.subTest(value=value), self.assertRaises(ReceiptError):
                verify_receipt(seal(record))

    def test_duplicate_keys_and_nonfinite_literals_rejected(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ReceiptError):
                strict_json(raw)

    def test_lying_correctness_flag_rejected(self):
        report = json.loads(fixture()["payload_text"])
        report["correctness"]["passed"] = False
        with self.assertRaisesRegex(ReceiptError, "correctness-gate"):
            verify_receipt(seal(report))

    def test_false_low_resolution_flag_rejected(self):
        report = json.loads(fixture()["payload_text"])
        report["low_clock_resolution_observed"] = True
        with self.assertRaisesRegex(ReceiptError, "low-resolution"):
            verify_receipt(seal(report))

    def test_wrong_label_is_rejected(self):
        report = json.loads(fixture()["payload_text"])
        report["candidates"][1]["label"] = "React"
        with self.assertRaisesRegex(ReceiptError, "candidates"):
            verify_receipt(seal(report))

    def test_claim_of_real_framework_is_rejected(self):
        report = json.loads(fixture()["payload_text"])
        report["methodology"]["attribution"] = "React outperformed"
        with self.assertRaisesRegex(ReceiptError, "attribution"):
            verify_receipt(seal(report))

    def test_fixture_fingerprint_tampering_rejected(self):
        report = json.loads(fixture()["payload_text"])
        report["phase_fingerprints"]["initial"] = "deadbeef"
        with self.assertRaisesRegex(ReceiptError, "fingerprint mismatch"):
            verify_receipt(seal(report))

    def test_bootstrap_interval_recalculated(self):
        report = json.loads(fixture()["payload_text"])
        report["statistics"]["update"]["paired_delta_bootstrap_95_ms"] = [0.1, 1.2]
        with self.assertRaisesRegex(ReceiptError, "bootstrap interval mismatch"):
            verify_receipt(seal(report))

    def test_python_bootstrap_known_constant(self):
        self.assertEqual(bootstrap_interval([1.0] * 8), [1.0, 1.0])

    def test_cross_language_fixture_vectors(self):
        self.assertEqual(phase_fingerprints(1, 100), {
            "initial": "cd03fdfa", "update": "262c209e", "reorder": "4da3f3bf"
        })
        self.assertEqual(phase_fingerprints(314159, 200), {
            "initial": "1fe43890", "update": "d437f12c", "reorder": "aff9394c"
        })

    def test_cross_language_bootstrap_vectors(self):
        self.assertEqual(bootstrap_interval([1,2,-1,4,6,-3,3,1]), [-1, 4])
        self.assertEqual(bootstrap_interval([(i % 5) - 2.25 for i in range(12)]),
                         [-1.75, 0.75])

    def test_bad_methodology_type_rejected(self):
        report = json.loads(fixture()["payload_text"])
        report["methodology"] = "bad"
        with self.assertRaisesRegex(ReceiptError, "attribution"):
            verify_receipt(seal(report))

    def test_tribunal_static_site_integration(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        for name in ("core.js", "direct.js", "keyed.js", "bench.js", "ui.js", "tribunal.css"):
            self.assertTrue((ROOT / "tribunal" / name).is_file())
        self.assertIn('id="tribunal"', html)
        self.assertIn("mountTribunal();", app)
        from site_bundle import SITE_FILES
        self.assertIn('python3 scripts/site_bundle.py stage --source .', workflow)
        for filename in ("tribunal/bench.js", "tribunal/ui.js", "tribunal/tribunal.css"):
            self.assertIn(filename, SITE_FILES)

    def test_disk_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(main([str(path), "--json"]), 0)
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(main([str(path)]), 1)

    def test_no_external_dependencies_in_tribunal_assets(self):
        for path in ("tribunal/core.js", "tribunal/direct.js", "tribunal/keyed.js",
                     "tribunal/bench.js", "tribunal/ui.js"):
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("from 'https://", source)
            self.assertNotIn('from "https://', source)


if __name__ == "__main__":
    unittest.main()
