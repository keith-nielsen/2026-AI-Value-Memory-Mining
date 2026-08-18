<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — add-fleet-inventory-conformance (Change A of two)

**Marker contract:** `[ ]` not started · `[~]` **built, untested** · `[x]` **tested — the check was
observed to FAIL without the change, and its evidence is cited.** Never tick `[x]` because code
exists.

**Evidence rule (constitution §3 Gate 3):** every result is evidenced by **its command and output** —
a tally with its denominator, a diff, or an exit status. Never a prose assertion, never a
shell-printed verdict string. An `echo "ok"` proves nothing: the shell knows only an exit code.

**Phases map onto the constitutional gates**, they do not replace them:

| Constitution §3 | Phase here |
|---|---|
| Gate 1 — CHECK | A0 |
| Gate 2 — PLAN | this file |
| Gate 3 — EXECUTE + REGRESSION-TEST | A1 – A3 |
| Gate 4 — RE-CHECK + HUMAN SIGN-OFF | A4 – A5 |

**Write scope:** every task below is **repo-side and agent-writable** (`tests/`, `tools/`,
`openspec/specs/`, `docs/`, `README.md`, `vault-template/`). No protected vault path is touched, and
nothing deploys. Measured 2026-08-17.

---

## A0 — CHECK: ground truth *(Gate 1)*

- [x] A0.1 Note set recorded. **14 notes.** Evidence: `baseline-conformance-record.md` §A0.1.
- [x] A0.2 Test baseline recorded. **328 passed, exit 0**, via `~/ai-env/bin/python3 -m pytest`.
      Evidence: §A0.2, incl. the preflight-misreport warning.
- [x] A0.3 The three drifting enumerations recorded verbatim with their commands. Evidence: §A0.3 —
      spec inventory **13 rows / `secret-scan` 0 occurrences in the whole spec**; README **heading 13,
      table 10, reality 14**; three cadence claims at `README.md:231`,
      `USING-THIS-TEMPLATE.md:264`, `maintenance/spec.md:106`.
- [x] A0.4 Coverage recorded per member. **9 of 11 covered**; `vault-orphans` and `vault-reprospect`
      uncovered in **both** harnesses. Evidence: §A0.4, incl. the note that measuring one harness
      alone previously overstated the gap as six.

**GATE A0 — PASSED 2026-08-18.** All four recorded in `baseline-conformance-record.md`, each with the
command that produced it. Cross-checked against Change B's `baseline-preflight-record.md`: the 14-note
set and the 328-test count agree across both files and both dates.
*Falsifier: any number quoted later from memory rather than from that file.*

---

## A1 — Build the instruments *(Gate 3)*

- [x] A1.1 `tests/test_inventory_conformance.py` — the `maintenance` Script Inventory names
      **exactly** the note set, reporting **both directions**. **RED:** `secret-scan-script.md`
      exists with no row.
- [x] A1.2 Extended to `README.md`'s table **and** its heading count. **RED:** 4 artifacts missing
      (`outbound-publish-guard.py`, `pre-push`, `vault_lib.py`, `vault_secrets.py`); heading 13 vs
      10 rows.
- [x] A1.3 `tests/test_settings_paths.py` — every script path in both settings files resolves to a
      declared `deploy_target`. **RED MANUFACTURED** and reverted; all three runs recorded.
- [x] A1.4 Cadence conformance. **RED:** `README.md:231` and `USING-THIS-TEMPLATE.md:264`. The
      premise (`no note declares cron/schedule`) is asserted, not assumed.
- [x] A1.5 **`vault-orphans.py`** — reports an unlinked note; does **not** report a linked one;
      detection-only. **Non-vacuity proven by mutation** (`if False` -> test fails).
- [x] A1.6 **`vault-reprospect.py`** — lists a slagged effort with metadata; ignores a non-index
      note; detection-only. **Non-vacuity proven by mutation** (glob narrowed -> tests fail).

**GATE A1 — PASSED 2026-08-18.** Evidence: `gate-a1-red-before-green.md`.
Suite **328 -> 344 collected** (16 new). Current: **339 passed, 5 failed** — the 5 are the intended
red, cleared in A2. Both mutations reverted; `git status` clean on the scripts.

*Falsifier: any check passing on the pre-change tree without a manufactured red state, and without
that manufacture recorded.*

---

## A2 — Correct what the instruments catch *(Gate 3)*

