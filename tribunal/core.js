// DOM-TRIBUNAL/1: deterministic pure protocol, zero external modules.
export const PROTOCOL = "DOM-TRIBUNAL/1";
export const PHASES = Object.freeze(["initial", "update", "reorder"]);

export function xorshift32(seed) {
  if (!Number.isInteger(seed) || seed < 1 || seed > 0xffffffff) throw new RangeError("seed must be nonzero uint32");
  let state = seed >>> 0;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0);
  };
}

export function makePhases(seed, count) {
  if (!Number.isInteger(count) || count < 1 || count > 1000) throw new RangeError("count outside 1..1000");
  const next = xorshift32(seed);
  const initial = Array.from({length: count}, (_, i) => ({
    id: "r" + i, label: "ITEM " + i + " · " + (next() % 100000).toString().padStart(5, "0")
  }));
  const update = initial.map((row, i) => ({
    id: row.id, label: i % 2 === 0 ? row.label + " *" : row.label
  }));
  const reorder = update.filter((_, i) => i % 3 !== 0).reverse();
  return Object.freeze({initial, update, reorder});
}

export function fingerprint(rows) {
  // Noncryptographic content checksum, never used as an evidence attestation.
  let h = 0x811c9dc5;
  for (const row of rows) {
    for (const char of row.id + "\u0000" + row.label + "\n") {
      h ^= char.charCodeAt(0);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
  }
  return h.toString(16).padStart(8, "0");
}

export function median(values) {
  if (!Array.isArray(values) || !values.length ||
      values.some(v => typeof v !== "number" || !Number.isFinite(v)))
    throw new RangeError("median requires finite nonempty numeric samples");
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function bootstrapMedianCI(differences, seed = 0x1a2b3c4d, resamples = 512) {
  if (!Array.isArray(differences) || differences.length < 8 ||
      differences.some(v => typeof v !== "number" || !Number.isFinite(v)))
    throw new RangeError("bootstrap requires at least eight finite paired differences");
  if (!Number.isInteger(resamples) || resamples < 100 || resamples > 4096)
    throw new RangeError("resamples outside 100..4096");
  const random = xorshift32(seed);
  const distribution = [];
  for (let i = 0; i < resamples; i++) {
    const draw = Array.from({length: differences.length},
      () => differences[random() % differences.length]);
    distribution.push(median(draw));
  }
  distribution.sort((a, b) => a - b);
  return [distribution[Math.floor((resamples - 1) * 0.025)],
    distribution[Math.ceil((resamples - 1) * 0.975)]];
}

export function assessPairs(pairs) {
  if (!Array.isArray(pairs) || pairs.length < 8 ||
      pairs.some(pair => !pair || !Number.isFinite(pair.direct) ||
        !Number.isFinite(pair.keyed) || pair.direct < 0 || pair.keyed < 0))
    throw new RangeError("need at least eight valid matched timings");
  const direct = pairs.map(x => x.direct);
  const keyed = pairs.map(x => x.keyed);
  const deltas = pairs.map(x => x.keyed - x.direct);
  return {
    trials: pairs.length,
    direct_median_ms: median(direct),
    keyed_median_ms: median(keyed),
    paired_delta_median_ms: median(deltas),
    paired_delta_bootstrap_95_ms: bootstrapMedianCI(deltas)
  };
}

export function validateOutput(container, rows) {
  const nodes = container.children;
  if (nodes.length !== rows.length) return false;
  for (let i = 0; i < rows.length; i++) {
    if (nodes[i].tagName !== "LI" || nodes[i].dataset.id !== rows[i].id ||
        nodes[i].textContent !== rows[i].label) return false;
  }
  return true;
}
