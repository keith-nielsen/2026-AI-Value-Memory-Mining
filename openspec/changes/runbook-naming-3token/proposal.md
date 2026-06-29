<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: runbook-naming-3token

**Change type:** `constitution-override`
**Principle(s) affected:** `maintenance` (`protects: [INV-2, INV-3, INV-6]` — Daily Close Lifecycle names the ritual) · `vault-structure` (`protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12]` — Folder Structure runbook examples + Frontmatter Schemas ritual reference). **Conforming amendment** — brings the last grandfathered system-artifact family (runbooks) to the ratified ≥3 / `silo-section-descriptor` convention (ADR-0015) and unifies the daily-close vocabulary; no principle weakened.
**Tier:** 0/1 — additive/conforming
**Proposer:** Keith Nielsen (drafted by Claude Code; authorized by Keith)
**Date:** 2026-06-29

---

## Why

Scripts, schemas, indexes, and molds conform (v0.1.7 / v0.1.9); the ≥3-token rule is ratified (v0.1.8 / ADR-0015). The two original runbooks — `close-daily`, `seal-provenance` — remain 2-token grandfathered names, the last system-artifact family off-convention (`session-bootstrap-loader` already conforms). They are also the source of a three-way vocabulary drift: the **script** was renamed `daily-close-script` (daily-close order), `session-bootstrap-loader` already refers to the runbook as `daily-close`, while `AGENTS.md` / specs still say `close-daily` (close-daily order). This change ends the drift by unifying on one stem family per ritual.

## What Changes

Rename the two runbook files to ≥3-token `silo-section-descriptor` form and **unify the ritual vocabulary** so the process, runbook, and script share one stem family (Option A):

| Concept | Ritual/process (vocab) | Runbook file + `id` | Script (exists) |
|---|---|---|---|
| Daily close | `close-daily` → **`daily-close`** | `close-daily` → **`daily-close-runbook`** | `daily-close-script` (already aligned) |
| Provenance seal | `seal-provenance` → **`provenance-seal`** | `seal-provenance` → **`provenance-seal-runbook`** | (none — runbook-only) |

`session-bootstrap-loader` already satisfies the ≥3-token floor → **unchanged** (avoids blast-radius into another runbook). The "-runbook" descriptor is adopted for the renamed files; the ritual vocabulary keeps the bare silo-section form (`daily-close`, `provenance-seal`).

**Spec deltas:** `maintenance` (Daily Close Lifecycle — ritual name), `vault-structure` (Folder Structure runbook examples + Frontmatter Schemas ritual reference). **No principle weakened**; reinforces INV-11 + CONST-01.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** `maintenance` (INV-2/3/6) governs the one-commit rule, the Layer-0 literate-script SSOT, and offline determinism — renaming the daily-close *ritual label* changes only how the requirement *names* the procedure, not the commit/SSOT/offline guarantees (the engine `vault-close-day.py` and its behavior are untouched). `vault-structure` (CONST-02/04/05, INV-1/12) fixes the layer model, folder numbering, flat-Treasury, and the frontmatter schemas — only two *illustrative references* to the runbooks/ritual change, not the layout, numbering, Treasury shape, or any schema field. Both are conforming; INV-11 (≥3-token) is reinforced, nothing relaxed.

**Blast radius — every artifact referencing the renamed runbooks/ritual:**

- [x] `openspec/specs/maintenance/spec.md` — MODIFIED Daily Close Lifecycle (`close-daily` → `daily-close` ritual)
- [x] `openspec/specs/vault-structure/spec.md` — MODIFIED Folder Structure (runbook examples) + Frontmatter Schemas (`close-daily` ritual ref)
- [x] `vault-template/96-Runbooks/close-daily.md` → `daily-close-runbook.md` (`git mv` + `id`/title/heading)
- [x] `vault-template/96-Runbooks/seal-provenance.md` → `provenance-seal-runbook.md` (`git mv` + `id`/title/heading)
- [x] `AGENTS.md` — runbook list (lines ~117-118) + `seal-provenance` operating note (~131) [not `protects:`-tagged]
- [x] `vault-template/96-Runbooks/session-bootstrap-loader.md` — "Other runbooks" cross-ref (`daily-close`/`seal-provenance` → new stems) [not `protects:`-tagged]
- [x] `CLAUDE.md` (repo root adapter) — runbook examples [not `protects:`-tagged]
- [x] `vault-template/99-Operations/scripts/daily-close-script.md` — "the `close-daily` runbook" → `daily-close-runbook`
- [x] `vault-template/99-Operations/scripts/dig-rollover-script.md` — "run close-daily first" → "run daily-close first"
- [x] `vault-template/99-Operations/schemas/note-frontmatter-schema.md` — "set by close-daily" → "set by daily-close"
- [x] `vocabulary-lint` glossary — `daily-close` / `provenance-seal` already use canonical mining verbs (close/seal); no new off-metaphor terms
- [x] _(ADR-0012, CHANGELOG, `openspec/changes/archive/**` left intact — history names artifacts as they were then)_
- [x] ADR-0017 (new — see Gate 4)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. `git mv` the two runbook files to their `-runbook` names; update each `id:`, `title:`, and `# Runbook —` heading.
2. Apply the two spec deltas to the change's `specs/` (synced to main specs at archive).
3. Repoint references in lockstep: AGENTS.md, root CLAUDE.md, `session-bootstrap-loader` cross-ref, `daily-close-script`, `dig-rollover-script`, `note-frontmatter-schema`.
4. Forks/live vaults run the same renames + repoints (no re-render needed — runbooks have no deploy target; they are read-and-follow procedures).

**Regression tests that MUST pass before Gate 3:**

- [x] `openspec validate runbook-naming-3token --strict` passes
- [x] `constitution-lint` passes (override acknowledgment + ADR present)
- [x] `vocabulary-lint` passes (no off-metaphor terms introduced)
- [x] residual-name grep: no `close-daily` / `seal-provenance` outside `openspec/changes/archive/`, ADR history, and CHANGELOG

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — 2 `git mv` (runbooks) + `id`/title/heading edits + 2 spec deltas + 6 reference repoints (AGENTS.md, root CLAUDE.md, session-bootstrap-loader, daily-close-script, dig-rollover-script, note-frontmatter-schema)
**All regression tests green (local):** ☑ — `openspec validate runbook-naming-3token` OK · residual-name grep clean (live tree)
**CI green on this PR:** ☐ (runs on push)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> Sacrifice: forks/vaults must `git mv` 2 runbook files + repoint references on upgrade (mechanical); the long-standing `close-daily` / `seal-provenance` ritual phrasing changes to `daily-close` / `provenance-seal` for coherence with the already-renamed `daily-close-script` and the `session-bootstrap-loader` cross-ref. No invariant, principle, or workflow is weakened — INV-11 is reinforced and the three-way vocabulary drift is eliminated.

**ADR created:** `openspec/adr/0017-runbook-naming.md` ☑
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: **Keith Nielsen** — "OK, so let's go Option A and get it all done." (transcribed by Claude Code at Keith's explicit instruction; the decision is the human's)
Date: 2026-06-29
