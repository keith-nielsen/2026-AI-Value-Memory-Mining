<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. The design pass — answered on paper, BEFORE any code

### 1.1 Question 1 — state lifetime: what is the exit condition?

- [x] 1.1 **Entry:** `AFTER_MUTATION == "merge"`. **Exit:** `confirm_mutation("merge")`, which already
      fires at the moment `post_merge()` observes `merged_at` and marks the step `ok`.
      **Therefore the cleanup steps that follow a confirmed merge — `remote-gone`, `local-gone` — are
      NOT suppressed.** This is queue item 22 exactly (a guard with an entry condition and no exit,
      which then blocked correct work), so it is the **first** test written, not the last.

### 1.2 Question 2 — reachability: which real invocation reaches each line?

- [x] 1.2 Answered by tracing the emit sites, not by intent:
      - **L1** is reached by the saved plan's verify tail — `--after-mutation merge
        --mutation-evidence <path>` — which runs on **every** merge. Not a rare path.
      - **L3** is reached by that same invocation whenever the list read is stale: **observed 1-in-3**
        (wrong on #76, correct on #77 and #78).
      - ⚠ Because it is intermittent, the test must **force** the stale-read geometry. Waiting to
        catch it live is not a test. And per the task-5.8 lesson, a stub can present geometry reality
        never has: the fixture supplies the **list read stale while the single-pull-request read is
        also stale**, which is #76's actual shape — not an idealised one where only one is behind.

### 1.3 Question 3 — exhaustiveness: do the categories partition?

- [x] 1.3 Both axes partition; every cell has a defined route. Queue item 25 shipped because a tally
      covered two of three values, so this table is written out in full rather than sampled.

**Evidence** (from `--mutation-evidence`, under `--after-mutation merge`) — any file is exactly one of:

| | |
|---|---|
| **E1** | parseable and asserts the merge landed (`merged: true`) |
| **E2** | parseable, silent on the merge |
| **E3** | present, unparseable |
| **E4** | absent (flag not passed) |

**Read** (the F34 lookup `pulls_for_branch(…, state="all")`) — exactly one of:

| | |
|---|---|
| **RA** | ≥1 pull request with `merged_at`, none open |
| **RB** | data present, but no merged pull request (open, or closed-unmerged) |
| **RC** | empty list |
| **RD** | read failed (`ReadError`) |

**Routes, under `AFTER_MUTATION == "merge"`:**

| | RA merged | RB no-merge | RC empty | RD failed |
|---|---|---|---|---|
| **E1** asserts merged | `post_merge` → confirms at once | `post_merge` → ladder → WAIT | `post_merge` → ladder → WAIT | `post_merge` → ladder → WAIT |
| **E2** silent | `post_merge` | WAIT | WAIT | WAIT |
| **E3** unparseable | `post_merge` | WAIT | WAIT | WAIT |
| **E4** absent | `post_merge` | WAIT | WAIT | WAIT |

- **No cell falls through to the pre-merge guards.** That is L3, and it is the property to test.
- `RA` is a positive from the read and is trusted on its own — a read that *sees* the merge cannot be
  a stale view of an unmerged state.
- The `E2–E4 × RB–RD` block is WAIT rather than an error: the mutation exited `0` (under `set -e` the
  tail would not run otherwise), so *something* merged and the only honest report is "not visible yet".
- Bounded by construction: the ladder exhausts after `(5, 8, 13)` and `waiting()` escalates to Monitor
  (PR #77), so WAIT never becomes a silent hang.

**Outside `AFTER_MUTATION == "merge"` nothing changes:** `RA` → `post_merge`; `RB`/`RC` → pre-merge
guards as today (a fresh branch genuinely has no pull request); `RD` → fall through, preserving the
offline local path.

## 2. Tests FIRST — each observed to fail before the change

- [ ] 2.1 **Adversarial, written first (item 22 regression):** a *confirmed* merge must still emit its
      `remote-gone` cleanup. Proves L3's exit condition works before L3 is trusted at all.
- [ ] 2.2 **L3, the real geometry:** `--after-mutation merge`, evidence absent, **both** reads stale.
      Assert the driver reports WAITING and that `git rebase` appears **nowhere** in the output.
      Must be observed to fail first — today it emits the rebase.
- [ ] 2.3 **L1:** evidence asserts merged, list read empty → routes to `post_merge`, no pre-merge
      guard runs, and the read spend is unchanged (no extra call before the ladder).
- [ ] 2.4 **L2:** an empty read and a failed read are distinguishable in the routing decision; assert
      on the branch taken, not on the printed text.
- [ ] 2.5 **Scoping / anti-over-denial:** outside `--after-mutation`, an unmerged branch behind its
      base still gets its rebase emitted. Pins that L3 did not become a general suppression.
- [ ] 2.6 **The lost observation:** after the fix, a merge whose list read is stale produces a verify
      series in the lag log. Today it produces none.
- [ ] 2.7 Table coverage: one test per **row**, asserting the routed branch for each read category.

## 3. Implementation

- [ ] 3.1 Evidence accessor — a structured reader beside `mutation_proof()` that answers *does the
      evidence assert this step landed?* rather than returning prose. `mutation_proof()` keeps its
      current job (quoting for humans); the two must not be conflated.
- [ ] 3.2 L1 routing in the F34 block, keyed to `AFTER_MUTATION`.
- [ ] 3.3 L2 — replace the bare `if prefetched:` with the three-way distinction.
- [ ] 3.4 L3 — extend `emit()`'s suppression axis so that under `AFTER_MUTATION == "merge"` a
      pre-merge step is refused, not merely an outward command. Keep `is_outward_mutation()` intact;
      this is a second, orthogonal condition, not a replacement.
- [ ] 3.5 Re-run the class sweep for bare truthiness on `(value, channel)` tuples and record the
      result in the commit body — measured, not assumed, exactly as it was for this proposal.

## 4. Docs

- [ ] 4.1 Update the F34 anchor comment: it states the principle correctly and was not enforced.
      Say what now enforces it.
- [ ] 4.2 Record in the commit body that this is logged as the **last edge-triggered patch** to this
      driver, and that the reconciliation question is deliberately held rather than folded in.

## 5. Ceremony

- [ ] 5.1 `openspec validate --all --strict` — check `openspec --version` against the `package.json`
      pin before treating any failure as a corpus defect.
- [ ] 5.2 Full suite + `validate-scripts.sh`.
- [ ] 5.3 Gate 4 — operator sign-off recorded here.
- [ ] 5.4 Archive on this branch, in this pull request (ADR-0040). No concurrent change carries a
      `maintenance` delta at time of writing — **re-check immediately before archiving.**
- [ ] 5.5 Close hardening-queue item 26.
