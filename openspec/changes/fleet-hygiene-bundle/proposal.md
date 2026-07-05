<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: fleet-hygiene-bundle

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
MODIFIES "Literate Meta-Script Format" (the `runtime:` enum gains `git hook`) and "Daily Close
Lifecycle" (one added close-lint scenario). **No principle overridden or weakened** — the enum
change legalizes a value two shipped notes already needed; the close-lint change makes an
existing verification actually verify. Conforming amendment per repo precedent.
**Tier:** 0-adjacent (§5 honored — Gate-4 human sign-off)
**Proposer:** Keith Nielsen (operator direction 2026-07-06: "proceed with queue"; drafted by
Claude Code)
**Date:** 2026-07-06

## Why

Three small debts from the fleet review, bundled as declared in its blueprint: (1) the spec's
`runtime:` enum says `cron | manual` while the two hook notes need `git hook` — and
`commit-gate-script.md` said `manual` where `push-guard-script.md` said `git hook` (R9 trivia);
(2) the close-lint vocabulary check was near-tautological (R7): it could only flag default-list
words *removed* from the env vocabulary — a typo'd disposition passed; (3) the bootstrap
runbook's clean-ops gate line ("source env for the commit-gate hook") went stale when
`fix-commit-gate-env-guard` made the hook env-free (proposal drafted in the live-vault Site
`ops-script-runbook-review`, applied here to the template mirror).

## What Changes

- **`maintenance` spec:** `runtime: cron | manual | git hook`; Daily Close Lifecycle gains the
  scenario "close-lint flags an out-of-vocabulary disposition".
- **`commit-gate-script.md`:** `runtime: manual` → `git hook` (frontmatter only; rendered hook
  byte-identical).
- **`daily-close-script.md` (`--check`):** manifest dispositions are extracted from the manifest
  row shape (`— \`word\`` at line end) and each MUST be in `DISPOSITIONS` — typos now FAIL;
  the old hardcoded-tuple guard is gone.
- **`vault-template/96-Runbooks/session-bootstrap-loader.md`:** clean-ops bullet updated (hooks
  and fleet are env-free; source config only for operator conveniences); `last-validated`
  bumped. Live `96-Runbooks/` copy is operator-applied from the Site proposal.
- **CHANGELOG** `[Unreleased]`. **No ADR** (three conformance repairs; no new decision).

**NOT in this change:** shell pair; B2-full skeleton; B5/B6/B7; capture helper.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: MODIFIED "Literate Meta-Script Format"; MODIFIED "Daily Close Lifecycle".

## Impact

- Delta: `maintenance`, two requirements — **neither touched by the four queued-for-archive
  deltas** (no new ordering constraint).
- Implementation: 2 script notes + 1 template runbook.
- Live apply: `cp` 2 notes + `render` (reconcile: commit-gate target unchanged, close-day
  re-rendered); operator hand-applies the runbook edit to live `96-Runbooks/`.
- **Behavioral delta:** a sealed day whose manifest carries an out-of-vocab word now fails
  `--check` (was: silently passed). Historical closes all used script-generated vocab — no
  retroactive failures expected; if one appears it is a true positive.

## Gate 1 — CHECK

**Restated:** INV-3 followed (notes + render; runbook is template content mirrored to the live
vault by the operator). INV-6 untouched. The enum change records reality; the close-lint change
turns a decorative check into the verification the runbook already claims ("vocab ∈ enum").

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — two MODIFIED requirements (delta; sync at archive)
- [x] `vault-template/99-Operations/scripts/{commit-gate,daily-close}-script.md`
- [x] `vault-template/96-Runbooks/session-bootstrap-loader.md` (runbook-lint CI must stay green)
- [x] `CHANGELOG.md`; constitution/project/ADR untouched; vocabulary clean

**Discrepancies for Gate 4:** live `96-Runbooks/session-bootstrap-loader.md` needs the same
hand-edit (outside agent scope; Site proposal `bootstrap-runbook-refresh-proposal` has the text).

## Gate 2 — PLAN

Merge → operator: `cp` 2 notes, `render` + `reconcile`; hand-apply the runbook edit live →
agent probes close-lint on a sandbox vault (live `--check` proof at next close).

**Regression (must pass before Gate 3 closes):**
- [ ] `openspec validate fleet-hygiene-bundle --strict` + `--all --strict`
- [ ] `validate-scripts.sh` → `VALIDATION OK` (incl. close-lint smoke)
- [ ] Runbook-lint equivalent on the edited template runbook (frontmatter keys + six sections)
- [ ] Battery: valid close → `close-lint OK` rc 0; manifest typo (`bankedd`) → FAIL + rc 1;
      rendered pre-commit byte-identical across the runtime-frontmatter change

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All repo-side regression tests green (local, 2026-07-06):** ☑ — validate strict 12/12;
validate-scripts.sh OK; battery: clean close-lint rc 0, typo'd manifest (`recordedd`) FAIL rc 1,
rendered pre-commit byte-identical, runbook frontmatter+sections intact
**CI green on this PR:** ☐ (human) · **Live acceptance:** ☐ (post-apply)

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☐
**Consequences explicitly accepted:**

> Sacrifice: none — a stale doc line, a dead check, and an enum/reality mismatch are repaired;
> the only new behavior is that close-lint can now fail on genuinely bad manifests, which is its
> job.

**ADR:** none

**SIGN-OFF** (human only — agents may not sign):
Name: ______________________
Date: ______________________
