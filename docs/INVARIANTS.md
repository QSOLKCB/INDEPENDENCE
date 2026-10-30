# Engineering invariants

INDEPENDENCE demonstrates a deliberately narrow policy. The rules below apply to this repository, not every QSOL-IMC repository.

1. GitHub Pages can serve the root index.html directly. No build, bundling, code generation, or server runtime.
2. The deployed interface uses only HTML, CSS, and standard browser JavaScript modules. All executable script and CSS resources are first-party repository files. No CDNs, analytics, remote fonts, or runtime API calls.
3. No Node.js, npm, Docker, Kubernetes, or third-party Python package is required to develop, test, or serve the site.
4. The offline audit uses Python standard-library modules only. Its JSON report is deterministic for unchanged repository bytes and path structure; no wall-clock timestamps, OS-specific paths, or network requests are emitted.
5. Reproducibility primitives use integer arithmetic, fixed boundary conditions, deterministic seeds, and explicit rule ranges. Do not substitute Math.random() or variable time steps into the reproducibility demo.
6. Browser self-tests must report actual results. Never hard-code a passed status.
7. Synthetic graph numbers must remain labelled as synthetic, never represented as measured ecosystem security, build size, or software performance data.
8. Security vulnerabilities must be handled by reproducible, non-destructive testing and responsible disclosure; do not launch attacks on third-party systems.
9. Do not imply dependency-free means vulnerability-free, or that GitHub Pages and browser platform dependencies vanish.
10. Preserve the original declaration and its satire. Distinguish rhetorical claims from observed metrics and documented evidence.

Verification commands (no installation):
    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

The browser test button runs a separate native-JavaScript suite.

11. Public ledger claims are scoped to GitHub metadata and Git tree filenames; a container/manifest marker alone does not establish a runtime dependency. Never turn unknown/partial into a negative finding.
12. QSOL-IMC catalogue categories are editorial. QSOL-CONTEXT is private and must never be queried, ingested, linked as public evidence, or exposed through the ledger. Its high-level provenance design is inspiration only.
13. Browser ledger code accesses only packaged same-origin static JSON. Only Python collector and manual deployment contact GitHub REST. No browser token.
14. Preserve canonical snapshot hashing. The receipt SHA-256 must exclude the digest itself. Regression tests must be able to run offline.

15. DOM-TRIBUNAL/1 compares a first-party direct DOM baseline against a *local illustrative* keyed reconciler only, never a production third-party framework.
16. Paired trials must share identical deterministic input, alternate candidate order, validate exact DOM identity/order/content after each phase, and discard measurements if correctness fails.
17. Timings are local observed measurements, not deterministic fixtures or global rankings. No precomputed benchmark results or claimed winners.
18. Receipt exports use WebCrypto SHA-256 over exact UTF-8 payload text. Offline verifier tests payload integrity/internal consistency, not trusted provenance or authentic timing.
19. No external packages, remote assets, telemetry, third-party network calls, or client-side GitHub API access in Tribunal.
