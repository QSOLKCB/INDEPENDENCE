# INDEPENDENCE v1.1.0 — Formalisation of Independent Software Claims
**Subtitle:** Mathematical Proof, Bounded Conformance, Evidence Custody and the Limits of a Checksum

**Author:** Trent Slade, QSOL-IMC, independent researcher, Adelaide, Australia.  
**Status:** Versioned research report; proposed v1.1.0, not peer-reviewed journal publication.  
**Repository:** https://github.com/QSOLKCB/INDEPENDENCE  
**User-supplied Zenodo identifier:** https://doi.org/10.5281/zenodo.23816739 — the identifier was reportedly minted; final public record metadata/publication were not independently confirmed.  
**Baseline source commit:** `065cc1f1015d3e2faa4c1257fa7efa32f2ca2395` (post-Rocq-fix merge). Record the eventual **v1.1.0 release tag SHA separately**, after the release exists.

## Abstract

This report treats INDEPENDENCE as a bounded, falsifiable case study of software independence and formal-methods evidence, **not** proof that first-party software is categorically faster, safer, smaller or universally correct. Its elementary cellular-automaton reference specifies four binary cells, all 256 rule bytes, simultaneous updates and fixed-zero exterior cells, yielding a canonical 4,096-vector finite corpus. Uploaded, byte-preserved receipts report six Lean 4 kernel-checked mathematical model theorem statements with empty axiom audits, ten GNATprove-discharged conditions on a SPARK-mode Ada kernel, 4,096 fresh Ada and production-JavaScript executable comparisons each, ten invalid Ada CLI cases, and fifteen Rocq 9.2 kernel-checked theorem/example obligations concerning a mathematical Boolean-list model of arbitrary finite width. Historical Chromium/Firefox receipts record 92 passing assertions across ordinary, locally injected failure and narrow-window scenarios. Two **original** uploaded proof archives are retained exactly, with immutable SHA-256 fingerprints and an offline fail-closed verification gate. This report separates model theorems, contract discharge, finite executable observations, local browser observations and independently verified **bytes**. None establishes formal refinement of production JavaScript, remote execution attestation, general security certification, WCAG compliance or continuous CDN correctness.

**Keywords:** formal verification, reproducibility, elementary cellular automata, Lean 4, SPARK/Ada, GNATprove, Rocq/Coq, source provenance, finite conformance, first-party software, evidence trust boundaries.

## 1. The actual argument

A dependency is not a bug. Removing a dependency is not a theorem. A checksum is not an eyewitness. A formal theorem is not a production incident report. The useful question is whether each engineering claim has an exact subject, an independently understandable specification, reproducible method, original evidence, and a declared failure condition.

We distinguish five propositions that must **never** be exchanged for one another:

1. **Byte identity:** a given blob equals the bytes named by a pinned digest.
2. **Mathematical proof:** a proof kernel accepted a proposition under its model and assumptions.
3. **Contract discharge:** the named program analysis reported the selected verification conditions proved.
4. **Bounded executable conformance:** an actual implementation matched a reference on an enumerated finite domain.
5. **Operational observation:** a particular browser/HTTP exercise reported passing under specific timing and configuration.

The scientific merit is maintaining these boundaries even when it makes the headline less impressive.

## 2. Reference semantics

The canonical authority is `formal/spec/automata4-v1.json` (`INDEPENDENCE-AUTOMATA4-SPEC/1`). Four cells are Boolean values, interpreted left-to-right; exterior neighbours have value zero. For rule `r` in `[0,255]`, and Boolean neighbours `(l,c,t)`, the conventional rule-bit index is:

```text
index(l,c,t) = 4*l + 2*c + t
cell(r,l,c,t) = (r // (2**index(l,c,t))) % 2
```

All next-state cells are calculated from the **pre-step** row. There are 256 rule bytes and 16 four-cell rows: **4,096** vectors. The reference corpus digest is `f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635`. The original versioned specification's `NOT_RUN` defaults remain unchanged; later executed receipts state their own scoped outcomes.

The `AUTOMATA-LIST/1` Rocq model generalises the **mathematical function** to any finite Boolean-list length, including the empty and singleton cases. It separately defines an arithmetic rule-bit evaluator, an explicit eight-pattern table and two structurally recursive row transitions. They share the **same agreed rule numbering**, so independent coding of the mathematical evaluator is not independent empirical discovery or proof of production-code refinement.

