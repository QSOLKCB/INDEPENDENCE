# Evidence protocol: v1

## What is proved here

- GitHub Pages serves a static site composed of index.html, styles.css, app.js, lab/core.js, and lab/tests.js.
- The browser automaton is deterministic at fixed rule, seed, width, and height. The browser test button checks a known xorshift32 vector, Rule 90 evolution, a known FNV-1a vector, replay identity, validation boundaries, and arithmetic.
- scripts/audit.py checks for known package manifest filenames across this repository, static remote resource patterns in the five deployed assets, and creates SHA-256 fingerprints of those assets.
- tests/test_audit.py checks the audit itself for positive/negative cases.

## Reproduce

On a normal Python 3 installation:

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json

To use the interactive experiment locally:

    python3 -m http.server 8000

Then open http://localhost:8000/ . No third-party package installation is required. ES modules need an HTTP origin; opening index.html as a file may be blocked by browser module security policies.

## What is NOT proved

- That all QSOL-IMC repositories have no dependencies. The declaration's 99-repository number is a historical author claim, not an independently verified organization-wide inventory.
- That browsers, operating systems, Python, web hosting, compilers, or their supply chains are dependency-free.
- That all forms of external network activity, direct or indirect, are impossible. The audit is scoped, pattern-based static inspection; it is not dynamic instrumentation or a full security analysis.
- That dependency count is a proxy for vulnerabilities, that containers are always inappropriate, or that the browser render-time reading is a cross-stack performance benchmark.
- That a noncryptographic FNV-1a checksum provides tamper resistance. The audit report's SHA-256 hashes serve artifact identification, not third-party attestation.

## Independent scrutiny

Review the source in lab/core.js, read the pure-JS tests in lab/tests.js, run the Python tests, inspect the emitted JSON report and challenge the assumptions. For security findings, use authorized test targets and responsible disclosure. Report a flaw with its test case and expected/actual behavior.

## Audit design limits

The manifest list is finite and can miss unconventional build tools; source scanning covers five named runtime files. The report avoids timestamps to make identical source inputs produce identical JSON output. Filesystem-specific content (e.g., cached directories) is excluded from audit interpretation as described by scripts/audit.py. No CI provider is required to reproduce the command locally.

## v0.2 — Public organisation-wide filename evidence

The standard-library collector (scripts/build_ledger.py) queries the GitHub public repository listing with pagination, reads the optional QSOL-IMC curated catalogue for categories, does not read QSOL-CONTEXT (a private design reference), and fetches recursive default-branch Git trees. This is **not** a dependency import graph or project test.

A successful untruncated tree is labelled scanned. A negative filename finding is labelled no known manifest and is **never** interpreted as dependency-free. Truncation, HTTP failures, and missing branches are always unknown. Canonical SHA-256 receipts exclude their own digest member. No private GitHub repositories or personal context contents are intentionally collected.

The committed ledger/data.json is a source-labelled bootstrap inventory; the manually triggered GitHub Pages workflow regenerates an up-to-date published snapshot, without writing it back to main. See docs/LEDGER.md.

## v0.3 — Dependency Tribunal

DOM-TRIBUNAL/1 uses same-origin first-party JavaScript adapters on identical seeded DOM-list operations. The user starts the trial explicitly. Warmups precede measured trials, candidate order alternates, and both implementations must pass complete DOM ID, order, and text checks. Results contain paired samples, medians, deterministic bootstrap percentile intervals, adapter-source byte lengths, and an exported SHA-256 receipt. See docs/TRIBUNAL.md.

**Boundaries:** Direct DOM versus a locally authored keyed adapter is NOT an actual React/Vue/Svelte comparison. Detached DOM timing excludes layout and painting; uncontrolled browser/JIT/CPU scheduling affects outcomes. The Python verifier tests data integrity and arithmetic, but cannot authenticate a real measurement.

## v0.4 — Gremlin Museum

