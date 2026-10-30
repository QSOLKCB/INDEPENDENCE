"""v0.7 Proof Contracts — stdlib-only registry and receipt regression checks."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from check_proof_contracts import (  # noqa: E402
    ContractError, check_registry, strict_json as load_registry,
)
from verify_proof_receipt import (  # noqa: E402
    InvalidProofReceipt, expected_report, verify, strict_json as load_receipt,
    main as verify_main,
)


def seal(report):
    text = json.dumps(report, ensure_ascii=False, indent=2)
    return {"format": "PROOF-CONTRACT-RECEIPT/1",
            "algorithm": "SHA-256/UTF-8",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "payload_text": text}


class ProofTests(unittest.TestCase):
    def test_registry_contracts_exist_and_no_proofs_claimed(self):
        result = check_registry(ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["obligations"], 8)
        self.assertEqual(result["formally_proved"], 0)

    def test_registry_digest_is_stable(self):
        self.assertEqual(check_registry(ROOT), check_registry(ROOT))

    @staticmethod
    def fixture_dir():
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        for path in ("proof/contracts.json", "lab/core.js", "ledger/ledger.js",
                     "scripts/verify_museum.py"):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        return tmp, root

    def test_registry_rejects_false_proof_status(self):
        tmp, root = self.fixture_dir()
        with tmp:
            file = root / "proof/contracts.json"
            data = json.loads(file.read_text(encoding="utf-8"))
            data["obligations"][0]["formal_status"] = "PROVED"
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "mislabelled"):
                check_registry(root)

    def test_registry_rejects_target_substitution(self):
        tmp, root = self.fixture_dir()
        with tmp:
            file = root / "proof/contracts.json"
            data = json.loads(file.read_text(encoding="utf-8"))
            data["obligations"][2]["target"]["path"] = "unrelated.js"
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "target/order"):
                check_registry(root)

    def test_registry_rejects_missing_source(self):
        tmp, root = self.fixture_dir()
        with tmp:
            (root / "lab/core.js").unlink()
            with self.assertRaisesRegex(ContractError, "missing referenced target"):
                check_registry(root)

    def test_registry_rejects_duplicate_json_properties(self):
        with self.assertRaises(ContractError):
            load_registry('{"proof":1,"proof":2}')

    def test_receipt_accepts_expected_fixed_report(self):
        result = verify(seal(expected_report()))
        self.assertEqual((result["contracts_checked"], result["counterexamples"],
                          result["formally_proved"]), (5, 1, 0))

    def test_receipt_rejects_payload_tampering(self):
        data = seal(expected_report())
        data["payload_text"] += " "
        with self.assertRaisesRegex(InvalidProofReceipt, "SHA-256 mismatch"):
            verify(data)

    def test_resealed_false_formal_proof_rejected(self):
        report = expected_report()
        report["formal_proofs"]["lean"] = "PROVED"
        with self.assertRaisesRegex(InvalidProofReceipt, "mismatch"):
            verify(seal(report))

    def test_resealed_false_counterexample_rejected(self):
        report = expected_report()
        report["checks"][4]["status"] = "BOUNDED_EXHAUSTIVE"
        with self.assertRaisesRegex(InvalidProofReceipt, "mismatch"):
            verify(seal(report))

    def test_resealed_fabricated_test_count_rejected(self):
        report = expected_report()
        report["checks"][0]["cases"] = 130561
        with self.assertRaisesRegex(InvalidProofReceipt, "mismatch"):
            verify(seal(report))

    def test_resealed_bool_instead_of_integer_rejected(self):
        report = expected_report()
        report["schema_version"] = True  # Python normally considers True == 1
        with self.assertRaisesRegex(InvalidProofReceipt, "mismatch"):
            verify(seal(report))

    def test_resealed_extra_attestation_rejected(self):
        report = expected_report()
        report["execution_witnessed_by_third_party"] = True
        with self.assertRaisesRegex(InvalidProofReceipt, "mismatch"):
            verify(seal(report))

    def test_receipt_rejects_duplicate_keys_and_numeric_overflow(self):
        for raw in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(InvalidProofReceipt):
                load_receipt(raw)

    def test_receipt_rejects_malformed_envelope(self):
        for raw in ({}, [], {"format": "wrong"}):
            with self.subTest(raw=raw), self.assertRaises(InvalidProofReceipt):
                verify(raw)

    def test_receipt_disk_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(seal(expected_report())), encoding="utf-8")
            self.assertEqual(verify_main([str(path), "--json"]), 0)
            path.write_text("{}", encoding="utf-8")
            self.assertEqual(verify_main([str(path)]), 1)

    def test_ui_is_static_and_deployed(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text(encoding="utf-8")
        audit = (ROOT / "scripts/audit.py").read_text(encoding="utf-8")
        self.assertIn('id="proof"', page)
        self.assertIn('href="#proof"', page)
        self.assertIn("mountProof();", app)
        self.assertIn("python3 scripts/check_proof_contracts.py --json", workflow)
        self.assertIn('cp proof/core.js proof/ui.js proof/proof.css proof/contracts.json "$site/proof/"', workflow)
        for path in ("proof/core.js", "proof/ui.js", "proof/proof.css",
                     "proof/contracts.json"):
            self.assertIn('"' + path + '"', audit)

    def test_ui_does_not_interpret_evidence_as_html(self):
        source = (ROOT / "proof/ui.js").read_text(encoding="utf-8")
        self.assertIn("textContent", source)
        for forbidden in ("innerHTML", "new Function(", "eval(", "fetch("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
