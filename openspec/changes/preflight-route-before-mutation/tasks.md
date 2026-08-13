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
- [ ] 1.5 Confirm ordinary, not override — ADD-only; a discharged *follow-on* is a recorded intention,
      not a requirement, so nothing is overridden. **Not** derived from a green `constitution-lint`

## 2. ADR-0041

- [ ] 2.1 `openspec/adr/0041-<slug>.md` — Context / Options / Decision / Consequences / Sacrifice
- [ ] 2.2 **Discharge ADR-0040's follow-on** explicitly: the concurrency exception IS decidable from
      repository state, because a change that cannot archive is one that must defer. Do not edit
      ADR-0040 — it is an immutable record; supersede forward
- [ ] 2.3 Record the four re-run causes from v0.1.39 with their denominators, and which are *settling*
      problems rather than prediction problems (those are items 16/19, not this change)
- [ ] 2.4 Sacrifice: a pre-flight that duplicated logic would rot; this one runs the shipped check, so
      it costs a subprocess per check and cannot cover non-stdlib jobs

## 3. Tool — `tools/preflight.py`

⚠ **`[~]` = PROTOTYPE COMMITTED, NOT INTEGRATED.** `tools/preflight.py` exists and was measured
(see proposal *Evidence*), but it is a standalone script: not wired into `pr-flow.py` (§4), no tests
in `tests/` (§6), and its output format is not settled. Do not tick `[x]` on the strength of the
prototype runs — they were ad hoc, not a suite.

- [~] 3.1 Step 7 `body` — declared scope vs the real merge-base diff, via the shipped scripts
- [~] 3.2 Step 8 `checks` — extract every stdlib heredoc from `ci.yml` and run it
- [~] 3.3 Step 9 `mergeable` — `git merge-tree` trial merge; report conflicting paths
- [~] 3.4 Step 11 `archive` — simulate the archive; judge with the archive-sensitive checks; name the
      blocking artifact
- [~] 3.5 Concurrency — report ordering when two live changes carry a delta on one capability spec
- [~] 3.6 **SKIP vs FAIL** — an unrunnable check is named as such and excluded from findings
- [~] 3.7 Steps held by the platform are reported as not locally decidable, never predicted
- [~] 3.8 Stdlib-only; no third-party code added to the trust ring

## 4. Driver — `tools/pr-flow.py`

- [ ] 4.1 `--preflight` runs the above and exits meaningfully
- [ ] 4.2 The `archive` step consults the simulation instead of only noting that a change is unarchived
- [ ] 4.3 Do **not** make the pre-flight a hard gate on the push step without measuring the false-
      positive rate first — an over-denying gate gets disabled, which is worse than an advisory one

## 5. Lockstep

- [ ] 5.1 `CONTRIBUTING.md` — pre-flight before the push, in the landing sequence
- [ ] 5.2 `README.md` — ADR count 40 → 41; range → `ADR-0001–0041`

## 6. Tests — must exercise the states the mechanism itself creates

- [ ] 6.1 **Archive simulation, observed failing first**: at `507fe2f` it must report `MUST DEFER`
      naming ADR-0040. Prototype already measured this; re-assert against the shipped tool
- [ ] 6.2 Concurrency: two live changes on one capability spec → ORDERED, both named. Build the
      fixture — this state has never occurred naturally, so it cannot be observed, only constructed
- [ ] 6.3 Scope: a **rename** whose source path is undeclared → FAIL naming the removed side. This is
      PR #64's exact geometry
- [ ] 6.4 Trial merge: two branches appending to the same spec file → conflict predicted
- [ ] 6.5 **SKIP vs FAIL**: a check that cannot run (the `/tmp` write in the secret-scan job) is
      reported SKIP and does **not** fail the pre-flight. Adversarial case — write it before 6.6
- [ ] 6.6 A clean branch → pre-flight passes with no findings
- [ ] 6.7 End-to-end on a real branch at least once, output pasted into this change

## 7. Gate 4 — human sign-off (not agent-delegatable)

- [ ] 7.1 **Approved** — _<operator>, YYYY-MM-DD_ · pending

## 8. Archive — on this branch, per ADR-0040

- [ ] 8.1 Move to `openspec/changes/archive/<date>-preflight-route-before-mutation/`
- [ ] 8.2 Apply the delta into `openspec/specs/maintenance/spec.md`; CHANGELOG entry
- [ ] 8.3 **Run the pre-flight on itself before archiving.** It should report `MUST DEFER` until
      ADR-0041 exists (this change cites it), then `CAN ARCHIVE`. The tool proving itself on its own
      change is the strongest available end-to-end
- [ ] 8.4 Confirm the concurrency exception does not apply at merge time

## 9. Ship

- [ ] 9.1 PR body declares the full scope — including **both** sides of every rename (item 18)
- [ ] 9.2 Land via `tools/pr-flow.py --plan --branch BR` first, then the driven route

## 10. Explicitly out of scope

- [ ] 10.1 GitHub **eventual consistency** — head-propagation lag, read-after-write on merge, orphaned
      check runs. These are *settling* problems, not prediction problems: the remedy is bounded retry
      and cross-checking the job-level view, tracked separately. Folding them in here would blur a
      tool that predicts with a tool that waits
- [ ] 10.2 `ship-release.py`'s `gh`-only reads — a separate compliance defect against an existing
      requirement, and a defect fix rather than new capability
