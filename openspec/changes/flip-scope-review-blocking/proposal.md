<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: flip-scope-review-blocking

## Why

The `scope-review` job has been **report-only since 2026-07-14** — `continue-on-error: true`, Phase A
burn-in. The `maintenance` spec anticipated exactly this change: *"the flip to blocking is its own
governed change after clean burn-in."*

Two things make it overdue rather than merely due:

1. **`pr-flow.py` validates the declared-scope block before opening a PR and reports it verified.** A
   gate that reports verification while being incapable of failing is the class-9 shape — assurance
   asserted by something with no power to withhold it.
2. **The plan of record said "watch 3–5 PRs → Phase-B flip."** It has been ~23 merged PRs.

**Burn-in measured, not assumed:** the 14 most recent merged PRs (#41–#57) were sampled via the
check-runs API. `scope-review` concluded **`success` on every one; zero failures.** The precondition
the spec names is satisfied by evidence, not by elapsed time.

## What Changes

- **`.github/workflows/ci.yml`** — remove `continue-on-error: true` from `scope-review`; the job can
  now fail a run. Comment rewritten to state where the block binds and where it does not.
- **Job renamed** `Scope review (declared-scope gate, burn-in)` → `Scope review (declared-scope gate)`.
  **The name is the check-context identity**, so this is done deliberately *now*, while the context is
  still **absent** from the ruleset's required contexts. Renaming a required context deadlocks merges.
- **MODIFIED requirement** (`maintenance`, *Scope-Review CI Gate*) — the two-stage bullet is replaced
  by the completed end state, plus an explicit statement of **where the block binds**. Two scenarios
  added: failures are unsuppressed, and renaming happens only while unrequired.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance` — *Scope-Review CI Gate (Declared Scope)*: Phase-A burn-in bullet → Phase-B blocking;
  binding surface stated; two scenarios added.

## Deliberately NOT in this change

**Adding `Scope review` to the ruleset's `required_status_checks`.** The job is `skipped` on the
`push` trigger (its `if` excludes it) and on **dependabot** PRs (actor excluded) — measured: dependabot
#48 emits the context as skipped. Whether GitHub counts a `skipped` conclusion as satisfying a required
context **cannot be dry-run on this plan** (ADR-0034: `evaluate` enforcement is Enterprise-only), and a
wrong required context deadlocks every merge.

So the flip binds through **`pr-flow.py` step 8**, which refuses to emit a merge command while any
check is failing. That is a real block today, applied by the tool the ceremony already mandates.
Adding the ruleset context is a separate decision with the skipped-conclusion question attached —
recorded, with its trigger, rather than left open-ended. This is the same discipline ADR-0038 used for
its own two exclusions.

## Impact

`.github/workflows/ci.yml` (one job) · `openspec/specs/maintenance/spec.md` (one MODIFIED requirement,
via the change's spec delta). No `.py` changes; no `vault-template/` delta; no schema change.

**Behaviour change to be aware of:** any PR whose diff touches a path outside its declared `scope`
block now **fails CI** rather than reporting quietly. That is the intent, and it will bite the first
author who forgets to widen a declaration — including on ceremony changes, where the declaration must
mirror the Gate-1 blast radius.

**This PR is its own first live test:** the flipped, renamed job must pass on this very change before
it can merge.