## 3. Evidence summary

| Evidence class | What the uploaded record reports | What it does **not** show |
| --- | --- | --- |
| Lean 4.35.0 | **6/6** width-four model theorems, `KERNEL_CHECKED`, exit 0, empty dependency audits | Correctness of executable JavaScript or Ada |
| GNATprove / SPARK | **10/10** generated conditions discharged, exit 0 | Whole-site or arbitrary Ada CLI input/output proof |
| Fresh Ada CLI | **4,096** reference-matching valid cases and **10** invalid CLI cases | Universal correctness or an Ada-to-model refinement proof |
| First-party JavaScript | **4,096** canonical width-four cases compared with actual `lab/core.js:evolve` | All row widths, aliasing, exceptions, browser implementations |
| Rocq 9.2 | **15/15** mathematical theorem/example obligations, `KERNEL_CHECKED`, 15 closed assumption audits | Production JavaScript refinement, third-party execution attestation |
| Historical Chromium/Firefox | **92/92** assertions reported passing in the original PR workflow | Live deployment, physical 390px device, WCAG audit or continuous availability |
| Two uploaded proof archives | **13/13** internal checksum entries and both original tarball digests verified | Independent proof of who generated or ran the receipts |

### 3.1 Lean obligations

Source: `formal/lean/AutomataReference.lean`; SHA-256 `74cb8349ba99feae805a31b74931cbb8da0d98e2020bb738da95d42198f16b98`. The six model theorem names are `pattern_bounded`, `rule_zero_cell`, `rule_all_cell`, `rule_zero_row`, `rule_all_row`, and `rule90_known_row`. The known Rule-90 example is `0010 → 0101`. The preserved command was `lean --trust=0 formal/lean/AutomataReference.lean`, with six empty named axiom-audit lists and exit 0. These are the **specified width-four mathematical propositions**, not universal production-program correctness.

### 3.2 SPARK contract discharge

The standalone `formal/spark/automata_reference.ads/.adb` kernel has contracts for `Neighborhood`, `Cell` and `Step4`. The original GNATprove report contains `Success: all checks proved (10 checks).` It lists division checks, termination and postcondition obligations for the specified reference source. Ten tool-generated verification conditions do not imply ten new proofs of the whole project, the CLI parser, or browser code.

### 3.3 Executable differential observations

The preserved receipts report a freshly compiled Ada CLI run against all 4,096 valid cases and ten invalid inputs; they also report a developer Node invocation of the **real first-party** JavaScript `evolve` implementation against all 4,096 cases. Both are bound to the canonical vector digest. These are complete comparisons of the **declared width-four domain**, not arbitrary-width execution proofs. Mathematical refinement from Rocq/Lean to Ada/JavaScript remains an open formal obligation.

### 3.4 Rocq arbitrary-finite-width obligations

Source: `formal/rocq/Automata.v`, SHA-256 `6f814063141fbed564db239c3e5abaf4bdd833e2819889d7a6be005ee937ada1`; Git blob SHA-1 `15dfdf5925492c5647477d8f2970664bdd827d93`. Obligations:

1. `neighborhood_bounded`; 2. `arithmetic_table_cell`; 3. `arbitrary_width_length`; 4. `arbitrary_width_table_length`; 5. `independent_models_equivalent`; 6. `rule_zero_cell`; 7. `rule_255_cell`; 8. `rule_zero_all_widths`; 9. `rule_255_all_widths`; 10. `rule90_cell_xor`; 11. `rule90_all_widths`; 12. `automata4_model_bridge`; 13. `zero_boundary_empty`; 14. `zero_boundary_singleton`; 15. `rule90_known_four` (concrete example).

The result of greatest mathematical interest is equivalence between **two separately defined** arithmetic/table-based row evaluators for every finite Boolean list. The uploaded local receipt records Rocq 9.2 (opam `rocq-core.9.2.0`), OCaml 4.14.2, `rocq compile -q -Q . IndependenceRocq Automata.v`, exit 0, all 15 `Print Assumptions` outputs `Closed under the global context`, and a compiled `.vo` SHA-256 of `a83e3199550408ed188a6ccd35200edb3cc10af2c99a43e75daca06bb95a3fed`. **The .vo binary itself was not retained**: the hash is in the original receipt. No Rocq proof claimed here equates production `lab/core.js` with its mathematical model.

