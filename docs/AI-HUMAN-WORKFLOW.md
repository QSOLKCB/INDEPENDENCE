# THE SECRET SOURCE — AI–Human GitHub Workflow (v0.6.0)

> **AI + WEB TECH = UNLIMITED POTENTIAL.**
>
> An optimistic engineering slogan, **not a scientific finding, literal
> limitlessness claim, productivity benchmark, or guarantee of accuracy**.

## The actual mechanism

The value does not come from asking a model to "build an app" and assuming it is
correct. It comes from a repeatable human-controlled development loop:

**Human goal → bounded specification → invariants → AI implementation →
executed verification → adversarial review → exact HEAD check → human merge and
manual deployment → feedback to the next version.**

The human supplies intent, prioritisation, authority, release approval, and
judgment. AI can propose implementations, explain trade-offs, generate tests,
investigate failures, and help review patches. GitHub retains the history and
the exact code being reviewed. Native browser standards allow a surprising
range of real applications without introducing a framework or package manager
when the problem does not require one.

This is **human–AI collaboration**, not AI autonomy or automatic correctness.
Tool observations (test output, exact Git SHAs, source diffs) are different from
an assistant's claims about those observations.

## Eight gates to reduce drift

1. **Intent:** State one observable user outcome. A broad aspiration alone is
   not a specification. Define what will be different after the PR.
2. **Scope:** Name files, behaviours and allowed dependencies. **Also name what
   must not change.** This forbids helpful but unrequested changes.
3. **Invariants:** Read existing project contracts before editing, including
   README, AGENTS.md or CLAUDE.md if present, and docs/INVARIANTS.md. Preserve
   determinism, formats, privacy, licensing, CSP, tests and user expectations.
4. **Implement:** Build the smallest reviewable patch on a feature branch.
   Separate a requested change from a speculative enhancement. Do not silently
   replace tools or architecture.
5. **Verify:** Run positive, negative, boundary and regression tests. Run the
   complete suite when feasible. Report the **exact command and outcome**,
   failures, skipped checks, and tooling limitations. Never claim a test ran
   when the tool could not execute it.
6. **Adversarial review:** Ask a reviewer to find counterexamples. Classify
   actionable findings by severity (P0/P1/P2/P3), reproduce where possible,
   and add a targeted regression test **before or with the repair**. AI review
   is valuable but is not formally independent proof.
7. **Fresh HEAD:** Re-fetch the PR branch head after every code change. Review
   the **exact full SHA** being merged. An older clean review does not cover a
   newer commit or dirty checkout. Keep the branch up to date.
8. **Human control:** Only the human decides whether to merge, trigger
   deployment, create tags, and publish claims. Inspect the deployed site
   separately from reviewing code.

A "done" response is not an outcome. **A merged, reproducible and observed
result** is a stronger outcome, though still not a proof of zero defects.

## A concrete anti-drift practice

**Unhelpful prompt:** "Make the page better and fix everything."

**Bounded prompt:** "Add an educational workflow section to index.html using
only new first-party workflow/* assets, documentation, browser checks and
stdlib Python tests. Preserve the exact dependency policy and the existing
automata, ledger, tribunal, museum and breeding experiments. No packages,
remote services, telemetry or refactors. Run tests, report actual results,
open a PR and provide its exact latest SHA for independent review. Do not
merge or deploy without approval."

The second prompt reduces ambiguity because it states:
- the observable change;
- the positive scope and **negative scope**;
- existing invariants and intended interfaces;
- verification and evidence;
- explicit authority limits.

**This reduces predictable failure modes.** It does not guarantee that any
particular AI response will be correct or that the agent will obey every rule.

## The hostile-review loop

A practical review request:

> Review ONLY this PR at HEAD <full SHA>, against the task and
> docs/INVARIANTS.md. Prioritise actual regressions, broken trust boundaries,
> non-determinism, missing negative tests, compatibility and unsupported
> claims. Return P0/P1/P2/P3 findings with file/line, minimal reproduction,
> expected/actual behaviour and evidence. Do not invent findings. Do not
> introduce new features.

For a finding:

> Apply a minimal repair for the reproduced issue at the latest PR HEAD. Add
> a regression test that fails before the fix and passes afterward. Preserve
> unrelated files, repository contracts, hashing and public APIs. Run all
> available tests, list unrun checks explicitly, then report the new HEAD SHA
> for another review. Do not merge.

If an AI silently broadens scope, claims a test ran without a tool result, or
cannot distinguish fact from inference, **stop the task and respecify the
contract**. Never reward confident drift with an unverified merge.

## Real INDEPENDENCE examples — check the sources

These five PRs are public records of the project, not a controlled experiment
comparing AI-only or human-only productivity:

| Phase | Merged PR | Engineering lesson |
| --- | --- | --- |
| Declaration | [#1](https://github.com/QSOLKCB/INDEPENDENCE/pull/1) | Start with explicit dependency and reproducibility constraints |
| Evidence Ledger | [#2](https://github.com/QSOLKCB/INDEPENDENCE/pull/2) | Distinguish observed indicators from missing or unknown data |
| Dependency Tribunal | [#3](https://github.com/QSOLKCB/INDEPENDENCE/pull/3) | Define comparison scope, verification and statistical limitations |
| Gremlin Museum | [#4](https://github.com/QSOLKCB/INDEPENDENCE/pull/4) | A P2 review exposed a weak provenance prefix check; the branch gained exact-match validation and adversarial tests |
| Gremlin Breeding Lab | [#5](https://github.com/QSOLKCB/INDEPENDENCE/pull/5) | A bounded mutation suite reveals the difference between passing tests and detecting defects |

A report that a review had "no issues" means only that no issues were
reported in that review, not that the code is flawless. The official releases
were tagged and published separately, by the maintainer.

## Browser guide and local prompt composer

The site section at [/#workflow](https://qsolkcb.github.io/INDEPENDENCE/#workflow)
provides eight navigable stages, a self-reported checklist and a prompt
composer. The composer **does not use AI**. It converts typed plain text into a
visible, copyable task contract. If a required goal is missing or a field is
overlong, it refuses to generate.

All inputs stay in page memory. No local storage, tracking, form submission,
external endpoints, or network-based prompt generation. Copy requires the
browser clipboard permission and may be unavailable without a secure context.
No checklist state or prompt is saved for the next session.

## Limits and responsibility

"Unlimited potential" describes creative possibilities, not unlimited
compute, budgets, reliability, or legal authority. Good uses of AI include
ideation, code authoring, targeted debugging, tests, explanatory docs and
structured review. The user remains responsible for security, licensing,
access control, claims, and external deployments. AI-generated code and
review comments can be wrong; two AI systems agreeing is not independent
evidence of truth.

This project does not measure AI coding accuracy, quantify a reduction in
drift, endorse a specific model as infallible, or establish that low
dependency count guarantees security.

## Reproduction

    python3 -m unittest discover -s tests -v
    python3 scripts/audit.py --json
    python3 -m http.server 8000

Open http://localhost:8000/#workflow. Run browser self-checks from the
Evidence section; inspect source under workflow/. No packages are needed.
