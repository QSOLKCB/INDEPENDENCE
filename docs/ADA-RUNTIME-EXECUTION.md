# v0.7.4 — Real executable Ada/Python conformance

The command below compiles the historical, verified-source Ada CLI in a **new temporary build directory** before running any comparisons. This is a real local execution pathway, not a precomputed or simulated runtime result.

## Scope and authority

The shared source of truth is formal/spec/kernel-v1.json. The Ada CLI calls the Ada Reference_Kernel; the independent Python reference and arithmetic oracle are in formal/python/kernel.py and scripts/run_kernel_conformance.py. The Ada inputs come from the pinned PR #13 snapshots in formal/evidence/spark/pr13/source, whose five source digests and kernel-v1 specification are checked by scripts/verify_spark_evidence_archive.py. The historical SHA is 9900e57f2283c534815657dd6c079d0e966715f4. No existing Ada kernel code is changed.

## Reproduce on a computer with GNAT and GPRbuild

From the repository root:

~~~bash
export PATH="$HOME/opt/edgewalk-spark-toolchain/bin:$PATH"
python3 -m unittest discover -s tests -v

# Fresh real build + 128 valid + 16 numeric-invalid + 6 lexical-invalid:
python3 scripts/build_and_compare_ada.py --samples 128 --output ada-runtime-evidence.json
python3 scripts/verify_ada_runtime_evidence.py ada-runtime-evidence.json

# Full defined domain: 8,881 valid plus 22 invalid = 8,903 CLI processes:
python3 scripts/build_and_compare_ada.py --full --output ada-runtime-evidence-full.json
python3 scripts/verify_ada_runtime_evidence.py ada-runtime-evidence-full.json
~~~

The runner requires gprbuild and gnatmake on PATH, checks their versions, builds using literal argv with shell=False, verifies the resulting executable exists, then invokes it for every selected vector. The CLI must produce **exactly one LF-terminated expected line**, zero exit code and empty stderr. Invalid numeric and lexical inputs are tested using their original spellings, including based literals.

The result records the complete compiler output and SHA-256 digest, compiler versions, input source hashes, compiled binary SHA-256, deterministic vector digest, seed, case counts, and a previously defined Python/Ada bridge receipt. Neither a stale executable nor a successful Python-only test can substitute for compilation and execution. Any missing compiler, build failure, unexpected output, timeout or disagreement must return nonzero with status FAILED_OR_NOT_RUN and must not issue a passing receipt.

On a successful actual run, the status is LOCAL_BUILD_AND_DIFFERENTIAL_PASSED_UNATTESTED. The offline verifier checks the record's **internal consistency**, not the authenticity of the execution. A malicious person can fabricate a self-consistent report. The separately archived Lean theorems and 21 GNATprove reference checks must not be conflated with verified CLI input handling or proof of arbitrary Python/JavaScript applications.

The v1.1.0 Zenodo research archive should retain the actual local output JSON, exact Git source revision, toolchain information and unresolved scope exclusions.
