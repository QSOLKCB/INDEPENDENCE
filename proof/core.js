// PROOF-CONTRACTS/1: bounded tests of real first-party code against independent oracles.
// These observations are not Lean proofs, SPARK proofs, or execution attestation.
import {evolve,buildAutomaton,dependencyExposure,fnv1a} from "../lab/core.js";
import {validTreeSha,validReceiptSha} from "../ledger/ledger.js";

export const PROTOCOL="PROOF-CONTRACTS/1";
export const CONTRACT_IDS=Object.freeze(["AUTOMATA-TRANSITION","DEPENDENCY-SUM",
  "AUTOMATA-REPLAY","SHA-FORMAT","FINGERPRINT-IMMUTABILITY"]);
export const LIMITATIONS=Object.freeze([
  "Bounded exhaustive and finite tests are not formal proofs of all JavaScript inputs.",
  "Receipt SHA-256 checks payload bytes, not authorship or actual browser execution.",
  "No Lean or SPARK theorem has been discharged for INDEPENDENCE in v0.7.0."
]);

function oracleStep(bits,rule){
  return bits.map((center,i)=>{
    const left=i?bits[i-1]:0,right=i===bits.length-1?0:bits[i+1];
    return Math.floor(rule/(2**(4*left+2*center+right)))%2;
  });
}
function oracleSum(direct,fanout,depth){
  let total=0n,term=BigInt(direct);
  for(let n=0;n<=depth;n++){total+=term;term*=BigInt(fanout);}
  return total;
}
function oracleFnv(bytes){
  let hash=2166136261n;
  for(const byte of bytes)hash=((hash^BigInt(byte))*16777619n)%4294967296n;
  return hash.toString(16).padStart(8,"0");
}
const eq=(a,b)=>a.length===b.length&&a.every((x,i)=>x===b[i]);

export function checkAutomata(){
  let cases=0,cells=0;
  for(let width=1;width<=8;width++)
    for(let mask=0;mask<2**width;mask++){
      const bits=Array.from({length:width},(_,i)=>Math.floor(mask/2**i)%2);
      const before=Uint8Array.from(bits);
      for(let rule=0;rule<256;rule++){
        if(!eq(evolve(before,rule),oracleStep(bits,rule))||!eq(before,bits))
          throw new Error("automaton mismatch width="+width+" mask="+mask+" rule="+rule);
        cases++;cells+=width;
      }
    }
  return {id:"AUTOMATA-TRANSITION",status:"BOUNDED_EXHAUSTIVE",cases,assertions:cells};
}
export function checkDependencySum(){
  let cases=0;
  for(let direct=0;direct<=10;direct++)
    for(let fanout=0;fanout<=5;fanout++)
      for(let depth=0;depth<=6;depth++){
        const result=dependencyExposure(direct,fanout,depth);
        if(!Number.isSafeInteger(result)||BigInt(result)!==oracleSum(direct,fanout,depth))
          throw new Error("dependency sum mismatch");
        cases++;
      }
  const edge=dependencyExposure(100,10,8);
  if(!Number.isSafeInteger(edge)||BigInt(edge)!==oracleSum(100,10,8))
    throw new Error("boundary sum mismatch");
  return {id:"DEPENDENCY-SUM",status:"FINITE_CASES",cases:cases+1,assertions:cases+1};
}
export function checkReplay(){
  let cases=0;
  for(const seed of [1,314159,4294967295])
    for(const rule of [30,90,110,184])
      for(const [width,height] of [[1,1],[8,7],[32,12]]){
        const a=buildAutomaton(rule,seed,width,height);
        const b=buildAutomaton(rule,seed,width,height);
        if(a.columns!==width||a.rows!==height||!eq(a.cells,b.cells)||
           a.fingerprint!==b.fingerprint||a.fingerprint!==oracleFnv(a.cells)||
           a.fingerprint!==fnv1a(a.cells))
          throw new Error("seeded replay or FNV oracle mismatch");
        cases++;
      }
  return {id:"AUTOMATA-REPLAY",status:"FINITE_CASES",cases,assertions:cases};
}
export function checkShaFormat(){
  const samples=[
    ["a".repeat(40),true,false],["A".repeat(40),false,false],
    ["g".repeat(40),false,false],["a".repeat(39),false,false],
    ["a".repeat(41),false,false],["b".repeat(64),false,true],
    ["B".repeat(64),false,false],["g".repeat(64),false,false],
    ["b".repeat(63),false,false],["b".repeat(65),false,false],
    [null,false,false],[0,false,false]
  ];
  for(const [value,git,receipt] of samples)
    if(validTreeSha(value)!==git||validReceiptSha(value)!==receipt)
      throw new Error("SHA identifier boundary mismatch");
  return {id:"SHA-FORMAT",status:"FINITE_CASES",cases:samples.length,assertions:samples.length};
}
export function checkFingerprintImmutability(){
  const result=buildAutomaton(30,314159,8,8);
  const original=result.cells[0],oldHash=result.fingerprint;
  result.cells[0]=original^1;
  const newHash=fnv1a(result.cells);
  if(result.cells[0]!==original^1||newHash===oldHash)
    throw new Error("counterexample changed; revisit immutability contract");
  return {id:"FINGERPRINT-IMMUTABILITY",status:"COUNTEREXAMPLE",cases:1,assertions:1,
    stored_fingerprint:oldHash,recomputed_fingerprint:newHash,
    implication:"Object.freeze does not make the returned Uint8Array immutable."};
}
export function runProofChecks(){
  const checks=[checkAutomata,checkDependencySum,checkReplay,checkShaFormat,
    checkFingerprintImmutability].map(check=>check());
  if(checks.some((row,i)=>row.id!==CONTRACT_IDS[i]))
    throw new Error("proof obligation ordering mismatch");
  return {protocol:PROTOCOL,schema_version:1,
    scope:"bounded first-party behaviour; no formal proofs",
    checks,formal_proofs:{lean:"NOT_RUN",spark:"NOT_RUN"},
    limitations:[...LIMITATIONS]};
}
