"""Integrity and provenance regression tests for AUTOMATA4/1 evidence reports."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_automata_formal as lab  # noqa: E402
import verify_automata_evidence as evidence  # noqa: E402


class AutomataEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = lab.inspect()

    def test_no_toolchain_receipt_still_valid_but_unproved(self):
        status = evidence.verify(self.report)
        self.assertEqual(status["archive_integrity"], "PASS")
        self.assertEqual(status["reference_cases"], 4096)
        for key in ("lean_status", "spark_status", "ada_status", "javascript_status"):
            self.assertEqual(status[key], "NOT_RUN")
        self.assertEqual(status["execution_attestation"], "NOT_INDEPENDENTLY_ESTABLISHED")

    def test_false_proof_success_without_logs_is_rejected(self):
        for name, status in (("lean", "KERNEL_CHECKED"),
                             ("spark", "GNATPROVE_REPORTED_DISCHARGED"),
                             ("ada", "LOCAL_ADA_FINITE_EXECUTED_UNATTESTED"),
                             ("javascript", "LOCAL_JS_FINITE_EXECUTED")):
            with self.subTest(stage=name):
                altered = copy.deepcopy(self.report)
                altered[name]["status"] = status
                with self.assertRaises(evidence.ReceiptError):
                    evidence.verify(altered)

    def test_missing_executables_cannot_forge_checks(self):
        for field in ("lean", "spark", "ada", "javascript"):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.report)
                altered[field]["command"] = ["synthetic-tool", "pretend-success"]
                with self.assertRaisesRegex(evidence.ReceiptError, "fabricates"):
                    evidence.verify(altered)

    def test_false_cross_language_vector_hash_is_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["vectors_sha256"] = "0" * 64
        with self.assertRaisesRegex(evidence.ReceiptError, "corpus"):
            evidence.verify(altered)

    def test_spec_version_substitution_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["protocol"] = "AUTOMATA4-FORMAL-LAB/999"
        with self.assertRaises(evidence.ReceiptError):
            evidence.verify(altered)

    def test_boolean_count_and_extra_attestation_rejected(self):
        for field, value in (("finite_cases", True), ("independently_certified", True)):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.report)
                altered[field] = value
                with self.assertRaises(evidence.ReceiptError):
                    evidence.verify(altered)

    def test_reject_duplicate_json_and_floating_point_overflow(self):
        for raw in ('{"status":1,"status":2}', '{"x":NaN}', '{"x":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(evidence.ReceiptError):
                evidence.strict_json(raw)

    def test_lean_receipt_rejects_rehashed_forged_axiom_list(self):
        altered = copy.deepcopy(self.report)
        log = "\n".join(
            "'IndependenceAutomata." + name + "' depends on axioms: [sorryAx]"
            for name in lab.THEOREMS)
        altered["lean"] = {
            "status": "KERNEL_CHECKED", "tool_version": "Lean (version 4.35.0, x86_64)",
            "command": evidence.LEAN_CMD, "exit_code": 0,
            "axiom_audit": {name: ["propext"] for name in lab.THEOREMS},
            "raw_output": log,
            "raw_output_sha256": hashlib.sha256(log.encode()).hexdigest()
        }
        with self.assertRaisesRegex(evidence.ReceiptError, "axioms differ"):
            evidence.verify(altered)

    def test_lean_receipt_rejects_duplicate_axiom_audits(self):
        altered = copy.deepcopy(self.report)
        log = "\n".join(
            "'IndependenceAutomata." + name + "' does not depend on any axioms"
            for name in lab.THEOREMS)
        log += "\n'IndependenceAutomata.rule_zero_cell' does not depend on any axioms"
        altered["lean"] = {
            "status": "KERNEL_CHECKED", "tool_version": "Lean (version 4.35.0, x86_64)",
            "command": evidence.LEAN_CMD, "exit_code": 0,
            "axiom_audit": {name: [] for name in lab.THEOREMS},
            "raw_output": log,
            "raw_output_sha256": hashlib.sha256(log.encode()).hexdigest()
        }
        with self.assertRaisesRegex(evidence.ReceiptError, "duplicated"):
            evidence.verify(altered)

    def test_stale_js_source_hash_rejected(self):
        altered = copy.deepcopy(self.report)
        altered["javascript_files_sha256"]["lab/core.js"] = "0" * 64
        with self.assertRaisesRegex(evidence.ReceiptError, "javascript_files_sha256"):
            evidence.verify(altered)

    def test_invalid_gnatprove_success_zero_checks_rejected(self):
        altered = copy.deepcopy(self.report)
        output = "Success: all checks proved (0 checks).\n"
        altered["spark"] = {
            "status": "GNATPROVE_REPORTED_DISCHARGED",
            "tool_version": "FSF 16.1.0",
            "command": evidence.SPARK_CMD,
            "exit_code": 0,
            "checks": 0,
            "raw_output": output,
            "raw_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        }
        with self.assertRaises(evidence.ReceiptError):
            evidence.verify(altered)

    def test_bad_adacorpus_count_rejected(self):
        altered = copy.deepcopy(self.report)
        output = "Compile\nBind\nLink\n"
        altered["ada"] = {
            "status": "LOCAL_ADA_FINITE_EXECUTED_UNATTESTED",
            "command": evidence.ADA_CMD, "build_exit_code": 0,
            "build_output": output,
            "build_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
            "binary_sha256": "a" * 64,
            "cases": 4095, "invalid_cases": len(lab.NEGATIVES),
            "vectors_sha256": lab.EXPECTED_VECTORS_SHA256,
        }
        with self.assertRaises(evidence.ReceiptError):
            evidence.verify(altered)


if __name__ == "__main__":
    unittest.main()
