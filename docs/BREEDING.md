# GREMLIN-BREEDING/1 — Deterministic Mutation-Testing Laboratory

## Purpose

Mutation testing evaluates whether tests can detect intentional behavioural changes. This lab uses a **fixed, inspectable catalogue of pure functions**, not dynamic modification of source code, installed dependencies or runtime APIs. All code is first-party and runs in the browser without a build tool.

There are five targets: receipt SHA-256 string format, HTML text encoding, finite JSON number checking, repository-relative dependency directory recognition, and remote module import text recognition. Each has three curated mutants, for a total of 15.

## Reproducible protocol

1. Choose a nonzero 32-bit seed and a test suite (smoke or full).
2. All 26 baseline oracle cases must pass regardless of suite choice. A mismatch terminates the experiment.
3. Fisher–Yates shuffles the fixed 15 mutants using deterministic xorshift32 seeded state.
4. Every mutant must differ from its baseline on at least one known fixed test input. An equivalent or unproven candidate aborts the run.
5. KILLED means an expected result is contradicted on a selected test. SURVIVED means no selected test detects the known difference. Survivor witness IDs show the missing coverage.
6. Score is exactly the fraction killed / all 15 non-equivalent curated mutants. No arbitrary source mutation, branch coverage, application-wide mutation score, or global claim of security is inferred.
7. Every finished report can be exported as a WebCrypto SHA-256 digest of its exact UTF-8 JSON text. No network request or telemetry is sent.
8. The Python verifier independently encodes mutation IDs, operators, witness sets, expected outcomes and seeded order, and checks exact report integrity and format.

In the frozen v0.5.0 fixture catalogue, smoke detects 2 of 15 mutants while full detects 15 of 15. These are predetermined *fixture outcomes* demonstrated through actual function calls, not a performance benchmark or findings about external code.

## Reproduce

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Open http://localhost:8000/#breeding, run the two suites, export a receipt and verify:

    python3 scripts/verify_breeding.py /path/to/gremlin-breeding-<hash>.json --json

The verifier checks expected fixed-fixture classifications but **cannot attest execution provenance**. Someone with access to the public source could construct a self-consistent receipt. It also cannot claim tests detect all possible bugs. Full source, assumptions and limitations are intentionally public.

## Safety

The lab operates solely on fixed local values and predeclared functions. No arbitrary code generator, eval, Function constructor, shell invocation, filesystem modification, third-party package, remote import execution, external network call or exploit target is involved. Input strings resembling remote imports are never executed. Results display with DOM textContent, not HTML interpretation.
