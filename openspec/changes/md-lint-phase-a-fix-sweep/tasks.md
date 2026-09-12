## 1. The sweep (recovered from the abandoned branch, re-verified here)

- [x] 1.1 Mechanical `markdownlint --fix` pass, 1137 findings to 97.
      *Evidence:* commit `0140fee`. ⚠ This pass introduced the defect repaired in 3.1 — recorded
      here because the task succeeded and still caused harm.
- [x] 1.2 Repair MD018 by hand, label 17 fences, align 4 tables — 97 to 63.
      *Evidence:* commit `6083616`.
- [x] 1.3 Reflow 52 over-length lines — 63 to 11.
      *Evidence:* commit `f247418`.
- [x] 1.4 Resolve the MD025 and MD024 precedents — Phase A reaches 0.
      *Evidence:* commit `cb43d45`. MD025 scoped via `front_matter_title: ""` with its measurement
      recorded in `.markdownlint.yml`; MD024 resolved by consolidating duplicate sections within
      release `[0.1.17]`, verified lossless in 2.2.

## 2. Verify the sweep's own claim, rather than accepting it

- [x] 2.1 Token-multiset content check across all 44 changed files, whitespace fully collapsed so
      reflow and blank lines cannot mask a real change.
      *Done when:* every differing file is classified. **Result: 40 prose byte-identical, 4 differing.**
- [x] 2.2 Adversarial case before the confirming one: test the *suspected* defect first. Measured each
      `CHANGELOG.md` entry whose heading was removed, comparing `(release, section)` before and after.
      *Result:* **4/4 unchanged** — the suspicion was wrong and the consolidation is lossless.
- [x] 2.3 Confirm the two remaining differences are cosmetic: `_propose_` → `*propose*` renders
      identically; `docs/obsidian.md` gains a blockquote marker and a fence label.

## 3. Repair what the check found

- [x] 3.1 Restore the trailing space `markdownlint --fix` stripped from `` `trail ` `` in
      `openspec/specs/naming-rules/spec.md`, and exempt the single line from MD038.
      *Done when:* verified at byte level with `od -c`, and the file lints clean.
      *Evidence:* commit `b166cb1`. MD038 has no config options beyond `enabled`/`severity` — checked
      against the pinned markdownlint 0.49.1 schema — so an inline disable is the only targeted fix.
- [x] 3.2 Merge `main` in, so the branch contains the base tip the driver's `base` step requires.
      *Evidence:* commit `c16b27e`; merge clean.
- [x] 3.3 Blank lines after the two `#### Scenario:` headings PR #115 added to `maintenance`.
      *Done when:* `git diff -w -b --ignore-blank-lines` is EMPTY, proving no prose changed, and the
      tree lints 0. *Evidence:* commit `5f69ebc` — 2 insertions, 0 other changed lines.

## 4. Regression — the checks this repo already ships

- [x] 4.1 `markdownlint`, CI's exact scope → **0 findings, exit 0** (from 1138 on `main`).
- [x] 4.2 `openspec validate --all --strict` → 6 passed, 0 failed.
- [x] 4.3 `python3 -m pytest tests/ -q` → **386 passed**, matching the `main` baseline.
- [ ] 4.4 `tools/preflight.py . --body-file <PATH>` → CLEAR. ⚠ `--body-file` is not optional: without
      it step 7 prints `SKIP`, and a SKIP reads exactly like a PASS.

## 5. Gate 4 — operator authorization (Tier-0 touch)

This change touches **all six** `protects:`-tagged specs, and between them every CONST and INV
identifier in the constitution. The `AGENTS.md` hard stop requires the principle, its rationale and
its "what breaks" consequence surfaced, and explicit human confirmation received.

Surfaced, with the sacrifice stated rather than minimised:

- **The breadth is real even though the intent is narrow.** A corpus-wide formatter touched every
  protected spec. Four are prose-identical, one gains two blank lines, one has a destroyed character
  restored — but the operator is signing off on a diff spanning the whole protected surface.
- **One check is exempted, not satisfied:** `MD025.front_matter_title: ""`. The corpus keeps its
  frontmatter-title + H1 convention and the rule stops seeing it. Measured to be catching zero real
  defects before it was scoped, but it IS a rule turned off rather than obeyed.
- **What breaks if this is wrong:** a formatting change that silently altered a requirement would
  enter the protected specs with no reviewer able to spot it in a 623-line diff. That is precisely
  why 2.1 exists and why its result is reported as a number, not a reassurance.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [x] 5.1 Tier-0 touch surfaced with its consequence; **Approved** — operator, 2026-09-13
      Given after the pre-work, scoping and testing were presented: the token-multiset content check
      across all 44 files (40 prose byte-identical), the repair of the defect that check found, the
      verification that the CHANGELOG consolidation was lossless (4/4 entries keep their exact
      release and section), 0 lint findings from 1138, and all 16 `ci.yml` jobs run locally.
      The operator's words: *"The currently planned scope with all of the pre-work, scoping, and
      testing is Approved."*
      ⚠ Signed in full knowledge of the two sacrifices named above: the diff spans **all six**
      `protects:`-tagged specs, and **MD025 is exempted rather than satisfied**.
      ⚠ Scoped to the branches that completed that pre-work. It does **NOT** extend to
      `fix/render-root-resolution` or `fix/driver-subject-resolution`, whose Gate 4 remains UNSIGNED.

## 6. Land it

- [ ] 6.1 Archive this change on this feature branch, before the PR opens (ADR-0040).
- [ ] 6.2 Re-read the branch name against what the branch delivers. `docs/md-lint-phase-a-fix-sweep`
      still describes it; the `docs/` prefix is right for a formatting change.
- [ ] 6.3 Walk `tools/pr-flow.py` to `LIFECYCLE COMPLETE`. Never hand-compose the sequence.
      ⚠ Run it from the repository directory — the driver resolves its subject from the working
      directory (see change `fix-driver-subject-resolution`), so a vault-rooted invocation measures
      the wrong repository.

## 7. Do not fold in

- [ ] 7.1 **Phase B is NOT part of this change.** `ci.yml` instructs that removing the `exit 0`
      happens in its own governed change and never in one that edits markdown. This change edits 44
      markdown files. Leave `md-lint` in audit mode.
