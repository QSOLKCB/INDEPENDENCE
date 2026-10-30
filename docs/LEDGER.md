# Software Independence Evidence Ledger — Methodology v0.2

**What is collected:** Public GitHub repository metadata returned by the QSOLKCB organisation REST endpoint (explicit pagination), the default branch, archived/fork attributes, and the recursive Git tree for each available branch. No project source files are downloaded or executed.

**Public references:** QSOL-IMC app.js supplies optional editorial categories. The historical 99 curated project entries are not assumed to equal the live public repository count. QSOL-CONTEXT is a private design inspiration, not an evidence source. The collector does not query it, publish its metadata or inspect its contents.

## Collection and reproducibility

    GITHUB_TOKEN=... python3 scripts/build_ledger.py --as-of 2026-10-30 --output ledger/data.json
    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Python's standard library is sufficient. GITHUB_TOKEN is recommended for higher public API rate limits and is supplied by the manually triggered Pages workflow. The site itself has no package installation/build step. Pages refreshes the public data snapshot before tests and static upload. No GitHub credential enters the deployed artifact.

Visitors load only same-origin JSON, HTML, CSS, and JS. The committed initial ledger/data.json is a limited seed; the published Pages artifact has the freshly collected snapshot if deployment succeeds. The artifact is not an immutable historical archive; preserve copies externally for longitudinal research.

## Vocabulary and interpretation

- scanned: a complete (not truncated) recursive Git tree and a valid tree SHA.
- truncated: GitHub returned only a partial tree, always counted unknown.
- unavailable: HTTP, branch or unexpected API failure, always counted unknown.
- not_scanned: initial metadata seed, always counted unknown.
- manifest_count: known filenames such as package.json, requirements.txt, Cargo.toml. This is NOT a package installation count or full dependency graph. Test fixture files may appear.
- without_manifest_signals: only completely scanned trees with zero known manifest filenames. This is not evidence of no dependencies.
- container_marker_count: filename occurrences for Docker, Compose, Helm and Kustomize conventions; not proof that a project runs containers.
- vendored_file_count: file paths beneath known vendored directories; not a complete vendored-code scan.
- workflow_count: number of standard GitHub workflow YAML files, not evidence of CI passing.
- category: optional, editorial, sourced from QSOL-IMC app.js; otherwise null.
- tree_sha: object identity of the Git tree observed; it is not a signed attestation, and the branch can advance after observation.
- receipt_sha256: SHA-256 of canonical UTF-8 JSON with sorted keys and compact separators, omitting receipt_sha256 itself; this detects changed snapshot bytes under the canonical algorithm, not malicious modification by a trusted signer.

The collector refuses an empty result or duplicates in a paginated listing. A rate-limit, network, tree truncation or repository error cannot manufacture a clean result. A GitHub REST listing is a snapshot and can change between pages; use the receipt and as-of date as the observation boundary.

## Known limitations

No project-wide tests are executed. No direct or transitive dependency graph is resolved, no binary or remote runtime imports are inspected, and no vulnerability/security score is assigned. The web stack still relies on browsers, operating systems, GitHub Pages, runners and the Python interpreter.

A full software supply-chain audit requires scoped workload-specific reviews. This project does not replace that work. It makes verifiable source-level indicators and unknowns public without making stronger claims than the evidence supports.
