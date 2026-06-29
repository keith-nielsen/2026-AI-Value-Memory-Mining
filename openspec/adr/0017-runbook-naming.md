<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0017 — Runbook naming: runbooks → ≥3-token; unify the daily-close / provenance-seal vocabulary

**Status:** Accepted
**Date:** 2026-06-29
**Relates:** `maintenance` · `vault-structure` specs · change `runbook-naming-3token` · extends ADR-0011 (spec-as-code runbooks) / ADR-0012 (daily close lifecycle) / ADR-0015 (≥3-token) / ADR-0016 (system-artifact naming)

## Context

ADR-0015 ratified the ≥3-token / `silo-section-descriptor` rule; ADR-0016 conformed scripts, schemas,
and indexes. The two original runbooks — `close-daily`, `seal-provenance` — were the last grandfathered
2-token system-artifact names (`session-bootstrap-loader` already conforms). They also anchored a
three-way vocabulary drift: the engine was already renamed `daily-close-script` (daily-close order),
`session-bootstrap-loader` already referred to the runbook as `daily-close`, while `AGENTS.md` and the
specs still said `close-daily` (close-daily order).

## Decision

- **Runbook files** → `<silo>-<section>-runbook` (`.md`): `close-daily.md` → `daily-close-runbook.md`,
  `seal-provenance.md` → `provenance-seal-runbook.md`. `id:` matches the filename stem (as
  `session-bootstrap-loader` does).
- **Ritual / process vocabulary unified** on the bare silo-section stem: `close-daily` → `daily-close`,
  `seal-provenance` → `provenance-seal`. Process, runbook, and script now share one family
  (`daily-close` ritual ↔ `daily-close-runbook` ↔ `daily-close-script`).
- **`session-bootstrap-loader` unchanged** — already ≥3-token; renaming it would pull a third runbook
  into the blast radius for no naming gain.

## Options considered

1. **Unify on `daily-close` / `provenance-seal` (Option A)** — chosen. Ends the three-way drift;
   coheres with the already-renamed `daily-close-script` and the `session-bootstrap-loader` cross-ref.
2. **Rename the runbook files only (Option B)** — rejected: leaves the ritual vocabulary divergent
   from the script and runbook; three names for one concept persists.
3. **Keep `close-daily` order, add `-runbook` (Option C)** — rejected: `close-daily-runbook` vs
   `daily-close-script` keeps the ordering mismatch.

## Consequences

- All runbooks now satisfy the ≥3-token rule; the convention holds across molds + scripts + schemas +
  indexes + runbooks. The daily-close vocabulary is internally consistent.
- Forks/live vaults `git mv` 2 runbook files + repoint references on upgrade (mechanical). No re-render
  (runbooks have no deploy target). CHANGELOG and ADR history are left intact (past entries name the
  runbooks as they were then).
- **Sacrifice:** the migration cost and the change of the long-standing `close-daily` / `seal-provenance`
  ritual phrasing to `daily-close` / `provenance-seal`. No principle, invariant, or workflow is
  weakened; INV-11 + CONST-01 are reinforced.
