<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: trust-write-evidence-over-stale-read

## Why

**Measured on PR #76's own merge, 2026-08-15.** The merge returned
`{"sha": "d538905…", "merged": true}`, and the verify tail then restarted the route from step 3 and
emitted:

```
git -C <root> rebase origin/main
```

— for a branch whose pull request had merged seconds earlier. The command was not run.

Every earlier defect in this family printed a false **alarm** (queue items 19, 22). This one printed
a false **instruction**. That is a different severity: an alarm invites a bad reaction, an
instruction supplies one.

### The guard that exists for this did not fire, and the reason is not "no retry"

`tools/pr-flow.py` already carries the F34 block — anchor comment *"TERMINAL STATE IS RESOLVED BEFORE
PRE-TERMINAL GUARDS"* — whose entire purpose is to stop exactly this. It reads the pull-request list
once and routes to `post_merge()` when it sees a merged pull request with none open.

Re-running the identical command minutes later, with no code change, produced the correct route. The
only variable was elapsed time. Then on PR #77's merge the two reads were captured in a single run
and **disagreed with each other about the same fact**:

| read | endpoint | saw `merged_at` at |
|---|---|---|
| F34 early lookup | `pulls_for_branch(…, state="all")` — the LIST | **~3s** |
| `post_merge` verify | `pull_request(slug, n)` — the SINGLE pull request | **17.13s** |

**So this is a race between two independently-lagging endpoints, not a missing retry.** The driver
routes on the one it never retries. When the list endpoint happens to be fresh the lifecycle works;
when it is stale the driver emits a wrong command. Observed **1-in-3**: wrong on #76, correct on #77
and #78. Intermittent is worse than deterministic — a fault that appears a third of the time is one
no operator can build a habit around.

Independently corroborated: Aviator, building commercial merge automation on GitHub, report the same
shape — a webhook reporting a CI run successful while a parallel API call for the same run still
reports it pending. See `30-Sites/github-vmm-operational-workflow/external-practice-review-github-automation`
in the vault.

### Three faults, and only one of them causes the bad command

1. **No lag tolerance on the terminal-state read.** `--after-mutation merge` is in effect and has no
   bearing here: lag tolerance lives inside `lag_tolerant()` and this call site does not use it.
   **This is what produces the wrong instruction.**
2. **`if prefetched:` is a bare test on a 2-tuple.** `pulls_for_branch` returns `(list, channel)`, so
   the test is true even when the list is empty. It was meant to ask *did I get an answer?* and can
   never be false, so it guards nothing — an empty (stale) result becomes an assertion that no merged
   pull request exists. Fixing this alone would **not** have prevented the rebase; it is what stops
   the code from being able to tell that it is in trouble.
3. **`emit()`'s post-mutation suppression does not cover local commands.** Item 19 added a guard that
   *"structurally cannot emit an outward mutation"* while verifying one — keyed on
   `is_outward_mutation(command)`. `git rebase` is local, so it passed straight through. The guard was
   correctly built and is simply scoped to the wrong axis for this failure.

⚠ **Class 9 — the fix was applied to the sighting, not the class.** `tools/pr-flow.py:1271` carries an
explicit comment: *"ITEM 23: `prefetched` is a 2-TUPLE `(list, channel)`, so a bare `if prefetched:` is
truthy…"*. The bare form survives ~80 lines above it, in the F34 block. The hazard was diagnosed,
written down, fixed where it was found, and left in place next door — the same shape as queue item 17,
where `approval_state()`'s archive path was keyed to the branch and its live path never was.

**A sweep was run rather than assumed.** `if prefetched:` is the *only* bare truthiness test on one of
these tuples; every other call site unpacks immediately (`payload, ch = …`), which is safe. So the
class is one instance — but it was found by looking, not by trusting that the earlier fix had covered it.

### Fourth consequence: the failure path records nothing

When the F34 lookup misses, `post_merge()` never runs, so **no lag observation is logged for that
merge**. PR #76's merge produced zero verify series; its four records are later manual re-invocations
at `attempt 0, visible=True`. The log silently drops exactly the failure cases — the mirror image of
the bias queue item 23 fixed, inside the dataset item 24 depends on.

## What Changes

The governing principle is the end-to-end argument (Saltzer, Reed & Clark, 1984): a correctness check
belongs at the endpoint that knows the answer. **The merge API's own response is that endpoint's
answer. A subsequent read of an eventually-consistent view is a weaker signal, and must not be allowed
to overrule it.** The driver currently holds the authoritative answer and believes the lagging read
instead.

Three layers, because a conclusive fix must not depend on correctly enumerating every way a read can
be wrong:

- **L1 — Route on the mutation's own evidence; use the read only to confirm.** When
  `--after-mutation merge` is set and the captured evidence asserts the merge landed, route directly
  to `post_merge()`, which already performs correct lag-tolerant confirmation and reports WAITING if
  the read never catches up. Costs **zero extra reads** and removes the race rather than out-waiting
  it. Also restores the lost observation, since `post_merge()` runs the ladder.
- **L2 — "No answer" is not "no merged pull request."** Distinguish read-failed, read-returned-empty
  and read-has-data. While verifying a mutation, empty means *unknown*, never *negative*.
