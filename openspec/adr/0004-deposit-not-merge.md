<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0004 — Deposit-Not-Merge: The Refine Pipeline Gate Model

**Status:** Accepted  
**Date:** 2026-06-10

## Context

The refine pipeline needs to move material from Sites (Layer 2) into the Treasury
(Layer 1) while satisfying two constraints:
1. No agent/LLM process may write Treasury directly (INV-4)
2. The human must remain the gate — automation proposes, humans approve

Options:
- **Direct agent write with review flag** — agent writes to Treasury, human reviews
  and may revert. Violates INV-4; trust-then-verify is weaker than gate-then-write.
- **PR-based merge** — agent opens a PR; human merges. Git-native but heavy-weight
  for single-person knowledge work; also couples the knowledge pipeline to the VCS
  review UI.
- **Deposit-not-merge** — agent deposits a proposal JSON into `_refine-proposals/`;
  human reviews and moves it to `_refine-approved/` (the gate); a deterministic
  script executes the write. Three distinct actors; human gate is a file-move.

## Decision

Adopt the **deposit-not-merge** model (CONST-01 runtime form):

1. Agent deposits `*.json` proposal into `20-Claims/_refine-proposals/`.
2. Human reviews and moves approved proposals to `20-Claims/_refine-approved/`.
   *Presence in `_refine-approved/` is the gate.*
3. The refine executor script reads `_refine-approved/` and writes Treasury.

The agent's definition of done is "proposal deposited." Kanban `done` is not a
Treasury write. The human gate and executor run outside the agent flow.

## Consequences

- INV-4 is satisfied structurally: the executor, not the agent, holds the write key.
- The gate is a file-move — simple, auditable, requires no UI beyond a file manager.
- An agent that cannot produce a clean proposal calls `kanban_block`, never a
  partial Treasury write.
- INV-13 (name conformance) is enforced at the executor boundary: a non-conforming
  `target_note` stem is rejected before any write, regardless of what the agent sent.
- Sacrifice: refining is a two-step human interaction (review + move), not one-click.
  This is intentional — the friction is the gate.
