// PROPERTY-LAB/1: deterministic, bounded property tests; no mutation of deployed code.
// Neither a generated test nor a self-hashed receipt is a mathematical proof.
import {xorshift32, evolve, buildAutomaton, fnv1a} from '../lab/core.js';

export const PROTOCOL = 'PROPERTY-LAB/1';
export const DEFAULT_CONFIG = Object.freeze({seed: 314159, trials: 128});
export const LIMITATIONS = Object.freeze([
  'The property sample is finite, not a proof of arbitrary JavaScript behaviour.',
  'The wraparound defect is deliberately injected inside this lab, not found in deployed evolve().',
  'The legacy mutable-fingerprint witness is a real public-API ownership counterexample.',
  'The guarded snapshot API is opt-in and does not make legacy buildAutomaton immutable.',
  'An exported SHA-256 receipt identifies payload bytes, not authentic browser execution.'
]);

export function validateConfig(config = DEFAULT_CONFIG) {
  if (!config || typeof config !== 'object' || Array.isArray(config) ||
      Object.keys(config).sort().join(',') !== 'seed,trials' ||
      !Number.isSafeInteger(config.seed) || config.seed < 1 || config.seed > 0xffffffff ||
      !Number.isSafeInteger(config.trials) || config.trials < 1 || config.trials > 512)
    throw new RangeError('seed must be uint32 nonzero; trials must be 1..512');
  return {seed: config.seed, trials: config.trials};
}

export function makeCases(config = DEFAULT_CONFIG) {
  const {seed, trials} = validateConfig(config);
  const next = xorshift32(seed);
  const cases = [];
  for (let i = 0; i < trials; i += 1) {
    const width = 1 + next() % 8;
    const rule = next() % 256;
    const mask = next() % (2 ** width);
    cases.push({width, rule, mask});
  }
  return cases;
}

export function bitsOf({width, mask}) {
  if (!Number.isInteger(width) || width < 1 || width > 8 ||
      !Number.isInteger(mask) || mask < 0 || mask >= 2 ** width)
    throw new RangeError('invalid finite row');
  return Array.from({length: width}, (_, i) => Math.floor(mask / (2 ** i)) % 2);
}

export function transitionOracle(row, rule) {
  if (!Array.isArray(row) || row.length < 1 || row.length > 8 ||
      row.some(v => v !== 0 && v !== 1) ||
      !Number.isInteger(rule) || rule < 0 || rule > 255)
    throw new RangeError('invalid transition oracle inputs');
  return row.map((center, i) => {
    const l = i === 0 ? 0 : row[i - 1];
    const r = i + 1 === row.length ? 0 : row[i + 1];
    return Math.floor(rule / 2 ** (4 * l + 2 * center + r)) % 2;
  });
}

// Explicitly faulty alternative, used only to teach a real boundary pitfall.
export function injectedWraparoundStep(row, rule) {
  if (!Array.isArray(row) || row.length < 1 || row.length > 8 ||
      row.some(v => v !== 0 && v !== 1) ||
      !Number.isInteger(rule) || rule < 0 || rule > 255)
    throw new RangeError('invalid mutant inputs');
  return row.map((center, i) => {
    const l = row[(i + row.length - 1) % row.length];
    const r = row[(i + 1) % row.length];
    return (rule >>> ((l << 2) | (center << 1) | r)) & 1;
  });
}

const equal = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);

export function mismatches(input, candidate = injectedWraparoundStep) {
  const bits = bitsOf(input);
  const expected = transitionOracle(bits, input.rule);
  const actual = candidate(bits, input.rule);
  if (!Array.isArray(actual) || !actual.every(v => v === 0 || v === 1) ||
      actual.length !== expected.length) throw new RangeError('candidate returned invalid row');
  return !equal(expected, actual);
}