GREMLIN-MUSEUM/1 is a browser-native, fixed-fixture teaching and verification system containing five safe, **inert** reproductions of bug patterns: a historical static import regex omission, a historical repo-path ancestry false positive, a historical Git/receipt SHA-size mix-up, illustrative JSON numeric overflow, and illustrative HTML output encoding. The last two are NOT asserted to have occurred in INDEPENDENCE.

Every specimen has explicit legacy and corrected behaviours and meaningful deterministic assertions. No payload is imported, fetched, evaluated, rendered as unsafe markup, or passed to a real service. The UI renders all samples using textContent and generates a SHA-256 of exact JSON payload bytes. An offline Python stdlib verifier checks payload integrity and known fixture outputs; receipts do not certify absence of vulnerabilities.

## v0.5 — Gremlin Breeding Laboratory

GREMLIN-BREEDING/1 implements five isolated pure-function targets and 15 deliberately changed versions. Each is known to diverge from a full, fixed oracle. The small smoke suite and extended fixture suite illustrate how detection capacity changes. Their mutation scores describe **only this fixed catalogue**, not application-wide coverage.

The exact text of the report is SHA-256 hashed by browser WebCrypto. The Python standard-library verifier independently encodes expected witness cases, operators, outcomes and seeded order, then checks the receipt. A valid digest plus expected report does not prove a real execution occurred, certify code quality or represent a security assessment. No dynamic source mutation is performed.

## v0.6 — AI–Human GitHub Workflow

The Secret Source documents the *engineering process* used to develop this project: human-directed tasks, AI-assisted implementation, scoped repository invariants, available test execution, adversarial review, Git HEAD checks and human-controlled merges/releases. Five actual merged PR URLs support the historical project progression. This evidence does not quantify the proportion of code written by AI, AI productivity, comparative accuracy, or a causal reduction in drift.

The static browser section explains eight stages and eight optional self-report checks. Its plain-text prompt generator requires an observable goal and provides an explicit negative scope, invariants, tests, disclosure of unrun checks and a human-only merge gate. Generating a prompt or checking a box performs no tests, repo operations, LLM inference or external verification. The slogan "AI + WEB TECH = UNLIMITED POTENTIAL" is rhetorical and has no numerical or literal basis. See docs/AI-HUMAN-WORKFLOW.md.

## v0.7 — Proof Contracts

The machine-readable proof/contracts.json specifies eight obligations, all formally NOT_PROVED, tied to the tagged v0.6.0 source baseline. The first four browser checks exercise actual production JavaScript against separate reference implementations: all 130,560 binary rows/rules for widths 1..8 (918,016 cell checks), 463 bounded exact-integer sum cases, 36 replay/FNV cases, and 12 SHA format fixtures.

A fifth result is a deliberate COUNTEREXAMPLE: a frozen return wrapper contains a mutable Uint8Array, so the stored fingerprint can be invalidated by client mutation. It is not a security exploit claim. Lean, SPARK and independent receipt execution attestation are PENDING, not passed.

scripts/check_proof_contracts.py validates the contract registry using stdlib, and scripts/verify_proof_receipt.py checks exact browser report integrity and fixed results. Neither is a full proof or attestation of source execution. See docs/PROOF-CONTRACTS.md and docs/FORMAL-ROADMAP.md.

## v0.7.1 — SPARK Ada reference, not proof by declaration

The project adds SPARK_Mode On Ada functions for bounded rectangular addressing, GF(2) parity addition/multiplication, modulo-3 phase addition and edge endpoint validation. The canonical input limits and explicit nonclaims live in formal/spec/kernel-v1.json.

The source-level Python gate checks files, hashes, forbidden proof-escape annotations and declared contracts. This is not GNATprove. An optional strict runner invokes GNATprove with checks-as-errors and records actual tool output; where it was unavailable, evidence remains NOT_RUN and outstanding. The reference does not establish Python or JavaScript equivalence.

A subsequent v0.7.2 conformance layer must separately compare Python/Ada results against the same versioned semantics. See docs/SPARK-REFERENCE.md.
