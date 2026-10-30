# INDEPENDENCE v1.1.0 — Research Formalisation Package

The **original, byte-preserved** Lean/SPARK/Ada/JS and Rocq local proof evidence archives are checked into this folder. Their SHA-256 digests and full 15-member file inventories are in \`evidence-manifest.json\`.

| File | Purpose |
|---|---|
| \`FORMALISATION_REPORT.md\` | Full paper-style report, evidence classes, methods, theorem inventory, limitations and research argument |
| \`automata4-proof-archive.tar.gz\` | Original local AUTOMATA4 Lean/SPARK/Ada/JS proof and finite-execution receipts (3,473 bytes) |
| \`INDEPENDENCE-rocq-proof-evidence.tar.gz\` | Original Rocq 9.2 proof source, local compiler receipt and toolchain inventory (3,658 bytes) |
| \`evidence-manifest.json\` | Independent original archive and member SHA-256 pins; provenance and claim limits |
| \`ZENODO_METADATA.md\` | Proposed record description, keywords, citation and metadata safety checks |

The original browser PR evidence is already separately preserved in \`formal/evidence/browser/v1.0.1/base64/\`; its exact 6,182-byte ZIP SHA-256 is \`76514017982d86c95003bd4f86ccdcf4404502ede4609ba8f7767b89ee6c396a\`.

Run the **Python-stdlib-only** verification gates:

\`\`\`sh
python3 scripts/verify_formalisation_archive.py --output formalisation-integrity.json
python3 -m unittest discover -s tests -p 'test_formalisation_archive.py' -v
python3 scripts/verify_browser_archive.py
\`\`\`

Passing these proves original archive *byte integrity and internal receipt consistency*, not independent execution attestation. The Rocq \`.vo\` is not in the uploaded archive, only its recorded digest. A final v1.1.0 GitHub tag and public Zenodo record must be checked before claiming publication.
