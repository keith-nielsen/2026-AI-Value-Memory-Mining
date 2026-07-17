---
type: meta-script
deploy_target: 99-Operations/schemas/note-frontmatter-schema.md
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

## `index` — `40-Treasury/Catalog/*.md`

```yaml
type: index
pillar: string             # one PILLARS value, or "home" for the Home index
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

---

## `effort` — `30-Sites/<slug>/<slug>.md` or `70-Tailings/<slug>/<slug>.md`

```yaml
type: effort
title: string
status: enum               # dig | ore | slagged
grade: enum                # one of GRADES; estimated at ore, confirmed at refine (blank while dig)
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
closed: YYYY-MM-DD          # set by daily-close; absent/blank = open (legacy or in-progress)
```

---

## `meta-script` — `99-Operations/scripts/*.md`

```yaml
type: meta-script
deploy_target: path        # host path the code block renders to
runtime: enum              # manual | git hook | harness hook
                           # (no cron: the vault is a self-priming pump, not a driven
                           #  one — nothing installs schedules; ADR-0028)
class: script              # literal (Layer 0 holds deterministic defs only)
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

---

## `runbook` — `96-Runbooks/*.md`

```yaml
type: runbook
id: kebab-slug             # stable id (matches filename stem)
title: string
trigger: string            # when to invoke
applies-to: enum           # vault | repo | both
class: procedure           # literal
last-validated: YYYY-MM-DD
```

See `99-Operations/schemas/runbook-format-schema.md` for the required body sections.

---

## `spoil` — `71-Spoil/<slug>/<slug>.md`

```yaml
type: effort
title: string
status: enum               # spent | waste
grade: enum                # grade at time of disposal (forensic record)
pillars: [string, ...]
started: YYYY-MM-DD
completed: YYYY-MM-DD
dumped: YYYY-MM-DD      # date moved to Spoil
```
