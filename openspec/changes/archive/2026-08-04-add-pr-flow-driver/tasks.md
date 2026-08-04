<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — add-pr-flow-driver

## 1. Gate 1 — CHECK (blast radius)

- [x] 1.1 `openspec/specs/maintenance/spec.md` — ADDED Requirements only; no existing Requirement
      modified or weakened
- [x] 1.2 `tools/pr-flow.py` (new), `tools/gh_read.py` (new), `tools/pr-state.py` (modified reads)
- [x] 1.3 `tests/test_pr_flow.py` (new)
- [x] 1.4 `CONTRIBUTING.md` — "Landing a change" section beside "Shipping a version"
- [x] 1.5 `CHANGELOG.md` — `[Unreleased]` entry
- [x] 1.6 Confirm NO `vault-template/` delta → no mirror, no `render`, no operator deploy step
- [x] 1.7 Confirm no new third-party dependency (stdlib `urllib` only)
- [x] 1.8 Re-confirmed 2026-08-04 after the design review: the second pass touched no new path
- [x] 1.9 **Scope block CORRECTED at close-out** — `README.md` **is** a new path. Its `tools/` inventory
      listed the fleet and omitted both tools this change adds, so it is updated and added to the
      declared scope. §1.8's "no new path" claim was true when written and is no longer; leaving it
      unqualified would have been a stale declaration in the change that exists to end those. The
      block is now: `CHANGELOG.md`, `CONTRIBUTING.md`, `README.md`,
      `openspec/changes/add-pr-flow-driver/`, `openspec/changes/archive/`,
      `openspec/specs/maintenance/spec.md`, `tests/test_pr_flow.py`, `tools/gh_read.py`,
      `tools/pr-flow.py`, `tools/pr-state.py`

## 2. Gate 2 — PLAN (build, first pass — complete)

- [x] 2.1 `tools/gh_read.py`: anonymous REST (Representational State Transfer) first, `gh` fallback,
      channel returned with every read
- [x] 2.2 `tools/pr-flow.py`: guards in order — worktree settled → base-current → commits exist →
      pushed → PR exists → head matches → checks green → merge → deletion verified
- [x] 2.3 Slug resolution made LAZY so the purely-local guards answer without a resolvable remote
- [x] 2.4 `--capabilities` probe: measures reads, `git` push (dry-run), `gh` auth; never raises
- [x] 2.5 `tools/pr-state.py`: degrade to anonymous channel; GraphQL-only layers report UNAVAILABLE
- [x] 2.6 Every emitted command carries an owner and a reason

## 3. Gate 3 — REGRESSION (first pass — complete)

- [x] 3.1 `tests/test_pr_flow.py` — offline, real git layers via a local bare origin
- [x] 3.2 Full suite green: **126 passed**
- [x] 3.3 `openspec validate --all --strict` clean under the pinned 1.6.0
- [x] 3.4 Dogfood `--capabilities` on the live repo
- [x] 3.5 Dogfood `pr-state.py` degraded path on merged PR #50 — **defect found and fixed**
- [x] 3.6 Dogfood `pr-flow.py` on this branch — correctly refused on an unclean worktree

## 3b. Flow review — all 49 pull requests in repo history (complete)

