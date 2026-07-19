<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: Folder Structure

The vault SHALL use the numbered folder structure below. `10-Logbook/` retains `Daily/` and
`Reviews/` as **working areas**; the framework no longer generates a dated note format for either
(ADR-0032).

```
00-Docs/
  README.md
  examples/
10-Logbook/
  Daily/
  Reviews/
20-Claims/
```

Rationale for the order: `10-Logbook/` is the **highest-touch silo by design** and sorts to the top
per CONST-04. The framework does not itself generate its contents (ADR-0032 retired the daily note);
the silo is **reserved** for the effort audit trail written by the external harness that drives
cadence, and the ordering is a reservation rather than a present observation — stated here as such
rather than justified by an artifact that no longer exists. `20-Claims/` is the capture inbox (an
unordered queue), and carries the refine gate (`_refine-proposals/`, `_refine-approved/`).

The three `97-Molds/` files are named on the `silo-section-descriptor` convention
(`<note-type>-mold-blank.md`) so each mold is self-identifying in any flat / search /
migrated view and never collides with content (e.g. the Catalog `<pillar>-domain-index.md` notes).

```
97-Molds/
  effort-mold-blank.md
  knowledge-mold-blank.md
  index-mold-blank.md
```

`96-Runbooks/` holds **runbooks** — literate, schema-validated procedure notes (spec-as-code)
for repeatable, error-prone operations (e.g. `provenance-seal-runbook`, `site-sort-runbook`). It is
operational machinery (Layer-0-adjacent, like `97-Molds`/`99-Operations`), sorts in the
infra region per CONST-04, and conforms to the numbering scheme — it does not override it.

#### Scenario: Logbook sorts above the capture inbox
- **WHEN** the vault root is listed in any file explorer
- **THEN** `10-Logbook/` sorts above `20-Claims/` per CONST-04 — the touch-frequency ordering is
  unchanged; no claim is made about what occupies the silo

### Requirement: Frontmatter Schemas

Each note type SHALL carry the frontmatter fields below.

| Type | Location | Key fields |
|---|---|---|
| `knowledge` | `40-Treasury/*.md` | type, title, pillars, grade, stage, crucible, created, updated |
| `index` | `40-Treasury/Catalog/*.md` | type, pillar, created, updated |
| `effort` | `30-Sites/<slug>/<slug>.md`, `70-Tailings/<slug>/<slug>.md` | type, title, status, grade, pillars, started |
| `meta-script` | `99-Operations/scripts/*.md` | type, deploy_target, runtime, class, created, updated |
| `runbook` | `96-Runbooks/*.md` | type, id, title, trigger, applies-to, class, last-validated |
| `spoil` | `71-Spoil/<slug>/<slug>.md` | type, title, status (spent\|waste), grade, pillars, dumped |

The `runbook` schema is defined in `99-Operations/schemas/runbook-format-schema.md`.

There is no framework-generated dated note type. The `daily` type and its `closed` field were
retired with the daily-close cycle (ADR-0032); pre-existing dailies in a deployed vault remain valid
historical artifacts and are not re-validated against this table.

#### Scenario: Linter validates knowledge note frontmatter
- **WHEN** the linter runs on a `40-Treasury/*.md` file
- **THEN** it exits 0 for a valid note and exits 1 if `pillars` contains an out-of-set value, `grade` is not one of the four grades, or `stage` is not `refined`/`polished`
