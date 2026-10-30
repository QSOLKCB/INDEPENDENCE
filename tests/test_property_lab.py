"""Property Lab receipts: strict stdlib checker and reproduction tests."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import verify_property_receipt as prop  # noqa: E402


def seal(report):
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    return {'format': prop.FORMAT, 'algorithm': 'SHA-256/UTF-8',
            'payload_text': payload, 'sha256': hashlib.sha256(payload.encode()).hexdigest()}


class PropertyLabTests(unittest.TestCase):
    def setUp(self):
        self.report = prop.expected_report(314159, 128)

    def test_seed_one_matches_independent_known_vector(self):
        self.assertEqual(prop.cases(1, 1), [{'width': 2, 'rule': 1, 'mask': 1}])

    def test_default_seed_known_vectors(self):
        self.assertEqual(prop.cases(314159, 5), [
            {'width': 8, 'rule': 94, 'mask': 125},
            {'width': 7, 'rule': 254, 'mask': 94},
            {'width': 2, 'rule': 228, 'mask': 1},
            {'width': 1, 'rule': 169, 'mask': 1},
            {'width': 7, 'rule': 49, 'mask': 34},
        ])

    def test_default_report_is_stable_and_bounded(self):
        self.assertEqual(self.report, prop.expected_report(314159, 128))
        self.assertEqual(len(self.report['generated_cases']), 128)
        self.assertEqual(self.report['mutant']['minimized'], {'width': 1, 'rule': 4, 'mask': 1})

    def test_ownership_counterexample_sha_diverges(self):
        witness = self.report['ownership']
        self.assertNotEqual(witness['legacy_stored'], witness['legacy_after_mutation'])
        self.assertEqual(witness['minimized'], {'columns': 1, 'rows': 1, 'rule': 0, 'seed': 1})

    def test_accepts_canonical_receipt_including_one_trial(self):
        for seed, trials in ((1, 1), (314159, 128), (4294967295, 512)):
            with self.subTest(seed=seed, trials=trials):
                result = prop.verify(seal(prop.expected_report(seed, trials)))
                self.assertTrue(result['valid'])
                self.assertEqual(result['generated_cases'], trials)
                self.assertEqual(result['execution_attestation'], 'NOT_INDEPENDENTLY_ESTABLISHED')

    def test_rejects_bad_seed_or_trials(self):
        for seed, n in ((0, 1), (-1, 1), (4294967296, 1), (1, 0), (1, 513), (True, 1), (1, False)):
            with self.subTest(seed=seed, trials=n), self.assertRaises(prop.ReceiptError):
                prop.expected_report(seed, n)

    def test_report_cannot_forge_mathematical_proof(self):
        obj = copy.deepcopy(self.report)
        obj['proof_status'] = 'THEOREM_PROVED'
        with self.assertRaisesRegex(prop.ReceiptError, 'proof status mismatch'):
            prop.verify(seal(obj))

    def test_generated_case_change_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.report)
        obj['generated_cases'][0]['mask'] ^= 1
        with self.assertRaisesRegex(prop.ReceiptError, 'generated fixtures'):
            prop.verify(seal(obj))

    def test_mutant_provenance_change_rejected(self):
        obj = copy.deepcopy(self.report)
        obj['mutant']['kind'] = 'FOUND_IN_PRODUCTION'
        with self.assertRaises(prop.ReceiptError):
            prop.verify(seal(obj))

    def test_fake_shrink_witness_rejected(self):
        obj = copy.deepcopy(self.report)
        obj['mutant']['minimized'] = {'width': 1, 'rule': 0, 'mask': 0}
        with self.assertRaises(prop.ReceiptError):
            prop.verify(seal(obj))

    def test_legacy_immutability_lie_rejected(self):
        obj = copy.deepcopy(self.report)
        obj['ownership']['status'] = 'LEGACY_ALREADY_IMMUTABLE'
        with self.assertRaises(prop.ReceiptError):
            prop.verify(seal(obj))

    def test_tampered_sha_rejected(self):
        receipt = seal(self.report)
        receipt['sha256'] = '0'*64
        with self.assertRaisesRegex(prop.ReceiptError, 'SHA-256 mismatch'):
            prop.verify(receipt)

    def test_extra_fields_and_boolean_schema_rejected(self):
        for key, value in [('authenticated_execution', True), ('schema_version', True)]:
            with self.subTest(key=key):
                obj = copy.deepcopy(self.report)
                obj[key] = value
                with self.assertRaises(prop.ReceiptError):
                    prop.verify(seal(obj))

    def test_bad_json_lexical_forms_rejected(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            with self.subTest(raw=raw), self.assertRaises(prop.ReceiptError):
                prop.read_json(raw)

    def test_generated_transition_checks_exact_typed_array_for_mutation(self):
        core = (ROOT / 'property/core.js').read_text(encoding='utf-8')
        browser_tests = (ROOT / 'property/tests.js').read_text(encoding='utf-8')
        self.assertIn('export function checkGeneratedTransition(input, transition = evolve)', core)
        self.assertIn('const source = Uint8Array.from(bits);', core)
        self.assertIn('const before = source.slice();', core)
        self.assertIn('const actual = transition(source, input.rule);', core)
        self.assertIn('if (!equal(source, before))', core)
        self.assertIn('checkGeneratedTransition(cases[i]);', core)
        self.assertIn('row.fill(255)', browser_tests)
        self.assertIn('correct output with mutated typed input is rejected', browser_tests)

    def test_core_and_ui_keep_first_party_invariants(self):
        core = (ROOT / 'property/core.js').read_text(encoding='utf-8')
        ui = (ROOT / 'property/ui.js').read_text(encoding='utf-8')
        page = (ROOT / 'index.html').read_text(encoding='utf-8')
        app = (ROOT / 'app.js').read_text(encoding='utf-8')
        deploy = (ROOT / '.github/workflows/deploy-pages.yml').read_text(encoding='utf-8')
        audit = (ROOT / 'scripts/audit.py').read_text(encoding='utf-8')
        for forbidden in ('Math.random(', 'fetch(', 'eval(', 'innerHTML', 'new Function('):
            self.assertNotIn(forbidden, core + ui)
        self.assertIn('textContent', ui)
        self.assertIn('id="property-lab"', page)
        self.assertIn('mountPropertyLab();', app)
        self.assertIn('cp property/core.js property/tests.js property/ui.js property/property.css "$site/property/"', deploy)
        for filename in ('property/core.js','property/tests.js','property/ui.js','property/property.css'):
            self.assertIn('"'+filename+'"', audit)


if __name__ == '__main__':
    unittest.main()
