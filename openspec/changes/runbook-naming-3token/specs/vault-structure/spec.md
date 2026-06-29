## MODIFIED Requirements

### Requirement: Folder Structure

The vault root SHALL contain exactly these numbered top-level folders, ordered by touch
frequency (ascending number = higher daily-touch frequency, daily logs at top per
CONST-04), zero-padded for correct lexicographic sort, gapped by 10s for insertion
headroom.

```
00-Docs/
  README.md
  examples/
10-Logbook/
  Daily/
  Reviews/
20-Claims/
  _refine-proposals/
  _refine-approved/
30-Sites/
40-Treasury/
  Catalog/
50-Mint/             (deferred — folder exists as placeholder)
60-Forge/            (deferred — folder exists as placeholder)
70-Tailings/
71-Spoil/
80-Crucible/         (deferred — folder exists as placeholder)
96-Runbooks/         (operational runbooks — spec-as-code procedures)
97-Molds/
  daily-mold-blank.md
  effort-mold-blank.md
  knowledge-mold-blank.md
  index-mold-blank.md
98-Warehouse/
99-Operations/
  config.env
  requirements.txt
  scripts/
  hooks/
  schemas/
```

Reserved number bands (folders NOT created until needed): 81–89 (Crucible-adjacent),
90–95 (future system).

`96-Runbooks/` holds **runbooks** — literate, schema-validated procedure notes (spec-as-code)
for repeatable, error-prone operations (e.g. `daily-close-runbook`, `provenance-seal-runbook`). It is
operational machinery (Layer-0-adjacent, like `97-Molds`/`99-Operations`), sorts in the
infra region per CONST-04, and conforms to the numbering scheme — it does not override it.

Rationale for the order: the daily note in `10-Logbook/Daily/` is the orienting surface
a user opens first each session, so it sorts to the top per CONST-04. `20-Claims/` is
the capture inbox (an unordered queue), and carries the refine gate
(`_refine-proposals/`, `_refine-approved/`).

The four `97-Molds/` files are named on the `silo-section-descriptor` convention
(`<note-type>-mold-blank.md`) so each mold is self-identifying in any flat / search /
migrated view and never collides with content (e.g. the Catalog `<pillar>-index.md` notes).
Scripts and the Obsidian Daily Notes template reference a mold by this filename.

#### Scenario: Folder tree is complete after Phase 0
- **WHEN** Phase 0 build completes
- **THEN** every directory in the structure above exists, including `20-Claims/_refine-proposals/`, `20-Claims/_refine-approved/`, `99-Operations/hooks/`, and `99-Operations/schemas/`

#### Scenario: Daily logs sort above the capture inbox
- **WHEN** the vault root is listed in any file explorer
- **THEN** `10-Logbook/` sorts above `20-Claims/`, placing the daily cockpit at the top (CONST-04)

#### Scenario: Runbooks sort in the infra region
- **WHEN** the vault root is listed in any file explorer
- **THEN** `96-Runbooks/` sorts below `80-Crucible/` and above `97-Molds/`, keeping operational procedures in the low-touch infra band (CONST-04 upheld)

#### Scenario: No pillar subfolders in Treasury
- **WHEN** the linter runs against `40-Treasury/`
- **THEN** it reports no subdirectories other than `Catalog/` (INV-12 enforced)

#### Scenario: Molds are self-identifying folder-notes
- **WHEN** the four `97-Molds/` files are listed flat (graph, search, or migration)
- **THEN** each stem reads `<note-type>-mold-blank` and none collides with a content stem such as `index`

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

The `daily` `closed` field records that the day passed the `daily-close` ritual: it is
absent (legacy/open) or an ISO date (the day it was closed). The `runbook` schema is
defined in `99-Operations/schemas/runbook-format-schema.md`.

#### Scenario: Linter validates knowledge note frontmatter
- **WHEN** the linter runs on a `40-Treasury/*.md` file
- **THEN** it exits 0 for a valid note and exits 1 if `pillars` contains an out-of-set value, `grade` is not one of the four grades, or `stage` is not `refined`/`polished`

#### Scenario: A runbook validates against the runbook schema
- **WHEN** `runbook-lint` runs on a `96-Runbooks/*.md` file
- **THEN** it exits 0 only if the frontmatter carries `id`, `title`, `trigger`, `applies-to`, `class`, `last-validated` and the body has the required sections (Purpose, Preconditions, Steps, Pitfalls, Verification, Rollback)
