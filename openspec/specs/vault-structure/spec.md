---
capability: vault-structure
protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: vault-structure

The physical and conceptual structure of the vault: folder layout, layer model,
frontmatter schemas, and note templates.

---

## Requirement: Three-Layer Model

The vault is organized into three named layers with distinct stability and access profiles.

- **Layer 0 — Operations** (`99-Operations/`): the mine's machinery. Human-write-only.
- **Layer 1 — Treasury** (`40-Treasury/`): refined + polished bullion. Never discarded by automation.
- **Layer 2 — Workings** (`10-Claims/`, `20-Logbook/`, `30-Sites/`, `70-Tailings/`, `71-Spoil/`): temporal capture, active effort, and disposal.

Additional areas outside the layer model: `00-Docs/` (onboarding, deletable),
`50-Mint/` + `60-Forge/` (future production, deferred), `80-Crucible/` (future
validation, deferred), `97-Molds/` + `98-Warehouse/` (infrastructure).

#### Scenario: Layer 0 is sealed from automation
- **WHEN** any automated process attempts to write `99-Operations/`
- **THEN** the write is blocked (INV-5); only human writes are permitted

#### Scenario: Treasury is sealed from direct agent writes
- **WHEN** an agent process attempts to write directly to `40-Treasury/`
- **THEN** the write is blocked (INV-4); only the refine executor script may write Treasury, and only when processing an approved proposal

---

## Requirement: Folder Structure

The vault root contains exactly these numbered top-level folders, ordered by touch
frequency (ascending number = higher daily-touch frequency), zero-padded for
correct lexicographic sort, gapped by 10s for insertion headroom.

```
00-Docs/
  README.md
  examples/
10-Claims/
  _refine-proposals/
  _refine-approved/
20-Logbook/
  Daily/
  Reviews/
30-Sites/
40-Treasury/
  Catalog/
50-Mint/             (deferred — folder exists as placeholder)
60-Forge/            (deferred — folder exists as placeholder)
70-Tailings/
71-Spoil/
80-Crucible/         (deferred — folder exists as placeholder)
97-Molds/
  daily.md
  effort.md
  knowledge.md
  moc.md
98-Warehouse/
99-Operations/
  config.env
  requirements.txt
  scripts/
  hooks/
  schemas/
```

Reserved number bands (folders NOT created until needed): 81–89 (Crucible-adjacent),
90–96 (future system).

#### Scenario: Folder tree is complete after Phase 0
- **WHEN** Phase 0 build completes
- **THEN** every directory in the structure above exists, including `_refine-proposals/`, `_refine-approved/`, `99-Operations/hooks/`, and `99-Operations/schemas/`

#### Scenario: No pillar subfolders in Treasury
- **WHEN** the linter runs against `40-Treasury/`
- **THEN** it reports no subdirectories other than `Catalog/` (INV-12 enforced)

---

## Requirement: Format Invariant

All content files are Markdown (`.md`) with YAML frontmatter, UTF-8 encoded (INV-1).
No proprietary formats. No binary content files outside `98-Warehouse/`.

#### Scenario: Mold templates are valid frontmatter Markdown
- **WHEN** all four `97-Molds/` files are parsed
- **THEN** each parses as valid YAML-frontmatter Markdown with no errors (A0.4)

---

## Requirement: Frontmatter Schemas

Each note type has an exact required frontmatter schema. The schemas are documented
in `vault-template/99-Operations/schemas/frontmatter.md` and enforced by the linter.

| Type | Location | Key fields |
|---|---|---|
| `knowledge` | `40-Treasury/*.md` | type, title, pillars, grade, stage, crucible, created, updated |
| `moc` | `40-Treasury/Catalog/*.md` | type, pillar, created, updated |
| `effort` | `30-Sites/<slug>/_effort.md`, `70-Tailings/<slug>/_effort.md` | type, title, status, grade, pillars, started |
| `daily` | `20-Logbook/Daily/YYYY-MM-DD.md` | type, date |
| `meta-script` | `99-Operations/scripts/*.md` | type, deploy_target, runtime, class, created, updated |
| `spoil` | `71-Spoil/<slug>/_effort.md` | type, title, status (spent\|waste), grade, pillars, disposed |

#### Scenario: Linter validates knowledge note frontmatter
- **WHEN** the linter runs on a `40-Treasury/*.md` file
- **THEN** it exits 0 for a valid note and exits 1 if `pillars` contains an out-of-set value, `grade` is not one of the four grades, or `stage` is not `refined`/`polished`

---

## Requirement: Pillar Configuration

Pillars are the major, durable life-domains the vault is organized around. The
canonical set is defined in `99-Operations/config.env` as the `PILLARS` variable.
The default set (`mental health financial social technology calling`) is an example;
every adopter is expected to replace it with their own durable life-domains.

`calling` is the deliberate catch-all pillar for personal pursuits that don't fit
the universal pillars — physical practices, devotions, games, craft disciplines.

A candidate earns pillar standing only if it is distinct (non-overlapping domain),
top-level (life-domain, not a sub-interest), and durable (years, not a phase).

The build creates one `Catalog/` MOC per pillar plus a Home MOC. The linter
validates every note's `pillars` field against the configured set.

#### Scenario: MOC count matches pillar count
- **WHEN** Phase 1 build completes
- **THEN** `count(PILLARS) + 1` Catalog MOC files exist (one per pillar + `pillar: home`)
