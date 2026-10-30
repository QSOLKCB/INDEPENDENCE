import {PROTOCOL, PHASES, makePhases, fingerprint, assessPairs, validateOutput} from "./core.js";
import * as direct from "./direct.js";
import * as keyed from "./keyed.js";

const CANDIDATES = Object.freeze([direct, keyed]);
const MAX_TRIALS = 60;

export function validateConfig(options) {
  const {seed, count, warmups, trials} = options;
  if (!Number.isInteger(seed) || seed < 1 || seed > 0xffffffff ||
      !Number.isInteger(count) || count < 20 || count > 400 ||
      !Number.isInteger(warmups) || warmups < 2 || warmups > 12 ||
      !Number.isInteger(trials) || trials < 8 || trials > MAX_TRIALS)
    throw new RangeError("seed 1..4294967295, rows 20..400, warmups 2..12, trials 8..60");
  return {seed, count, warmups, trials};
}

function measure(adapterModule, phases) {
  // Detached DOM isolates mutations from CSS/layout/paint. This is not an FPS test.
  const root = document.createElement("ul");
  const adapter = adapterModule.createAdapter(root);
  const times = {};
  for (const phase of PHASES) {
    const start = performance.now();
    adapter.render(phases[phase]);
    const elapsed = performance.now() - start;
    if (!Number.isFinite(elapsed) || elapsed < 0) throw Error("invalid clock sample");
    // Verify full row identity, order and text OUTSIDE the measured interval.
    if (!validateOutput(root, phases[phase]))
      throw Error("CORRECTNESS FAILURE: " + adapterModule.ADAPTER.id + "/" + phase);
    times[phase] = elapsed;
  }
  return times;
}

function snapshotSize(moduleName) {
  const file = moduleName === "direct" ? "direct.js" : "keyed.js";
  return fetch(new URL("./" + file, import.meta.url), {cache:"no-store"})
    .then(response => {
      if (!response.ok) throw Error("Cannot read first-party adapter bytes: " + file);
      return response.arrayBuffer();
    })
    .then(bytes => bytes.byteLength);
}

export async function compare(options, onProgress = () => {}) {
  const config = validateConfig(options);
  if (document.visibilityState === "hidden") throw Error("Run in a visible browser tab");
  if (!globalThis.crypto || !crypto.subtle) throw Error("SHA-256 requires HTTPS or localhost");
  const phases = makePhases(config.seed, config.count);
  const pairs = [];
  const all = config.warmups + config.trials;
  for (let i = 0; i < all; i++) {
    if (document.visibilityState === "hidden") throw Error("Tab became hidden; measurements discarded");
    const one = {};
    // Alternate execution order, but keep each candidate isolated per paired trial.
    const ordered = i % 2 ? [...CANDIDATES].reverse() : CANDIDATES;
    for (const candidate of ordered) one[candidate.ADAPTER.id] = measure(candidate, phases);
    if (i >= config.warmups) pairs.push(one);
    onProgress(i + 1, all);
    // Yield between pairs; this cost is never included in a timing.
    if ((i + 1) % 3 === 0) await new Promise(resolve => setTimeout(resolve, 0));
  }
  const statistics = {};
  for (const phase of PHASES) {
    statistics[phase] = assessPairs(pairs.map(pair => ({
      direct: pair.direct[phase], keyed: pair.keyed[phase]
    })));
  }
  const assetBytes = {
    direct: await snapshotSize("direct"),
    keyed: await snapshotSize("keyed")
  };
  const precision = pairs.some(pair => PHASES.some(phase =>
    pair.direct[phase] === 0 || pair.keyed[phase] === 0));
  return {
    schema_version: 1, protocol: PROTOCOL,
    observed_at: new Date().toISOString(),
    candidates: [
      {id: "direct", label: direct.ADAPTER.label, kind: "native"},
      {id: "keyed", label: keyed.ADAPTER.label, kind: "illustrative"}
    ],
    config, phase_fingerprints: Object.fromEntries(PHASES.map(p => [p, fingerprint(phases[p])])),
    methodology: {
      scope: "detached DOM mutation operations only; excludes layout/paint and network",
      work: "identical rows/updates/reorder; shared deterministic seeded data",
      order: "alternating within paired trials, no randomized machine environment",
      correctness: "full DOM identity/order/text verified after every phase",
      intervals: "paired median difference, deterministic 512-resample bootstrap percentile 95%",
      attribution: "local keyed adapter is illustrative; NOT a React/Vue/Svelte benchmark",
      storage: "local browser measurement, not a server-side or independently certified result"
    },
    samples_ms: pairs, statistics,
    adapter_source_bytes: assetBytes,
    low_clock_resolution_observed: precision,
    correctness: {passed: true, trials_verified: all * 2 * PHASES.length}
  };
}

export async function makeReceipt(report) {
  // Hash exact UTF-8 payload text. Do not confuse reproducibility with authenticity.
  const payload_text = JSON.stringify(report, null, 2);
  const buffer = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(payload_text));
  const sha256 = [...new Uint8Array(buffer)].map(x => x.toString(16).padStart(2, "0")).join("");
  return {format: "DOM-TRIBUNAL-RECEIPT/1", algorithm: "SHA-256/UTF-8", sha256, payload_text};
}

export function downloadReceipt(receipt) {
  const blob = new Blob([JSON.stringify(receipt, null, 2) + "\n"], {type:"application/json"});
  const url = URL.createObjectURL(blob);
  try {
    const a = document.createElement("a");
    a.href = url;
    a.download = "tribunal-" + receipt.sha256.slice(0, 12) + ".json";
    document.body.append(a);
    a.click();
    a.remove();
  } finally {
    // Deferred until after click's synchronous default action has been queued.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}
