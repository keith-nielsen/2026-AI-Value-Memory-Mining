---
type: meta-script
deploy_target: 99-Operations/schemas/frontmatter.md
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
# Frontmatter Schemas

Reference for all note types in this vault. The `knowledge` schema is enforced by the
linter (`lint.md`). All other schemas are enforced by convention and the pre-commit
hook's name-safety checks.

---

## `knowledge` — `40-Treasury/*.md`

```yaml
type: knowledge            # literal
title: string              # matches filename stem
pillars: [string, ...]     # non-empty subset of PILLARS
grade: enum                # one of GRADES (confirmed at refine)
stage: enum                # one of KNOWLEDGE_STAGES (refined | polished)
crucible: boolean          # true if validated via Crucible; default false
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [string, ...]        # optional
```

---

## `moc` — `40-Treasury/Catalog/*.md`

```yaml
type: moc
pillar: string             # one PILLARS value, or "home" for the Home MOC
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

---

## `effort` — `30-Sites/<slug>/_effort.md` or `70-Tailings/<slug>/_effort.md`

```yaml
type: effort
title: string
status: enum               # prospect | dig | ore | slagged
grade: enum                # one of GRADES; estimated at ore, confirmed at refine (blank while prospect/dig)
pillars: [string, ...]     # subset of PILLARS
started: YYYY-MM-DD
completed: YYYY-MM-DD      # optional
slag_reason: string        # required when status == slagged
```

---

## `daily` — `10-Logbook/Daily/YYYY-MM-DD.md`

```yaml
type: daily
date: YYYY-MM-DD
```

---

## `meta-script` — `99-Operations/scripts/*.md`

```yaml
type: meta-script
deploy_target: path        # host path the code block renders to
runtime: enum              # cron | manual
schedule: string           # cron expression; required iff runtime == cron
class: script              # literal (Layer 0 holds deterministic defs only)
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

---

## `spoil` — `71-Spoil/<slug>/_effort.md`

```yaml
type: effort
title: string
status: enum               # spent | waste
grade: enum                # grade at time of disposal (forensic record)
pillars: [string, ...]
started: YYYY-MM-DD
completed: YYYY-MM-DD
disposed: YYYY-MM-DD       # date moved to Spoil
```
