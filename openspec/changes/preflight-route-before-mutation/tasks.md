<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [x] 1.1 `maintenance` ADDED: *The Route Is Pre-Flighted Before A Mutation* (5 scenarios)
- [x] 1.2 Requirement mandates the **shipped check as oracle**, not a restatement — the drift defect
      this repo has now found in itself four times
- [x] 1.3 Requirement mandates **SKIP ≠ FAIL**; found by the prototype committing that error itself
- [x] 1.4 Requirement names what is **not** locally decidable, so the tool cannot grow into guessing
- [x] 1.5 Confirm ordinary, not override — ADD-only; a discharged *follow-on* is a recorded intention,
      not a requirement, so nothing is overridden. **Not** derived from a green `constitution-lint`

## 2. ADR-0041

- [x] 2.1 `openspec/adr/0041-<slug>.md` — Context / Options / Decision / Consequences / Sacrifice
- [x] 2.2 **Discharge ADR-0040's follow-on** explicitly: the concurrency exception IS decidable from
      repository state, because a change that cannot archive is one that must defer. Do not edit
      ADR-0040 — it is an immutable record; supersede forward
- [x] 2.3 Record the four re-run causes from v0.1.39 with their denominators, and which are *settling*
      problems rather than prediction problems (those are items 16/19, not this change)
- [x] 2.4 Sacrifice: a pre-flight that duplicated logic would rot; this one runs the shipped check, so
      it costs a subprocess per check and cannot cover non-stdlib jobs

## 3. Tool — `tools/preflight.py`

⚠ **`[~]` = PROTOTYPE COMMITTED, NOT INTEGRATED.** `tools/preflight.py` exists and was measured
(see proposal *Evidence*), but it is a standalone script: not wired into `pr-flow.py` (§4), no tests
in `tests/` (§6), and its output format is not settled. Do not tick `[x]` on the strength of the
prototype runs — they were ad hoc, not a suite.

- [x] 3.1 Step 7 `body` — declared scope vs the real merge-base diff, via the shipped scripts
- [x] 3.2 Step 8 `checks` — extract every stdlib heredoc from `ci.yml` and run it
- [x] 3.3 Step 9 `mergeable` — `git merge-tree` trial merge; report conflicting paths
- [x] 3.4 Step 11 `archive` — simulate the archive; judge with the archive-sensitive checks; name the
      blocking artifact
- [x] 3.5 Concurrency — report ordering when two live changes carry a delta on one capability spec
- [x] 3.6 **SKIP vs FAIL** — an unrunnable check is named as such and excluded from findings
- [x] 3.7 Steps held by the platform are reported as not locally decidable, never predicted
- [x] 3.8 Stdlib-only; no third-party code added to the trust ring

## 4. Driver — `tools/pr-flow.py`

- [x] 4.1 **DECLINED — see §11.** A second entry point to one tool is a second thing to
      remember, which is the control that already failed. Not built, by decision.
- [x] 4.2 **DECLINED for now — see §11.** Couples the driver to the tool so it can restate an
      answer the tool already gives. Not built, by decision.
- [x] 4.3 **SATISFIED as a decision.** Nothing consumes the exit code as a gate. Do not make
      the pre-flight a hard gate on the push step without measuring the false-
      positive rate first — an over-denying gate gets disabled, which is worse than an advisory one

## 5. Lockstep

- [x] 5.1 `CONTRIBUTING.md` — pre-flight before the push, in the landing sequence
- [x] 5.2 `README.md` — ADR count 40 → 41; range → `ADR-0001–0041`

## 6. Tests — must exercise the states the mechanism itself creates

- [x] 6.1 **Archive simulation, observed failing first**: at `507fe2f` it must report `MUST DEFER`
      naming ADR-0040. Prototype already measured this; re-assert against the shipped tool
- [ ] 6.2 Concurrency: two live changes on one capability spec → ORDERED, both named. Build the
      fixture — this state has never occurred naturally, so it cannot be observed, only constructed
- [x] 6.3 Scope: a **rename** whose source path is undeclared → FAIL naming the removed side. This is
      PR #64's exact geometry
- [ ] 6.4 Trial merge: two branches appending to the same spec file → conflict predicted
- [x] 6.5 **SKIP vs FAIL**: a check that cannot run (the `/tmp` write in the secret-scan job) is
      reported SKIP and does **not** fail the pre-flight. Adversarial case — write it before 6.6
- [x] 6.6 A clean branch → pre-flight passes with no findings
- [x] 6.7 End-to-end on a real branch at least once, output pasted into this change

## 7. Gate 4 — human sign-off (not agent-delegatable)

- [ ] 7.1 **Approved** — _<operator>, YYYY-MM-DD_ · pending

## 8. Archive — on this branch, per ADR-0040

