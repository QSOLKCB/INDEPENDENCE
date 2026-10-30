"""Gremlin Museum — offline fixture, receipt and deployment regression tests."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from verify_museum import EXPECTED, InvalidReceipt, main, strict_json, verify  # noqa: E402


def fixture():
    rows = [
        {"id": id_, "kind": kind, "input": input_text, "legacy": legacy,
         "hardened": hardened, "assertions": {"passed": count, "total": count}, "passed": True}
        for id_, kind, input_text, legacy, hardened, count in EXPECTED
    ]
    provenance = [
        {"id": id_, "provenance": (
            "Documented INDEPENDENCE v0.1 review" if index < 2 else
            "Documented INDEPENDENCE v0.2 review" if index == 2 else
            "Illustrative local case, not a reported INDEPENDENCE vulnerability"
        ), "source": (
            "https://github.com/QSOLKCB/INDEPENDENCE/pull/1" if index < 2 else
            "https://github.com/QSOLKCB/INDEPENDENCE/pull/2" if index == 2 else
            "https://github.com/QSOLKCB/INDEPENDENCE"
        )}
        for index, (id_, *_) in enumerate(EXPECTED)
    ]
    payload = {
        "protocol": "GREMLIN-MUSEUM/1", "schema_version": 1,
        "scope": "isolated deterministic examples, no external exploitation",
        "exhibits": rows, "provenance": provenance,
        "limitations": [
            "String and data demonstrations; no payload is executed or injected as HTML.",
            "Static regex detection is a scoped fixture, not a complete JavaScript parser.",
            "A valid receipt proves byte integrity only, not independent reproduction or absence of vulnerabilities."
        ],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    return {"format": "GREMLIN-MUSEUM-RECEIPT/1", "algorithm": "SHA-256/UTF-8",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "payload_text": text}


def seal(payload):
    text = json.dumps(payload, ensure_ascii=False)
    return {"format": "GREMLIN-MUSEUM-RECEIPT/1", "algorithm": "SHA-256/UTF-8",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "payload_text": text}


class MuseumTests(unittest.TestCase):
    def test_valid_receipt(self):
        result = verify(fixture())
        self.assertEqual(result["exhibits"], 5)
        self.assertEqual(result["assertions"], 18)

    def test_stable_fixture(self):
        self.assertEqual(fixture(), fixture())

    def test_modified_payload_hash_rejected(self):
        doc = fixture()
        doc["payload_text"] += " "
        with self.assertRaisesRegex(InvalidReceipt, "mismatch"):
            verify(doc)

    def test_resealed_fake_result_rejected(self):
        data = json.loads(fixture()["payload_text"])
        data["exhibits"][2]["hardened"] = "All security problems solved!"
        with self.assertRaisesRegex(InvalidReceipt, "specimen observation"):
            verify(seal(data))

    def test_false_pass_flag_rejected(self):
        data = json.loads(fixture()["payload_text"])
        data["exhibits"][0]["passed"] = False
        with self.assertRaisesRegex(InvalidReceipt, "assertions failed"):
            verify(seal(data))

    def test_resealed_illustrative_relabelled_as_historical_rejected(self):
        document = json.loads(fixture()["payload_text"])
        document["provenance"][3]["provenance"] = "Confirmed historical INDEPENDENCE vulnerability"
        with self.assertRaisesRegex(InvalidReceipt, "incorrect fixed provenance"):
            verify(seal(document))

    def test_resealed_repository_prefix_collision_rejected(self):
        document = json.loads(fixture()["payload_text"])
        document["provenance"][3]["source"] = (
            "https://github.com/QSOLKCB/INDEPENDENCE-unrelated/pull/999"
        )
        with self.assertRaisesRegex(InvalidReceipt, "incorrect fixed provenance"):
            verify(seal(document))

    def test_resealed_swapped_legitimate_review_url_rejected(self):
        document = json.loads(fixture()["payload_text"])
        # This URL is real, but belongs to a different historical exhibit.
        document["provenance"][2]["source"] = "https://github.com/QSOLKCB/INDEPENDENCE/pull/1"
        with self.assertRaisesRegex(InvalidReceipt, "incorrect fixed provenance"):
            verify(seal(document))

    def test_resealed_illustrative_source_claiming_review_rejected(self):
        document = json.loads(fixture()["payload_text"])
        document["provenance"][4]["source"] = "https://github.com/QSOLKCB/INDEPENDENCE/pull/2"
        with self.assertRaisesRegex(InvalidReceipt, "incorrect fixed provenance"):
            verify(seal(document))

    def test_missing_provenance_rejected(self):
        data = json.loads(fixture()["payload_text"])
        data["provenance"].pop()
        with self.assertRaisesRegex(InvalidReceipt, "incomplete"):
            verify(seal(data))

    def test_duplicate_keys_and_nonfinite_values_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with self.subTest(text=text), self.assertRaises(InvalidReceipt):
                strict_json(text)

    def test_truncated_or_bad_receipt_rejected(self):
        for doc in ({}, {"format":"wrong"}, []):
            with self.subTest(doc=doc), self.assertRaises(InvalidReceipt):
                verify(doc)

    def test_disk_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "museum-receipt.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            self.assertEqual(main([str(path), "--json"]), 0)
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(main([str(path)]), 1)

    def test_static_site_and_deployment_staged(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        js = (ROOT / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        audit = (ROOT / "scripts/audit.py").read_text(encoding="utf-8")
        self.assertIn('id="museum"', html)
        self.assertIn("mountMuseum();", js)
        from site_bundle import SITE_FILES
        self.assertIn('python3 scripts/site_bundle.py stage --source .', workflow)
        for filename in ("museum/core.js", "museum/ui.js", "museum/museum.css"):
            self.assertIn(filename, SITE_FILES)
        for name in ("museum/core.js", "museum/ui.js", "museum/museum.css"):
            self.assertTrue((ROOT / name).is_file())
            self.assertIn('"' + name + '"', audit)

    def test_browser_inert_output_contract(self):
        source = (ROOT / "museum/ui.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", source)
        self.assertIn("textContent", source)
        self.assertNotIn("eval(", source)
        self.assertNotIn("api.github.com", source)


if __name__ == "__main__":
    unittest.main()
