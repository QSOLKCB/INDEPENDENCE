# SPARK Ada kernel verification — PR #13 source

This directory preserves the **reported successful local GNATprove run** and the user's Python regression-suite summary from the terminal output shared on 2026-10-31 (Australia/Adelaide).

The user checked out **PR #13 HEAD** `9900e57f2283c534815657dd6c079d0e966715f4`, which was subsequently merged to `main` at `e52578ee630d619b7c0aa54b47ef05f997f80741`. This distinction matters: the evidence was executed on the PR HEAD, not on the later merge commit.

## Reported results

- **GNATprove:** `GNATPROVE_REPORTED_DISCHARGED`; **all 21 checks proved**, exit code 0.
- **Python unit tests:** **186/186 passed** on the local PR checkout.
- **Kernel source:** `formal/spark/reference_kernel.ads` and `reference_kernel.adb`, with five actual source/project SHA-256 values in the manifest.
- **Toolchain:** GNATprove FSF 16.1.0, Why3 1.8.2+git, Alt-Ergo 2.6.1, cvc5 1.3.2, Z3 4.15.4.
- **Proof-output SHA-256:** `834ff4418b98e36e011900c7c5a6897776d2db5f12d7874011a64a474a268fab`. Its bytes were transcribed from the pasted `proof_output` field.
- **Strict command:** `gnatprove -P kernel.gpr -u reference_kernel.adb --mode=all --checks-as-errors=on --warnings=error --report=all --level=2`

## Provenance and limitations

**The user's original `spark-evidence.json` was not separately uploaded.** The archived `spark-evidence.json` was reconstructed from the complete visible JSON fields provided in chat, preserving the reported `proof_output` and its SHA-256. Its total-file byte identity with the user's local original is **not independently confirmed**. It is user-reported local execution evidence, **not independent execution attestation**.

The tool output supports the 21 stated GNATprove kernel checks under their conditions; it does **not** establish that the Ada CLI was compiled or that Python and Ada outputs agree, nor that the website is formally proved. No changes to the analyzed Ada sources are made by this archive.

Run the stdlib integrity gate after checkout:

```bash
python3 scripts/verify_spark_evidence_archive.py
python3 -m unittest discover -s tests -v
```

The archive verifier validates claimed source identifiers, reported digest and outcome consistency; it cannot rerun GNATprove on its own. A new GNATprove execution, explicit CLI compilation and Python/Ada comparison are separate future steps.

## Exact archived inputs

The `source/` directory contains immutable copies of the five Ada/GPR input files and `kernel-v1.json` fetched from PR #13 HEAD `9900e57f2283c534815657dd6c079d0e966715f4`. The manifest stores each Ada/GPR file's reported SHA-256 and the canonical specification's Git blob ID. The archive verifier checks these **snapshots**, not the moving working tree, so future edits to `formal/spark/` won't break the historical verification record.

No SPARK source code is changed by adding these archival copies. Their retention does not make the user-provided terminal report independently attested.
