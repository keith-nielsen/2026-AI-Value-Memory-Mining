<\!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: Literate Meta-Script Format

Every operational artifact SHALL be stored as a literate meta-script note in
`99-Operations/scripts/`: a Markdown file with YAML frontmatter describing where
it deploys and when it runs, plus a `## Rationale` section and a single fenced
code block (the artifact). Layer 0 is the source of truth (INV-3); the code block
is the authoritative version of the script.

Required frontmatter fields:

```yaml
type: meta-script
deploy_target: <host path>   # absolute or ~/... path the code block renders to
runtime: cron | manual | git hook
schedule: "<cron expression>" # required iff runtime == cron
class: script                # literal — Layer 0 holds deterministic defs only
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

#### Scenario: render deploys all scripts and reconcile confirms zero drift
- **WHEN** `vault-render.py render` is run after Phase 1
- **THEN** an executable file is produced at each `deploy_target` declared in the scripts
- **WHEN** `vault-render.py reconcile` is then run
- **THEN** it reports `ok` for all scripts (zero drift)

#### Scenario: reconcile detects but does not fix drift
- **WHEN** a deployed host script is hand-edited after render
- **THEN** `reconcile` reports `DRIFT: <target> differs from <source>`
- **THEN** reconcile does not overwrite the deployed file (INV-3)

### Requirement: Daily Close Lifecycle

A daily note SHALL pass a deterministic `daily-close` ritual that assigns every item exactly
one disposition from the controlled `DISPOSITIONS` vocabulary
(`claim site crucible banked slagged spoiled realized recorded passover`) and records the
result in an appended `## Close` manifest, then sets the `closed:` frontmatter to the close
date. The ritual MUST preserve **append-only** (no item above `## Close` is edited or
removed), **total-disposition** (no untagged item), and **strict-order close** (day N+1 may
not be closed while day N is open). Capture MUST always have a home — the next day's stub is
created unconditionally — but **advancing** (rollover / carry-over) is gated on the prior day
being `closed`. The deterministic engine `vault-close-day.py` (`[script]`, INV-6, no LLM)
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

#### Scenario: close-lint flags an out-of-vocabulary disposition
- **WHEN** `vault-close-day.py --check` runs on a sealed day whose `## Close` manifest carries a
  disposition word not in the `DISPOSITIONS` vocabulary (e.g. a typo)
- **THEN** it prints `FAIL: disposition not in vocab: <word>` and exits `1`
