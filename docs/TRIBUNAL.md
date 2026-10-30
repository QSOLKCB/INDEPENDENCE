# DOM-TRIBUNAL/1 — Controlled Local Comparison Protocol

## Research question, candidates, boundaries

Can two first-party JavaScript implementations perform an identical fixed DOM workload and provide transparent locally measured differences? This experiment compares:

- **Direct DOM:** rebuild each LI from scratch for each phase.
- **Local keyed adapter:** preserve nodes by stable ID, patch content and set deterministic order.

The keyed adapter is intentionally small and illustrative. **It is NOT React, Vue, Svelte, Angular, or representative of any production framework.** It does not measure those frameworks' bundle sizes, patching, performance, ergonomics, accessibility, maintenance, security or supply-chain requirements. Real framework trials must be separate version-pinned, licensed, opt-in projects with equivalent workloads and environments.

## Paired methodology

1. Fixed xorshift32 seed produces N stable IDs and labels with no network access.
2. Workload consists of initial list render, even-index label updates, and filtering/reversing the list.
3. Each candidate uses a fresh detached UL. Only synchronous adapter render calls are timed with performance.now().
4. Resulting LI count, stable ID, order and text are checked outside each timed phase. A mismatch fails the run and prevents export.
5. Warmup pairs are discarded; measured order alternates per pair to reduce simple order bias. Tab visibility is required.
6. Report candidate medians, paired keyed-minus-direct median differences, and seeded 512-resample percentile 95% bootstrap intervals per phase.
7. Source-file byte lengths are measured with same-origin fetch of the two adapters after the benchmark. Shared runner/website and browser/OS runtime are excluded.
8. Each export contains raw paired millisecond samples, parameter values, fixture fingerprints, summary values, explicit scope and an exact UTF-8 payload text hashed with WebCrypto SHA-256. No results are uploaded.

## Reproduction

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Visit http://localhost:8000/#tribunal, run the paired experiment, then download a receipt. A browser secure context (HTTPS or localhost) is required for the WebCrypto SHA-256 export.

    python3 scripts/verify_tribunal.py /path/to/tribunal-xxxx.json --json

The stdlib verifier validates exact payload-text SHA-256, expected protocol, finite paired samples, correct trial counts, reported medians and metadata consistency. A SHA-256 receipt is not signed, and does not attest that a real browser produced the data: someone can fabricate a self-consistent receipt. Independent replication requires trusted capture and environment provenance.

## Statistical and engineering limits

Bootstrap intervals quantify resampling variability within observed paired samples, not environmental confidence. Browser engine, JIT, garbage collection, CPU frequency, other tasks and timer precision affect measurements. A zero-duration sample is flagged as insufficient timer resolution. Detached DOM mutations exclude layout and painting; this is not frames-per-second performance. No significance badge or global winner is shown.

The keyed approach has more abstraction and JS source but can reuse node identity; direct replacement has a smaller adapter but recreates nodes. That is an engineering tradeoff for this specific test, not a universal result.

No production framework or third-party dependency is installed to run this release.