## 4. Custody and provenance: original bytes, not reconstructed fiction

Two **unchanged original** user-supplied local proof archives are present in `formal/research/v1.1.0/`:

| Archive | Bytes | SHA-256 |
| --- | ---: | --- |
| `automata4-proof-archive.tar.gz` | **3,473** | `05990c6b614d463e973bdee55b20159b59a37844fe03d81f75927f729de99457` |
| `INDEPENDENCE-rocq-proof-evidence.tar.gz` | **3,658** | `c7a28f450c0cb50df51f16cec6190cbcfef850dcf88042e88911bb6167796d6f` |

The AUTOMATA4 evidence `SOURCE_COMMIT.txt` is `764aec4bda8381de2aed620037d5ff992dba25ea` (v1.0.0 source); the Rocq archive's `SOURCE_COMMIT.txt` is `00c093ce56071813b815805c86559b8b4b303cab` (successful hotfix branch, before PR merge). The v1.0.2 runner-fix merge is `065cc1f1015d3e2faa4c1257fa7efa32f2ca2395`. Their different commit IDs are **intentional historical provenance**, not bookkeeping mistakes. The AUTOMATA4 archive's `WORKTREE_STATUS.txt` records untracked generated evidence and cache/build artifacts; the report does not claim independent forensic workstation attestation.

The original browser ZIP was preserved earlier in v1.0.1 as lossless fragments under `formal/evidence/browser/v1.0.1/base64/`; its 6,182-byte SHA-256 is `76514017982d86c95003bd4f86ccdcf4404502ede4609ba8f7767b89ee6c396a`. Original GitHub Actions PR run: `41112613136`, artifact `13003029340`; receipt checkout revision: `9f5616aa76d1dd18448b8e0d1300f7c6eb43d3b3`. Reported narrow-view **actual** inner widths were 469px Chromium and 472px Firefox, although 390px was requested. This ZIP is **not** a v1.0.0 release-build attestation or proof of live GitHub Pages availability.

The machine-readable `evidence-manifest.json` pins the archives' original bytes and each tar member. Reformatting JSON or recompressing these files does not preserve their identity. A matching digest fixes *what was supplied*, not who supplied it or what actually executed.

## 5. Verification and falsification procedure

The new Python standard-library verifier and tests are deliberately independent of website packages. From a checkout of this research version:

```sh
python3 scripts/verify_formalisation_archive.py --output formalisation-integrity.json
python3 -m unittest discover -s tests -p 'test_formalisation_archive.py' -v
python3 scripts/verify_browser_archive.py
```

The first program checks **original compressed archive bytes**, hardcoded SHA-256 pins independent from the manifest, path/size inventory, all **13 original internal SHA256SUMS entries**, strict JSON, Lean/GNATprove output checksums, Ada/JS finite statuses, exact Rocq source and fifteen assumption-audit outcomes. Negative tests cover mutated original tarballs, re-pinning both archive and manifest, missing/symlinked entries, forged Rocq counts, false Zenodo publication/attestation claims and malformed JSON. Its successful result is `ORIGINAL_ARCHIVES_AND_RECEIPTS_INTERNALLY_VERIFIED_UNATTESTED`, **not** `INDEPENDENTLY_ATTESTED_EXECUTION`.

To re-run executable/formal proof stages with actual local developer tools, use the **source checkout that matches the original receipt**, or create separately versioned new receipts:

```sh
# Lean 4.35.0 + GNATprove + GPRbuild + Node
python3 scripts/check_automata_formal.py --require-all --output automata4-new-run.json
python3 scripts/verify_automata_evidence.py automata4-new-run.json

# Rocq 9.2.0 via the dedicated opam environment
eval "$(opam env --switch=independence-rocq-9.2 --set-switch)"
python3 scripts/check_rocq_semantics.py --require-rocq --output rocq-new-run.json
```

Do not expect re-executed compiler logs or binary SHA-256 values to be identical on unrelated machines. Keep any new receipts **separate** from the historical original archive.

