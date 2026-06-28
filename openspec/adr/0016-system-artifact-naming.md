<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0016 — System-artifact naming: scripts, schemas, indexes → silo-section-descriptor

**Status:** Accepted
**Date:** 2026-06-29
**Relates:** `maintenance` · `vault-structure` · `agent-integration` specs · change `system-artifact-naming` · extends ADR-0013/0014/0015

## Context

ADR-0015 ratified the ≥3-token / `silo-section-descriptor` naming rule (convention). Molds already
conform (ADR-0014). This brings the three remaining system-artifact families — operational **scripts**
(14), **schema** docs (3), and Catalog **indexes** (7) — into conformance.

## Decision

- **Scripts** → `<domain>-<action>-script` (`.md` notes only): `daily-close-script`, `spoil-dump-script`,
  `site-slag-script`, `tailings-reprospect-script`, `ore-detect-script`, `bank-execute-script`,
  `treasury-orphan-script`, `dig-rollover-script`, `knowledge-lint-script`, `naming-rules-script`,
  `kanban-render-script`, `daily-note-script`, `render-reconcile-script`, `commit-gate-script`.
  Canonical mining verbs (keeps `vocabulary-lint` green). **Deploy targets unchanged** — `.py`/`.sh`
  binary renames deferred; `commit-gate-script` keeps `deploy_target: …/hooks/pre-commit` (git requires
  the hook file be named `pre-commit`).
- **Schemas** (`.md`) → `note-frontmatter-schema`, `runbook-format-schema`, `refine-prompt-contract`
  (self-referential `deploy_target`s updated). `naming-rules.json` exempt (`.json`).
- **Indexes** → `<pillar>-domain-index` + `home-master-index` (D2 scope token; future sub-sectors
  narrow the scope, e.g. `technology-ai-index`).

## Options considered

1. **Bundle vs three separate changes** — chose **bundle**: the families are interdependent (the
   `refine-prompt` schema file holds the `index_links` pattern the index rename changes, and that
   pattern also lives in `agent-integration`); one pass keeps them consistent. Same shape as ADR-0013
   (which bundled two families).
2. **`.py` rename now vs deferred** — **deferred** per the operator: `.md` is information (high
   deconfliction value); `.py` are host executables (lower). Deploy targets unchanged this round.

## Consequences

- All system-artifact `.md` now follow the convention; the rule holds across molds + scripts +
  schemas + indexes.
- Forks/live vaults `git mv` 24 `.md` + repoint references on upgrade (mechanical). CHANGELOG history
  is left intact (past entries name files as they were then).
- **Sacrifice:** the migration cost. No principle, invariant, or workflow is weakened; INV-11 +
  CONST-01 reinforced. Note the `naming.md`→`naming-rules-script.md` note still deploys to
  `vault_naming.py` (underscore) — the `.py` consistency fix waits for the deferred binary-rename change.
