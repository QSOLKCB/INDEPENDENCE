import {runPropertyLab} from './core.js';

const $ = id => document.getElementById(id);
const node = (tag, cls, text) => {
  const element = document.createElement(tag);
  if (cls) element.className = cls;
  if (text !== undefined) element.textContent = String(text);
  return element;
};
let envelope = null;
let generation = 0;

function render(report) {
  const target = $('property-results');
  target.replaceChildren();
  const generated = node('article', 'property-case');
  generated.append(node('span', 'property-label', '01 / THE REAL SOURCE'),
    node('strong', 'property-success', report.generated_status),
    node('p', '', `${report.trials} deterministic generated input rows checked against an independently written transition oracle. Seed: ${report.seed}.`));
  target.append(generated);
  const mutant = node('article', 'property-case');
  mutant.append(node('span', 'property-label', '02 / DELIBERATELY INJECTED FAULT'),
    node('strong', 'property-warning', report.mutant.status),
    node('p', '', 'Incorrect wraparound boundaries. Original: ' + JSON.stringify(report.mutant.original) +
      ' → canonical minimum: ' + JSON.stringify(report.mutant.minimized) +
      '. Witnesses are checked again after shrinking; ordering: ' + report.mutant.ordering + '.'));
  target.append(mutant);
  const ownership = node('article', 'property-case');
  ownership.append(node('span', 'property-label', '03 / ACTUAL OWNERSHIP COUNTEREXAMPLE'),
    node('strong', 'property-warning', report.ownership.status),
    node('p', '', 'Legacy buildAutomaton: 8×8 → 1×1 witness. The returned Uint8Array changes while its stored fingerprint does not.'),
    node('p', '', 'Opt-in guardedSnapshot: ' + report.ownership.guarded_status +
      '. This does not silently change the legacy public API.'));
  target.append(ownership);
}

async function seal(report) {
  if (!globalThis.crypto?.subtle) throw new Error('WebCrypto needs HTTPS or localhost');
  const payload_text = JSON.stringify(report, null, 2);
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(payload_text));
  const sha256 = [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join('');
  return {format: 'PROPERTY-LAB-RECEIPT/1', algorithm: 'SHA-256/UTF-8', sha256, payload_text};
}

function download(record) {
  const blob = new Blob([JSON.stringify(record, null, 2) + '\n'], {type: 'application/json'});
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url;
  link.download = 'property-lab-' + record.sha256.slice(0, 12) + '.json';
  document.body.append(link);
  try { link.click(); }
  finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 0); }
}

export function mountPropertyLab() {
  if (!$('property-lab')) return;
  const seed = $('property-seed'), trials = $('property-trials'), run = $('property-run');
  const exportButton = $('property-export'), status = $('property-status'), hash = $('property-hash');
  const reset = () => {
    generation += 1;
    envelope = null;
    exportButton.disabled = true;
    hash.textContent = 'No receipt for the current inputs.';
    $('property-results').replaceChildren();
    status.textContent = 'Inputs changed. Run checks to produce new observations.';
  };
  for (const field of [seed, trials]) field.addEventListener('input', reset);
  exportButton.disabled = true;
  run.addEventListener('click', async () => {
    reset();
    const currentGeneration = generation;
    run.disabled = true;
    status.textContent = 'Running bounded deterministic properties and shrinking witnesses…';
    try {
      if (!/^\d+$/.test(seed.value) || !/^\d+$/.test(trials.value))
        throw new RangeError('only ASCII decimal integer inputs are accepted');
      const report = runPropertyLab({seed: Number(seed.value), trials: Number(trials.value)});
      render(report);
      status.textContent = 'Finite properties passed. One injected mutant and one legacy ownership defect exposed; neither is a formal proof.';
      try {
        const sealed = await seal(report);
        // Input can change while WebCrypto awaits: never export a stale result.
        if (currentGeneration === generation) {
          envelope = sealed;
          hash.textContent = 'SHA-256 of exact report bytes: ' + sealed.sha256;
          exportButton.disabled = false;
        }
      } catch (error) {
        if (currentGeneration === generation)
          hash.textContent = 'Receipt unavailable: ' + error.message;
      }
    } catch (error) {
      status.textContent = 'FAILED: ' + error.message + '. No valid receipt issued.';
      hash.textContent = 'No valid receipt.';
    } finally { run.disabled = false; }
  });
  exportButton.addEventListener('click', () => {
    if (envelope && !run.disabled) download(envelope);
  });
}
