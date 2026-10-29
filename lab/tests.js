import {xorshift32, evolve, fnv1a, buildAutomaton, dependencyExposure} from './core.js';

// No testing framework: assertions intentionally use only native JavaScript.
export function runTests() {
  const checks = [
    ['xorshift32 known vector', () => xorshift32(1)() === 270369],
    ['Rule 90 known evolution', () => String(evolve(Uint8Array.from([0,0,1,0,0]), 90)) === '0,1,0,1,0'],
    ['Rule 90 fixed zero boundary', () => String(evolve(Uint8Array.from([1,0,0,0]), 90)) === '0,1,0,0'],
    ['FNV-1a known vector', () => fnv1a(new TextEncoder().encode('hello')) === '4f9f2cab'],
    ['identical input replays', () => {
      const a = buildAutomaton(30, 314159);
      const b = buildAutomaton(30, 314159);
      return a.fingerprint === b.fingerprint && a.cells.every((value, i) => value === b.cells[i]);
    }],
    ['different seeds change state', () => buildAutomaton(30, 314159).fingerprint !== buildAutomaton(30, 314160).fingerprint],
    ['rule validation rejects out-of-range', () => { try { buildAutomaton(256, 1); return false; } catch (e) { return e instanceof RangeError; } }],
    ['seed validation rejects zero', () => { try { buildAutomaton(30, 0); return false; } catch (e) { return e instanceof RangeError; } }],
    ['synthetic tree arithmetic', () => dependencyExposure(2, 3, 2) === 26],
    ['zero-depth counts direct only', () => dependencyExposure(7, 3, 0) === 7]
  ];
  return checks.map(([name, check]) => {
    try { return { name, passed: check() === true }; }
    catch (error) { return { name, passed: false, error: String(error) }; }
  });
}
