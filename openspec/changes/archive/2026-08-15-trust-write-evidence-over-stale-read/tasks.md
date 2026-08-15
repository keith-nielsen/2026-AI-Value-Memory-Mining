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

- [x] 2.1 **Adversarial, checked first (item 22 regression):** a *confirmed* merge must still emit its
      `remote-gone` cleanup. **Already covered** by
      `test_after_mutation_clears_once_its_verified_step_is_confirmed` — so rather than duplicate it,
      it became the guard L3 had to not break. Verified passing after L3: `AFTER_MUTATION is None`
      once confirmed, and `push origin --delete` still emitted. L3 is also safe here by
      construction, since `remote-gone` is *after* merge and so not in `PRE_MERGE_STEPS`.
- [x] 2.2 **L3, the real geometry:** `--after-mutation merge`, evidence absent, both reads stale.
      Assert the driver reports WAITING and never presents the rebase as an instruction.
      **Assertion corrected during the work:** the first version banned the string `rebase`
      anywhere, which also banned quoting the refused command under `SUPPRESSED`. The property that
      matters is that it is not *instructed* — the production defect printed
      `NEXT COMMAND (run exactly this…)` above it — so the assertion now matches the item-19 sibling.
- [x] 2.3 **L1:** evidence asserts merged, read shows the pull request still `open` → routes to
      `post_merge`, no pre-merge guard runs, no extra read spent.
      **Fixture corrected during the work:** it first used an EMPTY list, which is the extreme case
      and never reaches L1 — with no pull request in the read there is no number to verify against.
      The realistic stale shape is the pull request present but reading `open`.
- [x] 2.4 **L2:** an empty read and a failed read are distinguishable in the routing decision; assert
      on the branch taken, not on the printed text.
- [x] 2.5 **Scoping / anti-over-denial:** outside `--after-mutation`, an unmerged branch behind its
      base still gets its rebase emitted. Pins that L3 did not become a general suppression.
- [x] 2.6 **The lost observation:** after the fix, a merge whose list read is stale produces a verify
      series in the lag log. Today it produces none.
- [x] 2.7 Table coverage: one test per **row**, asserting the routed branch for each read category.

## 3. Implementation

- [x] 3.1 Evidence accessor — a structured reader beside `mutation_proof()` that answers *does the
      evidence assert this step landed?* rather than returning prose. `mutation_proof()` keeps its
      current job (quoting for humans); the two must not be conflated.
      ⚠ **Keyed to the SPECIFIC claim (`merged: true`), never to "the mutation exited 0".** Under a
      merge queue (queue item 2) the response asserts *queued*, not *merged* — conflating the two
      would break silently at exactly the moment we adopt the queue. Test the queue-shaped payload
      now, while it costs nothing.
- [x] 3.2 L1 routing in the F34 block, keyed to `AFTER_MUTATION`.
- [x] 3.3 L2 — replace the bare `if prefetched:` with the three-way distinction.
- [x] 3.4 L3 — extend `emit()`'s suppression axis so that under `AFTER_MUTATION == "merge"` a
      pre-merge step is refused, not merely an outward command. Keep `is_outward_mutation()` intact;
      this is a second, orthogonal condition, not a replacement.
- [x] 3.5 Re-run the class sweep for bare truthiness on `(value, channel)` tuples and record the
      result in the commit body — measured, not assumed, exactly as it was for this proposal.
- [x] 3.6 Write L3 to be **easy to delete.** The regression check found it is scaffolding around a
      derivation defect: under a level-triggered driver a correctly-derived `merged` marks the
      pre-merge steps `na` and no suppression is needed. Keep it one condition in one place, not a
      concept threaded through the module.

## 4. Docs

- [x] 4.1 Update the F34 anchor comment: it states the principle correctly and was not enforced.
      Say what now enforces it.
- [x] 4.2 Record in the commit body that this is logged as the **last edge-triggered patch** to this
      driver, and that the reconciliation question is deliberately held rather than folded in.

## 5. Ceremony

- [x] 5.1 `openspec validate --all --strict` — check `openspec --version` against the `package.json`
      pin before treating any failure as a corpus defect.
- [x] 5.2 Full suite + `validate-scripts.sh`.
- [x] 5.3 Gate 4 — recorded in its own section below, per convention. **The driver caught this:**
      the sign-off was first written here under *Ceremony*, and `approval_state()` correctly reported
      `Gate 4 UNSIGNED` because it requires a ticked item inside a section named **Gate 4**. The gate
      was right and the record was in the wrong place. Fixed by relocating, never by loosening.