- **L3 — Structural backstop.** While verifying a merge, the driver SHALL NOT emit a pre-merge step's
  command at all. It confirms, or it waits. The F34 comment already states the principle — *"the
  pre-merge guards are only meaningful while the change is UNMERGED"* — but nothing enforces it.

**L3 is what makes this conclusive**, because it does not require L1 and L2 to have anticipated every
stale-read shape.

### Scoping, deliberately narrow

L3 applies **only** when `AFTER_MUTATION == "merge"`, where "the pre-merge guards are moot" is
definitionally true. It does not extend to other post-mutation modes, where a pre-terminal step could
legitimately be the right next move. Outside a post-mutation verify **nothing changes at all**.

This restraint is deliberate. The corpus warns against over-denial (`RC-E`), and queue item 22 was
precisely a guard given an entry condition and no exit, which then suppressed correct work. The exit
condition here is explicit: `confirm_mutation("merge")` clears the suppression the moment the merge is
observed to land, so the cleanup steps that legitimately follow are never suppressed. That is the
adversarial test, and it is written first.

## Why this takes a proposal

Per `CONTRIBUTING.md` → *When a change ships without a proposal*: **L3 adds a guard that can refuse
work**, which is trigger 3. The other two triggers do not fire — no new flag or caller-visible
surface, no persistent state introduced.

The three design questions the proposal exists to force are answered in `tasks.md` §1 **before any
code**, including the full evidence × read decision table, whose exhaustiveness is the specific thing
that went wrong in queue item 25.

## Regression check against the record, and against known future work

Run at the operator's challenge, before implementation. The result changed one design note.

### Backward — would this have caught our own history?

| Defect | Verdict |
|---|---|
| **item 19** — `REFUSED` printed under a successful merge | **Yes.** L1 routes on the evidence, so the contradiction never arises. Cheaper than the retry ladder that actually fixed it. |
| **item 23** — retry dead behind a bare 2-tuple test | **Yes, as a class.** L2 is the same defect at the sibling call site. |
| **item 26** — this one | Yes, by construction. |
| **F34** — terminal state resolved after pre-terminal guards | Hardens F34's own block; F34 was right and unenforced. |
| **item 22** — suppression not cleared after its mutation confirmed | ⚠ **No — and L3 is the same shape as the bug.** See below. |
| **item 16** — orphaned check-run strands the driver | **No.** It stalls at step 8 (`checks`), which is pre-merge and outside any post-mutation verify. L3 does not reach it. |
| **item 20** — stale `next.sh` replays a mutation | No. Unrelated mechanism. |
| **item 17** — change state unkeyed to the branch | No. Unrelated mechanism. |

**Three of eight, one actively in the risk class, four untouched.** Recording the score rather than
only the wins: this is a targeted fix, not a general hardening, and it should not be described as one.

⚠ **L3 is a new suppression with an entry condition — structurally the same object that caused item
22.** That is the strongest argument against it. It is mitigated three ways: the exit condition is
named (`confirm_mutation("merge")`), the adversarial exit test is written **first** (task 2.1), and
the scope is one mutation type rather than all of them. But the risk is real and is the reason L3 is
scoped as narrowly as it is.

### Forward — does it collide with work we know is coming?

**1. Merge queue (queue item 2) — a real collision, and L1 has a shelf life.**

Under a merge queue the driver does not `PUT /merge`; it **enqueues**. The mutation's response then
asserts *queued*, not *merged*, and the merge happens later, asynchronously, possibly **batched with
other pull requests**. L1's central premise — *the write response asserts the terminal state* — stops
holding.

This does not block the change: an evidence file that does not assert `merged` is row **E2** of the
decision table, which already routes to WAIT. But two consequences follow, and both are adopted here:

- The evidence accessor SHALL be keyed to the **specific claim** (`merged: true`), never to "the
  mutation exited 0". Conflating those is what would break silently under a queue.
- **L1's value is bounded by how long we keep merging directly.** Worth knowing before treating it as
  permanent architecture.

**2. The reconciliation turn — L3 becomes redundant, by design.**

Under a properly level-triggered driver, a route that correctly derives *merged* marks the pre-merge
steps `na` and never emits them; no suppression is needed. **L3 exists only because the derivation can
be wrong.** It is scaffolding around a derivation defect, not a permanent guard — so it should be
written to be easy to delete, and it should not be defended once the derivation is trustworthy.

**3. `feat/preflight-route-before-mutation`** models route steps by running the shipped check. If
`emit()` gains a second refusal axis, that model must track it. Coupling, not collision.

**4. `feat/estate-scoped-capability-probe`** — no interaction.

## Impact

- `tools/pr-flow.py` — F34 block, `emit()` suppression axis, evidence parsing.
- `tests/test_pr_flow.py` — adversarial tests first.
- `openspec/specs/maintenance/spec.md` — one MODIFIED requirement.
- No `vault-template/` change; INV-6 does not engage (maintainer tool, not fleet).
- Closes hardening-queue **item 26**. Logged as the **last edge-triggered patch** to this driver: the
  reconciliation question it belongs to is deliberately held, not folded in.
