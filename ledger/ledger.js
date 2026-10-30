// Public, read-only, first-party ledger. No browser GitHub API calls.
const byId = id => document.getElementById(id);
const make = (tag, cls, value) => {
  const element = document.createElement(tag);
  if (cls) element.className = cls;
  if (value !== undefined) element.textContent = String(value);
  return element;
};
const safeName = name => typeof name === 'string' && /^[A-Za-z0-9_.-]+$/.test(name);
// Git object IDs are 40 hex characters; SHA-256 evidence receipts are 64.
export const validTreeSha = sha => typeof sha === 'string' && /^[a-f0-9]{40}$/.test(sha);
export const validReceiptSha = sha => typeof sha === 'string' && /^[a-f0-9]{64}$/.test(sha);
const status = row => {
  const scan = row.scan || {};
  if (scan.state !== 'scanned' || !Number.isSafeInteger(scan.manifest_count) ||
      scan.manifest_count < 0) return 'unknown';
  return scan.manifest_count > 0 ? 'signals' : 'no-manifest';
};

export function mountLedger() {
  const root = byId('ledger');
  if (!root) return;
  const summary = byId('ledger-summary');
  const list = byId('ledger-list');
  const message = byId('ledger-message');
  const query = byId('ledger-search');
  const filter = byId('ledger-filter');
  const more = byId('ledger-more');
  const receipt = byId('ledger-receipt');
  let rows = [];
  let visible = 24;

  function repaint() {
    const term = query.value.toLocaleLowerCase().trim();
    const selected = filter.value;
    const matches = rows.filter(row => (
      (!term || row.name.toLocaleLowerCase().includes(term) ||
        (row.category || '').toLocaleLowerCase().includes(term)) &&
      (selected === 'all' || status(row) === selected)
    ));
    list.replaceChildren();
    const fragment = document.createDocumentFragment();
    for (const row of matches.slice(0, visible)) {
      if (!safeName(row.name)) continue;
      const state = status(row);
      const card = make('article', 'ledger-record');
      const top = make('div', 'ledger-record-top');
      const title = make('a', 'ledger-record-name', row.name);
      title.href = 'https://github.com/QSOLKCB/' + row.name;
      title.rel = 'noopener noreferrer';
      top.append(title);
      top.append(make('span', 'ledger-state ledger-state-' + state,
        state === 'signals' ? 'MANIFEST SIGNALS' :
        state === 'no-manifest' ? 'NO KNOWN MANIFEST' : 'UNKNOWN'));
      card.append(top);
      card.append(make('div', 'ledger-record-meta',
        (row.category || 'Uncategorised') + ' · ' +
        (row.archived ? 'Archived' : 'Public') + ' · ' +
        (row.branch || 'No default branch')));
      const indicators = make('div', 'ledger-record-indicators');
      const scan = row.scan || {};
      if (state !== 'unknown') {
        indicators.append(make('span', '', 'Manifest markers: ' + scan.manifest_count));
        indicators.append(make('span', '', 'Container markers: ' + scan.container_marker_count));
        indicators.append(make('span', '', 'Workflow files: ' + scan.workflow_count));
        indicators.append(make('span', '', 'Files seen: ' + scan.files_seen));
        const paths = Array.isArray(scan.manifest_paths) ? scan.manifest_paths : [];
        if (paths.length) card.append(make('p', 'ledger-paths', 'Observed: ' + paths.slice(0, 6).join(' · ') +
          (paths.length > 6 || scan.manifest_paths_omitted ? ' …' : '')));
      } else {
        indicators.append(make('span', '', 'Not certified: ' + (scan.reason || scan.state || 'no scan')));
      }
      card.append(indicators);
      if (validTreeSha(scan.tree_sha)) {
        const path = make('a', 'ledger-tree-link', 'Inspect tree ' + scan.tree_sha.slice(0, 12) + ' ↗');
        path.href = 'https://github.com/QSOLKCB/' + row.name + '/tree/' + scan.tree_sha;
        path.rel = 'noopener noreferrer';
        card.append(path);
      }
      fragment.append(card);
    }
    list.append(fragment);
    message.textContent = matches.length + ' matching repositories · showing ' +
      Math.min(visible, matches.length) + '. Status reflects filename evidence only.';
    more.hidden = matches.length <= visible;
  }

  query.addEventListener('input', () => { visible = 24; repaint(); });
  filter.addEventListener('change', () => { visible = 24; repaint(); });
  more.addEventListener('click', () => { visible += 24; repaint(); });
  message.textContent = 'Loading packaged evidence snapshot…';

  fetch(new URL('./data.json', import.meta.url), {cache: 'no-store'})
    .then(response => {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(report => {
      if (report.schema_version !== 1 || !Array.isArray(report.repositories) ||
          !report.coverage || report.coverage.total !== report.repositories.length)
        throw new Error('invalid evidence schema');
      if (!report.repositories.every(row => row && safeName(row.name)))
        throw new Error('invalid repository identifier');
      rows = report.repositories;
      const inspected = rows.filter(row => status(row) !== 'unknown');
      const derived = {
        total: rows.length,
        scanned: inspected.length,
        unknown: rows.length - inspected.length,
        with_manifest_signals: inspected.filter(row => status(row) === 'signals').length,
        without_manifest_signals: inspected.filter(row => status(row) === 'no-manifest').length,
        catalogued: rows.filter(row => row.category != null).length,
      };
      if (!Object.entries(derived).every(([key, value]) => report.coverage[key] === value))
        throw new Error('evidence coverage mismatch');
      summary.replaceChildren();
      const stats = [
        ['PUBLIC SNAPSHOT', report.coverage.total],
        ['TREES INSPECTED', report.coverage.scanned],
        ['MANIFEST SIGNALS', report.coverage.with_manifest_signals],
        ['NO KNOWN MANIFEST', report.coverage.without_manifest_signals],
        ['UNKNOWN / PARTIAL', report.coverage.unknown],
        ['CURATED CATEGORY', report.coverage.catalogued],
      ];
      for (const [label, value] of stats) {
        const item = make('div', 'ledger-summary-item');
        item.append(make('strong', '', value));
        item.append(make('span', '', label));
        summary.append(item);
      }
      const text = 'Snapshot: ' + report.as_of + ' · ' + report.method + '.';
      byId('ledger-method').textContent = text;
      receipt.textContent = validReceiptSha(report.receipt_sha256)
        ? 'Canonical JSON SHA-256 receipt: ' + report.receipt_sha256
        : report.receipt_sha256 == null
          ? 'Seed inventory only · no SHA-256 receipt until a collected deployment.'
          : 'Invalid SHA-256 receipt value · inspect the source dataset.';
      repaint();
    })
    .catch(error => {
      summary.replaceChildren();
      list.replaceChildren();
      receipt.textContent = 'Evidence unavailable; do not infer clean status.';
      message.textContent = 'Could not load evidence snapshot (' + error.message + '). See the source repository.';
      more.hidden = true;
    });
}
