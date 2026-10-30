// Developer-only full reference/production JS differential; Node is optional.
import {evolve} from '../lab/core.js';
import {createHash} from 'node:crypto';

function oracle(rule, bits) {
  return bits.map((center, i) => {
    const left = i === 0 ? 0 : bits[i - 1];
    const right = i === 3 ? 0 : bits[i + 1];
    return Math.floor(rule / (2 ** (4 * left + 2 * center + right))) % 2;
  });
}

function run() {
  const vectors = [];
  for (let rule = 0; rule < 256; rule += 1) {
    for (let mask = 0; mask < 16; mask += 1) {
      const bits = Array.from({length: 4}, (_, i) => (mask >>> (3 - i)) & 1);
      const source = new Uint8Array(bits);
      const before = source.slice();
      const actual = evolve(source, rule);
      const expected = oracle(rule, bits);
      if (!(actual instanceof Uint8Array) ||
          actual.length !== 4 ||
          !expected.every((b, i) => actual[i] === b) ||
          !before.every((b, i) => source[i] === b))
        throw new Error('production JS mismatch at rule=' + rule + ' mask=' + mask);
      vectors.push([rule, ...bits, expected.join('')]);
    }
  }
  const vectors_sha256 = createHash('sha256').update(JSON.stringify(vectors), 'utf8').digest('hex');
  return {protocol: 'AUTOMATA4-JS-EVIDENCE/1', status: 'LOCAL_JS_FINITE_EXECUTED',
    cases: vectors.length, vectors_sha256,
    limitation: 'Developer Node runtime executed production evolve; no Lean/Ada proof or browser attestation.'};
}

try {
  console.log(JSON.stringify(run()));
} catch (error) {
  console.error('FAIL: ' + String(error));
  process.exitCode = 1;
}
