import {xorshift32, evolve, fnv1a, buildAutomaton, dependencyExposure} from './core.js';
import {validTreeSha, validReceiptSha} from '../ledger/ledger.js';
import {makePhases, fingerprint, median, bootstrapMedianCI, assessPairs, validateOutput} from '../tribunal/core.js';
import {createAdapter as directAdapter} from '../tribunal/direct.js';
import {createAdapter as keyedAdapter} from '../tribunal/keyed.js';
import {validateConfig} from '../tribunal/bench.js';
import {EXHIBITS,runExhibit,runAll,assembleReport,encodeHtml,finiteJSON} from '../museum/core.js';
import {TARGETS,runMutationLab,validateConfig as validateMutationConfig} from '../breeding/core.js';
import {STAGES, CONTROLS, CASE_STUDIES, validateMission, makeHandoff, gateStatus} from '../workflow/core.js';
import {CONTRACT_IDS, runProofChecks, checkFingerprintImmutability} from '../proof/core.js';
import {runPropertySelfTests} from '../property/tests.js';
import {runFormalLabSelfTests} from '../formal-lab/tests.js';

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
    }],
    ['museum all five specimens pass deterministic checks', () =>
      EXHIBITS.length === 5 && runAll().every(r => r.passed && r.assertions.total === r.assertions.passed)],
    ['museum stable repeated observations', () =>
      JSON.stringify(runAll()) === JSON.stringify(runAll())],
    ['museum refuses unknown specimen', () => {
      try { runExhibit('unknown'); return false; } catch(e) { return e instanceof RangeError; }
    }],
    ['museum escape and nonfinite guards', () =>
      encodeHtml('<>&"\x27') === '&lt;&gt;&amp;&quot;&#39;' &&
      !finiteJSON({deep:[1,{n:Infinity}]}) && finiteJSON({deep:[1,{n:3}]})],
    ['museum report rejects failed results', () => {
      const results=runAll();
      results[0].passed=false;
      try { assembleReport(results); return false; } catch(e) { return true; }
    }],
    ['museum report preserves ordered provenance', () => {
      const result=assembleReport(runAll());
      return result.protocol === 'GREMLIN-MUSEUM/1' &&
        result.provenance.length === 5 && result.provenance.every((x,i)=>x.id===EXHIBITS[i].id);
    }],
    ['breeding smoke suite leaves known survivors', () => {
      const r=runMutationLab({seed:314159,suite:'smoke'});
      return r.mutants===15 && r.summary.killed===2 && r.summary.survived===13;
    }],
    ['breeding full fixture suite detects all curated mutants', () => {
      const r=runMutationLab({seed:314159,suite:'full'});
      return r.baseline_assertions===26 && r.summary.killed===15 && r.summary.survived===0;
    }],
    ['breeding reproducible run order', () => JSON.stringify(runMutationLab({seed:99,suite:'smoke'}))===
      JSON.stringify(runMutationLab({seed:99,suite:'smoke'}))],
    ['breeding seed changes order without changing scores', () => {
      const a=runMutationLab({seed:1,suite:'full'}),b=runMutationLab({seed:314159,suite:'full'});
      return a.results[0].id!==b.results[0].id && a.summary.killed===b.summary.killed;
    }],
    ['breeding has witnesses for all mutants', () => runMutationLab({seed:1,suite:'smoke'}).results.every(r=>r.witness_tests.length>0)],
    ['breeding invalid suite rejected', () => {
      try { validateMutationConfig({seed:1,suite:'oops'});return false; }catch(e){return e instanceof RangeError;}
    }],
    ['breeding invalid seed rejected', () => {
      try { validateMutationConfig({seed:0,suite:'full'});return false; }catch(e){return e instanceof RangeError;}
    }],
    ['breeding catalogue contains five targets and fifteen mutants', () =>
      TARGETS.length===5 && TARGETS.reduce((n,t)=>n+t.mutants.length,0)===15],
    ['workflow eight ordered human/AI stages', () =>
      STAGES.length===8 && STAGES[0].id==='intent' && STAGES.at(-1).id==='ship' &&
      STAGES.every(s=>s.instruction&&s.drift&&s.evidence&&s.owner)],
    ['workflow five merged PR records', () =>
      CASE_STUDIES.length===5 && CASE_STUDIES.every((c,i)=>
        c.pr===i+1 && c.source==='https://github.com/QSOLKCB/INDEPENDENCE/pull/'+(i+1))],
    ['workflow drift controls are unique', () => CONTROLS.length===8 &&
      new Set(CONTROLS.map(c=>c.id)).size===CONTROLS.length],
    ['workflow requires explicit goal', () => {
      try{makeHandoff({goal:'',scope:'x',excluded:'x',invariants:'x',acceptance:'x'});return false;}
      catch(e){return e instanceof RangeError;}
    }],
    ['workflow handoff preserves exact supplied boundaries', () => {
      const s=makeHandoff({goal:'Deliver A',scope:'Only B',excluded:'Never C',invariants:'Keep D',acceptance:'Check E'});
      return s.includes('Deliver A') && s.includes('Only B') && s.includes('Never C') &&
        s.includes('Keep D') && s.includes('Check E') && s.includes('exact PR HEAD');
    }],
    ['workflow handoff never fabricates verification', () => {
      const s=makeHandoff({goal:'A',scope:'',excluded:'',invariants:'',acceptance:''});
      return s.includes('NOT a completed review') && s.includes('unavailable tooling') &&
        s.includes('HUMAN MUST DEFINE');
    }],
    ['workflow rejects oversized mission content', () => {
      try{validateMission({goal:'a'.repeat(1201),scope:'',excluded:'',invariants:'',acceptance:''});return false;}
      catch(e){return e instanceof RangeError;}
    }],
    ['workflow guards need exact checked booleans', () => {
      const all=Object.fromEntries(CONTROLS.map(c=>[c.id,true]));
      const yes=gateStatus(all);
      all.human='true';
      const no=gateStatus(all);
      return yes.acknowledged===8 && yes.allAcknowledged && no.acknowledged===7 &&
        !no.allAcknowledged && no.selfReportedOnly;
    }],
    ['workflow accepts inert user text without interpretation', () => {
      const s=makeHandoff({goal:'<script>just text</script>',scope:'',excluded:'',invariants:'',acceptance:''});
      return s.includes('<script>just text</script>') && s.includes('Do not merge');
    }],
    ['proof contract bounded checks match fixed observations', () => {
      const r=runProofChecks();
      return r.checks.length===5 && r.checks[0].cases===130560 &&
        r.checks[0].assertions===918016 && r.checks[1].cases===463 &&
        r.checks[2].cases===36 && r.checks[3].cases===12;
    }],
    ['proof contract preserves known counterexample', () => {
      const x=checkFingerprintImmutability();
      return x.status==='COUNTEREXAMPLE' && x.stored_fingerprint!==x.recomputed_fingerprint;
    }],
    ['proof contract never reports a Lean or SPARK success', () => {
      const r=runProofChecks();
      return r.formal_proofs.lean==='NOT_RUN' && r.formal_proofs.spark==='NOT_RUN' &&
        r.limitations.length===3;
    }],
    ['property lab reproducible native assertions', () => runPropertySelfTests().every(r => r.passed)],
    ['property lab has sixteen actual assertions', () => runPropertySelfTests().length === 16],
    ['v0.9 finite bridge real-source assertions', () => runFormalLabSelfTests().every(r => r.passed)],
    ['v0.9 four synchronous self-tests', () => runFormalLabSelfTests().length === 4],
    ['proof contract IDs are unique and ordered', () =>
      CONTRACT_IDS.length===5 && new Set(CONTRACT_IDS).size===5 &&
      CONTRACT_IDS[4]==='FINGERPRINT-IMMUTABILITY']
  ];
  return checks.map(([name, check]) => {
    try { return { name, passed: check() === true }; }
    catch (error) { return { name, passed: false, error: String(error) }; }
  });
}
