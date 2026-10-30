# THE SOFTWARE DECLARATION OF INDEPENDENCE

### QSOL-IMC — October 30, 2026

**We hereby declare our independence from the Modern Software Industry.**

We reject the proposition that a simple application requires a container, a container orchestrator, a package manager, a dependency resolver, seventeen YAML files, and an army of consultants to deploy.

We reject the idea that software engineering is measured by the number of frameworks one can assemble.

We reject complexity masquerading as sophistication.

**Our grievances are numerous:**

- Kubernetes: We aren't deploying the fucking space shuttle.
- Docker: Not every executable needs its own shipping container.
- Node.js: JavaScript does not need to run the entire civilisation.
- npm: We would prefer not to download half the internet to compile a button.
- Dependency hell: Your supply chain is not our responsibility.
- Framework churn: Yesterday's revolutionary solution is tomorrow's deprecated liability.

We welcome AI as an instrument of independent security research, exposing vulnerabilities, auditing assumptions, and demonstrating the consequences of unnecessary complexity through reproducible evidence and responsible disclosure.

We do not claim that dependency-free software is invulnerable. We claim that every dependency introduces another relationship that must be understood, trusted, maintained, and defended.

**Our principles:**

1. Correctness outranks convenience.
2. Simplicity outranks fashion.
3. Auditability outranks abstraction.
4. Portability outranks platform lock-in.
5. Reproducibility outranks promises.
6. Zero dependencies wherever technically feasible.
7. No unnecessary infrastructure.
8. No mandatory cloud services.
9. No framework shall become our master.

We build software that can stand on its own.

**99 PUBLIC REPOSITORIES. ZERO DEPENDENCIES. ZERO FUCKS GIVEN.**

*Signed,*

**QSOL-IMC**  
*Independent Software Sovereignty Initiative*

**WE DID NOT LEAVE SOFTWARE ENGINEERING. SOFTWARE ENGINEERING LEFT US.**

**This is not War, This is a Divorce.**

**This Isn't War, This Is Pest Control**

---

## Live proof lab

The manifesto now has a working, no-build interactive demonstration on GitHub Pages:

**https://qsolkcb.github.io/INDEPENDENCE/**

- Deterministic, seeded elementary cellular automata (Rules 30, 90, 110 and 184), native Canvas 2D, and a replay fingerprint.
- Browser tests (including independently known vectors), executed only when requested.
- A clearly-labelled synthetic dependency-tree thought experiment.
- Zero third-party runtime packages or externally hosted executable browser assets.
- Python 3 standard-library dependency and resource audit, plus stdlib unittest tests.

No npm install, pip install, Docker pull, container orchestration, bundler, or third-party service is needed to build, test, or serve it:

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Open http://localhost:8000/ for local development. The browser uses relative ECMAScript module imports and therefore should be served over HTTP.

See docs/INVARIANTS.md, docs/EVIDENCE.md, and docs/ROADMAP.md. The scope and limitations are intentional: zero third-party packages is not zero platform dependencies, not an all-repositories audit, and not proof of invulnerability.

**The revolution will not be containerised.**

## v0.2.0 — Software Independence Evidence Ledger

