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