// Canonical bounded width-first minimisation, not an unbounded universal minimum.
// Enumerate every candidate of shorter width and all rules/masks; ties use
// numeric rule then mask. The initial witness must actually fail.
export function minimizeBoundaryWitness(initial, candidate = injectedWraparoundStep) {
  if (!mismatches(initial, candidate)) throw new RangeError('input is not a counterexample');
  let checked = 0;
  for (let width = 1; width <= initial.width; width += 1) {
    for (let rule = 0; rule <= 255; rule += 1) {
      for (let mask = 0; mask < 2 ** width; mask += 1) {
        checked += 1;
        const witness = {width, rule, mask};
        if (mismatches(witness, candidate))
          return {original: {...initial}, minimized: witness,
                  candidates_checked: checked, ordering: 'width,rule,mask',
                  status: 'INJECTED_MUTANT_COUNTEREXAMPLE'};
      }
    }
  }
  throw new Error('witness disappeared during shrinking');
}

export function guardedSnapshot(model) {
  if (!model || !Number.isInteger(model.columns) || !Number.isInteger(model.rows) ||
      model.columns < 1 || model.columns > 512 || model.rows < 1 || model.rows > 512 ||
      !(model.cells instanceof Uint8Array) || model.cells.length !== model.columns * model.rows ||
      !Array.from(model.cells).every(v => v === 0 || v === 1) ||
      typeof model.fingerprint !== 'string' || model.fingerprint !== fnv1a(model.cells))
    throw new RangeError('invalid or stale automaton snapshot');
  const privateCells = new Uint8Array(model.cells);
  return Object.freeze({columns: model.columns, rows: model.rows,
    fingerprint: fnv1a(privateCells), get cells() { return new Uint8Array(privateCells); }});
}

export function ownershipWitness() {
  const source = buildAutomaton(30, 314159, 8, 8);
  const stored = source.fingerprint, original = source.cells[0];
  source.cells[0] = original ^ 1;
  const recomputed = fnv1a(source.cells);
  if (recomputed === stored) throw new Error('legacy ownership counterexample absent');
  const minimal = buildAutomaton(0, 1, 1, 1);
  const minimalStored = minimal.fingerprint;
  minimal.cells[0] ^= 1;
  if (fnv1a(minimal.cells) === minimalStored) throw new Error('minimal legacy witness does not fail');
  const pristine = buildAutomaton(0, 1, 1, 1);
  const guarded = guardedSnapshot(pristine);
  const copy = guarded.cells;
  copy[0] ^= 1;
  if (fnv1a(guarded.cells) !== guarded.fingerprint ||
      guarded.cells[0] !== pristine.cells[0]) throw new Error('defensive ownership guard failed');
  return {status: 'LEGACY_MUTABILITY_COUNTEREXAMPLE',
    original: {columns: 8, rows: 8, rule: 30, seed: 314159},
    minimized: {columns: 1, rows: 1, rule: 0, seed: 1},
    legacy_stored: stored, legacy_after_mutation: recomputed,
    guarded_status: 'DEFENSIVE_COPY_CONFIRMED'};
}

export function runPropertyLab(config = DEFAULT_CONFIG) {
  const checked = validateConfig(config);
  const cases = makeCases(checked);
  for (let i = 0; i < cases.length; i += 1) {
    const input = cases[i], bits = bitsOf(input), before = bits.join(',');
    const expected = transitionOracle(bits, input.rule);
    const actual = [...evolve(Uint8Array.from(bits), input.rule)];
    if (!equal(expected, actual) || before !== bits.join(','))
      throw new Error('deployed evolve mismatch at generated case ' + i);
  }
  // A pinned probe guarantees that the intentionally defective candidate is
  // observable even for a one-case run; randomized cases never fake discovery.
  const injectedProbe = {width: 8, rule: 110, mask: 255};
  if (!mismatches(injectedProbe)) throw new Error('injected boundary probe did not fail');
  const shrunk = minimizeBoundaryWitness(injectedProbe);
  const witness = ownershipWitness();
  return {
    protocol: PROTOCOL, schema_version: 1, seed: checked.seed, trials: checked.trials,
    generated_cases: cases, generated_status: 'FINITE_GENERATED_CASES_PASSED',
    mutant: {kind: 'DELIBERATELY_INJECTED_WRAPAROUND', ...shrunk},
    ownership: witness, limitations: [...LIMITATIONS],
    proof_status: 'NOT_A_FORMAL_PROOF'
  };
}
