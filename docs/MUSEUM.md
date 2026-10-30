# GREMLIN-MUSEUM/1 — Security Research Exhibit Protocol

## Why this exists

INDEPENDENCE v0.4.0 preserves bounded reproductions of known mistakes to teach secure engineering and to document how evidence differs from assertion. These exhibits are **not** live vulnerabilities, CVEs or security scanning of external targets. They use hard-coded, deterministic inputs and no third-party packages.

## The exhibits

| ID | Origin | Example and repair |
| --- | --- | --- |
| side-effect-import | INDEPENDENCE v0.1 Codex review / PR #1 | Regex misses a bare remote module import; corrected regex detects it. A regex is still not a complete JavaScript parser. |
| checkout-ancestry | INDEPENDENCE v0.1 Codex review / PR #1 | Absolute filesystem ancestry creates a false vendored-directory finding; repository-relative scope avoids it. |
| sha-identity | INDEPENDENCE v0.2 Codex review / PR #2 | 40-hex Git tree identifier validator rejects 64-hex SHA-256 evidence receipt; separate validators fix the confusion. |
| json-overflow | Generic illustrative case, NOT an INDEPENDENCE incident | JSON numeric exponent overflows to Infinity, and JSON.stringify emits null; a finite-number check rejects it. |
| html-encoding | Generic illustrative case, NOT an INDEPENDENCE incident | Raw HTML string construction preserves markup; output encoding produces inert text. Payload strings are NEVER assigned to innerHTML or executed. |

## Reproduction and evidence

The museum loads only local first-party scripts. Selecting an exhibit displays its description; clicking REPRODUCE performs its deterministic checks and renders the observed strings with textContent. Clicking RUN ALL evaluates all five, rejects any failure, then computes WebCrypto SHA-256 over the exact UTF-8 JSON payload string. The optional downloaded JSON envelope contains the payload text, its SHA-256 and protocol identifier. No timestamp is inserted, so the same code and fixtures generate the same digest. Receipts are **not signed** and do not authenticate the software environment.

Reproduce offline:

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Open http://localhost:8000/#museum . For export, use HTTPS or localhost so WebCrypto is available. The Python standard-library verifier accepts exported receipts:

    python3 scripts/verify_museum.py /path/to/gremlin-museum-<hash>.json --json

It checks the exact payload hash, fixed records, expected safe/legacy strings, provenance fields and assertion counts. A malicious actor could forge a self-consistent SHA-256 envelope; this is *not trusted provenance* or proof the web app has no vulnerabilities.

## Safety and scope

Never run these examples against other people's infrastructure. No exploit, browser HTML injection, script evaluation, remote module loading, filesystem operation, credential use, monitoring or telemetry is performed. The sample string that looks like an event-handler payload is only shown as inert text, not inserted as markup. Refer to official secure coding guidance for real production mitigations: the hard-coded examples intentionally have narrow scope. The museum is a teaching and regression artifact, not a complete vulnerability scanner.

The site's original declaration, evidence ledger and DOM Tribunal remain unchanged except for adding navigation and a new static section. The manual Pages workflow includes the three museum web assets in its static package.
