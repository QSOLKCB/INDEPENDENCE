# v1.0.1 — Original Real-Browser Evidence Preservation

**This is an archival/verification patch, not a new browser feature.** Original
GitHub Actions artifact `independence-real-browser-evidence` from run
[41112613136](https://github.com/QSOLKCB/INDEPENDENCE/actions/runs/41112613136),
artifact ID `13003029340`, has been preserved without changing a single ZIP byte.

The original ZIP is 6,182 bytes. GitHub's Actions archive checksum and direct
SHA-256 verification both report:

```text
76514017982d86c95003bd4f86ccdcf4404502ede4609ba8f7767b89ee6c396a
```

## Restore / verify from a fresh checkout

```sh
python3 scripts/verify_browser_archive.py
python3 scripts/verify_browser_archive.py --restore independence-real-browser-evidence.zip
python3 scripts/verify_browser_archive.py --archive independence-real-browser-evidence.zip
python3 -m unittest discover -s tests -p 'test_browser_archive.py' -v
```

The SHA256SUMS manifest also enumerates the **original four JSON members**;
to check them independently, extract the restored original ZIP into a clean
directory and run `sha256sum -c SHA256SUMS.txt` from that directory with the
ZIP and its four members. The verifier checks them directly without extraction.

The original ZIP was stored as **nine plain-text, lossless, 1,024-character
base64 fragments** (final fragment 52 characters) because binary repository
upload was unavailable through the connected editing interface. Each fragment
has an individually pinned Git blob SHA-1, and reconstruction is required to
match the entire original ZIP's exact SHA-256 before it can be considered
verified. Neither a re-zipped nor reformatted JSON substitute is accepted.

## What the evidence records

| Engine | Recorded scenarios | Browser assertions |
| --- | --- | ---: |
| Chromium 156 | normal (14), HTTP 503 (9), malformed JSON (9), narrow (14) | 46 |
| Firefox 158 | normal (14), HTTP 503 (9), malformed JSON (9), narrow (14) | 46 |
| **Total** | **8 browser scenarios** | **92 / 92 reported PASS** |

The narrow scenarios **requested** 390x844, but the actual browser-reported
inner widths were **469px** Chromium and **472px** Firefox. This was a
narrow-window smoke test, not an exact 390px physical mobile test.

**Provenance boundary:** The browser reports record Actions PR-test checkout
revision `9f5616aa76d1dd18448b8e0d1300f7c6eb43d3b3` and staged tree
SHA-256 `d0350fe0b9123a3f4a21766e84122e9299de2872a3baa7a4a123226a6e473d62`.
The PR head `63553a4118dea389547fdf5b821f9e04a50b9dd5` and subsequent
v1.0.0 tag commit `764aec4bda8381de2aed620037d5ff992dba25ea`
are different revisions. **This archive is not v1.0.0 production Pages
deployment verification** and does not independently authenticate GitHub's
or the browsers' execution. It cannot establish a Lean/SPARK theorem, general
software correctness, no security vulnerabilities or WCAG conformance.

See `metadata.json` and `SHA256SUMS.txt` for exact member bytes and
digests. The first-party website and deployed Pages allowlist remain unchanged.
