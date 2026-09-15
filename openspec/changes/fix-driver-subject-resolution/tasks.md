## 1. Red proof first — every test observed to FAIL before its fix

- [x] 1.1 Subject resolution: 4 tests in `tests/test_pr_flow.py` — declared estate beats the working
      directory; `--repo` overrides the estate; a discovered subject is announced; a non-repository
      subject is refused with the blocked exit code and no traceback.
      *Observed:* all 4 failed against the old code.
- [x] 1.2 ⚠ One of those 4 passed **vacuously** and was tightened before being trusted.
      `test_repo_flag_overrides_the_declared_estate` asserted the repo path appeared in the output —
      which argparse's *"unrecognized arguments"* error also satisfies, because it echoes the path.
      It was passing *because* the flag did not exist. It now asserts that error is absent.
- [x] 1.3 Scope coverage: 3 tests — a covering block passes, a present-but-stale block is rejected,
      and the refusal names the undeclared path.
      *Observed:* all 3 failed; `scope_covers_diff` did not exist.
- [x] 1.4 Preflight accounting: 3 tests — `md-lint` is measured not excused, no exclusion reason
      cites a construct `ci.yml` no longer contains, and the local command matches the CI job's
      ignore set.
      *Observed:* all 3 failed.

## 2. The fixes

- [x] 2.1 `tools/pr-flow.py` — `resolve_subject()`: `--repo` > declared framework root > cwd
      toplevel, one stated total order. It mirrors the correction `capabilities()` already carries.
- [x] 2.2 `--repo PATH` added to the parser, overriding the declared estate.
- [x] 2.3 The subject and its source are printed on **every** invocation, not only on fallback.
      *Why stronger than proposed:* a route printed for the wrong repository is well-formed and
      indistinguishable from a real one; naming the subject unconditionally is what makes it visible.
- [x] 2.4 A subject that is not a git repository exits `EXIT_BLOCKED`, naming the path, no traceback.
- [x] 2.5 `scope_covers_diff()` — runs the two **shipped** gate scripts against the real merge-base
      diff. Invoked, not reimplemented, so the pre-verification cannot drift from the gate (class 9).
      An unreachable gate returns pass rather than inventing a refusal it cannot substantiate.
- [x] 2.6 Wired into the body step: a present-but-non-covering block now emits the body correction
      and states that the body-derived gate needs a PUSH, not a re-run.
- [x] 2.7 `tools/preflight.py` — `md-lint` deleted from `NOT_LOCAL` and added to `LOCAL_JOBS` with
      the CI job's exact ignore set and config. The stale string is removed, not reworded.

## 3. Consequences of the fixes, recorded rather than discovered later

- [x] 3.1 An existing test broke and was **re-pointed, not weakened**.
      `test_coverage_partitions_every_declared_job` used `md-lint` as its example of a job accounted
      for via `NOT_LOCAL` — the premise this change removes. It now uses `secret-scan`, which is
      structurally excluded; the invariant (every job lands in exactly one category) is unchanged.
- [x] 3.2 Preflight now reports failures it used to hide. On this branch it immediately flagged 25
      markdownlint findings in this change's own `proposal.md`, which the old exclusion would have
      passed to a red CI run. Fixed; the tree lints 0.
- [ ] 3.3 ⚠ The body step can now REFUSE where it previously passed. Watch the first few lifecycles
      for a false refusal — the gate scripts are invoked with a merge-base diff computed by the
      driver, and a disagreement between that diff and CI's would surface here first.
      *Done when:* observed across at least one full lifecycle, or a disagreement is found and fixed.

## 4. Regression

- [x] 4.1 `python3 -m pytest tests/ -q` → **417 passed** (407 baseline + 10).
- [x] 4.2 `openspec validate --all --strict` → 0 failed.
- [x] 4.3 `markdownlint`, CI's exact scope → 0 findings.
- [x] 4.4 End-to-end against the original defect: run from the vault, the driver names the declared
      estate as its subject and surfaces `Gate 4 UNSIGNED` — the finding the old behaviour concealed.
- [ ] 4.5 `tools/preflight.py . --body-file <PATH>` → CLEAR. ⚠ `--body-file` is not optional.
- [ ] 4.6 All 16 `ci.yml` jobs run locally; every failure attributable to a network/sysctl/PR-body
      precondition rather than to this change.

## 5. Gate 4 — operator authorization (Tier-0 touch)

Archiving syncs this delta into `openspec/specs/maintenance/spec.md`, `protects: [INV-2, INV-3,
INV-6]` — all **Tier 0**. The `AGENTS.md` hard stop requires the principle, its rationale and its
"what breaks" consequence surfaced, and explicit human confirmation received.

Surfaced, with the sacrifices stated rather than minimised:

- **The driver stops obeying the directory you stand in.** Once a framework root is declared, an
  operator who changes into a repository and expects the driver to act on it will have it act on the
  declared estate instead. `--repo` is the deliberate escape hatch; the loss is that the implicit,
  familiar gesture no longer governs.
- **A new refusal exists.** The body step can now stop a lifecycle that previously advanced. If the
  driver's merge-base diff ever disagrees with CI's, this is where a false refusal would appear.
- **What breaks if this is wrong:** these are the controls other work is judged by. A defect here
  does not fail loudly — it produces a confident, well-formed, wrong answer, which is precisely the
  class all three fixes address.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [ ] 5.1 Tier-0 touch surfaced with its consequence; **Approved** — operator, <date>
      *Agents may not sign this. Leave unticked until the operator records it.*

## 6. Land it

- [ ] 6.1 Archive this change on this feature branch, before the PR opens (ADR-0040).
      ⚠ Generate the PR body's scope block **after** the archive commit, never before: on PR #117 a
      block written before archiving left four paths undeclared and failed `scope-review`. Declare
      **both rename sides** — a directory moved into `archive/` touches the old path and the new.
- [ ] 6.2 Walk `tools/pr-flow.py` to `LIFECYCLE COMPLETE`.
      ⚠ Land this using the driver as it exists on `main`, not the version this branch modifies —
      otherwise the instrument and its subject share an author and a blind spot.
