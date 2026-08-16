<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [ ] 1.1 `maintenance` ADDED: *A Diff Touching A Protected Element Declares Its Constitutional
      Impact* (6 scenarios)
- [ ] 1.2 `maintenance` ADDED: *A Constitutional Declaration Is Read From The Tree, Not The
      Pull-Request Body* (3 scenarios)
- [ ] 1.3 Confirm nature is ordinary, not override — ADD-only against `maintenance`
      [`protects: [INV-2, INV-3, INV-6]`]; no existing requirement modified. Derived from
      `constitution.md` §3 and the #53 / #80 / #87 precedent, **not** from a green
      `constitution-lint` (which does no diff analysis — that is what this change fixes)

## 2. The declaration format

- [ ] 2.1 Define the fenced `constitutional-impact` block: `touches:` · `protects:` · `overrides:` ·
      `basis:` (free text, **not parsed** — for the human reviewer)
- [ ] 2.2 Add the block to this change's own `proposal.md` — **done in the proposal**; the change is
      its own first subject
- [ ] 2.3 Document the block in `CONTRIBUTING.md` beside the proposal-threshold table, at the point
      it is read rather than in a reference appendix

## 3. The gate — `.github/scripts/check-constitutional-impact.py`

- [ ] 3.1 Determine the subject set by parsing **YAML frontmatter only**. Fixture: the 17 PROSE-ONLY
      files from the proposal's sweep must all be outside the set
- [ ] 3.2 Read the declaration from the change directory in the diff — resolving **both** the live
      path `openspec/changes/<slug>/` and the archived path `openspec/changes/archive/<date>-<slug>/`
- [ ] 3.3 `overrides: none` → pass, with **no** evaluation of the claim's accuracy
- [ ] 3.4 Non-empty `overrides:` → require a `constitution-override` directory carrying the four gate
      sections; refuse where absent
- [ ] 3.5 Never refuse a change that carries a complete `constitution-override` (the
      refuses-its-own-ceremony failure)
- [ ] 3.6 Refusal message names the touched files, their tags, and the exact block to add — not a
      verdict alone
- [ ] 3.7 Stdlib-only, deterministic, no network (INV-6). No third-party YAML parser: the frontmatter
      needed here is a flat block, and a dependency would enlarge the trust ring for one field

## 4. CI wiring

- [ ] 4.1 New job `constitutional-diff-gate`, **`continue-on-error: true`** (Phase A). Do **not** touch
      the existing `constitution-lint` job or its name — a required context's name is its identity
- [ ] 4.2 `fetch-depth: 0` and diff against `origin/${{ github.base_ref }}...HEAD`, per `scope-review`.
      A shallow checkout cannot see the merge base, and `constitution-lint` today runs shallow
- [ ] 4.3 `if:` guard matching `scope-review` — pull-request events, not dependabot
- [ ] 4.4 Register in `tools/preflight.py` so the gate runs locally before every push (ADR-0041)

## 5. Tests — the over-denial cases first

The dangerous failure of a guard is refusing correct work. Adversarial cases before the confirming one.

- [ ] 5.1 Archive PR syncing a delta into a protected spec → **passes** (fixture from PR #64, the real
      shape, not a hand-built one)
- [ ] 5.2 A complete `constitution-override` change → **not refused by its own gate**
- [ ] 5.3 Each of the 17 PROSE-ONLY files edited alone → **does not fire**. Includes
      `openspec/constitution.md`, `CHANGELOG.md` and `ci.yml` — a substring implementation fails this
- [ ] 5.4 Protected spec touched, no declaration → **refuses**, and the message names file + tags + block
- [ ] 5.5 Declaration present in PR body only → **refuses**
- [ ] 5.6 Replay the last 25 merges through the gate: expect **4 fire / 21 quiet**, matching the
      proposal's measured table. A different number means the subject set is wrong
- [ ] 5.7 Every test above observed **failing without the change** before its box is ticked

## 6. Documents the gate makes true or false

- [ ] 6.1 `openspec/constitution.md` §4 — add one row for the new job, in the "point at the job, do
      not paraphrase it" form item 14 established. Keep the "What is NOT mechanically enforced" block
      accurate: after this change, the diff gate exists but is **report-only** until the Phase-B flip
- [ ] 6.2 `openspec/templates/constitution-override/proposal.md` — correct the **three** retracted
      claims it still carries (lines 9, 39/70, 105). Claim 1 becomes partially true; 2 and 3 are
      corrected to describe reality, **not deleted**
- [ ] 6.3 Verify **every other row** of §4 and every other CI claim in the template — item 14's
      standing rule is that fixing only the named rows reproduces the defect inside its own repair
- [ ] 6.4 ADR-0042 — context / options / choice / consequence

## 7. Deliberately NOT in this change

- [ ] 7.1 **The Phase-B blocking flip** — its own governed change after burn-in, threshold stated in
      the proposal: pass on 5 consecutive PRs touching a protected spec (~30 PRs at the measured 16%
      rate). Hardening-queue F29: do not fold a flip into the change that builds the thing
- [ ] 7.2 **Hashing the `CONST-01`–`05` principle sections** in `constitution-lint` — the answer to
      "`constitution.md` is not in the subject set", and a separate smaller change. Recorded here so
      it is owed rather than forgotten, which is the failure mode item 28 itself came from
- [ ] 7.3 **Adding the new context to `required_status_checks`** — meaningless while the job is
      `continue-on-error` (it cannot fail, so requiring it is theatre). Sequence with 7.1, per the
      hardening queue's item-1 note

## 8. Landing

- [ ] 8.1 `python3 tools/preflight.py .` green before any push
- [ ] 8.2 Driven landing via `tools/pr-flow.py --plan --branch feat/constitutional-diff-gate`, then
      the emitted command — never hand-composed
- [ ] 8.3 PR body carries a `scope` block declaring every path in the diff; a rename declares **both**
      sides
- [ ] 8.4 Archive on the feature branch in the same PR (ADR-0040), unless another in-flight change
      carries a `maintenance` delta — in which case defer and name the change deferred to
