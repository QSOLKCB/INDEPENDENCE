import {checkVectors, makeReceipt} from './core.js';

const $ = id => document.getElementById(id);
let exported = null;
let running = false;

function download(receipt) {
  const blob = new Blob([JSON.stringify(receipt, null, 2) + '\n'],
    {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'automata4-browser-' + receipt.sha256.slice(0, 12) + '.json';
  document.body.append(link);
  try { link.click(); }
  finally { link.remove(); setTimeout(() => URL.revokeObjectURL(url), 0); }
}

export function mountAutomataFormalLab() {
  const run = $('formal-lab-run');
  if (!run) return;
  const output = $('formal-lab-status');
  const hash = $('formal-lab-hash');
  const exportButton = $('formal-lab-export');
  exportButton.disabled = true;
  run.addEventListener('click', async () => {
    if (running) return;
    running = true;
    exported = null;
    run.disabled = true;
    exportButton.disabled = true;
    hash.textContent = 'No receipt issued.';
    output.textContent = 'Running the real evolve() across all 4,096 four-cell input/rule vectors…';
    try {
      const result = checkVectors();
      output.textContent = 'PASS: ' + result.cases +
        ' four-cell finite vectors, including fixed-zero boundaries, matched the oracle; ' +
        'original Uint8Array inputs remained unchanged. Not a formal proof.';
      try {
        exported = await makeReceipt(result);
        hash.textContent = 'Verified canonical vector digest: ' +
          JSON.parse(exported.payload_text).vectors_sha256 +
          '. Receipt SHA-256: ' + exported.sha256;
        exportButton.disabled = false;
      } catch (error) {
        output.textContent = 'FAIL: receipt could not be validated. No export authorised.';
        hash.textContent = String(error.message);
      }
    } catch (error) {
      output.textContent = 'FAIL: ' + error.message + '. No receipt issued.';
    } finally {
      running = false;
      run.disabled = false;
    }
  });
  exportButton.addEventListener('click', () => {
    if (exported && !running) download(exported);
  });
}
