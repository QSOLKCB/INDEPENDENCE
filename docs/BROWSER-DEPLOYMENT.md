# v1.0.0 — Real-Browser and GitHub Pages Verification

**Protocols:** PAGES-ARTIFACT/1, REAL-BROWSER-JOURNEYS/1,
GITHUB-PAGES-OBSERVATION/1. Development-only checks; no runtime packages.

## What is executed

1. **Exact artifact stage:** scripts/site_bundle.py selects only the
   source-reviewed first-party asset allowlist plus .nojekyll; includes
   deployment-manifest.json containing commit revision, path hashes and
   a canonical tree digest. Missing, extra, modified and symlinked assets
   fail closed; HTML is parsed to check CSP, module entry, stylesheet
   closure and unique IDs. This also catches the old missing-greater-than
   stylesheet regression that once swallowed app.js.
2. **Real browser engines:** scripts/run_browser_journeys.py launches actual
   headless Chromium via its binary; scripts/firefox_journeys.py launches
   Firefox using the W3C WebDriver protocol and Geckodriver. Both run the
   same real DOM harness in a loopback HTTP server against **staged bytes**,
   not the source tree or a simulated DOM.
3. **Journeys:** initial app module and automaton generation; replay
   equality; actual first-party native browser self-tests; 4,096-vector
   browser formal lab and local WebCrypto receipt; seeded Property Lab;
   static ledger loading/search; local workflow handoff; script-src CSP
   inline-code rejection; runtime resource-origin inspection; semantic
   landmarks, accessible names and horizontal-layout bounds.
4. **Faults:** the local server deliberately returns HTTP 503 or malformed
   JSON for packaged ledger/data.json. Both cases must clear records and
   report unavailable evidence, without disabling unrelated app modules.
   This is a local HTTP fixture, **not** a production GitHub incident.
   Separately, earlier v0.2 standard-library collector tests continue to
   exercise fake GitHub REST responses without live GitHub traffic.
5. **Remote deployment:** after the manually triggered GitHub Pages
   deployment succeeds, scripts/verify_deployed_site.py fetches the exact
   official HTTPS QSOLKCB/INDEPENDENCE path and matches the deployed manifest
   and *every asset byte* to the staged checksums. No arbitrary URL targets,
   credentials or browser-origin remote calls.

## Reproduce

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 scripts/site_bundle.py stage --source . --site /tmp/independence-site --revision "$(git rev-parse HEAD)"
    python3 scripts/site_bundle.py verify --source . --site /tmp/independence-site --revision "$(git rev-parse HEAD)"
    python3 scripts/run_browser_journeys.py --site /tmp/independence-site --require-browser --output chromium.json
    python3 scripts/firefox_journeys.py --site /tmp/independence-site --require-browser --output firefox.json

After deploying **only** to https://qsolkcb.github.io/INDEPENDENCE/ :

    python3 scripts/verify_deployed_site.py --manifest /tmp/independence-site/deployment-manifest.json --attempts 8 --delay 5 --output public-pages.json

Browser installs and drivers are optional local developer tools; the PR and
Pages CI use preinstalled GitHub-hosted runners. The site itself remains
plain first-party HTML, CSS and JavaScript. Python 3 stdlib is sufficient
to build and inspect the artifact offline; no Node/npm/pip/containers.

## Evidence and exclusions

- A real Chromium or Firefox result records the actual browser binary
  version, checked SHA-256 manifest and revision, journey assertions,
  negative-test outcomes and raw-output hash. Missing browser = NOT_RUN
  or a blocking strict-gate failure.
- A passing local browser is not proof of cross-device, accessibility
  standard, or production CDN correctness. The labels/landmark/overflow
  assertions are scoped smoke checks, **not a WCAG audit**.
- Post-deploy HTTPS observations verify specific bytes at a point in time
  only, not continuous uptime, authorship, absence of vulnerabilities, or
  that a remote visitor exercised JavaScript.
- The browser page itself never queries the GitHub API; it consumes only
  same-origin packaged JSON and has no new dependencies or telemetry.
- v0.9 Lean/SPARK model proofs remain separate and are not promoted by
  v1.0 browser/deployment evidence.
- Running against an exact staged artifact is intentionally different
  from executing browsers against a live, mutable production URL.


## Narrow responsive browser execution

Both developer browser runners support `--width 390 --height 844 --normal-only`
to execute the normal real DOM journey in a narrow window. The result records
the actual observed viewport, and fails if a requested narrow viewport is
ignored. The PR CI and the manual Pages preflight require narrow Chromium and
Firefox passes, separately from the standard 1280px three-scenario runs.
This is a responsive smoke test, **not** a device emulator or a full
WCAG/visual-regression audit.

## Public CDN propagation and honest deployment status

GitHub Pages can report the deployment action as successful before every
newly uploaded URL is observable from all public CDN edges. The original
v1.0.0 workflow incorrectly made the entire deployment run fail when the
separate public-byte verification returned HTTP 404 shortly after publish.
The actual deployment action had already reported SUCCESS.

The workflow now distinguishes:

- **Deployment: SUCCESS** means `actions/deploy-pages@v4` completed.
- **Public byte observation: REMOTE_BYTES_MATCHED_UNATTESTED** means the exact
  publicly fetched deployment manifest and all file hashes matched.
- **Public byte observation: NOT_VERIFIED** means the observation failed,
  with the exact requested URL and HTTP code recorded. It is **never** counted
  as a public match or proof of website availability.

Each deploy stores the *exact deployed manifest* as a separately downloadable
Actions artifact called `independence-pages-manifest`. This is essential
because `ledger/data.json` can be freshly collected during each deploy,
so regenerating a manifest from a later Git checkout can change the bytes.

If propagation takes longer than the in-run bounded retries, launch the
**Verify Published INDEPENDENCE Bytes** workflow manually, entering the
original **deployment workflow run ID**. It downloads that run's original
`github-pages` artifact, extracts only `./deployment-manifest.json` from
`artifact.tar`, and strictly retries official HTTPS byte matching.
This also works with historical deployment run **41113714704**, whose
upload artifact was verified to contain both index.html and the exact
deployment-manifest.json. No republishing is needed to repeat the
observation, and a missing page is never silently treated as verified. A failed follow-up
verification run remains red, with a `NOT_VERIFIED` JSON evidence artifact.

If the main website remains 404 after propagation, inspect the repository's
Settings → Pages → Build and deployment → Source (GitHub Actions), and
review the Pages deployment logs. Do not attribute a persistent 404 to
propagation without evidence.

## Manifest artifact precedence — follow-up observation

The standalone `independence-pages-manifest` is the preferred exact source
for any deployment run that uploaded it. Unlike the special `github-pages`
upload, which defaults to roughly one-day retention, this independent upload
follows repository artifact-retention settings. The follow-up verifier first
downloads the standalone manifest. **Only if that artifact cannot be
downloaded** does it request the short-lived `github-pages` archive and
extract the historical manifest from its `artifact.tar`. The fallback
remains useful for early deployment runs such as `41113714704` while the
archive is retained.

Both paths pass through `scripts/select_public_manifest.py`: the exact
manifest must satisfy its strict checksum/schema contract before comparison.
An already-downloaded but corrupt primary manifest **fails closed**; it is
never silently replaced with data from another source. When both sources
are unavailable, the selector emits `NOT_VERIFIED` evidence and the
workflow fails instead of inventing a successful remote observation.