- [x] A2.1 Add the `secret-scan-script.md` → `vault_secrets.py` row to the `maintenance` Script
      Inventory (INV-7, ADR-0036 — ungoverned since 2026-07-28).
- [x] A2.2 Correct `README.md` operational scripts: heading count **and** all 14 rows — adds
      `vault_secrets.py`, `vault_lib.py`, `pre-push`, `outbound-publish-guard.py`.
- [x] A2.3 Remove the `0 6 * * *` cadence from `README.md:231`. *(Tier-2 convention — no ceremony.)*
- [x] A2.4 Correct `docs/USING-THIS-TEMPLATE.md:264` — nothing reads a `schedule:` field. *(Tier 2.)*
- [x] A2.5 Correct `maintenance/spec.md:106` — `treasury-orphan` is `manual`, matching its note.
- [x] A2.6 ⚠ **CORRECTED — this task was wrong.** It said "`CHANGELOG.md` entry"; CONTRIBUTING is
      explicit that *"the changelog is stamped **at release**, in a single `release(vX.Y.Z)` commit on
      the release branch. That is the practice without exception."* **Measured before reverting, not
      taken on the prose: 22 of the last 22 commits touching `CHANGELOG.md` are `release(...)`.**
      The entry was written, then reverted; `CHANGELOG.md` is byte-identical to `main` on this branch.
      The drafted text is preserved as `changelog-entry-draft.md` so the release stamp need not
      re-derive it. Caught by reviewing the branch diff before pushing, not by any check —
      **nothing in CI enforces this convention.**
- [x] A2.7 Two docstrings that called the fleet entirely host-deployed — `tools/template-parity.py`
      (*"`~/bin` target (note -> host)"*) and `tests/conftest.py` (*"into `$HOME/bin`"*). Inaccurate
      since the hooks and the harness guard became deploy targets: **3 of 14 are in-tree** and "host"
      silently excluded them. Both now name the mechanism (`deploy_target`), which is accurate before
      **and** after Change B — deliberately not repointed at `99-Operations/bin/`, which would make
      them false until B lands.

**GATE A2 — PASSED 2026-08-18.**
1. All 10 instrument tests pass (was 5 failed). Evidence: `pytest tests/test_inventory_conformance.py
   tests/test_settings_paths.py -q` -> `10 passed`.
2. Full suite **344 passed, 0 failed**. A0.2 baseline was **328**; delta **+16**, fully accounted for
   (7 inventory + 3 settings + 6 fleet). No pre-existing test changed state.
3. `template-parity.py` -> `18 lockstep files across 2 prefixes (1 excluded) - 0 drift`, exit 0 —
   unchanged from baseline.
4. `openspec validate --strict` -> valid.
5. **Re-measured the A0.3 drifts against ground truth (14 notes):** maintenance inventory **14 rows**;
   `secret-scan` **1 occurrence** (was 0); README heading **(14)**; README table **14 rows**. All four
   enumerations agree with the note set. All three cadence claims gone.

*Falsifier: any baseline measurement moved that this phase does not explain.*

---

## A3 — Full regression *(Gate 3)*

- [x] A3.1 `~/ai-env/bin/python3 -m pytest -q` — **EXIT 0**, `344 passed in 89.52s`.
- [x] A3.2 `bash .github/scripts/validate-scripts.sh` — **EXIT 0**. Its printed `VALIDATION OK` is
      recorded separately and was **not** used as the verdict (§3 Gate 3).
- [x] A3.3 `python3 tools/template-parity.py` — **EXIT 0**,
      `18 lockstep files across 2 prefixes (1 excluded) - 0 drift`.
- [x] A3.4 `python3 tools/inv6-offline-check.py` — **EXIT 0**,
      `14 fleet notes analysed - 0 violation(s), 0 unresolved`. Its own note that a clean static
      result does not prove offline behaviour is retained, not elided.
- [x] A3.5 `npx openspec validate --strict` — **EXIT 0**, valid.
- [x] A3.6 Coverage re-measured as the **union** of both harnesses: **11 of 11 covered, 0 uncovered**
      (A0.4 baseline: 9 / 2). `vault-orphans` and `vault-reprospect` now each carry `tests:1`.
- [x] A3.7 `python3 tools/preflight.py .` — **12 of 16 CI jobs reproduced, ZERO failures.** The two
      reported "issues" are `archive: <change> cannot archive yet` for both A and B, which is correct
      while A4/A5 are pending and B has not started.

