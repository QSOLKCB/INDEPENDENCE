# v0.7.2 — Proof-Conformance Bridge

The shared authority is [kernel-v1.json](../formal/spec/kernel-v1.json), **not Ada
source and not Python source**. Both implementations must be checked
separately. A SPARK proof of the Ada kernel does not prove Python conforms.

## What the bridge tests

The independent Python reference is in formal/python/kernel.py. A separately
written arithmetic oracle in scripts/run_kernel_conformance.py evaluates the
same versioned semantics using different calculations.

The finite sweep covers **8,881 valid cases**:
- ADDR: all widths 1..16, rows 0..15 and valid columns: 2,176 cases.
- DECODE: all valid positions under those widths: 2,176 cases.
- PARITY_ADD and PARITY_MUL: 4 cases each, total 8.
- PHASE_ADD: all nine pairs in Z/3Z.
- EDGE_VALID: counts 2..16 and endpoints 0..15: 3,840 cases.
- EDGE_STEP: counts 2..8, distinct endpoints and all parity inputs: 672 cases.

A further 16 negative/invalid cases are compared. Values outside these
finite domains are NOT exhaustively tested. A bounded exhaustive check is
not a mathematical proof.

The optional Ada CLI differential runner actually invokes the supplied
executable for a seeded deterministic selection (default 128 valid cases,
including all seven operations), plus all 16 numeric-invalid cases and six lexical-invalid Ada strings, or any larger
requested finite prefix/sample. It fails on a mismatch, abnormal exit, stderr,
or timeout. Missing executable means NOT_RUN, not a fabricated match.

## Commands

Using Python 3 stdlib only:

    python3 -m unittest discover -s tests -v
    python3 scripts/run_kernel_conformance.py --receipt conformance-receipt.json
    python3 scripts/verify_kernel_receipt.py conformance-receipt.json

In an environment with matching GNAT/gprbuild tools, build the v0.7.1 CLI:

    gprbuild -P formal/spark/cli.gpr

Then run a **real** differential comparison against the executable:

    python3 scripts/run_kernel_conformance.py --ada-cli formal/spark/bin/reference_cli --ada-cases 128 --receipt ada-conformance.json

For the entire finite set, specify `--ada-cases 8881`, although this
invokes a new Ada process for each valid case and may take longer.

Actual SPARK proof verification is separate:

    python3 scripts/check_spark_reference.py --require-proved --output spark-evidence.json

No code or report is permitted to promote an unexecuted theorem or an unrun
GNATprove contract to a passing category. The strict command must fail when
the prover is absent or obligations remain unresolved.

## Evidence classes

| Field | What it means |
| --- | --- |
| mathematical_proof: NOT_RUN | No kernel-checked Lean theorem recorded |
| ada_contracts: NOT_RUN | No GNATprove discharge recorded by this bridge |
| python_conformance: FINITE_EXHAUSTIVE_TESTED | Independent Python implementation matched the oracle across 8,881 valid + 16 negative fixtures |
| ada_cli_conformance: NOT_RUN | No actual Ada executable run in the current environment |
| ada_cli_conformance: ADA_CLI_TESTED_UNATTESTED | A supplied executable returned the expected outputs for the recorded sample; the binary was not independently attested |
| unresolved | Obligations explicitly not covered, including all existing Python/JS application behaviour |

The receipt is SHA-256 over exact UTF-8 payload bytes, with source/spec
hashes and fixed run metadata. The offline verifier recomputes expected Python
results, finite counts and selected Ada vectors. **A self-consistent receipt is
forgeable and does not independently attest the test execution or prove that
the Ada binary originated from the reviewed SPARK source.**

## Exclusions

Rectangular addressing is not CRT. In-range distinct endpoints are not
membership in the actual Penrose adjacency graph. Modulo-3 cyclic phase
addition is not a theorem about quantum qutrit dynamics. No claim is made
about production JS, arbitrary Python application functions, signed release
provenance, or a complete formal verification.

The v1.1.0 Zenodo research archive should preserve the distinct statuses,
exact commits, tool versions, raw logs and unresolved obligations rather than
collapsing them into a single green badge.

The separate lexical-negative suite includes Ada based numeric literals (`2#1#`), signs and underscores. Inputs must be ASCII decimal digits only before `Natural'Value` parses them; these additional cases are included in the Ada CLI vector receipt and verified offline.

## v0.7.4 — Executable compiled-Ada bridge

scripts/build_and_compare_ada.py compiles the source snapshot tied to PR #13 GNATprove evidence from scratch in an isolated temporary directory and invokes the actual Ada executable. Run with --samples 128 for 150 total comparisons (128 valid + 22 invalid), or --full for 8,903 total comparisons. The existing Python bridge independently checks the oracle and emits its original versioned receipt. The CLI output gate now demands exactly one expected LF-terminated line, no stderr and exit code 0.

scripts/verify_ada_runtime_evidence.py verifies the reported build/run record and the embedded Python/Ada receipt against the pinned source archive. This is internal consistency, **not independent attestation**. See [ADA-RUNTIME-EXECUTION.md](ADA-RUNTIME-EXECUTION.md).
