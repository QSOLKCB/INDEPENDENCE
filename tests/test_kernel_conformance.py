"""Independent Python/Ada bridge: statuses must not be conflated."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_kernel_conformance import (build_report, finite_cases, rejected_cases,
    oracle, sample_ada_cases, make_receipt, run_ada)
from verify_kernel_receipt import (InvalidReceipt, verify, strict_json)


class ConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_report()

    def test_finite_exhaustive_count(self):
        self.assertEqual(len(list(finite_cases())), 8881)
        self.assertEqual(len(rejected_cases()), 16)

    def test_python_finite_fixture_agreement(self):
        self.assertEqual(self.report["evidence"]["python_conformance"]["finite_cases"], 8881)
        self.assertEqual(self.report["evidence"]["python_conformance"]["rejected_cases"], 16)

    def test_ada_absence_never_certifies(self):
        self.assertEqual(self.report["evidence"]["ada_cli_conformance"]["status"], "NOT_RUN")
        self.assertEqual(self.report["evidence"]["ada_contracts"]["status"], "NOT_RUN")
        self.assertEqual(self.report["evidence"]["mathematical_proof"]["status"], "NOT_RUN")

    def test_existing_python_application_not_proved(self):
        self.assertTrue(any("Existing application Python/JavaScript" in x for x in self.report["unresolved"]))

    def test_each_finite_operation_represented(self):
        kinds = {op for op, _ in finite_cases()}
        self.assertEqual(kinds, {"ADDR", "DECODE", "PARITY_ADD", "PARITY_MUL",
                                 "PHASE_ADD", "EDGE_VALID", "EDGE_STEP"})

    def test_all_invalid_samples_rejected(self):
        self.assertTrue(all(oracle(*item) == "ERR:INVALID" for item in rejected_cases()))

    def test_seeded_ada_sample_determinism_and_coverage(self):
        finite = list(finite_cases())
        a = sample_ada_cases(finite, 128)
        b = sample_ada_cases(finite, 128)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 128)
        self.assertEqual({row[0] for row in a}, {row[0] for row in finite})

    def test_too_small_ada_sample_rejected(self):
        with self.assertRaises(ValueError):
            sample_ada_cases(list(finite_cases()), 3)

    def test_valid_receipt(self):
        self.assertTrue(verify(make_receipt(self.report))["valid"])

    def test_tampered_payload_rejected(self):
        receipt = make_receipt(self.report)
        receipt["payload_text"] += " "
        with self.assertRaisesRegex(InvalidReceipt, "payload SHA"):
            verify(receipt)

    def test_resealed_fabricated_lean_proof_rejected(self):
        report = json.loads(make_receipt(self.report)["payload_text"])
        report["evidence"]["mathematical_proof"]["status"] = "MATHEMATICALLY_PROVED"
        with self.assertRaisesRegex(InvalidReceipt, "classification"):
            verify(make_receipt(report))

    def test_resealed_fabricated_ada_contract_rejected(self):
        report = json.loads(make_receipt(self.report)["payload_text"])
        report["evidence"]["ada_contracts"]["status"] = "ADA_CONTRACT_VERIFIED"
        with self.assertRaisesRegex(InvalidReceipt, "classification"):
            verify(make_receipt(report))

    def test_resealed_fabricated_ada_cli_rejected(self):
        report = json.loads(make_receipt(self.report)["payload_text"])
        report["evidence"]["ada_cli_conformance"] = {"status":"ADA_CLI_TESTED_UNATTESTED", "cases":200,
            "vectors_sha256":"0"*64,"binary_sha256":"f"*64}
        with self.assertRaisesRegex(InvalidReceipt, "Ada CLI evidence"):
            verify(make_receipt(report))

    def test_resealed_wrong_python_count_rejected(self):
        report = json.loads(make_receipt(self.report)["payload_text"])
        report["evidence"]["python_conformance"]["finite_cases"] = 9999
        with self.assertRaisesRegex(InvalidReceipt, "classification"):
            verify(make_receipt(report))

    def test_duplicated_json_keys_rejected(self):
        with self.assertRaises(InvalidReceipt):
            strict_json('{"a":1,"a":2}')

    def test_nonfinite_json_rejected(self):
        for malformed in ('{"x":NaN}', '{"x":1e999}', '{"x":Infinity}'):
            with self.subTest(malformed=malformed), self.assertRaises(InvalidReceipt):
                strict_json(malformed)

    def test_fake_cli_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fake_ada"
            path.write_text("#!/bin/sh\necho OK:999\n")
            path.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError, "Ada mismatch"):
                run_ada(path, [("PARITY_ADD", (0, 0))])

    def test_genuine_comparison_is_not_attestation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stub"
            path.write_text("#!/bin/sh\necho OK:0\n")
            path.chmod(0o755)
            status = run_ada(path, [("PARITY_ADD", (0, 0))])
            self.assertEqual(status["status"], "ADA_CLI_TESTED_UNATTESTED")


if __name__ == "__main__":
    unittest.main()
