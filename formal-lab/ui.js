import {checkVectors, makeReceipt} from './core.js';

const $ = id => document.getElementById(id);
let receipt = null;

function download(data) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2) + '\n'],
    {type: 'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'automaton-proof-lab-' + data.sha256.slice(0, 12) + '.json';
  document.body.append(link);
  try { link.click(); }
  finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 0); }
}

export function mountAutomatonProofLab() {
  const run = $('formal-lab-run');
  if (!run) return;
  const exportButton = $('formal-lab-export');
  const status = $('formal-lab-status');
  const hash = $('formal-lab-hash');
  exportButton.disabled = true;
  run.addEventListener('click', async () => {
    receipt = null;
    exportButton.disabled = true;
    run.disabled = true;
    hash.textContent = 'No receipt for this run.';
    status.textContent = 'Running 2,048 neighbourhood and 512 boundary cases…';
    try {
      const checks = checkVectors();
      status.textContent = 'PASS: ' + checks.neighbourhoodCases + ' neighbourhood and ' +
        checks.boundaryCases + ' fixed-zero boundary cases. Finite execution only.';
      try {
        receipt = await makeReceipt(checks);
        hash.textContent = 'Exact payload SHA-256: ' + receipt.sha256;
        exportButton.disabled = false;
      } catch (error) { hash.textContent = 'Receipt unavailable: ' + error.message; }
    } catch (error) {
      status.textContent = 'FAIL: ' + error.message + '. No receipt issued.';
    } finally { run.disabled = false; }
  });
  exportButton.addEventListener('click', () => {
    if (receipt && !run.disabled) download(receipt);
  });
}
