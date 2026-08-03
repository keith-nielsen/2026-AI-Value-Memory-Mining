<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — add-pr-flow-driver

## 1. Gate 1 — CHECK (blast radius)

- [x] 1.1 `openspec/specs/maintenance/spec.md` — six ADDED Requirements, no existing Requirement
      modified or weakened
- [x] 1.2 `tools/pr-flow.py` (new), `tools/gh_read.py` (new), `tools/pr-state.py` (modified reads)
- [x] 1.3 `tests/test_pr_flow.py` (new)
- [x] 1.4 `CONTRIBUTING.md` — "Landing a change" section beside "Shipping a version"
- [x] 1.5 `CHANGELOG.md` — `[Unreleased]` entry
- [x] 1.6 Confirm NO `vault-template/` delta → no mirror, no `render`, no operator deploy step
- [x] 1.7 Confirm no new third-party dependency (stdlib `urllib` only)

## 2. Gate 2 — PLAN (build)

- [x] 2.1 `tools/gh_read.py`: anonymous REST first, `gh` fallback, channel returned with every read
- [x] 2.2 `tools/pr-flow.py`: guards in order — worktree settled → base-current → commits exist →
      pushed → PR exists → head matches → checks green → merge → deletion verified
- [x] 2.3 Slug resolution made LAZY so the purely-local guards answer without a resolvable remote
- [x] 2.4 `--capabilities` probe: measures reads, `git` push (dry-run), `gh` auth; never raises
- [x] 2.5 `tools/pr-state.py`: degrade to anonymous channel; GraphQL-only layers report UNAVAILABLE
- [x] 2.6 Every emitted command carries an owner and a reason

## 3. Gate 3 — REGRESSION

- [x] 3.1 `tests/test_pr_flow.py` — 17 cases, offline, real git layers via a local bare origin
- [x] 3.2 Full suite green: **121 passed** (no regression in `test_ceremony_tools.py`, which
      covers the `pr-state.py` this change modifies)
- [x] 3.3 `openspec validate --all --strict` clean under the pinned 1.6.0
- [x] 3.4 Dogfood `--capabilities` on the live repo — correctly reported `gh` UNAVAILABLE while
      `git push` and anonymous reads were OK, which is the exact division of labour the agent got
      wrong twice by recall
- [x] 3.5 Dogfood `pr-state.py` degraded path on merged PR #50 — **defect found and fixed**: it
      labelled a REST-sourced line `· GraphQL`, the channel-stripping error the tool exists to
      prevent
- [x] 3.6 Dogfood `pr-flow.py` on this branch — correctly refused on an unclean worktree

## 3b. Flow review — all 49 PRs in repo history (operator-directed, before ship)

- [x] 3b.1 Enumerate every PR #1–#50 from the API and classify by shape
- [x] 3b.2 **Bot/remote-only branch** (#1–5, #18, #46–48 open now): `rev-parse` DWIM read a
      Dependabot branch as local and proposed rebasing it — **fixed**: explicit `refs/heads/`
      lookup; no rebase/push/delete for foreign branches; merge omits `--delete-branch`
- [x] 3b.3 **Local command with another branch checked out**: bare `git rebase` acts on HEAD —
      **fixed**: emits `git switch` first
- [x] 3b.4 **Stacked PR** (#29, died irrecoverably, F21) — **fixed**: refuses to merge while open
      children exist, names them, prescribes the retarget; flags a PR that is itself stacked
- [x] 3b.5 **Closed-unmerged PR** (#18, #29) — **fixed**: queries all states, reports the dead PR
      instead of silently proposing a duplicate
- [x] 3b.6 **Completed-lifecycle re-run** — **fixed**: absence on both sides now reports LIFECYCLE
      COMPLETE instead of refusing, restoring the re-entrancy contract
- [x] 3b.7 Draft PRs and multiple-open-PRs-per-head now refuse rather than guess
- [x] 3b.8 Confirmed generic path already covers: release PRs, feature+archive two-PR ceremonies,
      docs-only recording ADRs, and the three non-vault repos. Fork PRs out of scope, stated.
- [x] 3b.9 Suite after extension: **126 passed** (17 → 22 cases in this file)

## 4. Gate 4 — HUMAN SIGN-OFF

- [ ] 4.1 Operator reviews this proposal and records **Approved** (agents may not sign)
- [ ] 4.2 Open the PR with a ```scope block covering every path in §1
- [ ] 4.3 Merge once checks are green
- [ ] 4.4 Archive on `main` in merge order; `openspec validate --all --strict` clean afterwards
- [ ] 4.5 Ship the version via `tools/ship-release.py` — tag → Release → parity tally

## 5. Queued separately (F29 — one change, one purpose)

- [ ] `github-state-reconcile` — F30's other ENFORCE candidate; declares required platform state
      (labels, ruleset rules, no stale merged branches) and diffs it against the live API,
      reporting drift and never auto-fixing. Answers a different question from this driver.
- [ ] ADR-0034's `required_status_checks` follow-on — unblocked for months; until it lands, a red
      check cannot stop a merge and this driver is the only gate.
- [ ] Prune the four stale merged remote branches.
- [ ] `failure-modes-root-cause-synthesis.md` owes a root cause for class 8.