- [ ] 8.1 Move to `openspec/changes/archive/<date>-preflight-route-before-mutation/`
- [ ] 8.2 Apply the delta into `openspec/specs/maintenance/spec.md`; CHANGELOG entry
- [x] 8.3 **Run the pre-flight on itself before archiving.** It should report `MUST DEFER` until
      ADR-0041 exists (this change cites it), then `CAN ARCHIVE`. The tool proving itself on its own
      change is the strongest available end-to-end
- [ ] 8.4 Confirm the concurrency exception does not apply at merge time

## 9. Ship

- [ ] 9.1 PR body declares the full scope — including **both** sides of every rename (item 18)
- [ ] 9.2 Land via `tools/pr-flow.py --plan --branch BR` first, then the driven route

## 10. Explicitly out of scope

- [x] 10.1 GitHub **eventual consistency** — head-propagation lag, read-after-write on merge, orphaned
      check runs. These are *settling* problems, not prediction problems: the remedy is bounded retry
      and cross-checking the job-level view, tracked separately. Folding them in here would blur a
      tool that predicts with a tool that waits
- [x] 10.2 `ship-release.py`'s `gh`-only reads — a separate compliance defect against an existing
      requirement, and a defect fix rather than new capability

## 11. Section 4 (driver wiring) — DECLINED, and why

Recorded as a decision, not an omission. The operator's stated goal is **fewer errors up front, not
more rails**: *"how do we target fewer incidence of errors, rather than increased blockage of things
that should not occur?"* Section 4 as proposed adds machinery that does not serve it.

- **4.1 `pr-flow.py --preflight` — DECLINED.** The deliverable is *one* command. A second entry point
  to the same tool is a second thing to remember, which is the control that already failed. The
  pre-flight is named at step 0 of the landing sequence in `CONTRIBUTING.md`, where it is read at the
  moment it applies.
- **4.2 driver consults the simulation — DECLINED for now.** It couples the driver to the tool so the
  driver can restate an answer the tool already gives. The `archive` NOTE is advisory either way, and
  more coupling is more surface in the module that produced items 19, 22, 23 and 26.
- **4.3 do NOT make it a hard gate before measuring the false-positive rate — SATISFIED**, as a
  decision. The tool reports and exits non-zero; nothing consumes that exit code as a gate. Revisit
  only with a measured false-positive rate, per RC-E and queue item 22.

## 12. Scope added beyond the original proposal

The original change modelled four route steps. The operator's follow-up — *wire the CI checks into one
local command* — extended it, and the extension is recorded here rather than folded in silently:

- [x] 12.1 `LOCAL_JOBS` — the non-heredoc CI jobs (`openspec validate`, `inv6-offline-check` ×2,
      `validate-scripts.sh`, `pytest`, `inv6-offline-dynamic`) run by the same command. These were the
      four commands being run by hand before every push.
- [x] 12.2 `NOT_LOCAL` — jobs deliberately not reproduced, each with its reason.
- [x] 12.3 **Coverage accounting that PARTITIONS.** Every job in `ci.yml` is reproduced,
      unrunnable-with-reason, or not-reproduced-with-reason. Anything else prints `⚠ UNACCOUNTED` and
      **fails the run**. Without this, a job added to `ci.yml` tomorrow silently shrinks what the tool
      covers while it keeps printing `CLEAR` — the precise way a green check comes to mean nothing.
- [x] 12.4 The clear verdict states its own limits: the unrun jobs were not checked, and `pr`,
      `children` and `merge` remain the platform's to decide.

## 13. Evidence

- **Measured before/after.** Before: **0** CI jobs reproducible by one command; four remembered
  separately. After: **12 of 15**, with the other three named and explained, and 0 unaccounted.
- **Dogfood, observed flipping.** Against its own branch the pre-flight reported
  `MUST DEFER preflight-route-before-mutation` — *"Check every cited ADR resolves"* failing on the
  **simulated** archive, because this change cites ADR-0041 which did not yet exist. Writing the ADR
  flipped it to `CAN ARCHIVE`. That is task 8.3 satisfied by observation, not assertion.
- **It reproduces the defect that motivated it.** PR #79's red `Spec lint` — a citation that became
  dangling only *because* the change was archived — is exactly what the step-11 simulation catches,
  before any push.
- **`tests/test_preflight.py`, 10 tests.** The anti-vacuity property is tested first: a job in
  `ci.yml` the tool neither runs nor explains must print `UNACCOUNTED` and fail. Also covered:
  SKIP-is-not-PASS across four real error shapes, the archive simulation catching *and then clearing*
  a dangling citation, and a clean repo passing so the tool does not cry wolf.
- ⚠ **A defect in the tests, found by running them.** The archive fixture used `textwrap.dedent`,
  which strips exactly the six-space indentation `ci_steps()` keys on — so the fixture produced a
  `ci.yml` with **no extractable steps** and the check "passed" by never running. That is the tool's
  own target class, reproduced in its own test suite.