## 6. Threats to validity and remaining proof obligations

**T1: model-to-code refinement** — open. Lean/Rocq mathematical results and SPARK contracts do not establish a theorem relating every valid JavaScript operation, typed array and exception path to the mathematical model.

**T2: bounded extrapolation** — 4,096 exhaustive cases exhaust only the *width-four* domain. Rocq's arbitrary-finite-width claim is a model theorem, not an arbitrary-width JavaScript execution audit.

**T3: mutable wrapper/fingerprint counterexample** — documented earlier; an outer frozen wrapper does not make an inner `Uint8Array` immutable. The opt-in guarded snapshot does not silently change legacy ownership semantics.

**T4: authentication** — source hashes and self-consistent tool reports are evidence integrity, **not** independent remote attestation of the compiler, author or machine.

**T5: browser and availability** — historical Chromium/Firefox smoke assertions do not establish WCAG certification, physical-device accuracy, absence of vulnerabilities, real GitHub incidents or persistent CDN serving.

**T6: unsupported ecosystem supremacy** — neither the project nor this report supplies representative version-pinned comparative studies proving all external dependencies, frameworks or build systems wasteful. First-party software can still be wrong.

**T7: archive gaps** — Rocq `.vo` is only represented by its recorded digest, not the original compiled binary bytes. Prior historical Lean evidence classes outside AUTOMATA4 have separate status and should not be silently combined into these six model checks.

**T8: independence of models** — the arithmetic function and explicit eight-pattern truth table share the assumed Wolfram rule numbering. Their equivalence checks two expressions of an agreed mathematical convention, not independent experimental evidence about the physical world.

**T9: DOI/version custody** — the author reported minting `10.5281/zenodo.23816739`. Public metadata, deposited files and whether this exact version is published were **not independently verified**. Do not claim a peer-reviewed article, a published v1.1.0 DOI record or a final Git tag until those events occur.

## 7. The rigorous rant: what the experiment actually says

The defensible software-independence declaration is not *“we wrote everything ourselves, therefore we are correct.”* It is *“we can name our assumptions, expose source, execute declared tests, run real theorem checkers, preserve original bytes and specify exactly where the evidence ends.”* A small application can harbour a profound defect, and a large dependency can provide extraordinary value. Whether a dependency is worth having is a question for scoped evidence, not ideology.

A checksum cannot replace a theorem. A theorem cannot replace executable integration testing. A passing test cannot replace a chain of custody. A chain of custody cannot replace a threat model. And a clever slogan cannot replace any of them. These instruments address different failure modes; making their limitations visible is the strongest argument for engineering independence we can support.

**The most rigorous rant is the one that tells you exactly where its own argument stops.**

## 8. Release and Zenodo policy

1. Preserve both original proof archives and their fixed SHA-256 values; no recompression or JSON editing.
2. Keep the original v1.0.1 browser evidence fragment set and historical checkout identity unchanged.
3. When v1.1.0 is merged and tagged, record its **actual tag commit and CI run** separately from the old local SOURCE_COMMIT.txt values.
4. Do not automatically mark the author-supplied DOI as published. Verify the final Zenodo title, license, creators, resource type, version and file inventory before claiming the published record. If the DOI refers to a distinct earlier dataset, use a related-identifier relationship rather than relabelling it.
5. Retain every negative result, `NOT_RUN`, and known proof boundary in citations and abstracts.

**Proposed citation, pending Zenodo confirmation:** Slade, T. (2026). *INDEPENDENCE: Formal Models, Bounded Conformance, and Evidentiary Trust Boundaries* (Version 1.1.0) [Software and research dataset]. QSOL-IMC. User-supplied associated DOI: https://doi.org/10.5281/zenodo.23816739.

**Conclusion:** The archived receipts report six Lean mathematical theorems, ten GNATprove conditions, finite 4,096-vector Ada and JavaScript comparisons, ten negative Ada CLI tests, fifteen Rocq model theorem/example obligations and ninety-two historical dual-browser assertions. Their original bytes are preserved and can be examined. These results do **not** establish formal correctness of production JavaScript, externally attested execution or universal claims about dependency quality. Their scientific merit is precisely that the report refuses to claim otherwise.
