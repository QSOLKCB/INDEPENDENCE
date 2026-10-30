import {buildAutomaton, dependencyExposure} from './lab/core.js';
import {runTests} from './lab/tests.js';
import {mountLedger} from './ledger/ledger.js';
import {mountTribunal} from './tribunal/ui.js';
import {mountMuseum} from './museum/ui.js';
import {mountBreeding} from './breeding/ui.js';
import {mountWorkflow} from './workflow/ui.js';
import {mountProof} from './proof/ui.js';
import {mountPropertyLab} from './property/ui.js';
import {mountAutomatonProofLab} from './formal-lab/ui.js';

const $ = id => document.getElementById(id);
const canvas = $('automaton');
const context = canvas.getContext('2d', {alpha: false});
let last = null;
let lastParams = null;

function inputs() {
  const rule = Number($('rule').value);
  const seed = Number($('seed').value);
  if (!Number.isSafeInteger(seed) || seed < 1 || seed > 4294967295) {
    $('seed').setCustomValidity('Enter an integer from 1 to 4294967295.');
    $('seed').reportValidity();
    return null;
  }
  $('seed').setCustomValidity('');
  return { rule, seed };
}

function paint(result) {
  if (!context) {
    return false;
  }
  const scaleX = canvas.width / result.columns;
  const scaleY = canvas.height / result.rows;
  context.fillStyle = '#101b18';
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = '#ff563d';
  for (let y = 0; y < result.rows; y += 1) {
    for (let x = 0; x < result.columns; x += 1) {
      if (result.cells[y * result.columns + x]) context.fillRect(x * scaleX, y * scaleY, scaleX, scaleY);
    }
  }
  return true;
}

function generate() {
  const params = inputs();
  if (!params) return;
  const start = performance.now();
  const result = buildAutomaton(params.rule, params.seed);
  const painted = paint(result);
  const duration = performance.now() - start;
  $('fingerprint').textContent = result.fingerprint.toUpperCase();
  $('cells').textContent = result.cells.length.toLocaleString();
  $('duration').textContent = duration.toFixed(2);
  $('replay').textContent = painted ? 'READY' : 'CANVAS UNAVAILABLE';
  $('replay').style.color = painted ? '' : '#ff957e';
  last = result;
  lastParams = params;
}

function verifyReplay() {
  if (!context) { $('replay').textContent = 'CANVAS UNAVAILABLE'; return; }
  if (!last || !lastParams) { $('replay').textContent = 'GENERATE FIRST'; return; }
  // Verify original inputs even if control fields have been edited.
  const repeat = buildAutomaton(lastParams.rule, lastParams.seed);
  const equal = repeat.fingerprint === last.fingerprint &&
    repeat.cells.length === last.cells.length &&
    repeat.cells.every((value, index) => value === last.cells[index]);
  $('replay').textContent = equal ? 'PASS / BIT-EXACT' : 'FAIL / MISMATCH';
  $('replay').style.color = equal ? '#9be49b' : '#ff957e';
}

function updateTree() {
  const direct = Number($('direct').value);
  const fanout = Number($('fanout').value);
  const depth = Number($('depth').value);
  $('direct-value').textContent = String(direct);
  $('fanout-value').textContent = String(fanout);
  $('depth-value').textContent = String(depth);
  $('hypothetical').textContent = dependencyExposure(direct, fanout, depth).toLocaleString();
}

$('generate').addEventListener('click', generate);
$('repeat').addEventListener('click', verifyReplay);
$('rule').addEventListener('change', generate);
$('seed').addEventListener('change', generate);
for (const name of ['direct','fanout','depth']) $(name).addEventListener('input', updateTree);
$('run-tests').addEventListener('click', () => {
  const results = runTests();
  const passed = results.filter(r => r.passed).length;
  const output = $('test-results');
  output.textContent = results.map(r => (r.passed ? 'PASS ' : 'FAIL ') + r.name).join('\n') +
    '\n' + passed + '/' + results.length + ' checks passed. Executed locally.';
  output.className = 'test-results ' + (passed === results.length ? 'pass' : 'fail');
});
updateTree();
generate();
mountLedger();
mountTribunal();
mountMuseum();
mountBreeding();
mountWorkflow();
mountProof();
mountPropertyLab();
mountAutomatonProofLab();
