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

20. GREMLIN-MUSEUM/1 contains only fixed, inert local specimens. Never execute injected HTML, import remote code, touch real files via traversal, perform credential operations, or contact third-party services.
21. Historical review reproductions must be explicitly distinguished from illustrative cases. A class of failure is not automatically an exploit, CVE, or discovered project vulnerability.
22. Museum displays all input and observations with textContent, never innerHTML/eval/script injection. No user-provided arbitrary script, external target or remote payload execution is permitted.
23. Each exhibit must include a reproducible failing legacy condition, a corrected condition, meaningful assertions and provenance. Failed tests must prevent receipt export.
24. SHA-256 receipt verification checks exact payload integrity and fixed-fixture consistency, never authorship, vulnerability absence, or deployment safety.

25. GREMLIN-BREEDING/1 mutations are predeclared alternative pure functions over inert inputs. Never mutate deployed source, eval generated code, load packages, access files or contact external targets.
26. Baseline must pass the full oracle case set regardless of selected suite, and every mutant must have a concrete divergent witness; equivalent or unproven cases fail closed.
27. A survived mutant is a known divergence not detected by the selected suite. Mutation scores apply to curated fixtures only, not the repository or its security.
28. Seeded order, fixed IDs, observed failures and selected suite must be reproducible. Python verification independently checks fixed expectations and order but does not attest authentic execution.
29. UI renders findings through textContent, prevents export after failure and never sends measurements to a server.

30. AI-HUMAN-WORKFLOW/1 describes the human-controlled development process; the slogan "unlimited potential" must be labelled aspirational, not quantified, literal, guaranteed, or scientifically established.
31. AI's suggestions are not evidence of a successful test, review or deployment. Separate source-backed facts, tool observations, explicit human reports, and hypothetical examples.
32. The browser guide is educational only: its checklist is self-reported, never a code or security audit, and must not claim that ticking boxes authorises a merge.
33. The agent handoff composer is entirely local, plain text and never sends inputs to an AI, GitHub API or other server. No credentials, persistence, hidden telemetry, dynamic execution, or untrusted HTML rendering.
34. Preserve human authority over merges, deployments, releases, task scope and risk acceptance. Require a fresh PR HEAD SHA and rerun meaningful review after code changes.
35. The workflow's historical PR examples must use correct, publicly inspectable INDEPENDENCE PR URLs. Claims of reduced drift or improved accuracy remain qualitative recommendations unless tested in a controlled study.

36. PROOF-CONTRACTS/1 is a machine-readable specification and evidence ledger, NOT a claim of universal or mathematical correctness; every obligation names scope and currently says NOT_PROVED.
37. Bounded exhaustive results apply only to finite stated domains. Model-to-production-code equivalence must be established separately.
38. Preserve and report the mutable Uint8Array/fingerprint counterexample. v0.7 must not silently change the public automaton API to hide it.
39. Never report Lean/SPARK as PROVED without actual checked artefacts, source/version/assumption records and resolved obligations.
40. SHA-256 receipt integrity and a self-consistent report do not authenticate an actual browser run.
41. The stdlib registry gate rejects false proof statuses, malformed obligations, missing target symbols and missing provenance/limitations.
42. Proof dashboard results must come from user-triggered execution against real first-party functions, and be rendered only with inert textContent.
43. Lean, SPARK, GNATprove and other optional proof toolchains remain development-only and cannot become GitHub Pages or Python-stdlib runtime dependencies.

44. SPARK-REFERENCE-KERNEL/1 uses a human-reviewable shared versioned specification and pure Ada functions. The CLI and all input/output concerns remain outside the SPARK proof boundary.
45. A declared Ada Pre/Post contract is NOT a discharged proof. Never report ADA_CONTRACT_VERIFIED unless actual GNATprove output at an exact source revision and recorded toolchain is verified.
46. Never treat rectangular addresses as CRT bijection, in-range distinct endpoints as proven graph adjacency, or modular phase closure as quantum phase behaviour.
47. Explicit modular integer input checking must occur before converting CLI parameters to Ada mod-2 or mod-3 types; invalid inputs must be rejected, not silently wrapped.
48. Keep GNATprove, GNAT, Ada compiler and CLI out of the GitHub Pages runtime and default Python-only deployment gate.
49. Python and JavaScript remain separate, unresolved conformance obligations until differential execution evidence exists.

50. Proof-Conformance Bridge version 1 treats the shared kernel specification, not Ada or Python source, as the authority. No Ada proof implies Python or JavaScript correctness by association.
51. Python conformance must compare a distinct implementation with an independently constructed oracle over exactly declared finite input domains; invalid inputs must be tested separately.
52. The optional Ada CLI must be genuinely executed and checked on recorded inputs. When no executable/toolchain exists, the only permitted result is NOT_RUN; a supplied matching executable is marked UNATTESTED without binary provenance.
53. Lean mathematical theorem status, GNATprove contract status, Python conformance and Ada runtime agreement are independent receipt fields. Unproved or unexecuted obligations remain unresolved even if other fields pass.
54. Source/spec hashes bind local bytes but neither a checksum nor a Python verifier authenticates real execution. Never report a successful application-wide Python or JavaScript proof from reference fixtures.
