"""GREMLIN-BREEDING/1 offline tests: no packages, source mutation or network."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_breeding import (  # noqa: E402
    InvalidReceipt, MUTANTS, expected_report, main, shuffled, strict_json, verify,
)


def seal(report):
    text = json.dumps(report, ensure_ascii=False, indent=2)
    return {
        "format": "GREMLIN-BREEDING-RECEIPT/1",
        "algorithm": "SHA-256/UTF-8",
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "payload_text": text,
    }


class BreedingTests(unittest.TestCase):
    def test_valid_smoke_receipt(self):
        result = verify(seal(expected_report(314159, "smoke")))
        self.assertEqual((result["mutants"], result["killed"], result["survived"]), (15, 2, 13))

    def test_valid_full_receipt(self):
        result = verify(seal(expected_report(314159, "full")))
        self.assertEqual((result["mutants"], result["killed"], result["survived"]), (15, 15, 0))

    def test_seeded_order_stable(self):
        self.assertEqual(shuffled(314159), shuffled(314159))
        self.assertNotEqual(shuffled(1), shuffled(314159))
        self.assertEqual([target + "/" + mutant for target, mutant, _, _ in shuffled(1)][:3],
                         ["finite/shallow", "receipt/accept40or64", "imports/fromOnly"])

    def test_all_mutants_have_nonempty_divergence_witnesses(self):
        self.assertEqual(len(MUTANTS), 15)
        self.assertTrue(all(witnesses for _, _, _, witnesses in MUTANTS))

    def test_seed_limits(self):
        for seed in (0, -1, 0x100000000, True, 1.5, "1"):
            with self.subTest(seed=seed), self.assertRaises(InvalidReceipt):
                expected_report(seed, "full")

    def test_unknown_suite_rejected(self):
        with self.assertRaises(InvalidReceipt):
            expected_report(1, "sketchy")

    def test_tampered_payload_detected(self):
        doc = seal(expected_report(1, "full"))
        doc["payload_text"] += " "
        with self.assertRaisesRegex(InvalidReceipt, "SHA-256 mismatch"):
            verify(doc)

    def test_resealed_false_survivor_rejected(self):
        data = expected_report(1, "full")
        data["results"][0]["status"] = "survived"
        with self.assertRaisesRegex(InvalidReceipt, "classification mismatch"):
            verify(seal(data))

    def test_resealed_false_score_rejected(self):
        data = expected_report(1, "smoke")
        data["summary"]["killed"] = 15
        with self.assertRaisesRegex(InvalidReceipt, "classification mismatch"):
            verify(seal(data))

    def test_resealed_forged_witness_rejected(self):
        data = expected_report(1, "full")
        data["results"][0]["witness_tests"].append("invented")
        with self.assertRaisesRegex(InvalidReceipt, "classification mismatch"):
            verify(seal(data))

    def test_resealed_swapped_mutant_identity_rejected(self):
        data = expected_report(1, "full")
        data["results"][0]["id"] = "finite/malicious"
        with self.assertRaisesRegex(InvalidReceipt, "classification mismatch"):
            verify(seal(data))

    def test_resealed_extra_claim_rejected(self):
        data = expected_report(1, "smoke")
        data["extra_security_certification"] = True
        with self.assertRaisesRegex(InvalidReceipt, "classification mismatch"):
            verify(seal(data))

    def test_duplicate_json_properties_rejected(self):
        with self.assertRaises(InvalidReceipt):
            strict_json('{"score":0,"score":100}')

    def test_nonfinite_json_rejected(self):
        for raw in ('{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(InvalidReceipt):
                strict_json(raw)

    def test_non_sha_receipt_rejected(self):
        receipt = seal(expected_report(1, "smoke"))
        receipt["sha256"] = "a" * 40
        with self.assertRaisesRegex(InvalidReceipt, "invalid SHA-256"):
            verify(receipt)

    def test_disk_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(seal(expected_report(1, "full"))), encoding="utf-8")
            self.assertEqual(main([str(path), "--json"]), 0)
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(main([str(path)]), 1)

    def test_site_and_deployment_invariants(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        audit = (ROOT / "scripts/audit.py").read_text(encoding="utf-8")
        self.assertIn('id="breeding"', html)
        self.assertIn("mountBreeding();", app)
        self.assertIn('cp breeding/core.js breeding/ui.js breeding/breeding.css "$site/breeding/"',
                      workflow)
        for name in ("breeding/core.js", "breeding/ui.js", "breeding/breeding.css"):
            self.assertTrue((ROOT / name).is_file())
            self.assertIn('"' + name + '"', audit)

    def test_no_dynamic_execution_or_outbound_access(self):
        source = (ROOT / "breeding/core.js").read_text(encoding="utf-8")
        ui = (ROOT / "breeding/ui.js").read_text(encoding="utf-8")
        for token in ("eval(", "new Function(", "innerHTML", "api.github.com", "fetch("):
            self.assertNotIn(token, source)
            self.assertNotIn(token, ui)
        self.assertIn("textContent", ui)


if __name__ == "__main__":
    unittest.main()
