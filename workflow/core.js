// AI-HUMAN-WORKFLOW/1: static educational workflow, local prompt builder.
// No model calls, credentials, telemetry, network requests or claims of verified execution.
export const PROTOCOL = "AI-HUMAN-WORKFLOW/1";
export const STAGES = Object.freeze([
  Object.freeze({
    id:"intent",title:"Human sets the intent",owner:"HUMAN",
    instruction:"Describe the desired user-visible outcome and the reason it matters.",
    drift:"Vague aspirations let the agent choose a different objective.",
    evidence:"One observable acceptance outcome, written before implementation.",
    example:"Implement a static, local-only workflow explainer accessible from the navigation."
  }),
  Object.freeze({
    id:"scope",title:"Freeze the change boundary",owner:"HUMAN + AI",
    instruction:"List exact in-scope paths and forbidden changes. Read the repository contracts first.",
    drift:"Helpful extras create new dependencies, unexpected interfaces and scope creep.",
    evidence:"An explicit in-scope/out-of-scope list, and a small diff reviewed against it.",
    example:"Only add first-party browser assets and docs; preserve existing experiments."
  }),
  Object.freeze({
    id:"invariants",title:"Pin non-negotiable invariants",owner:"HUMAN",
    instruction:"State the conditions that must not change: privacy, determinism, formats, safety and dependencies.",
    drift:"The AI optimises one subtask by silently weakening the original constraints.",
    evidence:"Written invariants and tests that fail if any are violated.",
    example:"No remote script imports, external packages, fabricated benchmark claims or auto-merges."
  }),
  Object.freeze({
    id:"implement",title:"AI builds a bounded patch",owner:"AI",
    instruction:"Implement only the approved task. Prefer a focused PR, no adjacent refactors.",
    drift:"The agent solves a related problem or rewrites stable code unnecessarily.",
    evidence:"A per-file change summary and exact branch HEAD SHA.",
    example:"Separate pure logic, browser UI and CSS; explain every new file."
  }),
  Object.freeze({
    id:"verify",title:"Reproduce, don't merely assert",owner:"AI + TOOLS",
    instruction:"Run relevant tests, negative tests and the full suite when available. Distinguish executed from unexecuted checks.",
    drift:"Plausible narration or green-looking mock outputs replace real results.",
    evidence:"Commands, outputs, failed cases and tool/environment limitations.",
    example:"Run Python unittest, local browser checks and dependency audit; mark unavailable checks pending."
  }),
  Object.freeze({
    id:"attack",title:"Review adversarially",owner:"REVIEWER + HUMAN",
    instruction:"Ask a separate reviewer to challenge edge cases, trust boundaries and unsupported claims; classify P0/P1/P2/P3.",
    drift:"The implementing AI endorses its own assumptions without trying to falsify them.",
    evidence:"Review findings with concrete repros; targeted regression tests for each fix.",
    example:"Try forged receipts, invalid input, stale state, hidden network calls and ambiguous source claims."
  }),
  Object.freeze({
    id:"freshness",title:"Inspect the freshest HEAD",owner:"HUMAN + TOOLS",
    instruction:"Re-fetch the actual PR HEAD after every fix. Review that exact SHA before merging.",
    drift:"A review of an older commit is misapplied to a newer branch or dirty checkout.",
    evidence:"Current full commit SHA, review target, and a clean diff against main.",
    example:"If a fix changes HEAD, repeat review on the new SHA; old approval is not automatically current."
  }),
  Object.freeze({
    id:"ship",title:"Human merges and publishes",owner:"HUMAN",
    instruction:"The human accepts the residual risk, merges the PR and triggers permitted deployment/release steps.",
    drift:"AI treats a proposed change or local test as a deployed, verified result.",
    evidence:"Merged PR, merge SHA, deployment result, release tag and explicitly stated outstanding checks.",
    example:"Merge only after review; manually run Pages workflow and verify the public URL."
  })
]);
export const CONTROLS = Object.freeze([
  Object.freeze({id:"goal",label:"One testable user-visible goal",why:"A goal with observable acceptance criteria limits interpretations."}),
  Object.freeze({id:"scope",label:"In-scope AND out-of-scope changes",why:"The negative space is what prevents helpful scope creep."}),
  Object.freeze({id:"rules",label:"Read and preserve repository invariants",why:"Local instructions beat generic coding conventions."}),
  Object.freeze({id:"checks",label:"Executed tests + negative test cases",why:"Tests must distinguish correct from incorrect behaviour."}),
  Object.freeze({id:"evidence",label:"Report commands, actual outputs and pending checks",why:"Model statements are not tool observations."}),
  Object.freeze({id:"review",label:"Independent adversarial review + regression fixes",why:"Challenge assumptions before trusting the implementation."}),
  Object.freeze({id:"sha",label:"Re-review the exact latest HEAD SHA",why:"Reviewing stale code is not reviewing the code you'll merge."}),
  Object.freeze({id:"human",label:"Human-controlled merge, deploy and release",why:"AI assists, but release authority remains with a person."})
]);
export const CASE_STUDIES = Object.freeze([
  Object.freeze({version:"v0.1.0",title:"The Declaration",pr:1,lesson:"Set the dependency-free invariant and run offline checks.",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/1"}),
  Object.freeze({version:"v0.2.0",title:"The Evidence Ledger",pr:2,lesson:"Separate observed repository indicators from unknown data.",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/2"}),
  Object.freeze({version:"v0.3.0",title:"The Dependency Tribunal",pr:3,lesson:"Compare like with like and label the measurement boundaries.",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/3"}),
  Object.freeze({version:"v0.4.0",title:"The Gremlin Museum",pr:4,lesson:"Reject resealed forged provenance using exact fixed metadata.",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/4"}),
  Object.freeze({version:"v0.5.0",title:"The Breeding Laboratory",pr:5,lesson:"Use known mutations to show what an insufficient test suite misses.",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/5"})
]);

export function validateMission(values) {
  if(!values || typeof values!=="object" || Array.isArray(values)) throw new TypeError("mission must be an object");
  const fields=["goal","scope","excluded","invariants","acceptance"];
  const out={};
  for(const key of fields){
    const value=values[key];
    if(typeof value!=="string" || value.length>1200 || /\u0000/.test(value))
      throw new RangeError(key+" must be plain text of at most 1200 characters");
    const trimmed=value.trim();
    if(key==="goal" && !trimmed) throw new RangeError("goal is required");
    out[key]=trimmed||"(not provided — HUMAN MUST DEFINE before implementation)";
  }
  return out;
}

export function makeHandoff(values) {
  const v=validateMission(values);
  return [
    "# AI–HUMAN GITHUB WORKFLOW — BOUNDED IMPLEMENTATION HANDOFF",
    "This is a human-authored mission template, NOT a completed review, authorization or execution record.",
    "",
    "## Goal / observable outcome",v.goal,"",
    "## In scope",v.scope,"",
    "## Explicitly out of scope",v.excluded,"",
    "## Invariants — do not weaken",v.invariants,"",
    "## Acceptance and negative tests",v.acceptance,"",
    "## Operating rules",
    "1. Read the repository README, AGENTS.md/CLAUDE.md if present, and docs/INVARIANTS.md before editing. Report conflicts; do not silently resolve them.",
    "2. State an implementation plan and exact in-scope files. Do not introduce features, frameworks, packages, network calls or unrelated refactors without human approval.",
    "3. Make a focused feature branch and pull request. Preserve all existing interfaces, formats, hashes, privacy boundaries and tests unless explicitly authorised.",
    "4. Add positive, boundary and adversarial regression tests; run the relevant checks and the full suite when feasible. Never present a mock, guess or static inspection as a live run.",
    "5. Report each executed command and its real outcome. List unavailable tooling and skipped checks separately. If you lack permission or access, stop and identify the blocker.",
    "6. Ask for independent adversarial P0/P1/P2/P3 review of the exact PR HEAD. For every actionable finding, reproduce, patch minimally, test, and request re-review of the new HEAD.",
    "7. Include the latest FULL commit SHA, file summary, findings, remaining risks, and explicit human approval gates in the PR handoff.",
    "8. Do not merge, publish, release, deploy, share secrets, or claim external verification without explicit human authorization.",
    "",
    "## Stop conditions",
    "- Any conflict with invariants, unclear authority, missing credentials, unverified tests or unexpected scope expansion: STOP, report facts, request direction.",
    "- A passing check supports only its stated scope. Zero findings does not prove zero defects.",
    "",
    "Success = an inspectable bounded PR with reproducible evidence and the HUMAN deciding whether to merge."
  ].join("\n");
}

export function gateStatus(values) {
  if(!values || typeof values!=="object" || Array.isArray(values)) throw new TypeError("gate map required");
  const checked=CONTROLS.filter(c=>values[c.id]===true).length;
  return {acknowledged:checked,total:CONTROLS.length,
    selfReportedOnly:true,allAcknowledged:checked===CONTROLS.length};
}
