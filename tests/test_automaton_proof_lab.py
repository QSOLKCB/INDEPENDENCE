"""v0.9 proof lab: executable stdlib fixtures and honest optional-tool boundaries."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import automaton_proof_lab as lab


class AutomatonProofLabTests(unittest.TestCase):
    def test_source_gate(self):
        result = lab.source_gate(ROOT)
        self.assertEqual(result["source_status"], "INSPECTED_NOT_PROVED")
        self.assertEqual(len(result["ada_sha256"]), 4)

    def test_all_2048_truth_table_vectors(self):
        result = lab.finite_check()
        self.assertEqual(result["neighbourhood_cases"], 2048)
        self.assertEqual(result["single_cell_boundary_cases"], 512)
        self.assertEqual(len(result["vector_sha256"]), 64)

    def test_two_independent_arithmetic_paths(self):
        for args in lab.vectors():
            self.assertEqual(lab.oracle(*args), lab.independent_bit(*args))
        self.assertEqual(lab.oracle(90, 1, 0, 0), 1)
        self.assertEqual(lab.oracle(90, 1, 1, 1), 0)

    def test_reject_invalid_operands(self):
        for values in [(256, 0, 0, 0), (-1, 0, 0, 0),
                       (30, 2, 0, 0), (30, True, 0, 0),
                       (30, 0, 0, 3)]:
            with self.subTest(values=values), self.assertRaises(lab.LabError):
                lab.oracle(*values)

    def test_vector_bytes_are_deterministic(self):
        first = lab.vector_bytes()
        self.assertEqual(first, lab.vector_bytes())
        self.assertEqual(first.count(b"\n"), 2048)
        self.assertEqual(hashlib.sha256(first).hexdigest(),
                         lab.finite_check()["vector_sha256"])

    def test_real_tools_not_synthetically_passed(self):
        with patch.object(lab.shutil, "which", return_value=None):
            self.assertEqual(lab.check_lean(ROOT)["status"], "NOT_RUN")
            self.assertEqual(lab.check_spark(ROOT)["status"], "NOT_RUN")

    def test_unrun_cli_not_claimed(self):
        self.assertEqual(lab.compare_ada(None)["status"], "NOT_RUN")
        report = lab.run(ROOT)
        self.assertEqual(report["lean"]["status"], "NOT_RUN")
        self.assertEqual(report["spark"]["status"], "NOT_RUN")
        self.assertEqual(report["ada_cli"]["status"], "NOT_RUN")
        self.assertEqual(report["browser"]["status"], "NOT_RUN")

    def test_strict_gates_fail_without_proofs(self):
        with patch.object(lab.shutil, "which", return_value=None):
            self.assertEqual(lab.main(["--require-proofs"]), 1)
        self.assertEqual(lab.main(["--require-ada"]), 1)

    def test_browser_receipt_round_trip(self):
        payload = {"protocol": "AUTOMATON-BROWSER/1", "status": "FINITE_JS_CONFORMANCE",
                   "neighbourhood_cases": 2048, "boundary_cases": 512,
                   "vector_sha256": lab.sha(lab.vector_bytes()),
                   "proof_status": "NOT_A_FORMAL_PROOF"}
        data = json.dumps(payload, separators=(",", ":"))
        envelope = {"format": "AUTOMATON-BROWSER-RECEIPT/1",
                    "sha256": lab.sha(data.encode()), "payload_text": data}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.json"
            path.write_text(json.dumps(envelope))
            self.assertEqual(lab.verify_browser_receipt(path)["status"],
                             "INTERNALLY_CONSISTENT_UNATTESTED")
            payload["proof_status"] = "KERNEL_CHECKED"
            bad = json.dumps(payload, separators=(",", ":"))
            envelope["payload_text"] = bad
            envelope["sha256"] = lab.sha(bad.encode())
            path.write_text(json.dumps(envelope))
            with self.assertRaises(lab.LabError):
                lab.verify_browser_receipt(path)

    def test_reject_forged_digest_duplicate_and_nonfinite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.json"
            for record in ('{"format":"AUTOMATON-BROWSER-RECEIPT/1",'
                           '"sha256":"0","payload_text":"{}"}',
                           '{"format":"a","format":"b","sha256":"0","payload_text":"{}"}',
                           '{"format":NaN,"sha256":"0","payload_text":"{}"}'):
                path.write_text(record)
                with self.assertRaises(lab.LabError):
                    lab.verify_browser_receipt(path)

    def test_tampered_lean_source_fails_static_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            dst = Path(temp)
            (dst / "formal/lean").mkdir(parents=True)
            (dst / "formal/spark").mkdir(parents=True)
            (dst / "formal/spec").mkdir(parents=True)
            for file in (lab.SPEC, lab.LEAN, "lean-toolchain", *lab.ADA):
                shutil.copy2(ROOT / file, dst / file)
            target = dst / lab.LEAN
            target.write_text(target.read_text() + "\naxiom bad : False\n")
            with self.assertRaises(lab.LabError):
                lab.source_gate(dst)

    def test_ada_mock_does_not_create_false_pass(self):
        fake = type("Run", (), {"returncode": 0, "stdout": "OK:1\n", "stderr": ""})
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "fakecli"
            p.write_text("not an executable")
            with patch.object(lab, "_run", return_value=fake):
                self.assertEqual(lab.compare_ada(p)["status"], "FAILED_OR_MISMATCH")


if __name__ == "__main__":
    unittest.main()
