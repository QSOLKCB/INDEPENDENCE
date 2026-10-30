// AUTOMATA4-BROWSER/1: user-triggered finite check of the real first-party evolve().
// No proof claim, package, remote data, dynamic evaluation or telemetry.
import {evolve} from '../lab/core.js';

export const PROTOCOL = 'AUTOMATA4-BROWSER/1';
export const RECEIPT = 'AUTOMATA4-BROWSER-RECEIPT/1';
export const EXPECTED_SHA256 = 'f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635';

function reference(rule, bits) {
  return bits.map((center, i) => {
    const left = i === 0 ? 0 : bits[i - 1];
    const right = i === 3 ? 0 : bits[i + 1];
    return Math.floor(rule / (2 ** (4 * left + 2 * center + right))) % 2;
  });
}

export function checkVectors(transition = evolve) {
  const vectors = [];
  for (let rule = 0; rule < 256; rule += 1) {
    for (let mask = 0; mask < 16; mask += 1) {
      const bits = Array.from({length: 4}, (_, i) => (mask >>> (3 - i)) & 1);
      const source = Uint8Array.from(bits);
      const before = source.slice();
      const expected = reference(rule, bits);
      const actual = transition(source, rule);
      if (!(actual instanceof Uint8Array) || actual.length !== 4 ||
          !expected.every((bit, i) => actual[i] === bit) ||
          !before.every((bit, i) => source[i] === bit))
        throw new Error('real evolve mismatch or input mutation at rule=' + rule + ', mask=' + mask);
      vectors.push([rule, ...bits, expected.join('')]);
    }
  }
  if (vectors.length !== 4096) throw new Error('incomplete vector corpus');
  return {cases: vectors.length, vectorsJSON: JSON.stringify(vectors)};
}

async function digest(input) {
  if (!globalThis.crypto?.subtle) throw new Error('SHA-256 WebCrypto needs HTTPS or localhost');
  const hashed = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(input));
  return Array.from(new Uint8Array(hashed), b => b.toString(16).padStart(2, '0')).join('');
}

export async function makeReceipt(results) {
  if (!results || results.cases !== 4096 || typeof results.vectorsJSON !== 'string')
    throw new Error('missing completed vector report');
  const observed = await digest(results.vectorsJSON);
  if (observed !== EXPECTED_SHA256)
    throw new Error('browser corpus differs from canonical AUTOMATA4/1');
  const payload_text = JSON.stringify({
    protocol: PROTOCOL,
    status: 'FINITE_JS_CONFORMANCE',
    cases: 4096,
    vectors_sha256: observed,
    proof_status: 'NOT_A_FORMAL_PROOF'
  });
  return {format: RECEIPT, sha256: await digest(payload_text), payload_text};
}
