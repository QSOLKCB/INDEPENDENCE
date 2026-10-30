# Original Ada/Python runtime evidence — v0.7.4

The user uploaded `INDEPENDENCE-proof-evidence.zip` together with a matching SHA-256 checksum file. The ZIP integrity check passed (23 entries). **This folder contains the byte-identical original sample and full Ada runtime JSON files**, stored as Git blobs verified against the original ZIP entry bytes.

| Evidence | Ada comparisons | SHA-256 |
| --- | ---: | --- |
| `ada-runtime-evidence.json` | 150 | `78ce9e40d221634391a9cf6a982848521369efa0bd9926459ec028a649e87aa6` |
| `ada-runtime-evidence-full.json` | 8,903 | `3dff931e123f55f0b3e7e8f3a8247d381d06cfbbb1135dc3fb637b03eba80b0a` |

Original ZIP SHA-256: `429b946d083c2b0562450704f924eb3370e5c9a9c62eb81ef5ac90d41a5e2256`.

The binary ZIP itself is **not** committed to Git; preserve it and the accompanying checksum file for the intended Zenodo v1.1.0 deposit. The original uploaded `spark-evidence.json` also matches the earlier committed `formal/evidence/spark/pr13/spark-evidence.json` exactly. The Lean file in the ZIP is a copy of the previously archived transcript-reconstructed Lean record, and its original-file provenance is unchanged.

## Source, proof and execution boundaries

- GNATprove's analyzed Ada source: PR #13 HEAD `9900e57f2283c534815657dd6c079d0e966715f4`.
- Sample runtime runner checkout: PR #15 HEAD `554627bdd8813b6106624f5e435659fbabb5f9c5`.
- Full runtime runner checkout: PR #15 merged `main` `765e00d7f6a361b0ee3744157c2a35c9dfc7ae59`.
- Sample and full runs report the same compiled-binary SHA-256: `9d74484857e3937586003a0dea2a648704c58e039ad6812b8a75167b1169fddf`.
- The recorded GNATmake version is 16.1.0 and GPRbuild is 26.0.0.
- Both records retain `independent_execution_attestation: false`.

Reproduce self-consistency checks:

```bash
python3 scripts/verify_ada_runtime_evidence.py formal/evidence/ada-runtime/v0.7.4/ada-runtime-evidence.json
python3 scripts/verify_ada_runtime_evidence.py formal/evidence/ada-runtime/v0.7.4/ada-runtime-evidence-full.json
python3 scripts/verify_original_ada_evidence.py
```

Internal consistency checks and hash matches confirm the preserved bytes and reported results, **not independent attestation of execution**, proof of CLI parsing or correctness of arbitrary JavaScript/Python applications. See `manifest.json` for exact file identities, prior archives and limitations.
