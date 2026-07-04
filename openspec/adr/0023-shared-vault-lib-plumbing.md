<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0023 — Shared vault_lib fleet plumbing (root resolution, config SSOT, exit-code contract)

**Status:** Accepted (Gate-4 human sign-off 2026-07-05 — explicit in-session operator approval,
recorded in the change's `proposal.md`)
**Date:** 2026-07-05
**Relates:** `maintenance` spec · change `add-shared-vault-lib` · ADR-0022 (the drive-path /
exclusion-list contract this makes usable) · live-vault Sites `ops-script-runbook-review`
(findings R1–R10, blueprint B1–B8) and `protocol-harness-framework` (`phase-1a-acceptance-probes`,
the P5/SE-5 evidence)

## Context

The Phase-1a sandbox burn-in (2026-07-04/05) proved the ADR-0022 drive path unusable as shipped:
probe P5 — the bare exact invocation the exclusion list requires — crashes with
`KeyError: 'VAULT_ROOT'` because a fresh tool shell has no sourced environment and the exact-match
exclusion forbids an env prefix (SE-5). The crash is fail-safe but blocks the driver contract and
makes SE-5 (does the exclusion actually lift the sandbox?) unprovable.

A same-week review of the whole ops fleet (`ops-script-runbook-review`) found the ~530-line fleet
healthy but idiomatically divergent where it matters long-term: three frontmatter parsers giving
opposite answers to "is this day closed" on `closed: false` (R2); rollover's gate refusal exiting
0, indistinguishable from success for any driver or model (R3); config vocabulary with three homes
so `config.env` edits silently fail to propagate to kanban (R4); commit scoping split between
scoped adds and sweeps (R5). All five defects share one shape.

## Options considered

1. **Per-script patches.** Fixes P5 six times in six slightly different ways; leaves R2/R3/R4
   divergence in place; every future script re-improvises the same five concerns. Rejected.
2. **Extend `vault_naming` into a general library.** One import instead of two, but couples a
   governed naming SSOT (its own ADR lineage and ceremony cadence) to plumbing churn, and gives
   the naming module an unrelated API surface. Rejected.
3. **New shared module `vault_lib.py`, incremental adoption (chosen).** One literate note; the
   drive-path set + render adopt now (where the burn-in evidence is), the rest adopt as next
   touched. Bootstrap exception: `render` carries an inline copy of the resolution contract
   because it deploys the module itself.

## Decision

- Ship `vault-lib-script.md` → `~/bin/vault_lib.py`: `find_vault_root()` (env-first; marker-walk
  from cwd to a `99-Operations/` config file; hard-block on a bad explicit env); `load_config` /
  `vocab()` (precedence: process env > `config.env` > `config.defaults.env` > code default — the
  shell sourcing order, mirrored, raw strings, no shell evaluation); `fm()` / `is_closed()`
  (YAML-typed, fleet-wide); `commit_paths()` (scoped adds, one commit — the INV-2 shape); the
  fleet exit-code contract `0` ok · `1` violation · `2` needs-input · `3` gate-blocked; a
  read-only self-check CLI. Lazy `frontmatter` import keeps root/config helpers usable outside
  the venv.
- Adopt in `daily-close`, `daily-note`, `dig-rollover`, `kanban-render`, `bank-execute` (the
  ADR-0022 exclusion-list set) and `render-reconcile` (inline bootstrap copy).
- Gate refusals across the adopted set exit **3** with a `BLOCKED:` line.

## Consequences

- The ADR-0022 drive path becomes real: bare exact invocations work with no environment, so P5
  passes and SE-5 becomes provable (a bare run that writes proves the exclusion lifted the
  sandbox).
- Drivers and future models can key on exit codes instead of parsing prose — the same
  structure-over-trust posture as ADR-0022, applied to script outcomes.
- One vocabulary chain: a `config.env` edit propagates to kanban and close without script edits.
- **Sacrifice:** a shared single point of failure — a `vault_lib` defect hits every adopter at
  once (mitigated by CI's render + fleet smoke on every push); five enumerated behavioral deltas
  (rollover 0→3, close-day 1→3 on refusal; `closed: false` uniformly open; kanban vocabulary from
  config; `DISPOSITIONS` config-sourced below env) — anything keying on the old behavior must
  re-key; and a deliberately two-idiom fleet during wave-2 transition, documented rather than
  silent.
