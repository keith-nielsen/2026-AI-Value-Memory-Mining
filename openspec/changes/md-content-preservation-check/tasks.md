## 1. The instrument

- [x] 1.1 `tools/md_content_check.py` — stdlib-only, offline, detection-only. Three verdicts
      (`identical` / `reordered` / `changed`), structural tokens excluded, `--allow` to record an
      accepted difference rather than weaken the check.
      *Done when:* it runs over a real range and classifies every file. **Observed** against
      `main..docs/md-lint-phase-a-fix-sweep`: 40 identical, 4 changed, 2 added, exit 1.
- [x] 1.2 `--selftest` proving BOTH directions — formatting ignored, and the real 2026-08-27
      trailing-space defect caught.
      *Done when:* it exits 0 and would exit 1 if either direction regressed. Matches the idiom
      `secret-scan` already uses.
- [x] 1.3 State the blind spot in the module itself: standalone-dash edits are not detected.
      *Done when:* written in the docstring **and** pinned by a test, so it cannot widen silently.

## 2. Prove the suite can fail

- [x] 2.1 21 tests, each formatting-insensitivity case paired with a mutation that must be caught.
      *Done when:* `pytest tests/test_md_content_check.py -q` → **21 passed**.
- [x] 2.2 Mutation matrix against the checker itself, **one mutant at a time**.
      *Done when:* every mutant is KILLED and attribution is unambiguous. **5/5 killed**; tool
      restored byte-identical; post-restore suite passes.
      ⚠ Isolation is the whole point — a compounded matrix in this estate reported `6/6 killed` and
      meant nothing.
- [x] 2.3 Reproduce the real defect verbatim as a named regression test, not an invented one.
      *Done when:* `test_detects_the_real_trailing_space_defect` asserts the exact edit
      `markdownlint --fix` made on 2026-08-27.

## 3. Regression — the checks this repo already ships

- [ ] 3.1 `python3 -m pytest tests/ -q` → expect **407** (386 baseline + 21).
- [ ] 3.2 `openspec validate --all --strict` → 0 failed.
- [ ] 3.3 `markdownlint` on the new files, CI's exact scope → 0 findings.
- [ ] 3.4 All 16 `ci.yml` jobs run locally; every failure attributable to a network/sysctl/PR-body
      precondition rather than to this change.
- [ ] 3.5 `tools/preflight.py . --body-file <PATH>` → CLEAR. ⚠ `--body-file` is not optional: without
      it step 7 prints `SKIP`, and a SKIP reads exactly like a PASS.

## 4. Gate 4 — operator authorization (Tier-0 touch)

Archiving syncs this delta into `openspec/specs/maintenance/spec.md`, `protects: [INV-2, INV-3,
INV-6]` — all **Tier 0**. The `AGENTS.md` hard stop requires the principle, its rationale and its
"what breaks" consequence surfaced, and explicit human confirmation received.

Surfaced, with the sacrifice stated rather than minimised:

- **The change is purely additive** — a new requirement and a new tool. Nothing is removed, relaxed,
  or rewired; no existing gate changes behaviour.
- **The cost is a standing obligation.** Once the requirement exists, a corpus-wide reformat that
  ships without this evidence is out of conformance. That is the intent, and it is a real constraint
  on future work, not a free addition.
- **What breaks if this is wrong:** if the checker's structural classification is too broad, it would
  report `identical` for a change that altered content — lending false authority exactly where
  review has already been shown to fail. That is why §2.2 exists and why its result is `5/5`, not a
  reassurance.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [x] 4.1 Tier-0 touch surfaced with its consequence; **Approved** — operator, 2026-09-13
      Given after the pre-work, scoping and testing in §1–§3 were presented: the isolated mutation
      matrix (5/5 killed), the stated blind spot and the test pinning it, and the end-to-end run
      against the real sweep. The operator's words: *"The currently planned scope with all of the
      pre-work, scoping, and testing is Approved."*
      ⚠ Scoped to the branches that completed that pre-work. It does **NOT** extend to
      `fix/render-root-resolution` or `fix/driver-subject-resolution`, whose Gate 4 remains UNSIGNED.

## 5. Land it

- [ ] 5.1 Archive this change on this feature branch, before the PR opens (ADR-0040).
- [ ] 5.2 Write the PR body with its `scope` block; `scope-review` fails closed on an empty body.
- [ ] 5.3 Walk `tools/pr-flow.py` to `LIFECYCLE COMPLETE`. Never hand-compose the sequence.
      ⚠ Run it from the repository directory — the driver resolves its subject from the working
      directory (change `fix-driver-subject-resolution`), so a vault-rooted invocation measures the
      wrong repository.

## 6. Deliberately NOT in this change

- [ ] 6.1 **Wiring the checker into CI as a gate.** It changes merge behaviour for every markdown PR
      and carries its own blast radius, so it is a separate decision.
      ⚠ Record the honest consequence: until that happens, this instrument only runs when someone
      chooses to run it. An unrun check is the failure class this estate already has six instances
      of, and adding a seventh unrun control would be a poor outcome for this work.
