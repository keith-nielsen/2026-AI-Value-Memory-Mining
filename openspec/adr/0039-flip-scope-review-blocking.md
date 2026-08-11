<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0039 — Flip the declared-scope gate to blocking (Phase B), while its check context stays unrequired

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-08-06)
**Date:** 2026-08-06 · **Recorded retroactively 2026-08-11** (see *Provenance*)
**Change:** `flip-scope-review-blocking` (PR #58, merged 2026-08-06; archived by PR #59). The change
carried the `maintenance` spec delta and the `ci.yml` edit; this ADR records the decision behind them.
**Relates:** **ADR-0034** (server-side branch & tag rulesets — establishes `required_status_checks` and
the Enterprise-only `evaluate` limitation this ADR runs into); **ADR-0038** (completion of the required
check contexts — 13 → 16, the work this gate is queued behind).

---

## Provenance — why this ADR is dated 2026-08-06 but written 2026-08-11

`.github/workflows/ci.yml:513` has cited *"Phase B (ADR-0039): BLOCKING"* since PR #58. **No such ADR
existed.** The originating change never planned one — its proposal cites ADR-0034 and ADR-0038 only —
so the number was coined in the comment and never redeemed. Discovered 2026-08-11 while auditing ADR
citation integrity; 40 distinct ADR ids were cited corpus-wide against 38 files on disk.

This ADR is written to make the existing citation true, and its content is **consolidated from
artifacts that already existed** (the `ci.yml` comment block and `flip-scope-review-blocking`'s
proposal) rather than reconstructed from memory. The alternative — deleting the claim by rewriting the
comment to cite the change slug — was considered and rejected: the decision has a real sacrifice and a
named unresolved follow-on, which is ADR-shaped, and ADR-0038 is precedent for a recording-only ADR
written after the fact.

The companion change `enforce-adr-reference-integrity` adds the check that would have caught this at
the time. **That check cannot pass until this ADR exists**, which is why the two ship together.

## Context

`scope-review` is the declared-scope gate: it extracts a declared scope from the pull request body,
diffs the branch against its merge base, and reports work the body did not declare. It answers the
overreach failure class — a change that quietly grows past what it proposed — which prose review
catches unreliably and late.

It shipped in Phase A as **advisory**: `continue-on-error: true`, so a finding was visible but never
consequential. Advisory gates decay; the question was when it had earned consequence.

The burn-in answered it with a denominator rather than an impression: **14 consecutive merged pull
requests, #41 through #57, every one `success`.** No false positive was observed across that window,
so flipping it could not silently convert routine work into blocked work.

Two platform facts constrain how far the flip can go:

- The job is `skipped` on the `push` trigger and on `dependabot[bot]` pull requests (both `if` clauses).
- Whether GitHub counts a `skipped` conclusion as **satisfying** a required context **cannot be
  dry-run on this plan** — ADR-0034 records that ruleset `evaluate` enforcement is Enterprise-only.

So "make it blocking" and "make it required" are separable, and only the first is safely decidable now.

## Options

1. **Remain advisory indefinitely.** Zero risk of a false block; the gate never binds, and a finding
   nobody must act on trains readers to scroll past it. Rejected — this is the state the burn-in
   existed to end.
2. **Flip to blocking AND add to `required_status_checks` together.** Maximum enforcement in one step.
   Rejected: with the `skipped`-conclusion question undecidable on this plan, adding the context risks
   a permanently unsatisfiable required check on exactly the pull requests where the job does not run
   (push-triggered, dependabot) — a merge deadlock introduced by a gate meant to prevent overreach.
3. **Flip to blocking; leave the context unrequired; bind through the driver.** Chosen.

## Decision

Remove `continue-on-error` from the `scope-review` job. A scope finding now fails the check.

**Do not** add `Scope review` to the `main` ruleset's `required_status_checks` yet. Until the
`skipped`-conclusion question is settled, the gate binds through **`pr-flow.py` step 8**, which
refuses to emit a merge command while any check is failing. The enforcement is real; its enforcer is
the driver rather than the platform.

**The job name dropped ", burn-in" in this same change — deliberately, while the context was still
UNREQUIRED.** The check-context identity *is* the job name: renaming a context that appears in
`required_status_checks` leaves the ruleset waiting forever on a name nothing will report, which
deadlocks every merge. Renaming was therefore free at this moment and would not be free afterwards.
This ordering is load-bearing and is the single most reusable fact in this record.

## Consequences

- A pull request whose diff exceeds its declared scope now fails a check, and `pr-flow.py` will not
  emit its merge. The remedy is to correct the pull request **body**, then **push** — a body-derived
  check reads the event payload as of push time, so re-running the job after editing the body does not
  pick up the correction.
- Work that a change did not propose can no longer ride along in its pull request. This is the
  intended effect, and it means genuinely separate concerns must be split into their own changes.
- The gate is invisible on push-triggered runs and on dependabot pull requests, where the job is
  `skipped`. Those paths are ungated by this mechanism.
- Enforcement depends on the driver being used. A merge performed outside `pr-flow.py` bypasses the
  binding entirely, because the platform is not yet holding the context.

## Sacrifice (what is knowingly given up)

**A false positive can now block legitimate work**, and the gate's input is a human-written pull
request body — the least reliable input in the ceremony. Fourteen clean pull requests bound the risk;
they do not eliminate it. We accept a class of avoidable friction in exchange for scope drift becoming
mechanically visible rather than dependent on a reviewer noticing.

**We also accept a knowingly incomplete enforcement chain**: blocking but unrequired, held by a local
driver rather than by the server. That is weaker than the rulesets ADR-0034 established, and it is
recorded here as a deliberate interim state rather than presented as finished.

## Follow-on

**Trigger:** resolve whether a `skipped` conclusion satisfies a required context on this plan (it
cannot be dry-run — ADR-0034). **Then:** add `Scope review` to the `main` ruleset's
`required_status_checks`, moving the binding from `pr-flow.py` to the platform, and record the
completion the way ADR-0038 recorded its own.
