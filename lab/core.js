// Pure, browser-independent logic. No packages, environment globals, or network calls.
export function xorshift32(seed) {
  let state = seed >>> 0;
  if (state === 0) state = 1;
  return function next() {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    state >>>= 0;
    return state;
  };
}

export function evolve(previous, rule) {
  const width = previous.length;
  const next = new Uint8Array(width);
  for (let x = 0; x < width; x += 1) {
    const left = x === 0 ? 0 : previous[x - 1];
    const center = previous[x];
    const right = x + 1 === width ? 0 : previous[x + 1];
    const neighbourhood = (left << 2) | (center << 1) | right;
    next[x] = (rule >>> neighbourhood) & 1;
  }
  return next;
}

export function fnv1a(bytes) {
  let hash = 0x811c9dc5;
  for (const value of bytes) {
    hash ^= value;
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, '0');
}

export function buildAutomaton(rule, seed, columns = 128, rows = 76) {
  if (!Number.isInteger(rule) || rule < 0 || rule > 255) throw new RangeError('rule must be 0..255');
  if (!Number.isInteger(seed) || seed < 1 || seed > 0xffffffff) throw new RangeError('seed must be uint32 nonzero');
  if (!Number.isInteger(columns) || columns < 1 || columns > 512) throw new RangeError('columns out of bounds');
  if (!Number.isInteger(rows) || rows < 1 || rows > 512) throw new RangeError('rows out of bounds');
  const next = xorshift32(seed);
  let state = new Uint8Array(columns);
  for (let i = 0; i < columns; i += 1) state[i] = next() & 1;
  state[Math.floor(columns / 2)] = 1;
  const cells = new Uint8Array(columns * rows);
  for (let y = 0; y < rows; y += 1) {
    cells.set(state, y * columns);
    state = evolve(state, rule);
  }
  return Object.freeze({ columns, rows, cells, fingerprint: fnv1a(cells) });
}

// Synthetic perfect tree; counts nodes, not unique packages.
export function dependencyExposure(direct, fanout, depth) {
  if (![direct, fanout, depth].every(Number.isInteger) || direct < 0 || direct > 100 ||
      fanout < 0 || fanout > 10 || depth < 0 || depth > 8) throw new RangeError('parameters out of bounds');
  let total = 0;
  let level = direct;
  for (let n = 0; n <= depth; n += 1) {
    total += level;
    level *= fanout;
  }
  return total;
}
