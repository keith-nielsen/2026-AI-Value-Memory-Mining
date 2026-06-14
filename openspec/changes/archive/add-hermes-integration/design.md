<!-- SPDX-License-Identifier: Apache-2.0 -->
## Context

Hermes Agent v0.15.2 (Nous Research) executes workers with the operator's uid
and full filesystem access — it is a trusted-local-user, single-host runtime.
It does not sandbox workers to their declared workspace. This means containment
must be enforced externally: the refine executor checks the proposal boundary,
and the commit-gate hook (INV-11) fires on every commit including the worker's.

## Goals / Non-Goals

**Goals:**
- Fix the Hermes workspace type, dispatch mode, done/blocked API calls, profile,
  and toolset constraint so the mapping cannot be silently widened
- Implement the Phase 3 harness as disabled-by-default (`--dry-run`)
- Provide the agent prompt contract as `refine-prompt.md`

**Non-Goals:**
- Wiring a live model (deferred, §14.1)
- Implementing the Hermes Kanban board UI
- Sandboxing the worker at the OS level (deferred, §14.1)

## Decisions

**`dir:` workspace, not `scratch` or `worktree`.** `scratch` workspaces are wiped
on completion (the proposal would be lost). `worktree` creates an unnecessary Git
branch for what is just a file deposit. `dir:<VAULT_ROOT>/30-Sites/<slug>` is
preserved on completion and is the agent's natural working area.

**One-shot dispatch, not `--goal` mode.** The per-turn judge loop in `--goal` mode
risks saturating the local LLM (Strix Halo / llama.cpp) for what is a single
discrete artifact (a JSON proposal). One-shot is cheaper, faster, and predictable.

**`kanban_complete()` on deposit, not on Treasury write.** The Kanban board's
concept of "done" is decoupled from the vault's concept of "refined." A worker
that completes its board card has deposited a proposal — nothing more.

## Risks / Trade-offs

- The containment model relies on the executor + hook, not the runtime. If a
  future Hermes version changes the worker execution model, the containment
  analysis must be re-validated before live wiring.
- Single-host boards mean multi-machine setups require `delegate_task` or a
  message queue bridge — no shared SQLite DB across machines.
