<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

**Evidence run, 2026-08-16** — `openspec validate --all --strict`: 7 passed / 0 failed ·
`pytest tests/`: **291 passed** (36 new) · `tools/preflight.py .`: **CLEAR**, 12/16 CI jobs.

**Mutation evidence for the whole section 3/5 block.** The frontmatter parser was replaced with the
naive `"protects:" in text` substring match and the suite re-run: **20 failed, 16 passed** (against
36/36 correct). That is the "observed to fail without the change" evidence for the subject-set
tests; without it they would pass against a gate that refuses everything.

## 1. Spec (ordinary change — ADDED only)

- [x] 1.1 `maintenance` ADDED: *A Diff Touching A Protected Element Declares Its Constitutional
      Impact* (6 scenarios) — `openspec validate --strict` green
- [x] 1.2 `maintenance` ADDED: *A Constitutional Declaration Is Read From The Tree, Not The
      Pull-Request Body* (3 scenarios)
- [x] 1.3 Nature confirmed ordinary, not override — ADD-only against `maintenance`
      [`protects: [INV-2, INV-3, INV-6]`]; no existing requirement modified. Follows the
      #53 / #80 / #87 precedent, **not** a green `constitution-lint` (which does no diff analysis)

## 2. The declaration format

- [x] 2.1 Fenced `constitutional-impact` block: `touches:` · `protects:` · `overrides:` · `basis:`
      (free text, **not parsed** — asserted by `test_declaration_is_not_second_guessed`)
- [x] 2.2 Block added to this change's own `proposal.md`. **Proven end-to-end**: the simulated
      archive PR (below) located it at the archived path and passed
- [x] 2.3 Documented in `CONTRIBUTING.md` beside the proposal-threshold table — at the point it is
      read, not in a reference appendix

## 3. The gate — `.github/scripts/check-constitutional-impact.py`

- [x] 3.1 Subject set from **YAML frontmatter only**. All 17 measured PROSE-ONLY files are outside
      the set (`test_prose_only_protects_mention_does_not_fire`, parametrized ×17); substring
      mutation fails 20 tests
- [x] 3.2 Declaration resolved at **both** the live and archived change paths —
      `test_archive_sync_into_a_protected_spec_passes`, plus the live simulated archive below
- [x] 3.3 `overrides: none` → pass, with no evaluation of accuracy
- [x] 3.4 Non-empty `overrides:` → require the ceremony (`test_declared_override_without_ceremony_is_refused`);
      an incomplete ceremony is still refused (`test_incomplete_ceremony_is_refused`)
- [x] 3.5 Never refuses a complete `constitution-override`. Anchored to the **real** template by
      `test_the_real_template_is_recognised_as_a_ceremony` — which caught the first draft's regex
      failing on `**Change type:** \`constitution-override\``
- [x] 3.6 Refusal names touched files, their tags, and the exact block to add
      (`test_refusal_names_file_tags_and_the_block_to_add`)
- [x] 3.7 Stdlib-only, deterministic, no network — `inv6-offline-static` green in pre-flight

## 4. CI wiring

- [~] 4.1 Job `constitutional-diff-gate`, `continue-on-error: true` (Phase A). **Built, not
      observed running on the platform** — this session cannot push, so no real check-run exists.
      `[x]` is not available until it has run once on a real PR
- [~] 4.2 `fetch-depth: 0` + diff against `origin/${{ github.base_ref }}...HEAD` — written,
      unexercised on the platform for the same reason
- [~] 4.3 `if:` guard matching `scope-review` — written, unexercised on the platform
- [x] 4.4 Registered in `tools/preflight.py` as **STEP 7b** and in `NOT_LOCAL`. Verified by running
      pre-flight: the step executes and the coverage partition still accounts for every `ci.yml` job
      (12 reproduced / 4 not reproduced, none unlisted)

## 5. Tests — the over-denial cases first

- [x] 5.1 Archive PR syncing a delta into a protected spec → **passes**
- [x] 5.2 A complete `constitution-override` → **not refused by its own gate**
- [x] 5.3 All 17 PROSE-ONLY files → **do not fire**, incl. `constitution.md`, `CHANGELOG.md`, `ci.yml`
- [x] 5.4 Protected spec, no declaration → **refuses** with file + tags + block
- [x] 5.5 Declaration in PR body only → **refuses**
- [x] 5.6 Replay of the last 25 merges → **4 fire / 21 quiet**, matching the proposal's measured table
      (`test_replay_last_25_merges_matches_the_measured_rate` — the only test whose input production
      actually produced)
