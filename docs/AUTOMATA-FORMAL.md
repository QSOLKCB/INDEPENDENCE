# v0.9.0 — Lean 4 + SPARK/Ada Elementary-Automata Laboratory

## Scope of the new formal slice

This release adds a **separate, four-cell** binary elementary cellular automaton reference. The human-reviewable shared authority is `formal/spec/automata4-v1.json`. Its boundaries and bit ordering are explicit: four cells, 256 rules, simultaneous transitions, fixed-zero exterior cells, and the conventional `(rule // 2**(4*left+2*center+right)) % 2` neighborhood lookup.

The defined finite corpus has **256 × 16 = 4,096 rule/input vectors**, enumerated in numeric rule and left-to-right row-mask order. Its Python-independent-model digest is `f1ecce4798a35f6642a065a0ffbf87e6bdfcbb30ba0afffb5fb0da69c7c40635`. This corpus is **not** a universal proof, and only applies to width four.

## What is new, and what remains historical

- `formal/lean/AutomataReference.lean`: six new model theorem obligations: neighborhood index bound; rules 0 and 255 yielding constant output at each cell and across an entire four-cell row; and the known Rule-90 vector `0010 → 0101`.
- `formal/spark/automata_reference.ads/.adb`: new standalone SPARK-mode cell/neighborhood/Step4 reference, with declared exact postconditions. Its CLI is a **separate** Ada developer executable, not part of the SPARK proof boundary.
- `scripts/check_automata_formal.py`: Python stdlib orchestrator with mandatory static review gate, a deterministic independent 4,096-case reference, optional real Lean 4.35.0 kernel checking plus theorem-by-theorem transitive axiom audits, GNATprove check discharge, a fresh compiled Ada CLI differential run and optional first-party JavaScript differential run via a developer-installed Node runtime.
- `scripts/check_automata_js.mjs`: imports **the real production** `lab/core.js:evolve`, compares every one of 4,096 vectors, and confirms that each input typed array is unchanged. This is Node **developer tooling only**, not a browser dependency. Javascript semantics are still not formally refined from Lean/Ada.
- `tests/test_automata_formal.py`: stdlib regression tests for the finite corpus, pinned specification, proof escape rejection, unavailable tools, fake success outputs, and real source references.

The prior `formal/lean/FiniteFoundation.lean` (13 historically checked theorems) and the existing SPARK reference kernel (21 historically reported GNATprove checks) are **not modified or counted as new v0.9 proofs**. The original 150 and 8,903 Ada/Python runtime receipts remain immutable.

## Reproduce without new dependencies

These run on Python 3 stdlib, with **no** Lean, Ada, Node, npm, Docker or network required:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_automata_formal.py --output automata4-static.json
python3 scripts/audit.py --json
```

The status of each unexecuted optional proof/runtime class is `NOT_RUN`. The static script checks all 4,096 independently generated vectors and their pinned SHA-256. A finite scan is not proof of compiler correctness or of the browser.

## Execute real verification on a workstation

Use the exact pinned Lean toolchain `leanprover/lean4:v4.35.0` and the known GNATprove/GPRbuild installation. From the repository root:

```bash
export PATH="$HOME/opt/edgewalk-spark-toolchain/bin:$PATH"
lean --version
gnatprove --version
gprbuild --version

# Individual experiments can run without all tools installed:
python3 scripts/check_automata_formal.py --run-lean --output automata4-lean.json
python3 scripts/check_automata_formal.py --run-spark --output automata4-spark.json
python3 scripts/check_automata_formal.py --run-ada --output automata4-ada.json
python3 scripts/check_automata_formal.py --run-js --output automata4-js.json

# All stages must actually run and pass; any NOT_RUN, failed proof or mismatch blocks:
python3 scripts/check_automata_formal.py --require-all --output automata4-evidence.json
```

Lean is invoked with `lean --trust=0 formal/lean/AutomataReference.lean`. GNATprove uses its strict `--mode=all --checks-as-errors=on --warnings=error --report=all --level=2` options. The Ada compiler runs on **fresh temporary copies** of this version's sources, not stale objects. The CLI is executed for all 4,096 correct vectors plus invalid lexical/range/arity inputs, with **raw byte-exact output checking** and no stderr.

The optional Node 22 tool invokes the actual first-party source with `--experimental-default-type=module`; no `package.json` or npm install is introduced.

For each individual optional stage, a missing tool causes `NOT_RUN` and a nonzero exit status when explicitly requested. `--require-all` requires all four new stages to succeed before returning zero. Save the original JSON receipts and checkout Git SHA for a later Zenodo package.

## Proof boundary and open obligations

**A Lean model proof does not prove Ada, Python or production JavaScript; SPARK postconditions are not proven until real GNATprove output discharges all relevant checks; and 4,096 exact differential matches are not an executable refinement theorem.** No stage independently attests its own execution or compiler provenance. The Ada CLI's parsing and I/O remain outside SPARK. This model does not claim general cellular automaton widths, arbitrary Unicode/JSON inputs, Penrose geometry, or full application correctness.

## Verify captured tool output offline

The stdlib `scripts/verify_automata_evidence.py` checks exact source/spec identity,
the finite vector corpus, separate stage status schemas, recorded output SHA-256,
positive Lean theorem-by-theorem axiom declarations, positive GNATprove check
count and explicit unresolved-obligation rejection. It validates *internal
consistency*, **not** independently witnessed execution.

```bash
python3 scripts/verify_automata_evidence.py automata4-static.json
python3 scripts/verify_automata_evidence.py automata4-evidence.json
```

Requiring a new actual proof still requires executing `--run-lean`,
`--run-spark` or `--require-all` on a trusted local toolchain; a forged
self-consistent report is possible in principle.

The new proof/status vocabulary applies only to this `AUTOMATA4/1` revision and must not rewrite earlier evidence or existing proof-contract UI classifications.
