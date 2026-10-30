"""AUTOMATA4/1 new proof candidates are NOT historical proof successes."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_automata_formal as lab  # noqa: E402


class AutomataFormalTests(unittest.TestCase):
    def test_reference_corpus_exactly_4096_and_locked(self):
        rows = list(lab.vectors())
        self.assertEqual(len(rows), 4096)
        self.assertEqual(lab.vectors_digest(rows), lab.EXPECTED_VECTORS_SHA256)
        self.assertEqual(rows[0], [0, 0, 0, 0, 0, "0000"])
        self.assertEqual(rows[-1], [255, 1, 1, 1, 1, "1111"])

    def test_distinct_known_boundary_vectors(self):
        self.assertEqual(lab.reference_step(90, (0, 0, 1, 0)), (0, 1, 0, 1))
        self.assertEqual(lab.reference_step(90, (1, 0, 0, 0)), (0, 1, 0, 0))
        self.assertEqual(lab.reference_step(0, (1, 0, 1, 1)), (0, 0, 0, 0))
        self.assertEqual(lab.reference_step(255, (0, 0, 0, 0)), (1, 1, 1, 1))

    def test_invalid_reference_inputs_rejected(self):
        for rule, bits in ((256, (0, 0, 0, 0)), (-1, (0, 0, 0, 0)),
                           (False, (0, 0, 0, 0)), (0, (0, 2, 0, 0)),
                           (0, (0, 0, 0)), (0, [0, 0, 0, 0])):
            with self.subTest(rule=rule, bits=bits), self.assertRaises(lab.FormalLabError):
                lab.reference_step(rule, bits)

    def test_sources_are_inspected_not_proved(self):
        result = lab.inspect()
        self.assertEqual(result["reference_status"], "FINITE_ENUMERATION_CHECKED")
        self.assertEqual(result["finite_cases"], 4096)
        self.assertEqual(len(result["theorem_inventory"]), 6)
        self.assertEqual(result["lean"]["status"], "NOT_RUN")
        self.assertEqual(result["spark"]["status"], "NOT_RUN")
        self.assertEqual(result["ada"]["status"], "NOT_RUN")
        self.assertEqual(result["javascript"]["status"], "NOT_RUN")
        self.assertFalse(result["independent_execution_attestation"])

    @staticmethod
    def fixture():
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        for path in (lab.SPEC, lab.LEAN, Path("lean-toolchain")):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
        for name in ("lab/core.js", "scripts/check_automata_js.mjs"):
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        for name in lab.ADA_FILES:
            path = lab.SPARK / name
            dest = root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, dest)
        return directory, root

    def test_js_source_hashes_bind_production_and_comparator(self):
        report = lab.inspect()
        self.assertEqual(set(report["javascript_files_sha256"]),
                         {"lab/core.js", "scripts/check_automata_js.mjs"})
        tmp, root = self.fixture()
        with tmp:
            path = root / "lab/core.js"
            path.write_text(path.read_text() + "\n// drift\n")
            self.assertNotEqual(report["javascript_files_sha256"],
                                lab.inspect(root)["javascript_files_sha256"])

    def test_node_command_is_portable_mjs_invocation(self):
        good = subprocess.CompletedProcess([], 0, json.dumps({
            "protocol": "AUTOMATA4-JS-EVIDENCE/1",
            "status": "LOCAL_JS_FINITE_EXECUTED",
            "cases": 4096, "vectors_sha256": lab.EXPECTED_VECTORS_SHA256,
            "limitation": "Developer Node runtime executed production evolve; no Lean/Ada proof or browser attestation.",
        }), "")
        with patch.object(lab.shutil, "which", return_value="/usr/bin/node"), \
             patch.object(lab, "invoke", return_value=good) as invoked:
            self.assertEqual(lab.check_js(ROOT, lab.EXPECTED_VECTORS_SHA256)["status"],
                             "LOCAL_JS_FINITE_EXECUTED")
        self.assertEqual(invoked.call_args.args[0], ["node", "scripts/check_automata_js.mjs"])

    def test_spec_change_fails_closed(self):
        tmp, root = self.fixture()
        with tmp:
            path = root / lab.SPEC
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaisesRegex(lab.FormalLabError, "unreviewed"):
                lab.inspect(root)

    def test_pinned_lean_version_required(self):
        tmp, root = self.fixture()
        with tmp:
            (root / "lean-toolchain").write_text("leanprover/lean4:stable\n")
            with self.assertRaisesRegex(lab.FormalLabError, "pin changed"):
                lab.inspect(root)

    def test_lean_axiom_audit_missing_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            p = root / lab.LEAN
            p.write_text(p.read_text().replace(
                "#print axioms IndependenceAutomata.rule90_known_row", ""))
            with self.assertRaisesRegex(lab.FormalLabError, "axiom audit"):
                lab.inspect(root)

    def test_lean_escapes_rejected(self):
        for bad in ("\naxiom fabricated : True\n", "\nset_option kernelChecking false\n",
                    "\ntheorem wrong : True := by sorry\n"):
            with self.subTest(bad=bad):
                tmp, root = self.fixture()
                with tmp:
                    p = root / lab.LEAN
                    p.write_text(p.read_text() + bad)
                    with self.assertRaises(lab.FormalLabError):
                        lab.inspect(root)

    def test_spark_assume_rejected(self):
        tmp, root = self.fixture()
        with tmp:
            p = root / lab.SPARK / "automata_reference.adb"
            p.write_text(p.read_text() + "\npragma Assume (True);")
            with self.assertRaisesRegex(lab.FormalLabError, "assumption"):
                lab.inspect(root)

    def test_missing_all_optional_tools_cannot_be_proved(self):
        with patch.object(lab.shutil, "which", return_value=None):
            report = lab.check(run_lean=True, run_spark=True, run_ada=True, run_js=True)
        self.assertEqual([report[k]["status"] for k in ("lean", "spark", "ada", "javascript")],
                         ["NOT_RUN"] * 4)

    def test_missing_lean_cannot_imply_kernel_checked(self):
        with patch.object(lab.shutil, "which", return_value=None), \
             patch.object(lab, "invoke") as cmd:
            self.assertEqual(lab.check_lean(ROOT)["status"], "NOT_RUN")
            cmd.assert_not_called()

    def test_lean_output_without_theorem_axiom_audits_fails(self):
        version = subprocess.CompletedProcess([], 0, "Lean (version 4.35.0, x86_64)\n", "")
        proof = subprocess.CompletedProcess([], 0, "Lean emitted no theorem output\n", "")
        with patch.object(lab.shutil, "which", return_value="/bin/lean"), \
             patch.object(lab, "invoke", side_effect=[version, proof]):
            x = lab.check_lean(ROOT)
        self.assertEqual(x["status"], "FAILED_OR_UNRESOLVED")

    def test_gnatprove_zero_check_or_unproved_claim_rejected(self):
        version = subprocess.CompletedProcess([], 0, "FSF 16.1.0\n", "")
        for output in ("Success: all checks proved (0 checks).\n",
                       "Success: all checks proved (5 checks).\n1 unproved obligation\n",
                       "No checks generated.\n"):
            with self.subTest(output=output), \
                 patch.object(lab.shutil, "which", return_value="/bin/gnatprove"), \
                 patch.object(lab, "invoke", side_effect=[
                     version, subprocess.CompletedProcess([], 0, output, "")]):
                self.assertEqual(lab.check_spark(ROOT)["status"], "FAILED_OR_UNPROVED")

    def test_js_report_must_match_independent_python_vectors(self):
        incorrect = {"protocol": "AUTOMATA4-JS-EVIDENCE/1",
                     "status": "LOCAL_JS_FINITE_EXECUTED", "cases": 4096,
                     "vectors_sha256": "0" * 64, "limitation": "fixture"}
        with patch.object(lab.shutil, "which", return_value="/bin/node"), \
             patch.object(lab, "invoke", return_value=subprocess.CompletedProcess(
                 [], 0, json.dumps(incorrect), "")):
            self.assertEqual(lab.check_js(ROOT, lab.EXPECTED_VECTORS_SHA256)["status"],
                             "FAILED_OR_MISMATCH")

    def test_cli_negative_lexical_cases_are_present(self):
        self.assertGreaterEqual(len(lab.NEGATIVES), 10)
        code = (ROOT / lab.SPARK / "automata_cli.adb").read_text()
        self.assertIn("C not in '0' .. '9'", code)
        self.assertIn("when Constraint_Error => IO.Put_Line", code)
        self.assertTrue(any("2#90#" in x for args in lab.NEGATIVES for x in args if isinstance(x, str)))

    def test_javascript_runner_uses_real_implementation(self):
        js = (ROOT / "scripts/check_automata_js.mjs").read_text()
        self.assertIn("import {evolve} from '../lab/core.js';", js)
        self.assertIn("evolve(source, rule)", js)
        self.assertIn("before.every((b, i) => source[i] === b)", js)

    def test_no_runtime_package_or_page_deployment_change(self):
        for path in ("formal/lean/AutomataReference.lean",
                     "formal/spark/automata_reference.ads",
                     "formal/spark/automata_reference.adb"):
            self.assertTrue((ROOT / path).is_file())
        deploy = (ROOT / ".github/workflows/deploy-pages.yml").read_text()
        self.assertIn('python3 -m unittest discover -s tests -v', deploy)
        self.assertNotIn("gprbuild", deploy)
        self.assertNotIn("lean --trust=0", deploy)


if __name__ == "__main__":
    unittest.main()
