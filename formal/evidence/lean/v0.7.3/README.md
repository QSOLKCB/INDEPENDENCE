# Lean 4 proof evidence — v0.7.3 (preserved)

This directory preserves the user's **reported successful local Lean 4 kernel check** for the 13 theorem statements in `formal/lean/FiniteFoundation.lean`. The report was recovered from the complete JSON block printed in a user-provided terminal transcript; the **original `lean-evidence.json` file was not uploaded**. Therefore this archive does not claim byte-for-byte verification against that original file. The terminal's JSON was reinserted without changing its visible formatting (with a final newline).

## Provenance and status

- Repository: QSOLKCB/INDEPENDENCE
- **Execution source commit:** `68351489e8bbbb879efdcac19d02869124fcf724` (PR #11 merge, reported local checkout `main`).
- Proof source path: `formal/lean/FiniteFoundation.lean`
- Proof source SHA-256: `0a71bba7fa1d8e81a73051c9c5e508126ba97242bf88537d2e55779019e2756d`
- Lean toolchain pin: `leanprover/lean4:v4.35.0`
- Reported Lean version: `Lean (version 4.35.0, x86_64-unknown-linux-gnu, commit eb6cafb7290e8bd5f2937522d8d804f58f02bafc, Release)`
- Reported command: `lean --trust=0 formal/lean/FiniteFoundation.lean`
- Reported exit code: **0**; reported kernel check: **KERNEL_CHECKED**.
- Reported Python unittest suite: **169 tests, OK**.
- Theorem/axiom audit: **13/13**, no `sorryAx`, standard `propext` and `Quot.sound` for three degree-lex theorems.
- Recovered evidence SHA-256: `ef3edf6cbfb7ac0b02ca6c30e3c9bfd3b21e89382f3ec0436f31093c5e4355a7`
- Raw Lean output SHA-256: `4a7103d532ffc078e714882184b74fe86ea53683e3147d64f0c7ac0f8b8239ca`
- Original uploaded terminal transcript SHA-256: `c3e9cd181dfe079205db5070f14de106b0e7594349718467bbd0b809b0491627`

This report is **user-supplied local execution evidence, not independently authenticated tool execution**. Hashes establish bytes and consistency, not authorship. Never use this record to assert that Ada contracts were discharged or that Python/JavaScript implementations were proved correct.

## Reproduction against exact historical source

```sh
git checkout 68351489e8bbbb879efdcac19d02869124fcf724
cat lean-toolchain
python3 -m unittest discover -s tests -v
python3 scripts/check_lean_foundation.py --require-checked --output lean-evidence.json
sha256sum formal/lean/FiniteFoundation.lean
```

The exact archived source revision should be compared to this report. A rerun may produce differing non-semantic log/version metadata. To independently verify a future publication package, retain the raw log, `lean-toolchain`, toolchain installation provenance, and exact tagged source.

See `manifest.json` for versioned machine-readable metadata. The subsequent archive-preservation PR/commit does **not** replace the historical execution source commit.
