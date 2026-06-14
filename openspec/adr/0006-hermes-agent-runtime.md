<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0006 — Hermes Agent as the Phase 3 Runtime

**Status:** Accepted (build deferred — see PRD §14.1)  
**Date:** 2026-06-10

## Context

Phase 3 (agent-assisted refine operations) needs an agent runtime that:
1. Supports a Kanban-style work queue (one card per refine task)
2. Operates locally with a local inference model (Strix Halo / llama.cpp)
3. Enforces a deposit-not-merge model (the worker's done state is "proposal deposited,"
   not "Treasury written")
4. Respects a single-host, trusted-local-user threat model

Options:
- **Claude Code as the agent** — excellent tooling; cloud model; violates the
  privacy/sovereignty posture for real personal content; deferred for cloud bootstrap
- **Raw llama.cpp subprocess** — maximum control, minimum framework; no built-in
  work queue, retry logic, or profile management
- **Hermes Agent v0.15.2 (Nous Research)** — Kanban work queue native; profile
  system; skill-based prompt pinning; local inference first; single-host boards

## Decision

Use **Hermes Agent v0.15.2** as the Phase 3 agent runtime. The mapping is fixed:

- **Workspace**: `dir:<VAULT_ROOT>/30-Sites/<slug>` (absolute path, preserved on completion)
- **Dispatch**: one-shot (not `--goal` mode; per-turn judge loop risks saturating local LLM)
- **Done state**: proposal deposited in `_refine-proposals/` → `kanban_complete()`
- **Blocked state**: cannot produce clean proposal → `kanban_block(reason=...)` never partial write
- **Profile**: dedicated refine profile; orchestration via the persistent `Kent` profile
- **Toolset constraint**: must not enable any toolset that can write `40-Treasury/` or `99-Operations/`

INV-4 is enforced by the executor + commit-gate hook (§12.13), not by Hermes.

## Consequences

- Hermes provides a visual kanban board and retry logic without custom orchestration.
- Single-host boards mean the two-workstation setup runs separate boards; bridged
  via `delegate_task` or a message queue, not a shared DB.
- Dashboard must bind to localhost only (`hermes dashboard`, never `--host 0.0.0.0`).
- Sacrifice: Hermes is a specific runtime dependency; switching runtimes later is a
  Phase 3 change that must re-validate the containment model.
- **Build deferred**: this ADR records the mapping for when Phase 3 is activated.
