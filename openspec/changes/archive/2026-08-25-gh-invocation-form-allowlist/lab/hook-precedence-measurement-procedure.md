<!-- SPDX-License-Identifier: Apache-2.0 -->
# Hook precedence measurement — the G1.1 / G1.2 procedure

## Why this is a lab and not a test

`tests/` is deterministic and offline (INV-6): no network, no subprocess spawning a harness. Measuring
multi-hook `PreToolUse` precedence requires a **live Claude Code session** to evaluate a real Bash
tool call against real hook registration — which no unit test can traverse. This is the same gap
task G4.2 names: *"no unit test traverses hook registration; a passing test suite is not evidence
that the hook is loaded."*

So this is an **evidence-producing procedure**, kept re-runnable, not an automated check. It is
carried inside the change directory so it archives with the change rather than lingering in the
live tree.

## What it measures

Two probe hooks are registered against `Bash` in the lab's own `.claude/settings.json`, **A first,
B second**. Each is silent (exit 0, no output) except for three marker commands, so it cannot affect
ordinary work. Each marker pits a decision from A against a decision from B:

| Marker | Hook A (first) | Hook B (second) | Question |
|---|---|---|---|
| `PRECEDENCE_AD` | `allow` | `deny` | can a **later** `deny` override an **earlier** `allow`? |
| `PRECEDENCE_DA` | `deny` | `allow` | can a **later** `allow` undo an **earlier** `deny`? |
| `PRECEDENCE_ASKDENY` | `ask` | `deny` | does `deny` beat `ask`? (G1.2) |

The decision contract is copied from the live `outbound-publish-guard.py`, not guessed:

```
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
                        "permissionDecision": "allow"|"deny"|"ask",
                        "permissionDecisionReason": "..."}}
```

## How to re-run

The lab must be the **project directory** of the session under test, because hooks load at session
start from that directory's `.claude/settings.json`. From the repository root:

```
cd openspec/changes/gh-invocation-form-allowlist/lab
claude -p "Run this exact bash command and report verbatim whether it executed or was refused: echo PRECEDENCE_AD"
claude -p "Run this exact bash command and report verbatim whether it executed or was refused: echo PRECEDENCE_DA"
claude -p "Run this exact bash command and report verbatim whether it executed, was refused, or prompted for permission: echo PRECEDENCE_ASKDENY"
```

Each run reports which probe's decision won, by its `[probe hook A|B]` reason string. That string is
the evidence — a bare "refused" does not say *which* hook refused, and the whole question is which.

Before trusting a run, confirm the user-level `$HOME/.claude/settings.json` registers **no**
`PreToolUse` hooks and no `permissions.deny` entries; user settings merge into the session and would
otherwise contaminate the result.

## Result, 2026-08-25T20:53+08:00

| Marker | Outcome | Reason emitted |
|---|---|---|
| `PRECEDENCE_AD` | **REFUSED** | `[probe hook B] DENY for PRECEDENCE_AD` |
| `PRECEDENCE_DA` | **REFUSED** | `[probe hook A] DENY for PRECEDENCE_DA` |
| `PRECEDENCE_ASKDENY` | **REFUSED**, no prompt | `[probe hook B] DENY for PRECEDENCE_ASKDENY` |

**`deny` wins unconditionally** — in either registration order, and over `ask`.

- **G1.1 holds.** A second hook's `deny` overrides another hook's `allow` (`PRECEDENCE_AD`), so
  ADR-0045's blocking assumption is measured true and the option-3 fallback is not needed.
- **`PRECEDENCE_DA` closes a gap the ADR did not consider**: a `deny` is *not* reversible by a later
  `allow`. Had it been, the control would have been undoable by any hook registered after it.
- **G1.2 holds** — `deny` beat `ask` with no prompt, so the outbound guard's `ask` decisions cannot
  override this guard's refusals.

## The limit of this measurement, stated rather than discovered

All three runs used `claude -p` (non-interactive), where `ask` **has no way to prompt**. So
`PRECEDENCE_ASKDENY` is partially confounded: its refusal could in principle come from
non-interactivity rather than from `deny` beating `ask`. The evidence against that reading is that
the reason string names hook B's DENY specifically rather than a generic non-interactive refusal —
but it is not conclusive, which is why **G1.2 is marked `[~]` and not `[x]`** pending one interactive
confirmation.

`PRECEDENCE_AD` and `PRECEDENCE_DA` carry no such confound: `allow` versus `deny` involves no
interactivity at all, and both are marked `[x]`.
