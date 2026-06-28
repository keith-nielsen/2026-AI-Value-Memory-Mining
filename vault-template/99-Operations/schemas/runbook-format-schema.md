<!-- SPDX-License-Identifier: Apache-2.0 -->
# Runbook schema — `96-Runbooks/*.md`

A **runbook** is spec-as-code: the single, harness-agnostic source of truth for a repeatable,
error-prone operation. Validated by `runbook-lint`.

## Frontmatter

```yaml
type: runbook
id: kebab-slug              # stable identifier (matches filename stem)
title: string
trigger: string            # when to invoke — what the operator/agent says or detects
applies-to: enum           # vault | repo | both
class: procedure           # literal
last-validated: YYYY-MM-DD  # last time the steps were run end-to-end
```

## Required body sections

- `## Purpose` — what it achieves, in one or two lines.
- `## Preconditions` — what must be true / installed before starting.
- `## Steps` — ordered. Deterministic steps **reference** meta-scripts (never restate them).
  Tag each step `[script]`, `[gate]` (human authority), or `[agent]` (AI — only at `unknown/other`).
- `## Pitfalls` — known footguns and how to avoid them.
- `## Verification` — machine-checkable assertions that the operation succeeded.
- `## Rollback` — how to undo / recover if a step fails.

## Rules

- Harness files (`CLAUDE.md`, `AGENTS.md`, tool-specific skills) are **adapters** that point
  here; they must never duplicate the runbook.
- **Determinism first:** push every step into a `.py`/`.sh` meta-script (INV-6); reserve
  `[agent]` for genuine interpretation, bounded to an `unknown/other` fallback over an
  enumerated state list. Harvest recurring `other` resolutions back into deterministic rules.
