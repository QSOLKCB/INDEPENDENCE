# PROOF-CONTRACTS/1 — Verification Scope and Known Counterexample

## Scope

v0.7 records what INDEPENDENCE expects its code to do, what finite domains are checked, and what remains unproved. The machine-readable registry is proof/contracts.json. Its source baseline is the published v0.6.0 release at commit cb1d8686cc7e11997fd7608d2ce52e032d7c0056.

| Contract ID | Executable evidence | Formal status |
| --- | --- | --- |
| AUTOMATA-TRANSITION | BOUNDED_EXHAUSTIVE: 256 rules across all binary rows of widths 1–8; 130,560 input/rule cases and 918,016 checked output cells | NOT_PROVED |
| DEPENDENCY-SUM | FINITE_CASES: 462 small input triples plus maximal allowed triple, with independent BigInt geometric-sum reference | NOT_PROVED |
| AUTOMATA-REPLAY | FINITE_CASES: 3 seeds × 4 rules × 3 sizes, bit-exact replay and BigInt FNV-1a reference | NOT_PROVED |
| SHA-FORMAT | FINITE_CASES: 12 type, length, case and hexadecimal boundary cases | NOT_PROVED |
| FINGERPRINT-IMMUTABILITY | COUNTEREXAMPLE: returned cells remain mutable despite frozen containing object | NOT_PROVED |
| RECEIPT-AUTHENTICITY | PENDING: hashes do not attest who ran a browser | NOT_PROVED |
| LEAN-TRANSITION | PENDING: no Lean model or theorem checked yet | NOT_PROVED |
| SPARK-TRANSITION | PENDING: no SPARK/Ada implementation or GNATprove obligation checked yet | NOT_PROVED |

The first four checks run actual first-party JavaScript functions against independently implemented reference calculations. The fifth records a real contract weakness. These are neither proof of arbitrary untested inputs nor authenticated execution.

## Reproduced mutable-state counterexample

Calling buildAutomaton(30,314159,8,8) produces a frozen wrapper holding a mutable Uint8Array. The first cell can be flipped from its original bit. The stored FNV-1a fingerprint remains 6d8aa545; the recomputed fingerprint of the modified cells is eb95c744.

The API's immutability guarantee is therefore NOT established. v0.7 documents the counterexample without silently changing production API semantics. A later release must explicitly decide whether this is an immutability requirement, caller-owned mutation, or a different contract.

## Run

    python3 -m unittest discover -s tests -v
    python3 scripts/check_proof_contracts.py --json
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Visit http://localhost:8000/#proof and click RUN BOUNDED CONTRACT CHECKS. The dashboard does not pre-populate fabricated results. It runs checks in the browser and shows formal Lean/SPARK statuses as NOT RUN. Export requires WebCrypto on HTTPS or localhost.

Verify the exported receipt:

    python3 scripts/verify_proof_receipt.py /path/to/proof-contracts-<hash>.json --json

The offline Python verifier checks exact payload SHA-256, fixed expected classifications and counts, strict JSON and status claims. It CANNOT attest that a real browser executed them; an author could forge a self-consistent envelope. The registry verifier checks declared metadata and named source-symbol presence, not source semantics.

## Trust boundaries

- An exhaustive finite-domain observation is not a theorem over unbounded programs.
- A Lean theorem would establish a model property under assumptions, not automatically prove browser JavaScript equivalent.
- A SPARK/Ada reference must have its own checked contracts, and cross-language conformance still needs explicit evidence.
- The existing regex/static filename audit is scoped, not a comprehensive SAST or security certification.
- Every new formal success needs the actual proof artifact, toolchain, assumptions, command log and full source SHA.

See docs/FORMAL-ROADMAP.md for the planned v0.8–v1.1 formalization programme.
