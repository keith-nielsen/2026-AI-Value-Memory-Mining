<!-- SPDX-License-Identifier: Apache-2.0 -->
## Why

Phase 3 of the vault build introduces agent-assisted refine operations, but the
system needs an explicit, immutable runtime mapping that prevents the agent from
widening its own trust boundary. Hermes Agent v0.15.2 provides the Kanban work
queue needed, but without a pinned workspace type, dispatch mode, and toolset
constraint, a future configuration change could silently expand the agent's write
scope — violating INV-4 (bounded write scope) or INV-5 (actor ≠ owner).

This change records the Hermes runtime mapping as a first-class spec so the
containment model is visible, testable, and frozen.

## What Changes

### New Capabilities

- `agent-integration`: The Phase 3 agent harness specification — the proposal JSON
  schema, the dry-run scaffolding, and the Hermes Kanban worker runtime mapping
  (workspace, dispatch mode, done/blocked states, profile, toolset constraint).

## Impact

- `openspec/specs/agent-integration/spec.md` is introduced (this change's delta spec)
- `vault-template/99-Operations/schemas/refine-prompt.md` is introduced (the agent prompt contract)
- The Phase 3 harness scaffolding is built as `--dry-run`-only; no live model is wired
- INV-4, INV-5, INV-8, and INV-11 all govern agent-integration behavior
- The deposit-not-merge model (ADR-0004) is the runtime consequence of this spec
