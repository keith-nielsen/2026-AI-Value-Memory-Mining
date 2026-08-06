## 1. Burn-in evidence (the spec's stated precondition)

- [x] 1.1 Sampled the 14 most recent merged PRs (#41–#57) via the check-runs API: `scope-review`
      concluded **`success` on every one, 0 failures**. Precondition *"after clean burn-in"* is
      satisfied by measurement, not by elapsed time.

## 2. Mechanism

- [~] 2.1 Remove `continue-on-error: true` from the `scope-review` job
- [~] 2.2 Rename the job to `Scope review (declared-scope gate)` — done **now**, while the context is
      UNREQUIRED, because the name is the check-context identity
- [~] 2.3 Rewrite the job comment to state where the block binds (`pr-flow.py` step 8) and where it
      does not (ruleset required contexts — deliberately deferred)

## 3. Spec

- [~] 3.1 MODIFIED `maintenance` / *Scope-Review CI Gate*: two-stage bullet → Phase-B complete, plus a
      bullet stating the binding surface explicitly
- [~] 3.2 Two scenarios added: failures are unsuppressed; renaming occurs only while unrequired

## 4. Regression

- [x] 4.1 `openspec validate --all --strict` — **7 passed, 0 failed**
- [x] 4.2 YAML parses via `yaml.safe_load`; 15 jobs; `scope-review.name` =
      `Scope review (declared-scope gate)`; `continue-on-error` key **absent**; `if` unchanged
- [ ] 4.3 CI green on this PR — **including the renamed, now-blocking job itself**

## 5. Dogfood — the gate must be exercised, not merely enabled

**Definition of Done: `[~]` = built, `[x]` = tested.** A flip that is never made to fail proves only
that the happy path still works.

- [x] 5.1 Passing case: this PR's own declared scope covers its diff, verified against
      `extract-declared-scope.py` before pushing
- [x] 5.2 **Failing case — the load-bearing test. RUN, against this change's real diff.** Both CI steps
      reproduced locally (`extract-declared-scope.py` then `check-scope-findings.py`, the exact
      invocation in the job):
      · **correct scope** → `PASS (5 file(s), all declared)`, exit **0**
      · **`.github/workflows/ci.yml` omitted from the block** → `FAIL — the diff exceeds the Declared
      scope`, `[MEDIUM] scope.file: File ".github/workflows/ci.yml" is not in the Declared scope`,
      exit **1**.
      The non-zero exit is what `continue-on-error` was previously swallowing, so this is the precise
      behaviour the flip changes — verified on the real geometry, not a stub.
- [ ] 5.3 Confirm the renamed context appears as `Scope review (declared-scope gate)` in the check-runs
      of this PR, and that the old name no longer appears
- [x] 5.4 **ESCAPE-HATCH REGRESSION — the operator's condition of approval: prove a blocking gate
      cannot corner us out of releasing or reverting.** Three routes tested independently:
      1. **The ruleset cannot block on it.** Live read of ruleset `19666243`: 16 required contexts,
         `Scope review` **not among them**. So even a comparator that failed every PR could not
         produce a server-side merge refusal — a merge remains available via `gh api -X PUT`.
      2. **The release path is independent.** `tools/ship-release.py` contains **zero** references to
         checks; its layers are `local-tag` / `remote-tag` / `release-object`. Tag and Release
         creation never consult CI, so a red gate cannot block a ship.
      3. **A revert passes its own gate.** Reverted **both** commits onto the post-flip tree, verified
         it restores `continue-on-error: True` and the old job name, then ran the **blocking**
         comparator on the revert's 5-file diff with a correct declaration → **PASS, exit 0**.
      ⚠ Two earlier attempts at (3) were INVALID and are recorded so the result is not over-read: the
      first branched from `origin/main`, which lacks the flip, so the revert was a no-op and an empty
      diff passed trivially; the second reverted only the first of two commits and left a `UD`
      conflict on `tasks.md`. Only the third drill reproduces the real geometry.

## 6. Gate 4 — authorization

- [x] 6.1 Operator reviewed the proposal and recorded **Approved** — Keith Nielsen, 2026-08-06.
      **Conditional:** *"conditional on there having been a regression test to make sure we don't paint
      ourselves into a corner and block our ability to release/regress completely."* **Condition
      DISCHARGED by §5.4** — three independent escape routes measured (ruleset cannot block, release
      path has no check dependency, a revert passes the blocking gate). The condition was raised
      before the drill existed, and the first two attempts at it were invalid; the discharge rests on
      the third only.

## 7. Deliberately deferred, with its trigger

- [ ] 7.1 Add `Scope review (declared-scope gate)` to the ruleset's `required_status_checks`
      (id `19666243`). **Blocked on one unknown:** the job reports `skipped` on the `push` trigger and
      on dependabot PRs, and whether GitHub treats `skipped` as satisfying a required context cannot be
      dry-run here (ADR-0034 — `evaluate` is Enterprise-only). **Trigger:** resolve that question, then
      PATCH with the NEW context name. Reversal is a cheap attributable ruleset PATCH if it deadlocks.
- [ ] 7.2 CHANGELOG entry — `[Unreleased]` is currently empty and #56/#57 both merged without one.
      Third instance of the same hole; not fixed here.
