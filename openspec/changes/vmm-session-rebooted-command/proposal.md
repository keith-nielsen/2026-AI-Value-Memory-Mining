<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: vmm-session-rebooted-command

## Why

The `session-bootstrap-loader` runbook (v0.1.10) + its SessionStart hook exist, but the **most
reliable trigger** is an explicit operator command (it makes *engaging* the prime the agent's literal
task, closing the "present-but-unengaged" gap). Add a memorable `/vmm-session-rebooted` slash command.

## What Changes

- **NEW** Claude Code command `vault-template/.claude/commands/vmm-session-rebooted.md` (ships to
  vaults) + repo `.claude/commands/vmm-session-rebooted.md` — **thin adapters** that point at the
  `session-bootstrap-loader` runbook (no duplication, per the adapter rule).
- No spec change; no `protects:`-tagged spec touched (regular change).

## Capabilities

### New Capabilities
- _(none — a harness command adapter; no spec capability)_

### Modified Capabilities
- _(none)_

## Impact

`vault-template/.claude/commands/vmm-session-rebooted.md` + `.claude/commands/vmm-session-rebooted.md`
(new). Live-vault mirror adds `.claude/commands/vmm-session-rebooted.md`. No `.py`, no spec.
