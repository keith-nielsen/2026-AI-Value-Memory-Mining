## Context

Finalized in the `llm-context-reboot` dig: the reboot mechanism is a minimal **session-bootstrap-loader**
— small always-present card + JIT pointers, not a pre-loaded rulebook. This change builds it.

## Goals / Non-Goals

**Goals:** the runbook (SSOT) + adapters (`AGENTS.md`, `CLAUDE.md`) + an in-repo Claude Code
SessionStart hook that surfaces it.

**Non-Goals:** mechanical enforcement of anything; inlining the Constitution/specs (the card *points*,
read JIT); the deferred `.py` rename.

## Decisions

- **Runbook = SSOT, harness files = adapters** (per AGENTS.md). The runbook is harness-agnostic; the
  SessionStart hook is the Claude-Code adapter.
- **Hook ships in-repo** (`.claude/settings.json` + `vault-template/.claude/settings.json`) — reproducible
  for any Claude Code user, per the operator's decision. The hook `cat`s the runbook into context at
  session start (read-only; benign).
- **Active prime over passive-only** — the `[gate]` acknowledgment is the point; auto-load alone proved
  insufficient (the breach).

## Risks / Trade-offs

- A SessionStart hook runs every session → kept benign (read-only `cat`); first run may prompt for
  hook permission (expected).
- Repo vs vault path differ → two `settings.json` (repo `cat`s `vault-template/96-Runbooks/…`; the
  vault one `cat`s `96-Runbooks/…`).

## Open Questions

- None. (The deferred `.py` rename + mechanical ≥3 enforcement remain separate future changes.)
