<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: shell-pair-conformance

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
MODIFIES "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)" (the shell-pair adoption
paragraph + one scenario). **No principle overridden or weakened** — the last two fleet members
adopt the contract the rest already follow. Conforming amendment per repo precedent.
**Tier:** 0-adjacent (§5 honored — Gate-4 human sign-off)
**Proposer:** Keith Nielsen (operator direction 2026-07-06: "proceed as planned"; drafted by
Claude Code)
**Date:** 2026-07-06

## Why

`vault-slag.sh` / `vault-dump.sh` were the last fleet members outside the contract: hard
`VAULT_ROOT` guard (bare invocation impossible), unvalidated `$1` passed straight to `git mv`
(no INV-11 boundary; a path-ish argument reaches git), no usage/source/destination gates, and a
`git add -A` sweep before the commit — the same F3/F4/F5 class removed from the Python fleet in
`commit-ownership-de-sweep` (and `git mv` already stages the rename, so the sweep collected only
*unrelated* content).

## What Changes

- **Both notes:** usage gate (exit 1); inline bash copy of the root-resolution contract (env if
  it marks a vault, else marker walk; `BLOCKED` exit 3 — bash cannot import `vault_lib`); INV-11
  slug validation via `vault_naming.py --check` (exit 1); source-missing / destination-exists
  gates (`BLOCKED` exit 3); `add -A` replaced by a pathspec-scoped commit of exactly the moved
  effort. Commit messages unchanged.
- **`maintenance` spec:** the vault_lib requirement's shell-pair sentence now records
  conformance; new scenario "A shell mover is env-free, validated, and scoped".
- **CHANGELOG** `[Unreleased]`. **No ADR** (contract adoption; no new decision).

**NOT in this change:** B2-full skeleton; B5/B6/B7; capture helper.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: MODIFIED "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)".

## Impact

- Delta: restates the requirement from the `wave-2-vault-lib-adoption` accretion. **Archive
  order:** `fix-commit-gate-env-guard` → `wave-2-vault-lib-adoption` → this change (B3/B4/hygiene
  touch other requirements; their order among themselves is already recorded).
- Implementation: 2 shell notes.
- Live apply: `cp` 2 notes + `render`/`reconcile`.
- **Behavioral deltas:** gate/validation failures now exit 1/3 with reasons (was: raw git errors
  or unbound-variable crash); unrelated staged content is no longer swept into slag/dump commits;
  bare no-env invocation works. Nothing legitimate relied on the old behaviors.
- **Residual:** the slug check validates the path component, not that the target is a *site*
  index with `status: slagged`/`slag_reason` set — the operator precondition stays procedural
  (Rationale), not mechanical.

## Gate 1 — CHECK

**Restated:** INV-2 — the move commits exactly the move; INV-11 — arguments cross the same naming
boundary every other producer crosses; INV-3/INV-6 — literate notes, deterministic, no new deps
(`vault_naming.py --check` is stdlib-only, already hook-proven env-free).

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — one MODIFIED requirement (delta; archive order noted)
- [x] `vault-template/99-Operations/scripts/{site-slag,spoil-dump}-script.md`
- [x] `validate-scripts.sh` — untouched; `bash -n` + shellcheck cover both (execution battery
      below)
- [x] `CHANGELOG.md`; constitution/project/ADR untouched; vocabulary clean (slag/dump/spoil are
      CONST-01 vocabulary)

**Discrepancies for Gate 4:** none new.

## Gate 2 — PLAN

Merge → operator: `cp` 2 notes + `render`/`reconcile` → agent sandbox battery is the acceptance
(live slag/dump run only when the operator genuinely slags or dumps an effort).

**Regression (must pass before Gate 3 closes):**
- [ ] `openspec validate shell-pair-conformance --strict` + `--all --strict`
- [ ] `validate-scripts.sh` → `VALIDATION OK` (bash -n + shellcheck on both)
- [ ] Battery (env-free sandbox vault): happy slag → rc 0, commit contains exactly the two move
      paths, planted staged file untouched; invalid slug → rc 1; missing source → rc 3;
      destination collision → rc 3; happy dump → rc 0; no-arg usage → rc 1

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All repo-side regression tests green (local, 2026-07-06):** ☑ — validate strict 13/13;
validate-scripts.sh OK (bash -n + shellcheck); battery env-free: happy slag committed exactly the
rename with a planted staged file untouched; invalid slug rc 1; missing source rc 3; destination
collision rc 3; happy dump rc 0; usage rc 1
**CI green on this PR:** ☐ (human) · **Live acceptance:** ☐ (at next real slag/dump)

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑ (2026-07-06 — diff = Gate-1 list; no `protects:` change)
**Consequences explicitly accepted:**

> Sacrifice: none — the movers lose the sweep and the ability to act on unvalidated arguments;
> operators gain reasons and exit codes instead of raw git failures.

**ADR:** none

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen
Date: 2026-07-06

> Provenance: operator directed ("next step" queue continuation), executed the publish sequence
> deliberately (PR #13, CI green, merge `b6ccbd8`), applied live (`3ff560b`). Recorded post-merge
> by the drafting agent; the operator's push is the confirming act.
