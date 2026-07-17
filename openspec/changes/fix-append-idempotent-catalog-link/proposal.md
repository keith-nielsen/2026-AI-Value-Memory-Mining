<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: fix-append-idempotent-catalog-link

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** one Requirement ("Catalog Linking Is Idempotent"). **No principle is overridden or
weakened**; it is a conforming bug fix that strengthens INV-12 reachability hygiene. Ships **without
a new ADR** per the `add-overreach-scope-review` / `add-template-parity-check` precedent for
conforming additive amendments.
**Tier:** 0-adjacent (a determinism/idempotency fix to the INV-3 fleet; §5 AI hard-stop honored —
surfaced for explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-18)
**Date:** 2026-07-18

---

## Why

The refine executor (`bank-execute-script` → `~/bin/vault-refine-execute.py`) unconditionally appends
`- [[<stem>]]` to every `index_links` target when banking. For `create` that is correct (a new note
is in no index). For **`append` it is a defect:** append extends a note that is *already* banked and
catalogued, so re-linking duplicates the note's existing Catalog bullet. There is no clean way to
append to an already-catalogued note — a non-empty `index_links` duplicates the link, and an empty
one defaults to the `pending-catalog` holding index (which mis-files an already-homed note, and is
absent on a vault that has not applied ADR-0024, so it hard-rejects).

This surfaced attempting the operator-directed errata append to the gold note
`unreconciled-invariants-are-wishes` (carry-forward item #2): the note is already linked from
`technology-domain-index.md`, so banking the errata would have written a duplicate bullet. The fix
makes catalog linking **idempotent** — link only if the index does not already carry it — which makes
`append` correct for its primary use (extending an existing note) while still linking a genuinely new
index. Chosen over accepting the duplicate (catalog debris in a gold note) or a manual Treasury edit
(bypasses the pipeline's atomic-commit discipline): operator decision, 2026-07-18.

## What Changes

- **`maintenance` spec:** +1 ADDED Requirement ("Catalog Linking Is Idempotent", 2 scenarios).
- **`vault-template/99-Operations/scripts/bank-execute-script.md`:** the bank-loop links only if
  `f"[[{note.stem}]]"` is not already in the index; Rationale documents the idempotency. `create`
  behavior, pre-flight, batch isolation, and the one-atomic-commit contract are unchanged (the
  index file is passed to `commit_paths` either way; when unchanged it is a no-op in the commit).
- **`tests/test_fleet.py`:** +1 case — an `append` to an already-catalogued note does not duplicate
  the catalog bullet; a create into a fresh index still links once.
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Out of scope:** the errata append itself (banked separately once this ships and mirrors to live);
the `pending-catalog` / ADR-0024 apply (untouched).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> The `maintenance` spec governs the deterministic fleet: INV-2 (one mutation, one commit), INV-3
> (literate source of truth, drift detected via render/reconcile), INV-6 (offline determinism). This
> fix makes the bank step **idempotent** — a re-link on an index that already has the bullet is a
> no-op — which is squarely an INV-6 determinism property (same inputs, no spurious duplicate). The
> single-atomic-commit contract (INV-2) is preserved: the index path is still named to `commit_paths`
> and simply contributes no diff when unchanged. Nothing is relaxed; a duplicate-write bug is removed
> and its absence codified as a spec requirement.

**Blast radius — every artifact this change touches:**

- [x] `openspec/specs/maintenance/spec.md` — ADDED Requirement (spec delta in this change)
- [x] `vault-template/99-Operations/scripts/bank-execute-script.md` — idempotent link guard + Rationale
- [x] `tests/test_fleet.py` — +1 behaviour case
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `openspec/adr/` + README ADR count — **no change** (conforming amendment, no ADR)
- [ ] Live vault — **no change in this PR**; the fixed script mirrors to the live vault post-merge,
      then `render` redeploys `~/bin/vault-refine-execute.py`, then `tools/template-parity.py`
      confirms the mirror (v0.1.27)

**External dependency being adopted: NONE.**

## Gate 2 — PLAN (Migration + Regression)

- Additive + a two-line behavioural change to one script; no migration of existing data.
- **Coexistence with in-flight `add-telemetry-segment`** (also modifies `maintenance`): this change
  ADDs a distinct requirement and modifies no shared requirement header → no last-writer-wins risk;
  archive in merge order regardless.
- Regression: full CI green (`openspec validate --all --strict`, the lints, `validate-scripts`,
  fleet-pytest incl. the new case). The fleet fixture renders the fixed executor and drives it as a
  subprocess — proving behaviour, not a re-implementation.
- Post-merge: mirror the fixed note into the live vault, `render`, then `tools/template-parity.py
  <VAULT_ROOT>` must report `0 drift` (the mirror-completeness check this repo just gained).
- Rollback: revert the guard + scenario + test + CHANGELOG line (single revert).

## Gate 3 — EXECUTE + REGRESSION-TEST

- Implementation in this PR. `tests/test_fleet.py` new case + full suite green locally (recorded when
  run). `openspec validate --all --strict` green.
- CI green on the PR = Gate 3 complete (recorded here when checks finish).

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [x] Blast radius re-checked against the final diff (4 surfaces, all declared: CHANGELOG.md,
      tests/test_fleet.py, vault-template/99-Operations/scripts/bank-execute-script.md,
      openspec/changes/fix-append-idempotent-catalog-link/ — nothing undeclared)
- [x] Consequences explicitly accepted (append mode now correct for already-catalogued notes; no
      behavioural change to `create`; **zero external runtime dependencies**)
- [x] Human sign-off recorded: **Approved — Keith Nielsen, 2026-07-18** (operator reviewed the
      proposal and replied `Approved`; recorded by Claude Code per the standing Gate-4 ritual — the
      human decision is the operator's reply, the agent only transcribes it)
