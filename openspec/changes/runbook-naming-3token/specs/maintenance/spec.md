## MODIFIED Requirements

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
