import {makeCases, runPropertyLab, minimizeBoundaryWitness, mismatches, guardedSnapshot,
        transitionOracle, injectedWraparoundStep, validateConfig} from './core.js';
import {buildAutomaton, fnv1a} from '../lab/core.js';

// Native browser assertions. No framework or test-time network activity.
export function runPropertySelfTests() {
  const assertions = [
    ['seeded generator is byte-reproducible', () =>
      JSON.stringify(makeCases({seed: 314159, trials: 64})) ===
      JSON.stringify(makeCases({seed: 314159, trials: 64}))],
    ['different seeds change generated samples', () =>
      JSON.stringify(makeCases({seed: 1, trials: 12})) !==
      JSON.stringify(makeCases({seed: 2, trials: 12}))],
    ['generator bound rejects unsafe seed and trial values', () => {
      for (const config of [{seed: 0, trials: 3}, {seed: 1, trials: 513},
                            {seed: 1.1, trials: 3}, {seed: 1, trials: true},
                            {seed: 1, trials: 3, extra: 'x'}]) {
        try { validateConfig(config); return false; } catch (error) {
          if (!(error instanceof RangeError)) return false;
        }
      }
      return true;
    }],
    ['candidate may return a Uint8Array like the real function', () =>
      !mismatches({width: 1, rule: 4, mask: 1}, (bits, rule) =>
        new Uint8Array(transitionOracle(bits, rule)))],
    ['known zero-boundary oracle result', () =>
      String(transitionOracle([0, 0, 1, 0, 0], 90)) === '0,1,0,1,0'],
    ['deliberate wraparound mutant has a real mismatch', () =>
      mismatches({width: 8, rule: 110, mask: 255})],
    ['canonical shrinker finds 1-bit rule-4 witness', () => {
      const report = minimizeBoundaryWitness({width: 8, rule: 110, mask: 255});
      const x = report.minimized;
      return x.width === 1 && x.rule === 4 && x.mask === 1 &&
        report.candidates_checked === 10 && mismatches(x);
    }],
    ['no mismatch cannot be shrunk', () => {
      try { minimizeBoundaryWitness({width: 1, rule: 0, mask: 0}); return false; }
      catch (error) { return error instanceof RangeError; }
    }],
    ['boundary mutant only differs from correct model', () =>
      String(transitionOracle([1], 4)) !== String(injectedWraparoundStep([1], 4))],
    ['guarded snapshot survives external typed-array mutation', () => {
      const model = buildAutomaton(30, 314159, 8, 8);
      const guarded = guardedSnapshot(model), fingerprint = guarded.fingerprint;
      guarded.cells[0] ^= 1;
      model.cells[0] ^= 1;
      return Object.isFrozen(guarded) && guarded.fingerprint === fingerprint &&
        fnv1a(guarded.cells) === fingerprint;
    }],
    ['guarded snapshot rejects stale fingerprint', () => {
      const model = buildAutomaton(30, 314159, 8, 8);
      model.cells[0] ^= 1;
      try { guardedSnapshot(model); return false; }
      catch (error) { return error instanceof RangeError; }
    }],
    ['property report preserves separate defect provenance', () => {
      const p = runPropertyLab({seed: 314159, trials: 5});
      return p.generated_cases.length === 5 &&
        p.mutant.kind === 'DELIBERATELY_INJECTED_WRAPAROUND' &&
        p.ownership.status === 'LEGACY_MUTABILITY_COUNTEREXAMPLE' &&
        p.proof_status === 'NOT_A_FORMAL_PROOF';
    }],
    ['same run yields identical report bytes', () =>
      JSON.stringify(runPropertyLab({seed: 45, trials: 8})) ===
      JSON.stringify(runPropertyLab({seed: 45, trials: 8}))],
  ];
  return assertions.map(([name, fn]) => {
    try { return {name, passed: fn() === true}; }
    catch (error) { return {name, passed: false, error: String(error)}; }
  });
}
