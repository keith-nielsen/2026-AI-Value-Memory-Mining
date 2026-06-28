## MODIFIED Requirements

### Requirement: Script Inventory

The following scripts SHALL be implemented as literate meta-script notes in Phase 1–2.
Each is offline and deterministic (INV-6).

| Script note | Deploy target | Runtime | Purpose |
|---|---|---|---|
| `render-reconcile-script.md` | `~/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to host targets; detect drift |
| `daily-note-script.md` | `~/bin/vault-daily-note.py` | cron `1 0 * * *` | Create today's daily note from Mold; idempotent |
| `knowledge-lint-script.md` | `~/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog index |
| `ore-detect-script.md` | `~/bin/vault-refine-detect.py` | cron daily | Queue ore whose grade cleared the Sort gate |
| `bank-execute-script.md` | `~/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury |
| `spoil-dump-script.md` | `~/bin/vault-dump.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
| `site-slag-script.md` | `~/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
| `tailings-reprospect-script.md` | `~/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
| `dig-rollover-script.md` | `~/bin/vault-rollover.py` | cron `2 0 * * *` | Append open dig carry-overs to today's daily note; gated on prior day `closed` |
| `daily-close-script.md` | `~/bin/vault-close-day.py` | manual | Disposition every item of a daily, write the `## Close` manifest, set `closed:`; emits the `unknown/other` worklist |
| `kanban-render-script.md` | `~/bin/vault-kanban-render.py` | manual | Render read-only Markdown Kanban board |
| `naming-rules-script.md` | `~/bin/vault_naming.py` | manual | Naming validator SSOT; also emits `naming-rules.json` |
| `commit-gate-script.md` | `99-Operations/hooks/pre-commit` | git hook | Commit-gate: block non-conforming file names (INV-11) |

The **note filenames** follow the `silo-section-descriptor` naming convention (silo first, `script`
trailing). **Deploy targets are unchanged** — the `~/bin/vault-*.py`/`.sh` and the
`99-Operations/hooks/pre-commit` host artifacts keep their names (the `.py` rename is deferred).

#### Scenario: Daily note creator is idempotent
- **WHEN** the daily-note creator runs twice on the same day
- **THEN** the note is created on the first run and `exists` is printed on the second; no duplicate is created

#### Scenario: Kanban render produces a structured board
- **WHEN** `vault-kanban-render.py` runs
- **THEN** `10-Logbook/kanban.md` is written with three status-column headings in pipeline order (Dig/Ore/Slagged), rows sorted grade-descending within each column, and a read-only notice; one commit produced
