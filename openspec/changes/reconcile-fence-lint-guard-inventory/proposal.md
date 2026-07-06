<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: reconcile-fence-lint-guard-inventory

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
MODIFIES "Literate Meta-Script Format" (`runtime:` enum + `harness hook`; single-fence scenario)
and "Script Inventory" (adds `outbound-publish-guard-script.md`). **No principle overridden or
weakened** — the fence lint enforces the requirement's existing "a single fenced code block"
text; the inventory row brings the last ungoverned operational script under INV-3. Conforming
amendment per repo precedent.
**Tier:** 0-adjacent (§5 honored — Gate-4 human sign-off)
**Proposer:** Keith Nielsen (operator direction 2026-07-06: "next step"; drafted by Claude Code)
**Date:** 2026-07-06

## Why

Fleet-review B5, both halves: (1) the render extractor takes the *first* `python|bash` fence —
the single-fence convention held 16/16 by discipline only; a second fence would silently never
render (or worse, an example block could shadow the real one). (2) `outbound-publish-guard.py`
(the INV-14 PreToolUse rail, ADR-0018) was the one operational script outside the render
inventory (R8): no literate source of truth, invisible to `reconcile`, hand-edit drift
undetectable.

## What Changes

- **`render-reconcile-script.md`:** a note with ≠1 fence is a `VIOLATION` — nothing renders for
  it, run exits 1 (both modes).
- **NEW `outbound-publish-guard-script.md`:** literate note whose code block is **byte-identical**
  to the shipped `.claude/hooks/outbound-publish-guard.py` (verified against both template and
  live copies); `deploy_target: .claude/hooks/…` (relative-target precedent:
  `99-Operations/hooks/*`); `runtime: harness hook` (enum extended). Live `.claude/` stays
  agent-write-denied — rendering there is operator-run, as with the git hooks.
- **`maintenance` spec:** LMF enum + fence scenario; Script Inventory + guard row.
- **CHANGELOG** `[Unreleased]`. **No ADR** (R8/INV-3 conformance).

**NOT in this change:** B2-full skeleton/B8; B6 runbooks; B7 floors; capture helper.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: MODIFIED "Literate Meta-Script Format"; MODIFIED "Script Inventory".

## Impact

- Delta bases: LMF restated from the `fleet-hygiene-bundle` accretion; Script Inventory from the
  `commit-ownership-de-sweep` accretion. **Archive order:** hygiene and B3 before this change
  (both merged; ordering is archive-sequence only).
- Implementation: 1 modified + 1 new note.
- Live apply: `cp` 2 notes + `render` (guard target byte-identical → reconcile zero drift;
  render of `.claude/` path is operator-run) + `reconcile`.
- **Behavioral deltas:** a malformed note now fails render/reconcile loudly (was: silent
  first-fence pick or WARN-and-continue for zero fences — the WARN path is upgraded to a
  violation with exit 1); the guard is drift-detectable.
- **Residual:** the fence rule counts `python|bash` fences only — other languages in a Rationale
  (e.g. a `json` example) stay legal.

## Gate 1 — CHECK

**Restated:** INV-3 says Layer 0 is the source of truth and drift is detected, never auto-fixed —
the guard finally gets that protection, and the extractor's silent-first-fence hazard becomes a
loud violation. INV-6 untouched. INV-2 unaffected (render commits nothing).

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — two MODIFIED requirements (delta; archive order noted)
- [x] `vault-template/99-Operations/scripts/render-reconcile-script.md`
- [x] `vault-template/99-Operations/scripts/outbound-publish-guard-script.md` (new; code
      byte-identical to `vault-template/.claude/hooks/outbound-publish-guard.py`, which stays —
      it is the *shipped* copy the note now governs)
- [x] `validate-scripts.sh` — untouched; bootstrap render + reconcile exercise the lint and the
      new note end-to-end
- [x] `CHANGELOG.md`; constitution/project/ADR untouched; vocabulary clean

**Discrepancies for Gate 4:** the note duplicates the guard code (source-of-truth note + shipped
`.claude` copy) — exactly the render/deploy relationship every other script has; `reconcile` now
alarms if they diverge, which is the point.

## Gate 2 — PLAN

Merge → operator: `cp` 2 notes, `render` + `reconcile` (zero drift expected — guard byte-identical)
→ agent records; fence lint is self-exercising on every future render.

**Regression (must pass before Gate 3 closes):**
- [ ] `openspec validate reconcile-fence-lint-guard-inventory --strict` + `--all --strict`
- [ ] `validate-scripts.sh` → `VALIDATION OK` (render now includes the guard note; reconcile zero
      drift on 17 notes)
- [ ] Battery: seeded two-fence note → `VIOLATION` + rc 1 + nothing rendered for it; guard note
      renders byte-identical to the shipped `.claude` copy; clean render rc 0

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All repo-side regression tests green (local, 2026-07-06):** ☑ — validate strict 14/14;
validate-scripts.sh OK (17-note render, reconcile zero drift); battery: seeded two-fence note →
VIOLATION + rc 1 + nothing rendered for it (others unaffected); guard renders byte-identical;
clean reconcile rc 0. Gate-3 also caught and repaired a drafting-tooling defect: bash history
expansion had corrupted `!` characters in four heredoc-generated files (this branch's render code +
the SPDX comment line of three merged-but-unarchived deltas) — all repaired in a declared
companion commit before any archive could sync the mangled bytes
**CI green on this PR:** ☐ (human) · **Live acceptance:** ☐ (post-apply)

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☐
**Consequences explicitly accepted:**

> Sacrifice: none — a convention becomes enforced, and the vault's exfil rail gains the same
> drift protection as the rest of the fleet. The only new failure mode is a loud render error on
> a malformed note, which is the feature.

**ADR:** none

**SIGN-OFF** (human only — agents may not sign):
Name: ______________________
Date: ______________________