[Browse the public evidence ledger](https://qsolkcb.github.io/INDEPENDENCE/#ledger) after this PR is merged and manually deployed.

The public catalogue at [QSOL-IMC](https://github.com/QSOLKCB/QSOL-IMC) provides curated categories. QSOL-CONTEXT informs the provenance philosophy but is a **private repository** and is neither queried by the collector nor imported into this public dataset. The ledger **never** publishes personal context records.

This is a *filename-signal inventory*, not a declaration that every repo is package-free. It distinguishes observed manifests, inspected trees without known manifests, truncated trees and failed scans. Counts come from the packaged JSON, not hard-coded website constants.

Regenerate using Python's standard library (GitHub REST network required):

    GITHUB_TOKEN=... python3 scripts/build_ledger.py --as-of 2026-10-30 --output ledger/data.json

The existing manually triggered Pages workflow now refreshes the snapshot before testing and packaging the site. Visitors load static JSON from GitHub Pages; **their browsers do not query the GitHub API**. See [ledger methodology](docs/LEDGER.md) for evidence scope, unknown states, failure handling, and receipt hashing.

## v0.3.0 — The Dependency Tribunal

[Open the experiment](https://qsolkcb.github.io/INDEPENDENCE/#tribunal) after merging and manually deploying.

DOM-TRIBUNAL/1 compares **direct DOM replacement** with a tiny **first-party keyed adapter**, both performing identical seeded list render, update and reorder operations on detached DOM elements. The latter is illustrative, NOT an actual React/Vue/Svelte or third-party framework benchmark. No default winning figures are provided: results only exist when the visitor explicitly runs the workload.

Every trial has matching output assertions, alternating execution order and warmups. The browser reports paired medians, seeded bootstrap 95% percentile intervals and first-party adapter source byte counts. SHA-256 receipts are downloadable locally, not sent to QSOL-IMC.

Verify an exported file with Python stdlib:

    python3 scripts/verify_tribunal.py /path/to/tribunal-receipt.json --json

Verification checks exact UTF-8 payload integrity and internal sample/summary consistency, not the authenticity of measured timings. Read [the protocol](docs/TRIBUNAL.md) for scope and limitations.

## v0.4.0 — THE GREMLIN MUSEUM

[Enter the Gremlin Museum](https://qsolkcb.github.io/INDEPENDENCE/#museum) after merge and manual Pages deployment.

Five safe, first-party, fixed-input demonstrations of software failure modes, each with a legacy observation, bounded corrective behaviour and reproducible assertions. Three reflect historic INDEPENDENCE review findings; two are explicitly marked illustrative. **Nothing malicious is executed:** all code-like inputs are inert strings shown with textContent. No external host, upload, installation, framework or package manager is needed.

Run a specimen individually or all five. For a passing full run, download an exact-payload SHA-256 JSON receipt and verify it offline:

    python3 scripts/verify_museum.py /path/to/gremlin-museum-xxxxxxxxxxxx.json --json

The verifier checks integrity and fixed observations, not authorship, real-world exploitability or the absence of undiscovered vulnerabilities. Read [docs/MUSEUM.md](docs/MUSEUM.md).

## v0.5.0 — The Gremlin Breeding Laboratory

[Visit the mutation-testing laboratory](https://qsolkcb.github.io/INDEPENDENCE/#breeding) after merging and manually deploying.

GREMLIN-BREEDING/1 creates **15 harmless, predeclared pure-function mutants** across five fixed targets. All 26 baseline oracle cases must pass. Each mutant must have a known divergent witness. A deliberately incomplete smoke suite misses several mutants; the expanded fixture suite catches them. This is a laboratory for testing the tests, not arbitrary mutation of repository files or a repository-wide security score.

Runs are deterministic by seed and show killed/survived classifications and failing test IDs. Download a local SHA-256 evidence receipt and verify it using Python's standard library:

    python3 scripts/verify_breeding.py /path/to/gremlin-breeding-xxxxxxxxxxxx.json --json

The verifier pins the catalogue, outcomes and seeded order but does not attest genuine browser execution. See [docs/BREEDING.md](docs/BREEDING.md) for methodology and limits.

## v0.6.0 — The Secret Source: AI + Web Tech = Unlimited Potential

[Explore the AI–Human GitHub Workflow](https://qsolkcb.github.io/INDEPENDENCE/#workflow) after merging and manually deploying.

The previously unspoken engine behind this repository is a human-directed loop:
**intent → bounded scope → invariants → AI-assisted implementation → real tests
→ adversarial review → fresh HEAD SHA → human-authorised merge and release**.

The slogan is aspirational, not a guarantee: models can be wrong, drift, miss edge cases and misreport unverified work. Practical guidance shows how to improve reliability by freezing scope, naming forbidden changes, checking provenance and tool outputs, testing failure cases, challenging patches with a hostile reviewer and reviewing the **actual latest commit** before merging.

The new static browser guide includes eight selectable workflow stages, eight self-reported drift safeguards, public links to five merged PR case studies, and a **local copyable agent-handoff prompt generator**. It does **not** call an AI, send prompts to a server, track activity or claim to check your repository. Only browser-standard code and Python stdlib tests are used.

Full method and copyable adversarial-review/fix prompts:
[docs/AI-HUMAN-WORKFLOW.md](docs/AI-HUMAN-WORKFLOW.md).

## v0.7.0 — PROOF CONTRACTS: Evidence Before Proof

[Run the proof-contract dashboard](https://qsolkcb.github.io/INDEPENDENCE/#proof) after merging and manually publishing.

The machine-readable [proof registry](proof/contracts.json) declares eight obligations. **Every one remains NOT_PROVED formally.** The browser executes bounded checks against the real first-party source: 130,560 elementary cellular-automaton transitions (all rules across all 1..8-wide binary rows), 918,016 output-cell comparisons, BigInt geometric-sum fixtures, seeded replay and SHA validation. A fifth observation is a real COUNTEREXAMPLE: the frozen automaton wrapper holds mutable cells, so a returned fingerprint can become stale.

Reproduce the registry check and verify a downloaded receipt with Python stdlib:

    python3 scripts/check_proof_contracts.py --json
    python3 scripts/verify_proof_receipt.py proof-contracts-<hash>.json --json

Hash verification does not attest execution. No Lean or SPARK proof has yet been constructed or discharged. The proof tools remain planned as optional development-only components, not runtime dependencies. Read [docs/PROOF-CONTRACTS.md](docs/PROOF-CONTRACTS.md) and [the formal programme through v1.1.0 Zenodo](docs/FORMAL-ROADMAP.md).

## v0.7.1 — SPARK Ada Reference Kernel

Introduces development-only SPARK/Ada source under `formal/spark/` for a narrow finite reference: rectangular addressing and decoding, GF(2) parity arithmetic, mod-3 phase addition and validated in-range, distinct endpoint transitions. Canonical semantics are versioned at `formal/spec/kernel-v1.json`.

The kernel specifies preconditions and postconditions. **No GNATprove execution was possible in the implementing environment; the contracts are NOT_RUN, not proved.** The CLI input boundary is not formally analyzed. There is no claim that this reference verifies existing Python or JavaScript.

    python3 scripts/check_spark_reference.py
    python3 scripts/check_spark_reference.py --prove --output spark-evidence.json
    python3 scripts/check_spark_reference.py --require-proved

The strict command fails unless actual GNATprove analysis reports discharged obligations. GNAT/GNATprove are optional development-only tools, never site runtime dependencies. See [docs/SPARK-REFERENCE.md](docs/SPARK-REFERENCE.md).

## v0.7.2 — Proof-Conformance Bridge

A separate, versioned conformance layer tests a newly written independent Python reference against the same kernel-v1 semantics used by the v0.7.1 SPARK/Ada kernel. **An Ada proof does not automatically prove Python correct.**

The bridge executes 8,881 valid finite-domain cases and 16 invalid inputs against an independently coded Python oracle. It can optionally compare real Ada CLI output for a deterministic, operation-covering sample, or the whole domain if Ada tools are available.

    python3 scripts/run_kernel_conformance.py --receipt conformance.json
    python3 scripts/verify_kernel_receipt.py conformance.json

To compare an actually built Ada CLI, supply the executable:

    python3 scripts/run_kernel_conformance.py --ada-cli formal/spark/bin/reference_cli --ada-cases 128 --receipt ada-comparison.json

The receipt distinctly reports Lean mathematical proofs, Ada contract verification, tested Python conformance, Ada CLI comparisons and unresolved obligations. In the source author's execution environment, GNAT/GNATprove were unavailable, so Ada contracts and differential comparison remain NOT_RUN. Matching a supplied executable is explicitly UNATTESTED; neither Python application-wide correctness nor production JavaScript is established. Details: [docs/PROOF-CONFORMANCE.md](docs/PROOF-CONFORMANCE.md).

## v0.7.3 — Lean 4 Mathematical Foundation (review candidate)

The first development-only Lean 4 proof source is in [formal/lean/FiniteFoundation.lean](formal/lean/FiniteFoundation.lean), pinned to **Lean 4.35.0** in [lean-toolchain](lean-toolchain). It defines 13 proposed theorem statements and accompanying proof terms for an explicit CRT (2,3) bijection, Boolean GF(2) identities, cyclic modulo-3 phase identities, and strict degree-lex order properties on natural exponent pairs.

**Verification is not yet complete:** the authoring environment does not have Lean installed. All 13 theorem declarations are **NOT RUN / NOT KERNEL CHECKED** pending real Lean execution. Static Python source checks cannot change that status. No Lean proof implies correctness of production Ada, Python or JavaScript.

To run actual Lean checks and a fail-closed axiom audit with a trusted Lean installation:

    python3 scripts/check_lean_foundation.py --require-checked --output lean-evidence.json

For source-level validation without Lean:

    python3 scripts/check_lean_foundation.py

General CRT, full monomial well-foundedness/totality, graph adjacency and model-to-code conformance remain open. See [docs/LEAN-FOUNDATION.md](docs/LEAN-FOUNDATION.md) for the exact scope, assumptions and reproducibility instructions.

## Preserved Lean 4 proof evidence — pinned v0.7.3 source

The user's successful local Lean 4.35.0 verification output (13/13 theorem audits; `--trust=0`; reported 169/169 Python tests) has been archived for the proposed v1.1.0 Zenodo formalization at [formal/evidence/lean/v0.7.3](formal/evidence/lean/v0.7.3). The archive includes `lean-evidence.json`, its manifest, a copy of the historical Lean source and `lean-toolchain`, and a provenance explanation.

**Source commit:** `68351489e8bbbb879efdcac19d02869124fcf724` (merged PR #11). **Provenance qualification:** the report was recovered intact from the user-shared terminal transcript, not independently byte-matched against an upload of the original `lean-evidence.json`; the local execution was not independently attested. Archive hashes establish internal consistency, not authorship or Ada/Python/JS verification.

    python3 scripts/verify_lean_evidence_archive.py

This offline integrity gate does not itself run Lean. Re-run the pinned compiler separately to reproduce the proof.

## SPARK verification milestone — PR #13 (reported local evidence)

The user reported an actual GNATprove FSF 16.1.0 execution against PR #13 HEAD `9900e57f2283c534815657dd6c079d0e966715f4`, with **all 21 kernel checks proved**, exit code 0 and a passing **186/186 Python regression suite**. The exact analyzed Ada source/project SHA-256 values and the copied proof-output digest are preserved in [formal/evidence/spark/pr13](formal/evidence/spark/pr13) for eventual Zenodo v1.1.0 formalization.

This receipt was reconstructed from a user-pasted terminal report, **not the unattached original `spark-evidence.json` bytes or an independently authenticated run**. It describes GNATprove's scoped Ada-reference checks; the Ada CLI and actual Python/Ada differential execution remain separate obligations.

    python3 scripts/verify_spark_evidence_archive.py

## v0.7.4 — Actual Ada CLI build and Python comparison

A new offline developer-only command compiles the pinned PR #13 Ada source snapshot in a **fresh temporary build directory**, then compares the executable against the independent Python oracle over either 150 sample/invalid inputs or the full **8,903-process finite set**. It records compiler versions, source and executable SHA-256 hashes, raw build output and a fail-closed self-consistency receipt. No Ada runtime success is claimed until the command really runs on a GNAT-equipped machine.

~~~sh
export PATH="$HOME/opt/edgewalk-spark-toolchain/bin:$PATH"
python3 scripts/build_and_compare_ada.py --output ada-runtime-evidence.json
python3 scripts/verify_ada_runtime_evidence.py ada-runtime-evidence.json
~~~

See [docs/ADA-RUNTIME-EXECUTION.md](docs/ADA-RUNTIME-EXECUTION.md). The archive verifier does not independently authenticate build execution, and Ada/Lean proofs do not establish production Python/JavaScript correctness.

## Original v0.7.4 runtime evidence preserved

The user uploaded the **original ZIP and checksum** following the actual Ada/Python runs. Both original JSON runtime receipts are now preserved byte-identically under [formal/evidence/ada-runtime/v0.7.4](formal/evidence/ada-runtime/v0.7.4), with 150-case and full 8,903-case results, their exact file SHA-256, Git blob IDs, reported Ada binary digest, historical Git revisions and a reproducibility/provenance manifest. The uploaded ZIP checksum is `429b946d083c2b0562450704f924eb3370e5c9a9c62eb81ef5ac90d41a5e2256`; **the ZIP itself is not stored in this Git repository**. The separately uploaded GNATprove JSON matches the already archived SPARK report byte-for-byte; the Lean ZIP member remains the previously transcript-reconstructed archive file.

    python3 scripts/verify_original_ada_evidence.py

File-byte identity and internal consistency are now established; independent authentication of local compiler execution is **not** asserted. The full set is finite, not a general formal proof of CLI or application behaviour.

## v0.8 — Deterministic Property Lab and Counterexample Minimisation

The deployed first-party [Property Lab](https://qsolkcb.github.io/INDEPENDENCE/#property-lab) generates up to 512 replayable seeded automaton cases, compares the real transition implementation against an independent oracle, exposes a **deliberately injected boundary-condition mutant**, and shrinks a failing 8-cell witness to its canonical 1-cell reproducer. It also reproduces the existing real mutable `Uint8Array`/fingerprint counterexample and provides an **opt-in defensive-copy snapshot API** without changing the legacy automaton interface. The browser exports exact SHA-256 property receipts, independently checked for consistency with Python stdlib:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/audit.py --json
python3 scripts/verify_property_receipt.py /path/to/property-lab-<hash>.json
```

The injected mutant is intentionally faulty, **not a discovered production defect**. Finite tests, self-hashed receipts and opt-in ownership guards establish no universal proof or independent browser execution attestation. See [docs/PROPERTY-LAB.md](docs/PROPERTY-LAB.md).

## v0.9.0 — Lean 4 + SPARK/Ada Elementary-Automata Laboratory

v0.9 introduces a distinct `AUTOMATA4/1` four-cell elementary automaton reference, specifying fixed-zero boundaries and all 256 rule masks over 16 possible input rows (**4,096 deterministic vectors**). It adds six new Lean 4 theorem candidates, an exact standalone SPARK-mode Ada reference and developer CLI, independent Python finite oracle, and a developer-only JavaScript check against the actual first-party `evolve` function. Unlike the earlier 13 Lean and 21 SPARK results, **new v0.9 formal proof statuses remain NOT_RUN until real local compilation and axiom audit evidence is supplied**.

Run without any additional dependencies:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_automata_formal.py --output automata4-static.json
```

On a machine with the pinned Lean 4.35.0, GNATprove, GPRbuild and optional Node, the strict executable gate is:

```bash
export PATH="$HOME/opt/edgewalk-spark-toolchain/bin:$PATH"
python3 scripts/check_automata_formal.py --require-all --output automata4-evidence.json
```

This checks formal proof outcomes, compiled Ada execution and all 4,096 real JavaScript transitions as **separate** evidence classes.

Check saved evidence integrity (not execution attestation):

```bash
python3 scripts/verify_automata_evidence.py automata4-evidence.json
```
 No build tool or external dependency is added to the deployed website. See [AUTOMATA-FORMAL.md](docs/AUTOMATA-FORMAL.md).


### v0.9.0 browser formal lab — unified AUTOMATA4/1

[Open the four-cell formal lab](https://qsolkcb.github.io/INDEPENDENCE/#formal-lab) after merging and manual Pages deployment. It runs the actual first-party automaton on **4,096** inputs (256 rules × 16 width-four rows), checks all outputs and source ownership against an independent reference, and exports a locally hashed JSON receipt. There is only **one authoritative four-cell formal specification**, not competing Lean/Ada reference implementations.

Verify a browser receipt with standard-library Python:

    python3 scripts/verify_automata_browser_receipt.py /path/to/automata4-browser-xxxxxxxxxxxx.json

The receipt verifies consistency with the canonical corpus but does **not** independently attest that the browser executed. Formal theorem checks and Ada differential execution remain optional developer-only tools.


## v1.0.0 — Real-browser and GitHub Pages deployment verification

The project now builds an exact, dependency-free Pages artifact from one
allowlist of first-party files. PAGES-ARTIFACT/1 generates a deterministic
SHA-256 manifest for every byte, rejects stale/missing/extra assets and malformed
HTML/CSP, and retains the Git commit revision. The manual Pages workflow
verifies that staged artifact before uploading it.

Two **actual** development-only browser engines exercise the staged website:
headless Chromium and headless Firefox via Geckodriver. Real DOM journeys
cover the deterministic automaton, first-party browser tests, property/formal
labs, ledger search, local workflow handoff, CSP restrictions, basic labels
and controlled ledger HTTP 503/malformed-JSON failure paths. Browser/tool
absence is NOT_RUN, never fabricated success. The workflow also compares
the official public GitHub Pages HTTPS asset bytes with the manifest **after**
deployment; local checks are not misrepresented as public-deployment evidence.

    python3 scripts/site_bundle.py stage --source . --site /tmp/independence-v1 --revision "$(git rev-parse HEAD)"
    python3 scripts/site_bundle.py verify --source . --site /tmp/independence-v1 --revision "$(git rev-parse HEAD)"
    python3 scripts/run_browser_journeys.py --site /tmp/independence-v1 --require-browser --output chromium.json
    python3 scripts/firefox_journeys.py --site /tmp/independence-v1 --require-browser --output firefox.json
    python3 scripts/verify_deployed_site.py --manifest /tmp/independence-v1/deployment-manifest.json

All Python utilities use the standard library. Firefox/Chromium binaries are
optional developer testing tools, not site requirements. See
[the complete v1.0 verification scope](docs/BROWSER-DEPLOYMENT.md).
