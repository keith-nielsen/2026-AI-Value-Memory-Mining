<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: system-artifact-naming

**Change type:** `constitution-override`
**Principle(s) affected:** `maintenance` (`protects: [INV-2, INV-3, INV-6]` — Script Inventory enumerates script note names) · `vault-structure` (`[CONST-02, CONST-04, CONST-05, INV-1, INV-12]` — schema doc references) · `agent-integration` (`[INV-4, INV-5, INV-8, INV-11]` — index-link pattern + refine-prompt reference). **Conforming amendment** — brings the remaining system-artifact families to the ratified ≥3 / `silo-section-descriptor` convention (ADR-0015); no principle weakened.
**Tier:** 0/1 — additive/conforming
**Proposer:** Keith Nielsen (drafted by Claude Code; authorized by Keith)
**Date:** 2026-06-28

---

## Why

Molds conform (v0.1.7) and the ≥3-token rule is ratified (v0.1.8 / ADR-0015). This brings the three remaining system-artifact families — operational **scripts**, **schema** docs, and Catalog **indexes** — to the same `silo-section-descriptor` form. **Bundled** because the families are interdependent: the `refine-prompt` schema file holds the `index_links` pattern that the index rename changes, and that pattern also lives in the `agent-integration` spec.

## What Changes

**Scripts** (`.md` notes only — deploy targets **unchanged** per the deferred `.py` decision; canonical verbs for `vocabulary-lint`):

| current | → | current | → |
|---|---|---|---|
| `render-reconcile` | `render-reconcile-script` | `dump` | `spoil-dump-script` |
| `daily-note` | `daily-note-script` | `slag` | `site-slag-script` |
| `lint` | `knowledge-lint-script` | `reprospect` | `tailings-reprospect-script` |
| `orphans` | `treasury-orphan-script` | `rollover` | `dig-rollover-script` |
| `refine-detect` | `ore-detect-script` | `close-daily` | `daily-close-script` |
| `refine-execute` | `bank-execute-script` | `kanban-render` | `kanban-render-script` |
| `naming` | `naming-rules-script` | `pre-commit` | `commit-gate-script` (deployed hook stays `pre-commit`) |

**Schemas** (`.md` only; `naming-rules.json` exempt — `.json`): `frontmatter` → `note-frontmatter-schema` · `runbook` → `runbook-format-schema` · `refine-prompt` → `refine-prompt-contract`.

**Indexes**: `mental/health/financial/social/technology/calling-index` → `…-domain-index` · `home-index` → `home-master-index`.

**Spec deltas:** `maintenance` (Script Inventory note names), `vault-structure` (Frontmatter Schemas doc references), `agent-integration` (Refine Proposal `index_links` pattern + `refine-prompt` reference). **No principle weakened**; reinforces INV-11 + CONST-01.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: Script Inventory note names (deploy targets unchanged).
- `vault-structure`: Frontmatter Schemas — schema doc filenames.
- `agent-integration`: Refine Proposal JSON Schema — `index_links` pattern + `refine-prompt` reference.

## Impact

- **Spec deltas:** `maintenance`, `vault-structure`, `agent-integration`.
- **Implementation (vault-template):** `git mv` 14 script notes, 3 schema docs, 7 Catalog index files; repoint — `home-master-index` links to the `<pillar>-domain-index` notes; `index_links` in `00-Docs/examples/*` and `refine-prompt-contract`; schema-doc `deploy_target` frontmatter (schemas render to themselves); any doc references to script/schema/index names (`docs/`, `00-Docs/`). Script `deploy_target`s **unchanged**; `commit-gate-script` keeps `deploy_target: …/hooks/pre-commit`.
- **No `.py` binary renames** (deferred). Re-render unaffected for scripts (deploy targets unchanged).
- New ADR (Gate 4). Live-vault mirror covers scripts + indexes (the live vault carries no openspec specs/schemas-as-meta; mirror the renames + reference repoints + re-render + reconcile).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** `maintenance` (INV-2/3/6) governs the literate-script format, render/reconcile, and the script inventory — renaming the note *files* changes only the inventory's labels, not the one-commit / Layer-0-SSOT / offline guarantees (deploy targets and code are untouched). `vault-structure` (CONST-02/04/05, INV-1/12) fixes layout + schemas — only the schema *doc filenames* change, not layers, numbering, flat-Treasury, or format. `agent-integration` (INV-4/5/8/11) fixes the proposal contract — only the `index_links` example *pattern* and the `refine-prompt` *reference* change, not the no-Treasury-write boundary or slug enforcement. All conforming; the ≥3 rule (INV-11) is reinforced.

**Blast radius (checked off in Gate 3):**

- [ ] `openspec/specs/maintenance/spec.md` — MODIFIED Script Inventory (note names; deploy targets unchanged)
- [ ] `openspec/specs/vault-structure/spec.md` — MODIFIED Frontmatter Schemas (schema doc references)
- [ ] `openspec/specs/agent-integration/spec.md` — MODIFIED Refine Proposal JSON Schema (`index_links` pattern + `refine-prompt` ref)
- [ ] `vault-template/99-Operations/scripts/*.md` — 14 `git mv` (deploy_target frontmatter unchanged; `commit-gate-script` keeps `…/hooks/pre-commit`)
- [ ] `vault-template/99-Operations/schemas/{frontmatter,runbook,refine-prompt}.md` — 3 `git mv` + their `deploy_target` frontmatter
- [ ] `vault-template/40-Treasury/Catalog/*.md` — 7 `git mv` + `home-master-index` link repoints
- [ ] `vault-template/00-Docs/examples/*` + `docs/*` — `index_links` / script / schema / index references
- [ ] `AGENTS.md`, `README.md` (repo root) — script/schema reference repoints
- [ ] `.github/scripts/validate-scripts.sh` (render bootstrap + `index_links` fixture); `.github/ISSUE_TEMPLATE/bug.yml` (example path)
- [ ] _(CHANGELOG history left intact — past entries name files as they were then)_
- [ ] ADR-00NN (new)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** `git mv` per family; repoint references in lockstep (home-index links, `index_links`, schema `deploy_target`s, doc refs). Forks/live vaults run the same renames + repoints + re-render. Script `deploy_target`s unchanged → deployed `~/bin/vault-*.py` names unchanged (`.py` rename deferred).

**Regression that MUST pass before Gate 3:** `openspec validate --all --strict`; `constitution-lint`; `vocabulary-lint`; `validate-scripts.sh` (renders + smoke-tests every script in a sandbox); link-check; CI green.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — 24 `.md` renames (14 scripts, 3 schemas, 7 indexes) + all reference repoints (vault-template, docs, AGENTS.md, README.md, .github)
**All regression tests green (local suite):** ☑ — `openspec validate --all` 8/8 · constitution-lint · vocabulary-lint · `validate-scripts.sh` sandboxed VALIDATION OK (renders every renamed script + smoke-tests) · residual-name grep clean
**CI green on this PR:** ☐ (runs on push)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑ (incl. the corrected `.github` / `AGENTS.md` / root `README.md` references)
**Consequences explicitly accepted:**

> Sacrifice: forks/vaults must `git mv` 24 `.md` files + repoint references on upgrade (mechanical). Script `.py` binaries keep their names (deferred). No principle, invariant, or workflow is weakened.

**ADR created:** `openspec/adr/0016-system-artifact-naming.md` ☑
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: **Keith Nielsen** — "Authorized." (transcribed by Claude Code at Keith's explicit instruction; the decision is the human's)
Date: 2026-06-29
