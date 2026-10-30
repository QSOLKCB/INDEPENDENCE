# v0.7.4 — Real executable Ada/Python conformance

The command below compiles the historical, verified-source Ada CLI in a **new temporary build directory** before running any comparisons. This is a real local execution pathway, not a precomputed or simulated runtime result.

## Scope and authority

The shared source of truth is formal/spec/kernel-v1.json. The Ada CLI calls the Ada Reference_Kernel; the independent Python reference and arithmetic oracle are in formal/python/kernel.py and scripts/run_kernel_conformance.py. The Ada inputs come from the pinned PR #13 snapshots in formal/evidence/spark/pr13/source, whose five source digests and kernel-v1 specification are checked by scripts/verify_spark_evidence_archive.py. The historical SHA is 9900e57f2283c534815657dd6c079d0e966715f4. No existing Ada kernel code is changed.

## Reproduce on a computer with GNAT and GPRbuild

From the repository root:

~~~bash
export PATH="$HOME/opt/edgewalk-spark-toolchain/bin:$PATH"
python3 -m unittest discover -s tests -v

# Fresh real build + 128 valid + 16 rejected fixtures + 6 lexical-invalid:
python3 scripts/build_and_compare_ada.py --samples 128 --output ada-runtime-evidence.json
python3 scripts/verify_ada_runtime_evidence.py ada-runtime-evidence.json

# Full defined domain: 8,881 valid plus 22 invalid = 8,903 CLI processes:
python3 scripts/build_and_compare_ada.py --full --output ada-runtime-evidence-full.json
python3 scripts/verify_ada_runtime_evidence.py ada-runtime-evidence-full.json
~~~

The runner requires gprbuild and gnatmake on PATH, checks their versions, builds using literal argv with shell=False, verifies the resulting executable exists, then invokes it for every selected vector. The CLI must produce **exactly one LF-terminated expected line in raw stdout bytes**, zero exit code and empty stderr. Python universal-newline decoding is explicitly disabled: CR-only and CRLF output are rejected. Invalid fixture and lexical inputs are tested using their original spellings, including based literals.

The result records the complete compiler output and SHA-256 digest, compiler versions, input source hashes, compiled binary SHA-256, deterministic vector digest, seed, case counts, and a previously defined Python/Ada bridge receipt. Neither a stale executable nor a successful Python-only test can substitute for compilation and execution. Any missing compiler, build failure, unexpected output, timeout or disagreement must return nonzero with status FAILED_OR_NOT_RUN and must not issue a passing receipt.

On a successful actual run, the status is LOCAL_BUILD_AND_DIFFERENTIAL_PASSED_UNATTESTED. The offline verifier checks the record's **internal consistency**, not the authenticity of the execution. A malicious person can fabricate a self-consistent report. The separately archived Lean theorems and 21 GNATprove reference checks must not be conflated with verified CLI input handling or proof of arbitrary Python/JavaScript applications.

The v1.1.0 Zenodo research archive should retain the actual local output JSON, exact Git source revision, toolchain information and unresolved scope exclusions.

A request with `--samples 8881` selects every finite valid vector and is **normalised to `FULL_FINITE_SET`** in the output, exactly like `--full`. The offline receipt verifier accepts the resulting full-domain evidence. Smaller sample counts retain `SEEDED_SAMPLE`.

## Byte-preserved actual sample/full run evidence

A later uploaded ZIP, checksum-confirmed with SHA-256 `429b946d083c2b0562450704f924eb3370e5c9a9c62eb81ef5ac90d41a5e2256`, contained the user's **original** 150-case and 8,903-case runtime JSON files. The original JSON members are stored byte-identically in `formal/evidence/ada-runtime/v0.7.4` and verified against the uploaded bytes by Git blob hash. Their provenance distinguishes PR #15 HEAD (sample) from the merged main checkout (full run). The ZIP itself is not committed to Git; retain it for later Zenodo deposit. This does not authenticate the user's execution environment independently.
