<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: runbooks-and-floors

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDs** a Requirement ("Platform and Dependency Floors"). **No principle overridden or
weakened**; the two new runbooks are content conforming to the existing Runbook Format
requirement. Conforming amendment per repo precedent. ADDED-only delta — no archive-order
constraint.
**Tier:** 0-adjacent (§5 honored — Gate-4 human sign-off)
**Proposer:** Keith Nielsen (operator direction 2026-07-06: queue continuation; drafted by
Claude Code)
**Date:** 2026-07-06

## Why

Fleet-review B6 + B7, bundled (both documentation-class): (R9) the two highest-stakes repeatable
operations had no runbook — the render/reconcile loop (the INV-3 core ceremony) and the refine
pipeline (the only sanctioned Treasury write path, now with B4 pre-flight semantics worth
writing down); (R10) the Python version, dependency policy, and platform assumptions were
undeclared — implied by CI and code, guessed by implementers.

## What Changes

- **NEW `vault-template/96-Runbooks/render-reconcile-runbook.md`** — the deploy/drift loop:
  governed-path precondition, operator-run render for protected targets, drift is
  detected-never-fixed, VIOLATION semantics.
- **NEW `vault-template/96-Runbooks/refine-pipeline-runbook.md`** — detect → propose → human
  approve (the move IS the gate) → atomic bank; B4 reject semantics; INV-9 rollback notes.
- **`maintenance` spec:** ADDED "Platform and Dependency Floors" (Python ≥ 3.12;
  `python-frontmatter` sole third-party dep with stdlib-only hook paths; Linux/POSIX floor,
  Windows a declared non-goal; new deps are governed decisions).
- **`docs/USING-THIS-TEMPLATE.md`:** floors paragraph under Prerequisites.
- **CHANGELOG** `[Unreleased]`. **No ADR** (documentation of existing reality).

**NOT in this change:** B2-full skeleton / B8 tests; capture helper.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: ADDED "Platform and Dependency Floors".

## Impact

- Delta: ADDED-only. Implementation: 2 new runbooks + 1 doc paragraph.
- Live apply: `cp` the 2 runbooks into live `96-Runbooks/` (operator area).
- Behavioral delta: none (documentation); the floors requirement makes silent dependency growth
  a spec violation going forward.

## Gate 1 — CHECK

**Restated:** INV-3's loop and INV-4's Treasury gate gain their six-section procedures; INV-6's
"model-agnostic" claim gets the concrete floors that make it checkable. Nothing executable
changes.

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — ADDED requirement (delta)
- [x] `vault-template/96-Runbooks/` +2 (runbook-lint CI must pass: frontmatter + six sections)
- [x] `docs/USING-THIS-TEMPLATE.md`
- [x] `CHANGELOG.md`; constitution/project/ADR untouched; vocabulary clean

**Discrepancies for Gate 4:** none new.

## Gate 2 — PLAN

Merge → operator `cp` 2 runbooks live → done (no render needed; runbooks are not meta-scripts).

**Regression (must pass before Gate 3 closes):**
- [ ] `openspec validate runbooks-and-floors --strict` + `--all --strict`
- [ ] Runbook-lint equivalent on both new runbooks (frontmatter keys + six sections)
- [ ] `validate-scripts.sh` unaffected → `VALIDATION OK`
- [ ] Floors scenario spot-check: `vault_naming.py --check` on system python with vault_lib and
      frontmatter absent

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All repo-side regression tests green (local, 2026-07-06):** ☑ — validate strict 15/15;
runbook-lint fields+sections OK on both new runbooks; validate-scripts.sh VALIDATION OK;
floors spot-check: `vault_naming.py --check` rc 0 with vault_lib and frontmatter absent
**CI green on this PR:** ☐ (human) · **Live acceptance:** ☐ (post-apply)

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑ (2026-07-06 — diff = Gate-1 list)
**Consequences explicitly accepted:**

> Sacrifice: none — undocumented operations and unstated floors become documented; the one new
> constraint is that adding a third-party dependency now requires saying so in a proposal.

**ADR:** none

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen
Date: 2026-07-06

> Provenance: operator-directed queue continuation; publish sequence executed deliberately
> (PR #15, CI green, merge `df13ea5`), applied live (`cc40a05` — both runbooks in live
> `96-Runbooks/`, now 5 runbooks). Recorded post-merge; the operator's push is the confirming
> act.
