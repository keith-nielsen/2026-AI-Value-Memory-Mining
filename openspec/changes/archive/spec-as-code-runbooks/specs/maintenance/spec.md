<!-- SPDX-License-Identifier: Apache-2.0 -->
# maintenance — delta: spec-as-code-runbooks

## ADDED Requirements

### Requirement: Runbook Format

A runbook SHALL be a literate, schema-validated procedure note in `96-Runbooks/` that is the
**single, harness-agnostic source of truth** for a repeatable operation. Its frontmatter
carries `id`, `title`, `trigger`, `applies-to` (`vault`|`repo`|`both`), `class`, and
`last-validated`; its body carries the required sections Purpose, Preconditions, Steps,
Pitfalls, Verification, and Rollback. Deterministic steps MUST reference meta-scripts rather
than restate them; AI MUST be invoked only where a step is genuine interpretation, narrowed
to an `unknown/other` fallback over an enumerated state list. Harness files (`CLAUDE.md`,
`AGENTS.md`, tool-specific skills) are adapters that point at the runbook and MUST NOT
duplicate it.

#### Scenario: runbook-lint validates a runbook
- **WHEN** `runbook-lint` runs on a `96-Runbooks/*.md` file
- **THEN** it exits 0 only if the required frontmatter keys and body sections are all present, and exits 1 otherwise

#### Scenario: A runbook is harness-agnostic
- **WHEN** the canonical runbook file is read
- **THEN** it contains no tool-specific invocation as its source of truth (any Claude Code / Hermes specifics live in adapter files that reference it)

### Requirement: Daily Close Lifecycle

A daily note SHALL pass a deterministic `close-daily` ritual that assigns every item exactly
one disposition from the controlled `DISPOSITIONS` vocabulary
(`claim site crucible banked slagged spoiled realized recorded passover`) and records the
result in an appended `## Close` manifest, then sets the `closed:` frontmatter to the close
date. The ritual MUST preserve **append-only** (no item above `## Close` is edited or
removed), **total-disposition** (no untagged item), and **strict-order close** (day N+1 may
not be closed while day N is open). Capture MUST always have a home — the next day's stub is
created unconditionally — but **advancing** (rollover / carry-over) is gated on the prior day
being `closed`. The deterministic engine `vault-close-day.py` ([script], INV-6, no LLM)
classifies by rule and **emits an `unknown/other` worklist** for an agent or human to resolve;
it never calls a model itself.

#### Scenario: A closed day is fully dispositioned
- **WHEN** `vault-close-day.py` finalizes a day
- **THEN** the `## Close` manifest accounts for every item, `closed:` is set to the close date, and `close-lint` exits 0

#### Scenario: Advancing is gated on the prior close
- **WHEN** rollover runs and the previous day is not `closed`
- **THEN** it does not carry over, and the new day's note carries a `⚠ BLOCKED: close <prev>` banner — while the capture stub still exists

#### Scenario: An empty day auto-closes
- **WHEN** `vault-close-day.py` runs on a day with no items
- **THEN** total-disposition is trivially satisfied and the day is marked `closed` without manual input
