---
capability: maintenance
protects: [INV-2, INV-3, INV-6]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: maintenance

The Layer-0 operational machinery: the literate meta-script format, the render/reconcile
GitOps pattern, and all deterministic scripts that automate vault maintenance.

---

## Requirement: Literate Meta-Script Format

Every operational artifact is stored as a **literate meta-script note** in
`99-Operations/scripts/`: a Markdown file with YAML frontmatter describing where
it deploys and when it runs, plus a `## Rationale` section and a single fenced
code block (the artifact). Layer 0 is the source of truth (INV-3); the code block
is the authoritative version of the script.

Required frontmatter fields:

```yaml
type: meta-script
deploy_target: <host path>   # absolute or ~/... path the code block renders to
runtime: cron | manual
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

---

## Requirement: Deterministic Scripts Are Offline (INV-6)

All `[script]` operations make no network calls and no LLM calls. They are
model-agnostic and will produce the same output given the same inputs regardless
of what AI tools are installed. This is a hard invariant; scripts that would
require network access are `[agent]` operations, not scripts.

---

## Requirement: One Mutation, One Commit (INV-2)

Every automated mutation ends in exactly one Git commit with a structured message.
No script produces zero commits (silent no-op on unchanged state is acceptable;
producing zero commits when a mutation occurred is not) or multiple commits.

Commit message format: `<verb>: <subject>` (e.g., `rollover: 2 open dig(s) → 2026-06-14`).

#### Scenario: rollover produces exactly one commit when digs exist
- **WHEN** the rollover script runs with at least one `status: dig` effort in `30-Sites/`
- **THEN** it appends wikilinks to today's daily note and produces exactly one commit

#### Scenario: rollover produces no commit when nothing changed
- **WHEN** the rollover script runs and all current digs are already in the carry-over heading
- **THEN** it exits cleanly with no commit produced

---

## Requirement: Script Inventory

The following scripts are implemented as literate meta-script notes in Phase 1–2.
Each is offline and deterministic (INV-6).

| Script note | Deploy target | Runtime | Purpose |
|---|---|---|---|
| `render-reconcile.md` | `~/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to host targets; detect drift |
| `daily-note.md` | `~/bin/vault-daily-note.py` | cron `1 0 * * *` | Create today's daily note from Mold; idempotent |
| `lint.md` | `~/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
| `orphans.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog MOC |
| `refine-detect.md` | `~/bin/vault-refine-detect.py` | cron daily | Queue ore whose grade cleared the Sort gate |
| `refine-execute.md` | `~/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury |
| `dispose.md` | `~/bin/vault-dispose.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
| `slag.md` | `~/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
| `reprospect.md` | `~/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
| `rollover.md` | `~/bin/vault-rollover.py` | cron `2 0 * * *` | Append open dig carry-overs to today's daily note |
| `kanban-render.md` | `~/bin/vault-kanban-render.py` | manual | Render read-only Markdown Kanban board |
| `naming.md` | `~/bin/vault_naming.py` | manual | Naming validator SSOT; also emits `naming-rules.json` |
| `pre-commit.md` | `99-Operations/hooks/pre-commit` | git hook | Commit-gate: block non-conforming file names (INV-11) |

#### Scenario: Daily note creator is idempotent
- **WHEN** the daily-note creator runs twice on the same day
- **THEN** the note is created on the first run and `exists` is printed on the second; no duplicate is created

#### Scenario: Kanban render produces a structured board
- **WHEN** `vault-kanban-render.py` runs
- **THEN** `20-Logbook/kanban.md` is written with four status-column headings in pipeline order (Prospect/Dig/Ore/Slagged), rows sorted grade-descending within each column, and a read-only notice; one commit produced
