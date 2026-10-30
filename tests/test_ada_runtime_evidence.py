"""Offline receipt integrity tests. Synthetic fixtures never attest real Ada execution."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify_ada_runtime_evidence as checked  # noqa: E402
from run_kernel_conformance import (
    build_report, make_receipt, finite_cases, rejected_cases, lexical_cases,
    oracle, sample_ada_cases,
)
from verify_spark_evidence_archive import SOURCE_SHA


class AdaRuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Entirely synthetic receipt, including fake compiler/binary hashes.
        # This demonstrates consistency checks, NOT genuine tool execution.
        report = build_report()
        cases = (sample_ada_cases(list(finite_cases()), 7)
                 + rejected_cases() + lexical_cases())
        rows = [[op, list(args), oracle(op, args)] for op, args in cases]
        vectors = hashlib.sha256(json.dumps(
            rows, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        binary = "a" * 64
        report["evidence"]["ada_cli_conformance"] = {
            "status": "ADA_CLI_TESTED_UNATTESTED", "cases": len(cases),
            "vectors_sha256": vectors, "binary_sha256": binary,
            "note": "CLI output matched oracle; binary provenance and SPARK compilation not independently attested",
        }
        report["unresolved"][3] = "Ada CLI execution matches selected inputs but provenance not attested"
        build_output = "SYNTHETIC UNIT TEST ONLY\n"
        cls.synthetic = {
            "protocol": checked.PROTOCOL,
            "status": "LOCAL_BUILD_AND_DIFFERENTIAL_PASSED_UNATTESTED",
            "historical_source_commit": checked.HISTORICAL_SHA,
            "source_sha256": {n: SOURCE_SHA[n] for n in checked.SOURCES},
            "tool_versions": {"gprbuild": "GPRBUILD synthetic fixture",
                              "gnatmake": "GNATMAKE synthetic fixture"},
            "build_command": checked.BUILD_COMMAND,
            "build_exit_code": 0,
            "build_output": build_output,
            "build_output_sha256": hashlib.sha256(build_output.encode()).hexdigest(),
            "binary_sha256": binary,
            "seed": 314159,
            "mode": "SEEDED_SAMPLE",
            "finite_cases_checked": 7,
            "rejected_fixture_checked": 16,
            "lexical_invalid_checked": 6,
            "ada_processes_checked": len(cases),
            "vectors_sha256": vectors,
            "python_bridge_receipt": make_receipt(report),
            "bridge_receipt_verification": "SELF_CONSISTENT_ONLY",
            "independent_execution_attestation": False,
            "limitations": checked.LIMITATIONS,
        }

    def test_synthetic_self_consistency_is_not_attestation(self):
        value = checked.verify(self.synthetic)
        self.assertEqual(value["integrity"], "PASS")
        self.assertEqual(value["execution_attestation"], "NOT_INDEPENDENTLY_ESTABLISHED")
        self.assertEqual(value["cases"], 29)

    def test_exhaustive_sample_receipt_uses_full_domain_mode(self):
        # Synthetic self-consistency fixture, not a claim of actual Ada execution.
        finite = list(finite_cases())
        selected = sample_ada_cases(finite, len(finite))
        rows = [[op, list(args), oracle(op, args)] for op, args in
                selected + rejected_cases() + lexical_cases()]
        expected_vectors = hashlib.sha256(json.dumps(
            rows, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")).hexdigest()
        bridge = build_report()
        bridge["evidence"]["ada_cli_conformance"] = {
            "status": "ADA_CLI_TESTED_UNATTESTED",
            "cases": len(rows),
            "vectors_sha256": expected_vectors,
            "binary_sha256": "a" * 64,
            "note": "CLI output matched oracle; binary provenance and SPARK compilation not independently attested",
        }
        bridge["unresolved"][3] = "Ada CLI execution matches selected inputs but provenance not attested"
        record = copy.deepcopy(self.synthetic)
        record.update({
            "mode": "FULL_FINITE_SET",
            "finite_cases_checked": len(finite),
            "ada_processes_checked": len(rows),
            "vectors_sha256": expected_vectors,
            "python_bridge_receipt": make_receipt(bridge),
        })
        verified = checked.verify(record)
        self.assertEqual(verified["integrity"], "PASS")
        self.assertEqual(verified["cases"], 8903)
        self.assertEqual(verified["execution_attestation"], "NOT_INDEPENDENTLY_ESTABLISHED")

        wrong_mode = copy.deepcopy(record)
        wrong_mode["mode"] = "SEEDED_SAMPLE"
        with self.assertRaisesRegex(checked.EvidenceError, "mode or count"):
            checked.verify(wrong_mode)

    def test_forged_execution_attestation_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["independent_execution_attestation"] = True
        with self.assertRaisesRegex(checked.EvidenceError, "provenance"):
            checked.verify(forged)

    def test_modified_source_digest_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["source_sha256"]["reference_kernel.adb"] = "0" * 64
        with self.assertRaisesRegex(checked.EvidenceError, "input digest"):
            checked.verify(forged)

    def test_wrong_historical_revision_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["historical_source_commit"] = "f" * 40
        with self.assertRaisesRegex(checked.EvidenceError, "provenance"):
            checked.verify(forged)

    def test_falsified_binary_sha_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["binary_sha256"] = "0" * 64
        with self.assertRaisesRegex(checked.EvidenceError, "bridge metadata"):
            checked.verify(forged)

    def test_falsified_vector_sha_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["vectors_sha256"] = "0" * 64
        with self.assertRaisesRegex(checked.EvidenceError, "bridge metadata"):
            checked.verify(forged)

    def test_resealed_fake_checked_count_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["ada_processes_checked"] = 30
        with self.assertRaisesRegex(checked.EvidenceError, "invocation count"):
            checked.verify(forged)

    def test_forged_full_sweep_status_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["mode"] = "FULL_FINITE_SET"
        with self.assertRaisesRegex(checked.EvidenceError, "mode or count"):
            checked.verify(forged)

    def test_boolean_build_success_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["build_exit_code"] = False
        with self.assertRaisesRegex(checked.EvidenceError, "build command or status"):
            checked.verify(forged)

    def test_changed_build_output_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["build_output"] = "another build output\n"
        with self.assertRaisesRegex(checked.EvidenceError, "build log fingerprint"):
            checked.verify(forged)

    def test_extra_claimed_ada_proof_field_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["ada_contracts_formally_proved"] = True
        with self.assertRaisesRegex(checked.EvidenceError, "schema"):
            checked.verify(forged)

    def test_bridge_receipt_mismatch_rejected(self):
        forged = copy.deepcopy(self.synthetic)
        forged["python_bridge_receipt"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(checked.EvidenceError, "bridge receipt invalid"):
            checked.verify(forged)

    def test_failed_execution_record_cannot_validate_as_green(self):
        forged = copy.deepcopy(self.synthetic)
        forged["status"] = "FAILED_OR_NOT_RUN"
        with self.assertRaisesRegex(checked.EvidenceError, "status or provenance"):
            checked.verify(forged)

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            for payload in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}'):
                with self.subTest(payload=payload):
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(checked.EvidenceError):
                        checked.load_json(path)


if __name__ == "__main__":
    unittest.main()
