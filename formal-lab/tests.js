import {checkVectors} from './core.js';
import {evolve} from '../lab/core.js';

export function runFormalLabSelfTests() {
  const assertions = [
    ['real transition vectors and boundaries', () => {
      const r = checkVectors();
      return r.neighbourhoodCases === 2048 && r.boundaryCases === 512 &&
        r.vectorText.startsWith('0,0,0,0:0\n');
    }],
    ['rule 90 neighbourhood XOR', () =>
      Array.from(evolve(Uint8Array.of(1, 0, 0), 90)).join(',') === '0,1,0'],
    ['mutating correct-output candidate is rejected', () => {
      try {
        checkVectors((input, rule) => {
          const result = evolve(input, rule);
          input.fill(1);
          return result;
        });
        return false;
      } catch (error) { return error.message.includes('production transition failed'); }
    }],
    ['wrong candidate output is rejected', () => {
      try { checkVectors(input => new Uint8Array(input.length)); return false; }
      catch (error) { return error.message.includes('production transition failed'); }
    }]
  ];
  return assertions.map(([name, fn]) => {
    try { return {name, passed: fn() === true}; }
    catch (error) { return {name, passed: false, error: String(error)}; }
  });
}