- [x] 5.4 Archive on this branch, in this pull request (ADR-0040). **Re-checked immediately before
      archiving, and the earlier note was WRONG**: two in-flight branches DO carry live `maintenance`
      deltas — `feat/preflight-route-before-mutation` and `feat/estate-scoped-capability-probe`.

      **Archived anyway; the exception does not fire.** Both are **ADDED-only** and introduce
      requirements this change does not touch (*The Route Is Pre-Flighted Before A Mutation*; *The
      Capability Probe Measures A Declared Estate*; *A Probe Reports Diagnoses, Not Internal
      Errors*). This change is the only `MODIFIED`, against *Asynchronous Platform State Is Awaited,
      Never Assumed*. Same file, disjoint requirements.

      The hazard ADR-0040 guards is a later archive rebuilding the spec from a base that predates an
      earlier one, silently dropping it. That requires archiving from a **stale base**, which the
      lifecycle's `base` guard structurally prevents — neither branch can merge without containing
      `origin/main`, which will carry this archive. Deferring would instead leave `openspec/specs/`
      describing a state the repo has left, for as long as those branches take (one owes an
      architecture decision record not yet written, the other most of its tasks) — the precise harm
      the archive rule exists to prevent.

      ⚠ **`Spec lint` failed on the first push and was right.** That owed record was originally cited
      by number. A forward citation is permitted inside a **live** change directory and not inside
      the **archive**, because an archived change is a *record* and a record must resolve — so the
      act of archiving is what converted a legitimate forward reference into a dangling one. The
      number is therefore deliberately not written here. This is `enforce-adr-reference-integrity`
      (PR #62) catching exactly the case it was built for, on a change that had already passed
      `openspec validate --all --strict`: the two checks are not substitutes.
- [x] 5.5 Hardening-queue item 26 closed (operator memory, 2026-08-15), recording: the L1
      merge-queue shelf life, that L3 is scaffolding to be deleted at the reconciliation turn, that
      L1 cannot route without a pull-request number and so does not make L3 redundant, and the two
      test defects found by running them.

## 6. Evidence

- **Tests observed to FAIL before the change**, with the final assertions, by stashing
  `tools/pr-flow.py`: 5 failed, 1 passed. The one that passes is 2.5, the anti-over-denial pin —
  correct, since it must hold both before and after.
- **The production defect reproduces deterministically in a test.** It is 1-in-3 in the wild; the
  fixture forces the geometry rather than waiting for it.
- ⚠ **Two defects in the tests themselves, found by running them** — both the traps this project
  keeps hitting:
  1. `commit_on(work, "main")` moved LOCAL main only. The base guard compares against
     `origin/main`, so the rebase never triggered and **the test passed vacuously against broken
     code**. Fixed by pushing. *A stubbed state that passes while reading as coverage.*
  2. The evidence file was written inside the work repo, dirtying the worktree, so the run was
     REFUSED at step 2 before reaching anything under test.
- ⚠ **The first fixture used an EMPTY pull-request list** — the extreme case. The realistic stale
  shape is the pull request present but still reading `open`, which is what exercises L1. With only
  the extreme fixtured, L1 was never reached. Task 5.8's lesson again: a stub can present geometry
  reality never has.
- **First assertion was wrong in an instructive way.** It banned the string `rebase` anywhere, which
  also banned quoting the command under `SUPPRESSED`. The property that matters is that it is never
  presented as an instruction — the production defect printed
  `NEXT COMMAND (run exactly this…)` above it. Assertion now matches the item-19 sibling.
- **Class sweep (3.5), measured not assumed:** no live bare truthiness test on a `(value, channel)`
  tuple remains; the only three matches are comments describing the hazard. Every call site unpacks
  immediately or routes through `read_outcome` / `lag_tolerant`.
- Suite **227 passed**; `validate-scripts.sh` `VALIDATION OK`; `openspec validate --all --strict`
  7 passed, 0 failed.

## 7. Gate 4 — human sign-off (not agent-delegatable)

- [x] 7.1 **Approved** — Keith Nielsen, 2026-08-15. Reviewed `proposal.md` and `tasks.md`, including
      the regression check against the recorded defect history and against known future work, the two
      stated limits (L1 cannot route without a pull-request number; L3 is scaffolding for the
      reconciliation turn), the merge-queue shelf life on L1, and the corrections made during the
      work. Gate 3 complete: tests written first and five observed to fail before the change, the
      production defect reproducing deterministically, 227 passed, `validate-scripts.sh` OK,
      `openspec validate --all --strict` clean.
