# v1.0.2 — Rocq Independent Semantic Verification

## Purpose

The baseline `AUTOMATA4/1` was restricted to four binary cells and 256
elementary rules. v1.0.2 adds `AUTOMATA-LIST/1`: a mathematically independent
finite-list model covering **any nonnegative finite width**. It is not a new
web feature and does not change `lab/core.js` or the published site.

## Model definitions

- `neighborhood left center right = 4*left+2*center+right`;
  zeros outside the row.
- `arithmetic_cell`: binary rule bit selected by integer division.
- `table_cell`: a separately enumerated 8-row explicit truth table.
- `arithmetic_step` and `table_step`: independent recursive row walkers,
  both use only the **pre-transition** row, so updates are simultaneous.
- `xor_step`: a structurally recursive Rule 90 reference.
- `step4`: specialised four-cell model with zero exteriors.

The independent `table_cell` still uses the same elementary rule-number
interpretation: the models are independently coded mathematical evaluators,
not independent formal specifications of the *meaning* of Wolfram rule
numbering.

## Fifteen mathematical proof obligations

1. `neighborhood_bounded`
2. `arithmetic_table_cell`
3. `arbitrary_width_length`
4. `arbitrary_width_table_length`
5. `independent_models_equivalent`
6. `rule_zero_cell`
7. `rule_255_cell`
8. `rule_zero_all_widths`
9. `rule_255_all_widths`
10. `rule90_cell_xor`
11. `rule90_all_widths`
12. `automata4_model_bridge`
13. `zero_boundary_empty`
14. `zero_boundary_singleton`
15. `rule90_known_four` (concrete example)

All obligations have actual Rocq source proofs and named
`Print Assumptions` statements. Source presence itself is **NOT** a
kernel-checked result.

## Run on the exact toolchain

Pinned **Rocq 9.2.0** ([official 9.2 documentation](https://rocq-prover.org/doc/v9.2/refman/index.html)).
No Rocq tooling is part of the website or its client asset allowlist.

```bash
python3 scripts/check_rocq_semantics.py --output rocq-static.json
rocq --version
python3 scripts/check_rocq_semantics.py --require-rocq --output rocq-executed.json
```

The last invocation requires version 9.2.0, uses `rocq compile -q` against
freshly copied `Automata.v`, detects a generated nonempty `.vo`, checks
the compiler exit code and fifteen closed assumption audits, and records
the compiled proof SHA-256, source SHA-256, tool version and raw stdout
fingerprint. It fails closed on `Admitted`, extra axioms, wrong version,
missing tool, source drift or an absent `.vo`. If the toolchain is absent,
the status is `NOT_RUN` and `--require-rocq` returns nonzero.

The CI default intentionally uses *static-only* `--output`: it can check
the proof file's reviewed Git blob SHA, theorem/assumption audit inventory,
prohibited proof holes and an independently implemented 4,096-case Python
table-model bridge. Those are checks, not actual Rocq kernel compilation.

## Scope and limits

A successful kernel report proves the listed Rocq **model-level** properties
for arbitrary finite Boolean lists and any valid rule index. The
`automata4_model_bridge` theorem equates two Rocq descriptions of a
four-cell step, **not** Rocq with executable JavaScript.

The finite bridge checks all 256 rule bytes against all 16 four-cell
inputs and further enumerates Rules 0, 90 and 255 for lengths 0–8; it is
not a proof for general JavaScript array widths, memory ownership,
input validity or external toolchain identity. Compiler receipts are not
independent execution attestations.

A separate refinement argument is needed before calling production JS
formally verified; the previously documented mutable `Uint8Array`
fingerprint issue and browser-receipt authenticity boundary are unchanged.

Existing Lean/SPARK local tool output must be archived separately with
its exact source commit and checksum. No proof summary may silently
promote those finite/runtime results into arbitrary-width implementation
correctness.