**GATE A3 — PASSED 2026-08-18.** Every result cited as an **exit status**, never as a printed verdict
string.

---

## A4 — LAND *(Gate 4 begins — the OpenSpec ritual)*

Walk the driver; do not hand-compose the sequence (CONTRIBUTING §"Landing a change").

- [x] A4.1 **Approved** — Keith Nielsen, 2026-08-18. Constitution §3 Gate 4 / §5: human-only, not
      agent-delegatable. The operator reviewed the proposal and this task list and replied `Approved`.
      ⚠ **This line lives in `tasks.md` on purpose.** `pr-flow.approval_state()` reads
      `openspec/changes/*/tasks.md`, scopes to a heading matching `Gate 4`, and requires a **ticked
      box + the word Approved + an ISO date** — a record with a shape, not a keyword. It was first
      recorded only in `proposal.md`, where the driver cannot see it, and step 1 reported
      `MEASURED no`. **Recording a sign-off where the gate does not read it is the same as not
      recording it.**
- [x] A4.2 Branched from `main` as `feat/add-fleet-inventory-conformance`; nothing committed on `main`.
- [ ] A4.3 `python3 tools/preflight.py .` **before the first push** (ADR-0041). ⚠ **Run it from a
      shell where `config.env` has NOT been sourced** — sourcing puts the vault venv first on `PATH`
      and that venv has no pytest, which preflight miscategorises as `fleet-pytest: failed` while
      claiming `0 unrunnable`. Measured both ways 2026-08-18; see `baseline-conformance-record.md`
      §A0.2. A clear preflight is not a promise the remote will be green.
- [ ] A4.4 `python3 tools/pr-flow.py --plan --branch BR` — the whole route first, each step with its
      executor, authority, and whether its guard was MEASURED or PROJECTED.
- [ ] A4.5 `python3 tools/pr-flow.py --branch BR` → proves each guard, emits **one** command, exits 2.
- [ ] A4.6 **Run the emitted command VERBATIM** — no shell variables, no `timeout` prefix, no
      re-wrapping. The INV-14 guard resolves targets from raw text. Failure **class 10, stage 1**;
      it recurred twice on 2026-08-17 alone.
- [ ] A4.7 Re-run `pr-flow.py` — it verifies the mutation landed before advancing. If NOT READY, poll
      `--ready`. **Never sleep.**
- [ ] A4.8 Repeat A4.5–A4.7 until `LIFECYCLE COMPLETE`, exit 0.
- [ ] A4.9 **Archive the change ON THE FEATURE BRANCH** (ADR-0040) — before merge, not after.
- [ ] A4.10 Merge via the driver's REST route carrying `sha`. **Never `gh pr merge --delete-branch`**
      — it cannot express a head precondition and its deletion is non-atomic while printing `✓ Merged`.

**GATE A4 —** `LIFECYCLE COMPLETE`; change archived on its own branch; `main` carries the merge.
*Falsifier: any hand-composed outward command; any step out of the driver's order.*

---

## A5 — RE-CHECK *(Gate 4 completes)*

- [ ] A5.1 Re-run every A0 command against merged `main` and **diff against the baseline record** —
      §3 Gate 4 requires re-running the transcript, not re-reading the composed sections.
- [ ] A5.2 Confirm the inventory now reads **14 of 14** in both enumerations.
- [ ] A5.3 State in writing anything that changed which this proposal did not predict.

**GATE A5 —** diff clean or every delta explained.
*Falsifier: an unexplained delta.*

---

## Deliberately NOT in this change

- **No relocation.** Every `deploy_target` still points at `~/bin`. That is Change B.
- **No ADR.** This change weighs no architectural options: it adds checks and corrects statements that
  contradict the tree. Change B carries its own ADR for the decisions that *do* involve a choice.
  ⚠ **That ADR's number is deliberately not cited here.** It is not allocated until B creates it, and
  a forward citation to an unallocated number is a dangling reference that `adr-reference-integrity`
  refuses. This file carried exactly that defect and `preflight.py` STEP 11 caught it before the
  first push — the archive simulation deferred rather than the check failing after a merge.
- **The three stale ADR headers** (0032, 0033, 0042 read "Proposed/pending" while signed, applied and
  archived) are real and out of scope — they touch no line this change edits.
- **The harness-exclusion limit stands.** A1.3 proves a path *resolves*; only a real agent invocation
  through Claude Code proves the exclusion *matches*. No test can close this.
