# v0.9.0 — Lean 4 + SPARK/Ada Automaton Proof Laboratory

AUTOMATON-SEMANTICS/1 defines the next bit of an elementary cellular
automaton: left, center, right are 0/1; rule is 0..255; index equals
4*left + 2*center + right; output is floor(rule / 2^index) modulo 2.
Missing row neighbours are literal zero. This model matches the intended
production semantics, but is not by itself a proof of the JavaScript source.

## Four distinct execution and proof boundaries

1. Lean 4.35.0 in formal/lean/AutomatonFinite.lean declares five finite
   theorem candidates: index bounds, all-zero/all-one rules, rule 90 XOR,
   and the rule-90 fixed-zero left edge. The runner invokes lean --trust=0
   and checks five transitive axiom inventories if explicitly requested.
   Source inspection alone is NOT a Lean proof.
2. SPARK/Ada in formal/spark/automaton_kernel.ads and .adb specifies
   bit arithmetic with a postcondition. GNATprove can analyze the pure kernel,
   not the unverified CLI input/output boundary.
3. The separate automaton_cli.adb validates four exact ASCII decimal
   arguments in RULE LEFT CENTER RIGHT order. An optional compiled executable
   is checked on 128 deterministic valid cases and eight invalid inputs.
   The source and a simulated CLI are not counted as runtime comparisons.
4. Python independently checks all 2,048 neighbourhood truth-table vectors
   using division and shift oracles plus 512 one-cell boundary vectors.
   The browser calls the real first-party JavaScript evolve() on the same
   2,048 cases (including the two edge outputs of each 3-cell row), checks 512
   one-cell rows, and rejects unexpected typed-array source mutation.
   Both generate identical ASCII decimal lines, ascending in the order
   rule,left,center,right, in the format rule,left,center,right:output followed
   by an LF. SHA-256 of those bytes is the cross-runtime comparison key.

## Reproduction

Run without third-party packages, compiler, internet or Node.js:

    python3 scripts/automaton_proof_lab.py --output automaton-evidence.json
    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json

For real optional development-tool checks:

    python3 scripts/automaton_proof_lab.py --prove --require-proofs --output automaton-proofs.json
    gprbuild -P formal/spark/automaton.gpr
    python3 scripts/automaton_proof_lab.py --ada-cli formal/spark/bin/automaton_cli --require-ada

The user-triggered browser experiment at #formal-lab can export a SHA-256
receipt on HTTPS or localhost. Verify its exact bytes and finite vector digest:

    python3 scripts/automaton_proof_lab.py --browser-receipt /path/to/automaton-proof-lab-xxxxxxxxxxxx.json

## Limitations and claims

- Lean Nat.testBit and Bool model bit extraction on Fin 256. Kernel checking
  requires the actual pinned Lean version and five valid axiom audits; missing
  tools must yield NOT_RUN.
- SPARK Bit is modular 2 and Rule_Type is 0..255. GNATprove postcondition
  proofs do not analyze the CLI, the browser, or execution provenance.
- Within this bounded domain, JavaScript bitwise coercions coincide with
  the stated integer arithmetic. No claim is made for arbitrary JS inputs.
- A self-hash or internal replay is not independent attestation of execution.
  User-reported historical Lean/SPARK evidence covers previous formal files,
  not these new v0.9 theorem and contract sources.
- Matching 2,048 finite vectors does not constitute a universal formal
  refinement between Lean, Ada, Python and JavaScript.
- Production code, previous proof registry, v0.8 Property Lab and all
  archived historical proof artefacts are intentionally unchanged.
