# PROPERTY-LAB/1 — Deterministic Generation and Counterexample Shrinking (v0.8)

This lab is a **real first-party browser experiment** with a separate stdlib-only Python verifier. It extends the existing Proof Contracts without modifying their historical evidence, contracts or earlier receipts. Generated input samples are **not** mathematical proof or independently authenticated execution.

## Run

Use the existing manual GitHub Pages workflow after merge, or from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/audit.py --json
python3 -m http.server 8000
```

Open `http://localhost:8000/#property-lab`, choose a nonzero uint32 seed and 1–512 trials, and click **RUN GENERATOR & SHRINKER**. The native browser self-tests also run with the existing **RUN TESTS** button. Export a SHA-256 report on HTTPS or localhost. Check an exported report offline:

```sh
python3 scripts/verify_property_receipt.py /path/to/property-lab-<hash>.json
```

No Node.js, packages, external CSS/JS, network API, tracking, or server-side execution is required by the deployed site.

## What executes

1. **Seeded property generation:** `property/core.js` uses the same first-party xorshift32 PRNG as the automaton. Each of at most 512 cases selects width 1..8, rule 0..255 and a binary row mask. It checks the actual `lab/core.js:evolve()` against an independently written arithmetic oracle with fixed-zero boundaries, also checking that source inputs are unchanged. Exact generated vectors are part of each receipt. The fixed seed and trials reproduce the same JSON.
2. **Fault injection and canonical shrinking:** a separately authored *deliberately faulty* step uses periodic wraparound boundaries. The pinned known-failing starting case is `{width:8,rule:110,mask:255}`. The shrinker checks its witness and enumerates smaller widths, rules and masks in **width, rule, mask** order, replaying the failure for every candidate. It returns `{width:1,rule:4,mask:1}` after checking 10 candidates. This is a minimum in the bounded ordering and domain; it is **not** proof of a production bug, and deliberately generated test cases are not passed off as the injected witness.
3. **Real ownership counterexample:** the existing public `buildAutomaton` returns an `Object.freeze` wrapper that still contains a writable `Uint8Array`. Flipping a cell makes its stored fingerprint stale. An 8×8 witness is independently reproduced and reduced to the smallest permitted 1×1 model, preserving the earlier v0.7 finding.
4. **Opt-in defensive-copy snapshot:** `guardedSnapshot(model)` validates the public model, checks the fingerprint and clones the source cells into private storage. Its `cells` getter returns a fresh copy each time, so mutating a returned typed array cannot alter stored fingerprint consistency. The legacy `buildAutomaton` API and its historical counterexample remain unchanged.

## Evidence and boundaries

`PROPERTY-LAB/1` reports `FINITE_GENERATED_CASES_PASSED`, `INJECTED_MUTANT_COUNTEREXAMPLE`, `LEGACY_MUTABILITY_COUNTEREXAMPLE`, `DEFENSIVE_COPY_CONFIRMED`, and an explicit `NOT_A_FORMAL_PROOF` status. The browser exports `PROPERTY-LAB-RECEIPT/1` with SHA-256 over the exact UTF-8 JSON payload.

The independent `scripts/verify_property_receipt.py` reconstructs the xorshift PRNG vectors, independent Python finite automaton/fingerprint fixtures, the bounded minimum and expected result statuses, and checks exact schema/type and digest. It detects tampered and re-hashed false reports, but **cannot attest a browser actually executed or that its JS implementation is universally correct**.

This does not change, inherit or promote Lean 4's 13 theorem checks, GNATprove's 21 Ada checks, or Ada/Python's 8,903 recorded runtime comparisons. The explicit injected mutant is a teaching case; it is not a discovered production vulnerability.

## Limits and future work

The generated sample covers widths up to eight and at most 512 trials; the existing bounded exhaustive automaton tests separately cover all binary rows of widths 1–8 under all 256 rules. Canonical shrinking is defined by **width,rule,mask** only for the intentionally faulty boundary function and a fixed bounded input space, not arbitrary JavaScript programs. A future phase may add general shrinker combinators, broader seeded program properties, coverage receipts and concrete production bug regressions.
