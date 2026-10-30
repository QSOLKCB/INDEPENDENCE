# v0.7.1 — SPARK Ada Reference Kernel

This is a narrowly scoped **reference implementation**, not a declaration of
formally proved JavaScript or Python. The versioned authority is
`formal/spec/kernel-v1.json`. The package `Reference_Kernel` is marked
`SPARK_Mode => On`; the input/output CLI is explicitly outside that proof boundary.

Functions include rectangular address + decode (width 1..16, rows 0..15),
GF(2) parity addition and multiplication, cyclic modulo-3 phase addition,
endpoint validation (distinct, in-range endpoints), and a parity edge step
requiring validated endpoints.

**Limits:** Address is not Chinese remainder bijection. Edge validity is not
adjacency in an arbitrary graph or Penrose patch. Modulo-3 phase closure is
not a quantum qutrit proof. Lean theorems and the actual production Python/
JavaScript semantics remain separate obligations.

## Verification / GNATprove

The repository's ordinary Python tests validate files, versioned specs,
absence of certain proof-escape pragmas, and fail-closed status reporting.
They DO NOT compile Ada or prove the bodies.

To run SPARK proof checks in an environment with a compatible GNATprove:

    python3 scripts/check_spark_reference.py --prove --output spark-evidence.json

Strict blocking version:

    python3 scripts/check_spark_reference.py --require-proved --output spark-evidence.json

The runner uses --mode=all, --checks-as-errors=on, --warnings=error,
--report=all, --level=2, and selects the reference kernel unit. It records
tool version, command, exit code and output. An exit code alone is NOT treated
as proof if the tool reports unresolved or missing checks. **Inspect actual
GNATprove output before claiming verified contracts**; a checked proof is
conditional on explicit preconditions and tool semantics. No unapproved
Assume, Skip_Proof or annotated justifications are allowed.

To compile the non-SPARK CLI with a matching GNAT toolchain:

    gprbuild -P formal/spark/cli.gpr

The CLI accepts ADDR, DECODE, PARITY_ADD, PARITY_MUL, PHASE_ADD,
EDGE_VALID and EDGE_STEP plus numeric arguments, returns OK:<value> or
ERR:INVALID. Input checks are outside the verified kernel and must be
separately tested (including modular-range validation).

Current recorded environment (development): GNAT/GNATprove unavailable,
so **ADA_CONTRACT_VERIFIED remains NOT_RUN** and any obligations remain
unproved until real tool output is supplied.

The next phase, v0.7.2, adds a separate Python/Ada conformance bridge using
fixed versioned input/output semantics. Ada proof is not evidence that Python
or JavaScript conforms.

## Real-toolchain GPR project syntax correction

An initial real GNATprove invocation stopped before any Ada contracts were
analysed because the `Object_Dir` project attribute was written as a
one-element list. GPR defines `Object_Dir` and `Exec_Dir` as scalar
directory attributes, unlike list-valued `Source_Dirs` and `Main`.

Both project files now use quoted scalar directory names. They also request
`Create_Missing_Dirs` for the generated `obj` and `bin` directories.
The offline source gate and regression tests check these exact declarations
before the actual prover runs. These checks are limited GPR syntax guards,
**not** substitutes for GPRbuild or GNATprove execution.

The previously recorded `FAILED_OR_UNPROVED` result was a project-parser
error, not a discharged or failed mathematical proof obligation. On a trusted
toolchain, rerun from the repository root:

    export PATH="$HOME/opt/edgewalk-spark-toolchain/bin:$PATH"
    python3 scripts/check_spark_reference.py --require-proved --output spark-evidence.json

Do not mark Ada contracts proved until that command's actual GNATprove
output reports the proof outcome and all obligations are resolved.

## Reported successful GNATprove run after PR #13

The user checked out PR #13 HEAD `9900e57f2283c534815657dd6c079d0e966715f4`, used their existing GNATprove FSF 16.1.0 toolchain, and supplied a report of **21/21 checks proved**, exit code **0**, and **186 passing Python unittest methods**. The record is preserved under `formal/evidence/spark/pr13` with all five analyzed source/project SHA-256 hashes. It supersedes the earlier parser-error state **for the reported historical revision**.

This is user-provided local execution evidence, not an independently witnessed proof run. It covers GNATprove's specified Ada reference-kernel proof obligations; **the CLI remains outside the SPARK proof scope**, and existing Python/JS conformance still needs separate differential execution. See `formal/evidence/spark/pr13/README.md`.
