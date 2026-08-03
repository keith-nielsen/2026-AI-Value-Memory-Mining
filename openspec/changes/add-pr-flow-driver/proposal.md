<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: add-pr-flow-driver

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** three Requirements ("PR Lifecycle Is Driven, Not Composed", "Platform Capability Is
Probed, Not Recalled", "GitHub Reads Degrade To An Unauthenticated Channel"). **No principle is
overridden or weakened.** All three are additive and repo-only; the driver is designed so the
INV-14 outbound ASK rail keeps firing (it never executes an outward mutation itself), and INV-6 is
not engaged because these are maintainer/ceremony tools, not `[script]` fleet members — the same
posture the spec already grants `ship-release.py`. Conforming amendment per repo precedent
(`add-ship-ceremony-tools` is the direct model; like it, this ships **without a new ADR**).
**Tier:** 0-adjacent (mechanizes the already-governed PR lifecycle; §5 AI hard-stop honored —
surfaced for explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-08-03)
**Date:** 2026-08-03

---

## Purpose (one sentence)

Make the branch→merge lifecycle a **driven state machine with named ownership**, so its ordering
and postconditions stop being re-authored from recall on every change.

## Why

**F30** (live vault `determinism-failure-modes-claude`, banked `fb7c359`, new **class 8** —
*declared outward end-state, never reconciled*) recorded six GitHub declarations that never reached
their stated end-state, and the operator's own framing is the finding: *"multiple failures of
specifying the wrong order of commands or saying that the human must do them when clearly the agent
can."* In one session:

- a child PR was pushed and opened **before its parent merged**, so its checks reported against a
  base that did not contain the fix under test;
- a required `gh api … -X PATCH` body correction was **named as mandatory and then dropped** from
  the final instruction list, and the PR merged carrying a claim already retracted in its own body;
- `gh pr merge --delete-branch` **half-failed** — the local delete was blocked by the worktree, gh
  aborted before deleting the remote, and still printed `✓ Merged`;
- a rebase was **reported complete** while `.git/rebase-merge` was still active, which is what
  blocked that deletion;
- three emitted commands were **not executable as written** (`git rev-parse --short` with three
  revisions; a `git grep -c` whose expected count was wrong; a wait-condition with no way to test
  it).

Every one is an **ordering, syntax, or postcondition** defect — which is what `ship-release.py`
already solves for the *other half* of the ceremony. That driver has been the standing mechanism
for tag→Release since v0.1.30 and works. The lifecycle **before** it was still hand-composed every
time. This change extends the proven contract rather than inventing a second pattern.

**A markdown table of command templates was considered and rejected as the primary mechanism.**
This repo's own record is that a prose ENFORCE has the reliability of recall (F16, F20 twice after
its corrective was written, F27, and ADR-0034's follow-on, which is a written-down step that simply
never happened). A list an agent is supposed to consult is a list it can skip. The enforceable unit
is an executable, re-entrant driver that refuses to advance.

**Ownership is the one class a driver cannot fix by ordering, so it is probed.** The agent asserted
"no GitHub egress this session" and it was false — plain `git` and the anonymous REST API both
worked; only `gh` was unavailable, because a sandboxed `gh` cannot reach the OS keyring and reports
a bogus 401. A static ownership table would have encoded that wrong answer **durably**. A probe
cannot, because it re-measures. Measured 2026-08-03 and now emitted by `--capabilities`:

| capability | channel | owner |
|---|---|---|
| read PR/check/branch state | anonymous REST, no token | **agent** |
| `git` mutations (push, force-with-lease, branch delete) | `GIT_TERMINAL_PROMPT=0` | **agent or operator**, through the INV-14 ASK |
| `gh` mutations (merge, label, issue, body PATCH) | keyring required | **operator** |

## What Changes

### New Capabilities

- **`tools/pr-flow.py`** — guarded, re-entrant state machine for branch → push → PR → checks →
  merge → branch deletion. Holds no state file; re-derives everything from the world each run.
  Proves each guard, then **emits the next single command verbatim with its owner named** and exits
  `2`; the caller runs exactly that and re-invokes, and the driver verifies the mutation actually
  landed before advancing. **Never executes an outward mutation** — the INV-14 guard text-matches
  the command the caller runs, so a wrapper that ran it internally would silently bypass the rail.
  Includes `--capabilities`.
- **`tools/gh_read.py`** — shared GitHub READ layer: anonymous REST first, `gh` only as fallback.
  Returns the answering **channel** with every payload so callers can print it; a read whose channel
  is stripped is indistinguishable from an assertion (class 7).

### Modified Capabilities

- **`tools/pr-state.py`** — reads now degrade to the anonymous channel instead of dying when `gh`
  is unavailable. The standing rule *"run `pr-state.py` first on any confusing PR state"* was
  **unrunnable by a sandboxed agent**, which is why hand-rolled `curl` replaced it at the exact
  moment of confusion. GraphQL-only layers (`mergeStateStatus`, the rollup, run-level aggregation)
  report **UNAVAILABLE and are never synthesised**, and the state-machine line now names the channel
  that actually answered — dogfooding caught it labelling a REST-sourced line "GraphQL", the very
  defect the reporter exists to prevent.

## Impact

- `openspec/specs/maintenance/spec.md` gains three ADDED Requirements (delta in `specs/`)
- New `tools/pr-flow.py`, `tools/gh_read.py`; modified `tools/pr-state.py`
- New `tests/test_pr_flow.py` (17 cases, weighted toward ordering/postcondition defects)
- `CONTRIBUTING.md` gains a "Landing a change" section beside "Shipping a version"
- **No `vault-template/` delta** — repo-only, so no mirror and no operator deploy step
- **No new dependency**: stdlib only (`urllib`), consistent with the trust-ring posture

## Deliberately excluded (F29 — one change, one purpose)

- **`github-state-reconcile`** (F30's other ENFORCE candidate) — answers *"is the world as
  declared?"*; this answers *"how do I correctly get from A to B?"*. Different purpose, its own
  change.
- **ADR-0034's `required_status_checks` follow-on** — genuinely queued and unblocked, but it is a
  server-side ruleset change, not a tool.
- **Pruning the four stale merged remote branches** — cleanup, not mechanism.
