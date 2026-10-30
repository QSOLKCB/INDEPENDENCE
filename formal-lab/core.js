// AUTOMATON-BROWSER/1: compare actual first-party evolve() with independent arithmetic.
import {evolve} from '../lab/core.js';

export const PROTOCOL = 'AUTOMATON-BROWSER/1';
export const RECEIPT = 'AUTOMATON-BROWSER-RECEIPT/1';
const bit = (rule, left, center, right) =>
  Math.floor(rule / (2 ** (4 * left + 2 * center + right))) % 2;

export function checkVectors(transition = evolve) {
  const lines = [];
  let neighbourhoodCases = 0;
  for (let rule = 0; rule <= 255; rule += 1) {
    for (let left = 0; left <= 1; left += 1)
      for (let center = 0; center <= 1; center += 1)
        for (let right = 0; right <= 1; right += 1) {
          const source = Uint8Array.of(left, center, right);
          const actual = transition(source, rule);
          const expected = [bit(rule, 0, left, center), bit(rule, left, center, right),
                            bit(rule, center, right, 0)];
          if (!(actual instanceof Uint8Array) || actual.length !== 3 ||
              expected.some((v, i) => actual[i] !== v) ||
              source[0] !== left || source[1] !== center || source[2] !== right)
            throw new Error('production transition failed at rule=' + rule +
              ' neighbourhood=' + left + center + right);
          lines.push(rule + ',' + left + ',' + center + ',' + right + ':' + expected[1] + '\n');
          neighbourhoodCases += 1;
        }
  }
  let boundaryCases = 0;
  for (let rule = 0; rule <= 255; rule += 1)
    for (let center = 0; center <= 1; center += 1) {
      const source = Uint8Array.of(center);
      const actual = transition(source, rule);
      if (!(actual instanceof Uint8Array) || actual.length !== 1 ||
          actual[0] !== bit(rule, 0, center, 0) || source[0] !== center)
        throw new Error('fixed-zero boundary failed at rule=' + rule + ' center=' + center);
      boundaryCases += 1;
    }
  return {neighbourhoodCases, boundaryCases, vectorText: lines.join('')};
}

async function digest(data) {
  if (!globalThis.crypto?.subtle) throw new Error('WebCrypto needs HTTPS or localhost');
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(data));
  return Array.from(new Uint8Array(bytes), v => v.toString(16).padStart(2, '0')).join('');
}

export async function makeReceipt(checks) {
  if (!checks || checks.neighbourhoodCases !== 2048 || checks.boundaryCases !== 512 ||
      typeof checks.vectorText !== 'string' || checks.vectorText.split('\n').length !== 2049)
    throw new Error('missing or incomplete finite vector checks');
  const report = {protocol: PROTOCOL, status: 'FINITE_JS_CONFORMANCE',
    neighbourhood_cases: 2048, boundary_cases: 512,
    vector_sha256: await digest(checks.vectorText), proof_status: 'NOT_A_FORMAL_PROOF'};
  const payload_text = JSON.stringify(report);
  return {format: RECEIPT, sha256: await digest(payload_text), payload_text};
}