- [x] 3b.1 Enumerate #1–#50 from the API (application programming interface) and classify by shape
- [x] 3b.2 Bot/remote-only branch: explicit `refs/heads/` lookup; no rebase/push/delete for foreign
- [x] 3b.3 Local command with another branch checked out: emit `git switch` first
- [x] 3b.4 Stacked PR (#29, F21): refuse to merge while open children exist
- [x] 3b.5 Closed-unmerged PR (#18, #29): query all states
- [x] 3b.6 Completed-lifecycle re-run: report LIFECYCLE COMPLETE, restoring re-entrancy
- [x] 3b.7 Draft PRs and multiple-open-PRs-per-head refuse rather than guess

## 3c. Design review — 2026-08-04, four rounds (complete; findings recorded)

- [x] 3c.1 **Planning gap.** The driver is a step oracle, not a route oracle: it cannot answer "what
      is the whole route from here", so planning fell back to recall (root cause RC-8 / failure mode
      F24 — dialogue and
      status summaries are unbound by every mechanism built so far)
- [x] 3c.2 **Authority gap.** A single `owner` field conflated *who executes* with *whose authority
      is required*, reproducing the exact defect F30 names in this change's own Why
- [x] 3c.3 **Regression replay.** All recorded GitHub failures replayed: **17 of 22 prevented or
      detected**; 5 out of scope (2 → `ship-release.py`, 3 → `github-state-reconcile`)
- [x] 3c.4 **Race gap.** `measure → emit → ⟨unbounded gap⟩ → execute` is a TOCTOU (time-of-check to
      time-of-use) window that is
      unbounded for any operator-executed step
- [x] 3c.5 **Rate budget MEASURED.** Anonymous REST is 60/hour; a full invocation costs ~3 reads.
      `304 Not Modified` responses **do** decrement the anonymous budget (measured 57→56→55) —
      conditional-request caching does not buy headroom here, contrary to the common claim
- [x] 3c.6 **Established practice survey.** Standard names adopted: level-triggered, plan/apply
      separation, challenge-and-response, optimistic concurrency control, TOCTOU, readiness,
      RACI (responsible, accountable, consulted, informed) / four-eyes, merge skew, ordering
      determinism
- [x] 3c.7 **`gh pr merge --delete-branch` is defective on three counts** — no `sha` precondition
      (`cli/cli#5686`), defeats the platform's stacked-PR retargeting (`cli/cli#1168`, which is how
      #29 died), and is non-atomic under a success tick (F30·3)

## 3d. Gate 2 — PLAN (build, second pass — complete)

- [x] 3d.1 Refactor the guard chain into one ordered step table; the emitter and the planner walk
      the same traversal (no second list, so no drift)
- [x] 3d.2 Route header on every invocation; `--plan` full projection with measured/projected marks;
      no command text for a projected step
- [x] 3d.3 Split `owner` into executor / authority / consent; `approve:` block on operator-authority
      steps, kept short; consent class measured by evaluating the outbound guard
- [x] 3d.4 Step 0 (Gate-4 approval) measured from this file; steps 4 and 12 reassigned to
      agent-executes-under-consent
- [x] 3d.5 Zero check runs and uncomputed mergeability → NOT READY (exit 2), never green
- [x] 3d.6 `git fetch` return code checked; base freshness reported
- [x] 3d.7 `--body-file` validated (exists, carries a fenced `scope` block); never emit a placeholder
- [x] 3d.8 `body-current` step; corrections via the REST endpoint with a re-read; body-derived gate
      failure prescribes a push, not a re-run
- [x] 3d.9 Merge emitted as the REST call carrying `sha`; `--delete-branch` never emitted; deletion
      is a separate verified step
- [x] 3d.10 Children retarget emitted via the REST endpoint, then the base is re-read
- [x] 3d.11 Archive advisory before the merge step
- [x] 3d.12 Saved plan written to `.git/pr-flow/`, with an expiry, a printed full command for review
      and a short runnable form; `--assert-preconditions` runs inside it ahead of the mutation
- [x] 3d.13 `--ready STEP`: one request, one line, meaningful exit code; no blocking or sleeping
- [x] 3d.14 Rate budget surfaced in `--capabilities` and in every NOT READY report; the remaining/
      reset/`Retry-After` headers are captured from **every** response, including the 403 or 429 that
      explains an exhaustion. **No retry loop with backoff was built, deliberately**: the driver
      never blocks, so backoff belongs to whatever polls it. The stated poll floor is 60s. (The
      original wording of this item promised "backoff with full jitter" in the driver; that would
      have been a claim with no mechanism behind it, so the item is restated rather than ticked
      over.)
- [x] 3d.15 Never emit a push without an explicit effective-target redirect

## 3e. Gate 3 — REGRESSION (second pass — complete)

- [x] 3e.1 All existing cases in `tests/test_pr_flow.py` pass **unchanged** (the refactor's safety
      net)
- [x] 3e.2 New cases for every item in §3d, weighted to ordering, authority and postcondition
- [x] 3e.3 Full suite green; `openspec validate --all --strict` clean under the pinned 1.6.0
- [x] 3e.4 Dogfood `--plan` on this branch at its real mid-lifecycle position
- [x] 3e.5 Confirm no false denial on the allow-check shapes recorded in the proposal
- [x] 3e.6 **Dogfooding found a real defect, fixed and locked down.** `--plan` on this branch
      reported step 0 as `approval  MEASURED ok` while Gate 4 was **unsigned**: the check matched the
      word "Approved" anywhere, so the UNTICKED task *describing* the sign-off read as the sign-off
      itself. A declared end-state reported as reached — class 8 — inside the driver built to prevent
      it. Now asserted structurally on a ticked checkbox, and an unsigned Gate 4 REFUSES the merge
      step rather than merely annotating it.

## 4. Gate 4 — HUMAN SIGN-OFF

- [x] 4.1 Operator reviewed this proposal and recorded **Approved** — Keith Nielsen, 2026-08-04
      (transcribed by the agent from the operator's explicit reply; agents may not sign)
- [ ] 4.2 Open the PR with a fenced `scope` block covering every path in §1
- [ ] 4.3 Merge once checks are green
- [ ] 4.4 Archive on `main` in merge order; `openspec validate --all --strict` clean afterwards
- [ ] 4.5 Ship the version via `tools/ship-release.py` — tag → Release → parity tally

## 5. Queued separately (F29 — one change, one purpose)

- [ ] `github-state-reconcile` — level-triggered outward sibling of `vault-render.py reconcile`.
      Read-only over the anonymous API **by design**: the established tools for this job all require
      an admin-scoped write token, which would delete the credential absence that is the real
      invariant INV-14 barrier. Must compare content, not timestamps — ruleset parameters can
      change without bumping `updated_at`.
- [ ] Architecture Decision Record ADR-0034's `required_status_checks` follow-on — unblocked for
      months; until it lands, a red
      check cannot stop a merge and this driver is the only gate. It is also the precondition for
      ever adopting a merge queue.
- [ ] Prune the four stale merged remote branches.
- [ ] `failure-modes-root-cause-synthesis.md` owes a root cause for class 8 — now named:
      **the operation is edge-triggered everywhere it faces GitHub.**
