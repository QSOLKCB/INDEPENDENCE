import {xorshift32, evolve, fnv1a, buildAutomaton, dependencyExposure} from './core.js';
import {validTreeSha, validReceiptSha} from '../ledger/ledger.js';
import {makePhases, fingerprint, median, bootstrapMedianCI, assessPairs, validateOutput} from '../tribunal/core.js';
import {createAdapter as directAdapter} from '../tribunal/direct.js';
import {createAdapter as keyedAdapter} from '../tribunal/keyed.js';
import {validateConfig} from '../tribunal/bench.js';

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
    ['zero-depth counts direct only', () => dependencyExposure(7, 3, 0) === 7],
    ['SHA-256 receipts accept exactly 64 hex characters', () =>
      validReceiptSha('a'.repeat(64)) && !validReceiptSha('a'.repeat(40)) &&
      !validReceiptSha('g'.repeat(64)) && !validReceiptSha(null)],
    ['Git tree IDs accept exactly 40 hex characters', () =>
      validTreeSha('b'.repeat(40)) && !validTreeSha('b'.repeat(64)) &&
      !validTreeSha('g'.repeat(40)) && !validTreeSha(undefined)],
    ['tribunal fixtures replay exactly', () => {
      const a = makePhases(12345, 24), b = makePhases(12345, 24);
      return fingerprint(a.initial) === fingerprint(b.initial) &&
        fingerprint(a.reorder) === fingerprint(b.reorder) && a.reorder.length === 16;
    }],
    ['tribunal statistics preserve paired semantics', () => {
      const summary = assessPairs(Array.from({length: 8}, (_, i) => ({direct: i + 1, keyed: i + 2})));
      return summary.direct_median_ms === 4.5 && summary.keyed_median_ms === 5.5 &&
        summary.paired_delta_median_ms === 1 && summary.paired_delta_bootstrap_95_ms.every(v => v === 1);
    }],
    ['tribunal bootstrap reproducibility', () =>
      JSON.stringify(bootstrapMedianCI([3,2,1,1,0,-1,2,3])) ===
      JSON.stringify(bootstrapMedianCI([3,2,1,1,0,-1,2,3]))],
    ['tribunal median rejects nonfinite values', () => {
      try { median([1, Infinity]); return false; } catch (e) { return e instanceof RangeError; }
    }],
    ['tribunal config rejects unsafe trial counts', () => {
      try { validateConfig({seed:1,count:100,warmups:2,trials:1000}); return false; }
      catch (e) { return e instanceof RangeError; }
    }],
    ['tribunal adapters match every DOM phase', () => {
      const phases = makePhases(55, 28);
      for (const adapter of [directAdapter, keyedAdapter]) {
        const root = document.createElement('ul'), instance = adapter(root);
        for (const phase of ['initial','update','reorder']) {
          instance.render(phases[phase]);
          if (!validateOutput(root, phases[phase])) return false;
        }
      }
      return true;
    }],
    ['tribunal keyed adapter preserves node identity', () => {
      const phases = makePhases(55, 28), root = document.createElement('ul');
      const adapter = keyedAdapter(root);
      adapter.render(phases.initial);
      const first = root.children[1];
      adapter.render(phases.update);
      return root.children[1] === first;
    }]
  ];
  return checks.map(([name, check]) => {
    try { return { name, passed: check() === true }; }
    catch (error) { return { name, passed: false, error: String(error) }; }
  });
}
