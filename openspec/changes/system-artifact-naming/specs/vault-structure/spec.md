## MODIFIED Requirements

### Requirement: Frontmatter Schemas

Each note type SHALL have an exact required frontmatter schema. The schemas are documented
in `vault-template/99-Operations/schemas/note-frontmatter-schema.md` and enforced by the linter.

| Type | Location | Key fields |
|---|---|---|
| `knowledge` | `40-Treasury/*.md` | type, title, pillars, grade, stage, crucible, created, updated |
| `index` | `40-Treasury/Catalog/*.md` | type, pillar, created, updated |
| `effort` | `30-Sites/<slug>/<slug>.md`, `70-Tailings/<slug>/<slug>.md` | type, title, status, grade, pillars, started |
| `daily` | `10-Logbook/Daily/YYYY-MM-DD.md` | type, date, closed |
| `meta-script` | `99-Operations/scripts/*.md` | type, deploy_target, runtime, class, created, updated |
| `runbook` | `96-Runbooks/*.md` | type, id, title, trigger, applies-to, class, last-validated |
| `spoil` | `71-Spoil/<slug>/<slug>.md` | type, title, status (spent\|waste), grade, pillars, dumped |

The `daily` `closed` field records that the day passed the `close-daily` ritual: it is
absent (legacy/open) or an ISO date (the day it was closed). The `runbook` schema is
defined in `99-Operations/schemas/runbook-format-schema.md`.

#### Scenario: Linter validates knowledge note frontmatter
- **WHEN** the linter runs on a `40-Treasury/*.md` file
- **THEN** it exits 0 for a valid note and exits 1 if `pillars` contains an out-of-set value, `grade` is not one of the four grades, or `stage` is not `refined`/`polished`

#### Scenario: A runbook validates against the runbook schema
- **WHEN** `runbook-lint` runs on a `96-Runbooks/*.md` file
- **THEN** it exits 0 only if the frontmatter carries `id`, `title`, `trigger`, `applies-to`, `class`, `last-validated` and the body has the required sections (Purpose, Preconditions, Steps, Pitfalls, Verification, Rollback)
