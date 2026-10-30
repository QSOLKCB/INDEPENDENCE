# v0.7.3 — Lean 4 Mathematical Foundation

**State as authored:** SOURCE AVAILABLE; KERNEL CHECK NOT RUN in the author's
execution environment. This is a reproducible proof *candidate*, not a claim
that Lean has accepted 13 theorems. There is no Lean or elan executable
available here, and download access is blocked.

## Trust boundary

- Lean version is **exactly** `leanprover/lean4:v4.35.0` in the root
  `lean-toolchain` file. Do not substitute `stable` or a floating release.
- `formal/lean/FiniteFoundation.lean` imports only the Lean distribution
  (`import Lean`). No Mathlib, npm, pip or application runtime dependencies.
- Proof execution uses `lean --trust=0 formal/lean/FiniteFoundation.lean`.
  Source uses `decide +kernel` for finite closed propositions and `omega`
  for natural-number ordering lemmas; no `native_decide`.
- Every theorem has a `#print axioms` command. The runner fails closed on
  unexpected/missing statements, tool version, tool exit code, or axiom output.
  The only permitted transitive axioms are the standard
  `propext`, `Quot.sound`, and `Classical.choice`.
- The Python source audit detects some common proof escapes and checks a
  fixed theorem inventory. It is **not** Lean compilation or a proof itself.
- A successful Lean run proves statements about **this Lean model**, subject
  to the toolchain and its imports, NOT the existing Ada, Python, JS, browser,
  or Penrose geometry.

## Exactly what is proposed for the kernel to check

| Group | Theorem obligations | Scope |
| --- | --- | --- |
| CRT | `crt_left_inverse`, `crt_right_inverse` | Explicit isomorphism between Fin 6 and Fin 2 × Fin 3; coprime 2,3 only |
| GF(2) | `gf2_add_comm`, `gf2_add_assoc`, `gf2_add_self`, `gf2_mul_comm`, `gf2_left_distrib` | Bool-based XOR/AND |
| Cyclic ternary phase | `phase_add_comm`, `phase_add_assoc`, `phase_zero` | Addition modulo 3, no quantum physics claim |
| Monomial degree-lex | `monomial_irrefl`, `monomial_trans`, `monomial_translate` | Strict degree-lex properties on pairs of natural exponents |

The monomial relation's full well-foundedness, totality/trichotomy, and
admissibility as a complete monomial order are **outstanding**. CRT for
arbitrary coprime moduli is also outstanding. Elementary automaton
semantics and a formal relation between Lean and Ada remain outstanding.

## How to check using a trusted local installation

Install the official Lean version manager (`elan`) separately, then from
the repository root verify the pinned toolchain:

    cat lean-toolchain
    lean --version
    python3 scripts/check_lean_foundation.py

Execute actual Lean kernel checking and obtain an evidence report:

    python3 scripts/check_lean_foundation.py --require-checked --output lean-evidence.json

Or inspect the raw command:

    lean --trust=0 formal/lean/FiniteFoundation.lean

On a missing or incompatible toolchain `--require-checked` exits nonzero,
the proof status is NOT_RUN or VERSION_MISMATCH, and **no theorem is
represented as successfully checked**. Real compilation errors, timeouts,
and unwanted axioms also block success. Retain the raw output alongside the
exact commit SHA and source digest when preparing a v1.1.0 Zenodo archive.

The output is a local, self-reported verification record, not a signed
third-party attestation. The fact that an executable calls itself Lean is
not independent proof of the executable's provenance. Verify the pinned
toolchain's binary source and version separately.

## Regression checks without Lean

    python3 -m unittest discover -s tests -v
    python3 scripts/check_lean_foundation.py
    python3 scripts/audit.py --json

These checks are available through the Python standard library and should
continue to pass without any Lean installation.

## Explicit next obligations

1. Execute this pinned file with real Lean and resolve any elaboration,
   typechecking, kernel, or proof-audit errors before a PROVED claim.
2. Independently inspect the exact theorem statements to ensure they match
   intended English semantics; a proved incorrect specification is still an
   incorrect specification.
3. Decide whether to prove full degree-lex well-foundedness and general CRT.
4. Keep the formal SPARK/Ada, independent Python conformance and production
   JavaScript obligations separate. Lean proof is never automatic transfer.