- [x] 5.7 Observed failing without the change — mutation run above; plus two defects the tests caught
      while building: the `--root` value counted as a positional, and the ceremony regex missing the
      real template's markdown emphasis

**Live end-to-end (the run that matters).** Simulated this change's own archive — moved the change
directory to `archive/2026-08-16-constitutional-diff-gate/`, appended the delta into the real
`openspec/specs/maintenance/spec.md`, and ran the gate on the resulting diff:

```
constitutional-diff-gate: protected elements touched by this diff
  openspec/specs/maintenance/spec.md  protects: [INV-2, INV-3, INV-6]
  PASS: declaration at openspec/changes/archive/2026-08-16-constitutional-diff-gate/proposal.md
        overrides nothing requiring ceremony
```

Against the branch's own current diff it reports `not applicable` — correct: this PR touches no
protected spec until the archive lands.

## 6. Documents the gate makes true or false

- [x] 6.1 `constitution.md` §4 — row added pointing at the script rather than paraphrasing it; the
      *"What is NOT mechanically enforced"* block reworded to say a job now **inspects** the diff but
      cannot yet **refuse**, plus a new bullet that no check will ever judge a declaration's truth
- [x] 6.2 `openspec/templates/constitution-override/proposal.md` — all **three** retracted claims
      corrected to describe reality (lines 9, 56, 88, 123). Verified none remain:
      `grep -n "CI will fail\|CI will reject"` → no matches
- [~] 6.3 Verified every CI claim in the **template** (grep above, exhaustive). **NOT** re-measured:
      §4's branch-protection row against the live ruleset — item 14 measured it on 2026-08-16 and
      this change does not touch it, but this session did not independently re-verify it
- [x] 6.4 ADR-0042 written — context / options / choice / consequence / **sacrifice**, incl. the
      declared limits (a false declaration still passes; `CONST-01`–`05` remain ungated)

## 7. Deliberately NOT in this change

- [ ] 7.1 **The Phase-B blocking flip** — its own governed change after burn-in. Threshold stated in
      the proposal and in the job comment: pass on 5 consecutive PRs touching a protected spec
      (~30 PRs at the measured 16% rate). Hardening-queue F29: do not fold
- [ ] 7.2 **Hashing the `CONST-01`–`05` principle sections** in `constitution-lint` — the answer to
      "`constitution.md` is not in the subject set" (operator decision, 2026-08-16). Separate change
- [ ] 7.3 **Adding the new context to `required_status_checks`** — theatre while the job is
      `continue-on-error`. Sequence with 7.1

## 8. Landing

- [x] 8.1 `python3 tools/preflight.py .` → **CLEAR** (caught and fixed a real README ADR-count drift
      on the first run: 41 claimed, 42 present)
- [ ] 8.2 Driven landing via `tools/pr-flow.py --plan --branch feat/constitutional-diff-gate`
      **— blocked: this session cannot push (operator authority, INV-14)**
- [ ] 8.3 PR body with a `scope` block covering every path; a rename declares both sides
- [ ] 8.4 Archive on the feature branch in the same PR (ADR-0040), unless another in-flight change
      carries a `maintenance` delta

## 9. Gate 4 — human sign-off (not agent-delegatable)

- [x] 9.1 **Approved** — Keith Nielsen, 2026-08-16. Reviewed the proposal, this task file and
      ADR-0042, including the two decisions named below, both argued in the proposal and ADR-0042:
      (a) **`constitution.md` is OUT of the subject set** — operator decision 2026-08-16. It carries
      no frontmatter tag, and gating it would have refused PR #85, the change that removed six false
      enforcement claims. `CONST-01`–`05` therefore remain ungated until task 7.2 hashes them.
      (b) **Phase A is report-only** — the gate cannot fail a build yet, so merging this does not
      make the constitution enforced; it makes the enforcement exist and observable. Anyone reading
      a green build as ceremony compliance would be repeating the error PR #85 corrected.
      Gate 3 status: 291 passed, `openspec validate --all --strict` 7/7, pre-flight `CLEAR`,
      mutation 20/36, live archive simulation passed. CI wiring is `[~]` — never run on the platform.
