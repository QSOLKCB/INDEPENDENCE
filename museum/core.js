// GREMLIN-MUSEUM/1 — pure, fixed, offline evidence fixtures.
// Unsafe examples are evaluated only as strings or inert data: NEVER executed,
// injected into the DOM as markup, fetched, or submitted to a real endpoint.
export const PROTOCOL = "GREMLIN-MUSEUM/1";
export const EXHIBITS = Object.freeze([
  Object.freeze({id:"side-effect-import",title:"The Side-Effect Stowaway",kind:"Static-audit bypass",
    provenance:"Documented INDEPENDENCE v0.1 review",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/1",
    lesson:"A remote side-effect import can evade a rule that only recognises from-clauses."}),
  Object.freeze({id:"checkout-ancestry",title:"The Phantom Dependency",kind:"Audit false positive",
    provenance:"Documented INDEPENDENCE v0.1 review",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/1",
    lesson:"An audit must inspect repository-relative paths, not unrelated ancestor directories."}),
  Object.freeze({id:"sha-identity",title:"The SHA Identity Crisis",kind:"Evidence integrity / validation",
    provenance:"Documented INDEPENDENCE v0.2 review",source:"https://github.com/QSOLKCB/INDEPENDENCE/pull/2",
    lesson:"40-digit Git object IDs and 64-digit SHA-256 receipts are distinct formats."}),
  Object.freeze({id:"json-overflow",title:"The Infinity Smuggler",kind:"JSON numeric correctness",
    provenance:"Illustrative local case, not a reported INDEPENDENCE vulnerability",source:"https://github.com/QSOLKCB/INDEPENDENCE",
    lesson:"A syntactically valid JSON exponent can exceed finite numeric range."}),
  Object.freeze({id:"html-encoding",title:"The Markup Masquerade",kind:"HTML output encoding",
    provenance:"Illustrative local case, not a reported INDEPENDENCE vulnerability",source:"https://github.com/QSOLKCB/INDEPENDENCE",
    lesson:"Untrusted text must not be interpreted as trusted HTML markup."})
]);

export function encodeHtml(value) {
  return String(value).replace(/[&<>"']/g, char =>
    ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
}

export function finiteJSON(value) {
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(finiteJSON);
  if (value && typeof value === "object") return Object.values(value).every(finiteJSON);
  return true;
}

export function runExhibit(id) {
  let input, legacy, hardened, checks;
  switch(id) {
    case "side-effect-import": {
      input = "import 'https://example.invalid/museum-only.js';";
      // Historical shape deliberately omits the optional bare-string form.
      const oldPattern = /\bimport\s*(?:\(|[^;\n]*?\bfrom\s*)['"]https?:\/\//i;
      const newPattern = /\bimport\s*(?:\(\s*|[^;\n]*?\bfrom\s*)?['"]https?:\/\//i;
      const missed = !oldPattern.test(input);
      const caught = newPattern.test(input);
      legacy = "Original static rule missed the remote side-effect import: " + missed;
      hardened = "Corrected rule detects the side-effect import: " + caught;
      checks = [missed,caught,!newPattern.test("import './local.js';")];
      break;
    }
    case "checkout-ancestry": {
      input = "Repository /workspace/.venv/repo; file app.js";
      const root = "/workspace/.venv/repo";
      const file = root + "/app.js";
      const absoluteParts = file.split("/");
      const relativeParts = file.slice(root.length + 1).split("/");
      const mistaken = absoluteParts.includes(".venv");
      const correct = relativeParts.includes(".venv") || relativeParts.includes("node_modules");
      legacy = "Absolute-ancestor scan reports a vendored directory: " + mistaken;
      hardened = "Repository-relative scan reports a vendored directory: " + correct;
      checks = [mistaken,!correct,["node_modules","lib.js"].includes("node_modules")];
      break;
    }
    case "sha-identity": {
      input = "Synthetic receipt: " + "a".repeat(64);
      const oldValidator = /^[a-f0-9]{40}$/;
      const receiptValidator = /^[a-f0-9]{64}$/;
      const gitValidator = /^[a-f0-9]{40}$/;
      const rejected = !oldValidator.test("a".repeat(64));
      const accepted = receiptValidator.test("a".repeat(64));
      legacy = "Reused 40-hex validator rejects this 64-hex receipt: " + rejected;
      hardened = "Dedicated 64-hex validator accepts it: " + accepted;
      checks = [rejected,accepted,gitValidator.test("b".repeat(40)),!receiptValidator.test("b".repeat(40))];
      break;
    }
    case "json-overflow": {
      input = '{"budget":1e999}';
      const parsed = JSON.parse(input);
      const becameInfinite = parsed.budget === Infinity;
      const serialized = JSON.stringify(parsed);
      legacy = "Native parse creates Infinity; stringification yields: " + serialized;
      hardened = "Deep finite-number check rejects the parsed value: " + !finiteJSON(parsed);
      checks = [becameInfinite,serialized === '{"budget":null}',!finiteJSON(parsed),
        finiteJSON({items:[1,2,{value:3}]})];
      break;
    }
    case "html-encoding": {
      // Only a string. Not assigned to innerHTML, loaded, or evaluated.
      input = '<img src=x onerror=alert(1)>';
      const raw = "<p>" + input + "</p>";
      const escaped = "<p>" + encodeHtml(input) + "</p>";
      legacy = "Unsafe HTML construction contains unescaped input: " + raw;
      hardened = "Encoded HTML string (displayed as TEXT, never rendered): " + escaped;
      checks = [raw.includes(input),!escaped.includes(input),
        escaped.includes("&lt;img"),encodeHtml("<>&\"'") === "&lt;&gt;&amp;&quot;&#39;"];
      break;
    }
    default: throw new RangeError("unknown museum exhibit");
  }
  const exhibit = EXHIBITS.find(entry => entry.id === id);
  return {
    id, kind:exhibit.kind, input, legacy, hardened,
    assertions:{passed:checks.filter(Boolean).length,total:checks.length},
    passed:checks.every(Boolean)
  };
}

export function runAll() {
  return EXHIBITS.map(exhibit => runExhibit(exhibit.id));
}

export function assembleReport(results = runAll()) {
  if (!Array.isArray(results) || results.length !== EXHIBITS.length ||
      results.some((result, i) => !result || result.id !== EXHIBITS[i].id ||
        !result.passed || result.assertions.passed !== result.assertions.total)) {
    throw new Error("refusing evidence export: at least one exhibit is incomplete or failed");
  }
  return {protocol:PROTOCOL,schema_version:1,scope:"isolated deterministic examples, no external exploitation",
    exhibits:results,provenance:EXHIBITS.map(({id,provenance,source})=>({id,provenance,source})),
    limitations:["String and data demonstrations; no payload is executed or injected as HTML.",
      "Static regex detection is a scoped fixture, not a complete JavaScript parser.",
      "A valid receipt proves byte integrity only, not independent reproduction or absence of vulnerabilities."]};
}
