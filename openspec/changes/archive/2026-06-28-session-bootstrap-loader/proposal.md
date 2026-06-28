<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: session-bootstrap-loader

## Why

A cold-start agent session must *reliably* load the governing context — the failure class catalogued
in the `llm-context-reboot` dig (the 2026-06-26 governance breach happened with `CLAUDE.md` loaded but
unengaged). Add a minimal **session-bootstrap-loader** so every session sets the env, engages the
non-negotiable gates, and knows the just-in-time pointers: **minimum bootstrap, maximum confidence.**

## What Changes

- **NEW runbook** `vault-template/96-Runbooks/session-bootstrap-loader.md` — the harness-agnostic SSOT
  for the cold-start prime (conforms to the existing runbook-format schema).
- **Adapters:** `AGENTS.md` + `vault-template/CLAUDE.md` point at it (and the runbook list).
- **Claude Code SessionStart hooks (in-repo):** `.claude/settings.json` (repo) and
  `vault-template/.claude/settings.json` (ships to vaults) surface the runbook into context at session
  start.
- **No spec requirement changes** — the runbook conforms to the existing `maintenance` Runbook-Format;
  no `protects:`-tagged spec is touched (this is a regular change, not a constitution-override).

## Capabilities

### New Capabilities
- _(none — no new spec capability; the runbook conforms to the existing Runbook-Format requirement)_

### Modified Capabilities
- _(none — no requirement changes)_

## Impact

`vault-template/96-Runbooks/session-bootstrap-loader.md` (new) · `AGENTS.md`, `vault-template/CLAUDE.md`
(adapters) · `.claude/settings.json` + `vault-template/.claude/settings.json` (SessionStart hooks).
Live-vault mirror: the runbook + the `CLAUDE.md` pointer + a `.claude/settings.json` hook. No `.py`
changes; no `protects:`-tagged spec touched.
