import {checkVectors, EXPECTED_SHA256} from './core.js';
import {evolve} from '../lab/core.js';

export function runFormalLabSelfTests() {
  const checks = [
    ['all 4096 real width-four vectors', () => {
      const x = checkVectors();
      return x.cases === 4096 && x.vectorsJSON.startsWith('[[0,0,0,0,0,"0000"]') &&
        x.vectorsJSON.endsWith('[255,1,1,1,1,"1111"]]');
    }],
    ['rule 90 fixed-zero sample', () =>
      String(evolve(Uint8Array.of(0, 0, 1, 0), 90)) === '0,1,0,1'],
    ['detect correct output with mutated original typed array', () => {
      try {
        checkVectors((source, rule) => {
          const result = evolve(source, rule);
          source.fill(1);
          return result;
        });
        return false;
      } catch (error) { return error.message.includes('input mutation'); }
    }],
    ['reject wrong output even if input unchanged', () => {
      try { checkVectors(source => new Uint8Array(source.length)); return false; }
      catch (error) { return error.message.includes('mismatch'); }
    }],
    ['canonical SHA-256 reference is pinned', () =>
      EXPECTED_SHA256 === 'f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635']
  ];
  return checks.map(([name, execute]) => {
    try { return {name, passed: execute() === true}; }
    catch (error) { return {name, passed: false, error: String(error)}; }
  });
}
