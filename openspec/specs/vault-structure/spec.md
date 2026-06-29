---
capability: vault-structure
protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: vault-structure

## Purpose

Define the physical and conceptual structure of the vault: the folder layout, the
three-layer model, frontmatter schemas, and note templates. This spec is the
authority for where things live and what shape they take on disk.
## Requirements
### Requirement: Three-Layer Model

The vault SHALL be organized into three named layers with distinct stability and access profiles.

- **Layer 0 — Operations** (`99-Operations/`): the mine's machinery. Human-write-only.
- **Layer 1 — Treasury** (`40-Treasury/`): refined + polished bullion. Never discarded by automation.
- **Layer 2 — Workings** (`10-Logbook/`, `20-Claims/`, `30-Sites/`, `70-Tailings/`, `71-Spoil/`): temporal capture, active effort, and disposal.

Additional areas outside the layer model: `00-Docs/` (onboarding, deletable),
`50-Mint/` + `60-Forge/` (future production, deferred), `80-Crucible/` (future
validation, deferred), `97-Molds/` (infrastructure), and `98-Warehouse/` — the
**reference stockroom**: retained source/reference material the operation draws on
repeatedly (binaries *and* digitized references), shelved by media type. It is *not*
mined value (not Treasury), *not* a working dig (not a Site), and *not* operations
machinery — it is low-traffic stock kept out of the way.

#### Scenario: Layer 0 is sealed from automation
- **WHEN** any automated process attempts to write `99-Operations/`
- **THEN** the write is blocked (INV-5); only human writes are permitted

#### Scenario: Treasury is sealed from direct agent writes
- **WHEN** an agent process attempts to write directly to `40-Treasury/`
- **THEN** the write is blocked (INV-4); only the refine executor script may write Treasury, and only when processing an approved proposal

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
98-Warehouse/        (reference stockroom — shelved by media type)
  Books/
  Music/
  Art/
  Pictures/
  Audio/
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

`98-Warehouse/` is the **reference stockroom** for retained source material the operation
draws on repeatedly: binary attachments (per the Format Invariant) and digitized references
(e.g. an owned-hardcopy book transcribed to Markdown). It is organized into **media shelves**
(`Books/`, `Music/`, `Art/`, `Pictures/`, `Audio/`) so stock stays out of the way and easy to
find. Shelf folder names are **human-friendly labels** under the universal path-component rule
(cross-platform-safe characters, no reserved device names) — they are deliberately **not** bound
by the kebab-case / ≥3-token convention, which is scoped to `.md` stems and to effort folders in
`30-Sites/`/`70-Tailings/` and Treasury stems in `40-Treasury/` (see `naming-rules`), none of
which a Warehouse shelf is. Shelves are created on demand; the set above is the default.

Rationale for the order: the daily note in `10-Logbook/Daily/` is the orienting surface
a user opens first each session, so it sorts to the top per CONST-04. `20-Claims/` is
the capture inbox (an unordered queue), and carries the refine gate
(`_refine-proposals/`, `_refine-approved/`).

The four `97-Molds/` files are named on the `silo-section-descriptor` convention
(`<note-type>-mold-blank.md`) so each mold is self-identifying in any flat / search /
migrated view and never collides with content (e.g. the Catalog `<pillar>-domain-index.md` notes).
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

#### Scenario: Warehouse shelves take human-friendly names
- **WHEN** a Warehouse shelf folder (e.g. `Books`, `Pictures`) is created or listed
- **THEN** it must only satisfy the universal path-component rule (cross-platform-safe characters, no reserved device names); the kebab-case / ≥3-token convention does not apply to it, because that convention is scoped to `.md` stems and to `30-Sites/`/`70-Tailings/` effort folders and `40-Treasury/` stems

### Requirement: Format Invariant

All content files SHALL be Markdown (`.md`) with YAML frontmatter, UTF-8 encoded (INV-1).
No proprietary formats. No binary content files outside `98-Warehouse/`.

#### Scenario: Mold templates are valid frontmatter Markdown
- **WHEN** all four `97-Molds/` files are parsed
- **THEN** each parses as valid YAML-frontmatter Markdown with no errors (A0.4)

---

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

### Requirement: Pillar Configuration

The canonical set of pillars SHALL be defined in `99-Operations/config.env` as the
`PILLARS` variable. Pillars are the major, durable life-domains the vault is organized around.
The default set (`mental health financial social technology calling`) is an example;
every adopter is expected to replace it with their own durable life-domains.

`calling` is the deliberate catch-all pillar for personal pursuits that don't fit
the universal pillars — physical practices, devotions, games, craft disciplines.

A candidate earns pillar standing only if it is distinct (non-overlapping domain),
top-level (life-domain, not a sub-interest), and durable (years, not a phase).

The build creates one `Catalog/` index per pillar plus a Home index. The linter
validates every note's `pillars` field against the configured set.

#### Scenario: index count matches pillar count
- **WHEN** Phase 1 build completes
- **THEN** `count(PILLARS) + 1` Catalog index files exist (one per pillar + `pillar: home`)

