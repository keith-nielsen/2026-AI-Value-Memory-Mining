---
type: runbook
id: session-bootstrap-loader
title: Session bootstrap loader (cold-start prime)
trigger: "a fresh or /clear'd agent session begins, before any vault/repo work — load env, engage the gates, know the pointers"
applies-to: both
class: procedure
last-validated: 2026-07-06
---
# Runbook — Session Bootstrap Loader

## Purpose

Prime a cold-start agent session with the **minimum** context for **maximum** governance confidence:
set the environment, engage the non-negotiable gates, and know where to read the rest just-in-time —
so the agent never operates from an empty or degraded context (the failure class catalogued in the
`llm-context-reboot` dig). Minimum bootstrap = small card + JIT pointers; maximum confidence = the
gates + verification, not loading the whole rulebook.

## Preconditions

- Operating in the live vault (`$VAULT_ROOT`) or the repo (`value-memory-mining`).
- The harness auto-loads `CLAUDE.md` / `AGENTS.md` and the memory `MEMORY.md` index — this runbook is
  their single source of truth; the SessionStart hook surfaces it automatically.

## Steps

1. `[script]` **Env** — `source 99-Operations/config.env` (sets `VAULT_ROOT` / `PILLARS` / venv on
   `PATH`). Re-source per shell (it does not persist). Kills the `VAULT_ROOT` wall.
2. `[gate]` **Engage the operating card** — acknowledge these four, don't merely possess them:
   - **Governance-first** — before any structural / naming / spec / mold / script change, *read*
     `openspec/constitution.md` + the relevant `protects:`-tagged spec; honor the §5 AI hard-stop;
     governed changes run the OpenSpec ceremony (propose → apply → human Gate-4 → archive → tag →
     mirror), never ad-hoc.
   - **Re-read before acting** — apply an established rule from its artifact (spec / memory / runbook),
     never from recollection.
   - **Autonomy bans** — no autonomous writes to `40-Treasury/` or `99-Operations/` (INV-4/5).
   - **Clean ops** — hooks and the script fleet are env-free (root self-resolution, ADR-0023);
     source `config.env` only for operator-shell conveniences (venv on `PATH`, vocabulary
     overrides); separate the action from its verification.
3. `[agent]` **Know the just-in-time pointers** (read only when a task touches them):
   - Built-but-unexercised ops + their docs → the `llm-context-reboot` Site load-list.
   - Deferred / not-built — do **not** attempt or assume available: Crucible, Mint, Forge, Hermes, n8n.
   - Other runbooks: `daily-close-runbook`, `provenance-seal-runbook`.
   - Durable rules: the auto-loaded memories (`MEMORY.md`).
4. `[script]` **Verify** — `: "${VAULT_ROOT:?}"` (env set); optionally `vault-render.py reconcile`
   (zero drift).

## Pitfalls

- Passive auto-load is **not** sufficient — the 2026-06-26 governance breach happened with `CLAUDE.md`
  already loaded. The `[gate]` acknowledgment is the whole point; do not skip it.
- Do **not** inline the Constitution / specs / load-list here — *name and point*; read just-in-time.
  Inlining bloats context and is what this runbook deliberately avoids.
- Env does not survive between shells — re-source `config.env` in each new shell.

## Verification

- `VAULT_ROOT` is exported and resolves to the vault root.
- The four gates are acknowledged before any governed action this session.
- (Optional) `vault-render.py reconcile` reports zero drift.

## Rollback

- None required — the prime only loads context and sets the environment; it mutates no vault content.
  If `config.env` was sourced from the wrong path, re-source the correct one.
