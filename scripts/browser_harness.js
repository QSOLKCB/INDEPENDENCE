// REAL-BROWSER-JOURNEY/1: runs inside an actual browser against the staged site.
// No mocks, frameworks, remote requests or external dependencies. Served only by
// scripts/run_browser_journeys.py; never packaged into GitHub Pages.
const resultNode = document.getElementById('verification-result');
const frame = document.getElementById('site-frame');
const mode = new URL(location.href).searchParams.get('mode') || 'normal';
const checks = [];

function assert(name, passed, detail = '') {
  checks.push({name, status: passed ? 'PASS' : 'FAIL', detail: String(detail).slice(0, 500)});
}

async function waitFor(predicate, timeout = 15000) {
  const start = performance.now();
  while (performance.now() - start < timeout) {
    try { if (predicate()) return true; }
    catch (_) { /* page may still be loading */ }
    await new Promise(resolve => setTimeout(resolve, 75));
  }
  return false;
}

async function run() {
  frame.src = '/#top';
  const loaded = await new Promise((resolve, reject) => {
    frame.addEventListener('load', () => resolve(true), {once: true});
    frame.addEventListener('error', () => reject(new Error('iframe navigation failed')), {once: true});
  });
  if (!loaded) throw new Error('actual site iframe did not load');
  const w = frame.contentWindow, d = w.document;
  assert('real document loaded with application script', !!d.querySelector('script[type="module"][src="./app.js"]') &&
    !!d.getElementById('automaton') && d.getElementById('fingerprint').textContent.trim() !== '--');
  const settled = await waitFor(() => {
    const msg = d.getElementById('ledger-message').textContent;
    return msg.includes('matching repositories') || msg.includes('Could not load evidence snapshot');
  });
  assert('ledger fetch completed rather than hanging', settled);
  if (mode !== 'normal') {
    const msg = d.getElementById('ledger-message').textContent;
    const records = d.querySelectorAll('#ledger-list .ledger-record').length;
    assert('controlled '+mode+' failure is fail-closed',
      msg.includes('Could not load evidence snapshot') &&
      records === 0 && d.getElementById('ledger-receipt').textContent.includes('unavailable'));
    assert('failed ledger cannot disable other first-party controls',
      !d.getElementById('generate').disabled && d.getElementById('formal-lab-run') !== null);
  } else {
    assert('real packaged ledger rendered',
      d.getElementById('ledger-message').textContent.includes('matching repositories') &&
      d.querySelectorAll('#ledger-list .ledger-record').length > 0);
    const record = d.querySelector('#ledger-list .ledger-record-name');
    if (record) {
      const field = d.getElementById('ledger-search');
      field.value = record.textContent;
      field.dispatchEvent(new Event('input', {bubbles: true}));
      assert('real ledger input filters records', d.querySelectorAll('#ledger-list .ledger-record').length >= 1);
      field.value = '';
      field.dispatchEvent(new Event('input', {bubbles: true}));
    } else assert('real ledger input filters records', false, 'no records');
    d.getElementById('repeat').click();
    assert('automaton deterministic replay', d.getElementById('replay').textContent.includes('PASS / BIT-EXACT'));
    d.getElementById('run-tests').click();
    const text = d.getElementById('test-results').textContent;
    const count = text.match(/(\d+)\/(\d+) checks passed/);
    assert('real first-party browser self tests',
      !!count && count[1] === count[2] && !text.split('\n').some(line => line.startsWith('FAIL ')),
      count ? count[0] : text.slice(-300));
    d.getElementById('formal-lab-run').click();
    const verified = await waitFor(() => d.getElementById('formal-lab-status').textContent.startsWith('PASS:'));
    const receiptReady = await waitFor(() => !d.getElementById('formal-lab-export').disabled, 6000);
    assert('real 4096-vector formal browser lab and WebCrypto receipt',
      verified && receiptReady &&
      d.getElementById('formal-lab-hash').textContent.includes('f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635'),
      d.getElementById('formal-lab-status').textContent.slice(0, 240));
    d.getElementById('property-run').click();
    assert('real property laboratory executed',
      await waitFor(() => d.getElementById('property-status').textContent.includes('Finite properties passed'), 12000),
      d.getElementById('property-status').textContent.slice(0, 200));
    d.getElementById('workflow-load-example').click();
    d.getElementById('workflow-build').click();
    assert('real workflow handoff built locally',
      d.getElementById('workflow-prompt').textContent.includes('Do not merge') &&
      !d.getElementById('workflow-copy').disabled);
  }
  // Baseline accessibility/layout checks, not a WCAG 2.x certification.
  const ids = [...d.querySelectorAll('[id]')].map(n => n.id);
  const inputs = [...d.querySelectorAll('input,textarea,select')].filter(n => !n.disabled);
  const unlabelled = inputs.filter(n =>
    !n.labels?.length && !n.getAttribute('aria-label') && !n.getAttribute('aria-labelledby'));
  const unnamedButtons = [...d.querySelectorAll('button')].filter(n =>
    !n.textContent.trim() && !n.getAttribute('aria-label'));
  assert('accessible headings/landmarks and unique IDs',
    d.documentElement.lang === 'en' && !!d.querySelector('h1') &&
    !!d.querySelector('main') && ids.length === new Set(ids).size);
  assert('form labels and button accessible names',
    unlabelled.length === 0 && unnamedButtons.length === 0,
    'unlabelled fields='+unlabelled.map(n => n.id).join(',')+
    '; unnamed buttons='+unnamedButtons.map(n => n.id).join(','));
  assert('viewport is not catastrophically horizontally clipped',
    d.documentElement.scrollWidth < w.innerWidth * 1.5,
    'scroll='+d.documentElement.scrollWidth+', width='+w.innerWidth);
  const inline = d.createElement('script');
  inline.textContent = 'window.__independence_inline_probe = true;';
  d.head.append(inline);
  await new Promise(resolve => setTimeout(resolve, 50));
  assert('real CSP blocks inline code', w.__independence_inline_probe !== true);
  const requests = w.performance.getEntriesByType('resource').map(e => e.name);
  const foreign = requests.filter(u => {
    try { return new URL(u).origin !== w.location.origin; }
    catch (_) { return true; }
  });
  assert('real page has no cross-origin runtime resource requests', foreign.length === 0, foreign.slice(0, 6).join(','));
  return {mode, user_agent: w.navigator.userAgent, viewport: {width: w.innerWidth, height: w.innerHeight},
    checks, resource_count: requests.length, external_resources: foreign};
}
try {
  const result = await run();
  result.status = result.checks.every(c => c.status === 'PASS') ? 'PASS' : 'FAIL';
  resultNode.textContent = JSON.stringify(result);
  resultNode.dataset.complete = 'yes';
} catch (error) {
  resultNode.textContent = JSON.stringify({
    mode, status: 'FAIL', checks: [{name:'browser harness execution',status:'FAIL',detail:String(error)}]
  });
  resultNode.dataset.complete = 'yes';
}
