# Formal Verification Roadmap — Lean 4, SPARK/Ada, Zenodo (planned)

**Everything beyond v0.7 is a plan, not a verified proof result.**

## v0.7.0 — Proof Contracts (implemented)

Machine-readable obligation registry, deterministic bounded checks against real first-party JavaScript, explicit counterexample, strict Python stdlib registry/receipt verifiers. All formal statuses NOT_PROVED; no Lean or GNATprove artifact exists yet.

## v0.8.0 — Generative and exhaustive verification (planned)

Add deterministic property generators with recorded seeds and minimal failing inputs, boundary/invalid-input testing, differential Python/JavaScript reference vectors, and controlled network failure simulations for the public ledger. Resolve the mutable typed-array/fingerprint contract through a reviewed API choice, not a silent behavioural change.

## v0.9.0 — Lean 4 and SPARK/Ada (executable model added; new proofs pending local tools)

A new four-cell `AUTOMATA4/1` formal experiment now has six Lean theorem obligations, an exact SPARK/Ada reference kernel, independent 4,096-case Python and developer Node/JavaScript vectors, a fresh Ada CLI build-and-test runner and strict, per-stage status reporting. The earlier 13 Lean theorem checks, 21 SPARK obligations and 8,903 Ada/Python comparisons remain separate historical evidence. **No new v0.9 proof is claimed discharged until the new toolchain reports are supplied.** See `docs/AUTOMATA-FORMAL.md`.

The original wider programme remains explicit:

1. Review a mathematical specification of elementary automaton transitions with fixed-zero boundaries and 0..255 rule indices.
2. Prove selected properties in Lean 4, record exact tool version, complete source, theorem statements, kernel-checked log and remaining assumptions. Unreviewed sorry, custom axioms or holes are unresolved.
3. Build a small executable SPARK/Ada reference with explicit pre/postconditions and GNATprove analysis. Unreviewed Assume pragmas and undischarged obligations remain visible.
4. Produce common input/output vectors and compare Lean reference, SPARK executable and real production JavaScript. Differential tests are not automatically a formal refinement proof.
5. Document integer and bit-vector semantics of JavaScript, Lean and Ada; do not equate their implicit numeric behaviour without evidence.
6. Keep all proof toolchains optional development tooling, never a GitHub Pages runtime dependency.

## v1.0.0 — Browser and deployment verification (planned)

Run actual browser journeys, CSP/privacy and asset checks, accessibility/layout testing, malformed-receipt tests and fault injections against controlled fake GitHub responses. Record actual versions, commands, source SHA and limitations. Mock DOM results are not live-browser results.

## v1.1.0 — Zenodo formalization of the repository (planned)

Only after substantive evidence exists, assemble a version-pinned archive with exact commit and tag; mathematical specs; Lean code and tool logs; SPARK/Ada sources, GNATprove output and unresolved obligations; differential conformance vectors; Python/browser tests; reproducibility commands; source and evidence SHA-256 manifest; and a candid report. Supply Zenodo metadata and a DOI only when published. A partial proof package must be labelled partial, not absolute correctness.

## Priority risk register

| Risk | Priority | Required disposition |
| --- | --- | --- |
| Mutable returned cells cause stale fingerprint | P1 | Clarify and test intended public API semantics |
| Model-to-JavaScript semantic gap | P1 | Cross-language vectors and explicit translation assumptions |
| Receipt digest is not execution attestation | P1 | Preserve explicit provenance limitations |
| Pattern-based audit misses unknown syntax classes | P2 | Adversarial fixtures; bounded claims |
| Formal tooling causes runtime dependency bloat | P2 | Strict development/runtime separation |

Proof statuses belong to exact versioned artefacts. Human review and a fresh Git HEAD remain mandatory.

## v0.7.1 / v0.7.2 accelerated foundation

The scoped SPARK/Ada kernel precedes the larger v0.9 Lean+SPARK proof laboratory. v0.7.1 introduces contracts and the optional actual GNATprove runner but never asserts discharged proofs without recorded output. v0.7.2 will introduce an independent Python oracle, bounded finite test vectors and an Ada CLI conformance bridge, reported separately from mathematical and Ada contract proof. The initial implementation deliberately does NOT prove CRT, monomial orders, quasicrystal adjacency, or production Python/JS.

## v0.7.2 — Conformance bridge, independent of proofs

A new Python reference and separately coded oracle now enable practical exhaustive finite checks. Ada CLI differential comparisons remain an optional **actual execution** gate when a GNAT binary exists. No Lean mathematical theorem, GNATprove contract or production Python/JS correctness claim is inferred from the reference comparison. Versioned receipts retain pending fields for the v1.1.0 formalization.

## v0.7.3 — Lean 4 Mathematical Foundation (pending actual compiler run)

A pinned, no-Mathlib Lean proof source and fail-closed stdlib kernel runner cover specific finite CRT (2,3), GF(2), cyclic phase and degree-lex properties. This release prepares but does not automatically establish kernel-checked theorems. General CRT, monomial well-foundedness/totality and correspondence with existing Ada/Python/JS implementations remain outstanding. Execute the locked Lean toolchain and preserve the actual output before the v1.1.0 formalization.

## v0.7.3 Lean evidence preservation (reported successful run)

After the v0.7.3 CRT-right-inverse correction merged in PR #11, the user supplied a terminal transcript reporting Lean 4.35.0 exit 0, `KERNEL_CHECKED`, 13 theorem axiom audits, no `sorryAx`, and 169 passing Python tests. A self-contained copy of the specific historical Lean source, toolchain pin, recovered JSON report and a provenance manifest is archived under `formal/evidence/lean/v0.7.3` for the proposed v1.1.0 Zenodo package. The evidence source is a user-reported local run; the original file was not uploaded and byte-identical provenance is not independently verified. This record proves neither Ada contract discharge nor Python/JS conformance.
