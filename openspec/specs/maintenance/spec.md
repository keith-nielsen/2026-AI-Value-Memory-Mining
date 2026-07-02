---
capability: maintenance
protects: [INV-2, INV-3, INV-6]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: maintenance

## Purpose

Define the Layer-0 operational machinery: the literate meta-script format, the
render/reconcile GitOps pattern, and all deterministic scripts that automate vault
maintenance.
## Requirements
### Requirement: Literate Meta-Script Format

Every operational artifact SHALL be stored as a literate meta-script note in
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

### Requirement: Deterministic Scripts Are Offline (INV-6)

All `[script]` operations MUST make no network calls and no LLM calls. They are
model-agnostic and will produce the same output given the same inputs regardless
of what AI tools are installed. This is a hard invariant; scripts that would
require network access are `[agent]` operations, not scripts.

#### Scenario: A deterministic script makes no network or LLM call
- **WHEN** any `[script]` operation runs
- **THEN** it completes using only local filesystem and Git operations
- **THEN** it issues no network request and invokes no model

### Requirement: One Mutation, One Commit (INV-2)

Every automated mutation SHALL end in exactly one Git commit with a structured message.
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
| `push-guard-script.md` | `99-Operations/hooks/pre-push` | git hook | Push-gate (INV-14): deny outbound push by default; permit a remote in `PUSH_ALLOWLIST` (full vault); for a remote in `PUBLIC_REMOTE_ALLOWLIST`, permit **only** paths matched by `99-Operations/schemas/publish-manifest.json` (`public_allow`), else refuse |

The **note filenames** follow the `silo-section-descriptor` naming convention (silo first, `script`
trailing). **Deploy targets are unchanged.** The `commit-gate` and `push-guard` hooks are deterministic
(INV-6): they read git state, `config.env`, and (for `push-guard`) the language-neutral
`publish-manifest.json` schema only — no network, no LLM.

The **`publish-manifest.json`** schema (`99-Operations/schemas/`) is a language-neutral, default-deny
allowlist of publishable framework paths, consumed by `push-guard-script` and by any future
public-export/mirror tool.

#### Scenario: Daily note creator is idempotent
- **WHEN** the daily-note creator runs twice on the same day
- **THEN** the note is created on the first run and `exists` is printed on the second; no duplicate is created

#### Scenario: Push-guard denies an un-allowlisted push
- **WHEN** `git push` runs from a deployed vault and the target remote URL is not listed in `PUSH_ALLOWLIST` or `PUBLIC_REMOTE_ALLOWLIST`
- **THEN** the `pre-push` hook aborts the push (non-zero) with an INV-14 message

#### Scenario: Push-guard applies the path-level manifest to a public remote
- **WHEN** `git push` targets a remote in `PUBLIC_REMOTE_ALLOWLIST` and the diff includes a path not in `publish-manifest.json` `public_allow`
- **THEN** the `pre-push` hook aborts with an INV-14 path-boundary violation; a push whose paths are all allowlisted is permitted

### Requirement: Runbook Format

A runbook SHALL be a literate, schema-validated procedure note in `96-Runbooks/` that is the
**single, harness-agnostic source of truth** for a repeatable operation. Its frontmatter
carries `id`, `title`, `trigger`, `applies-to` (`vault`|`repo`|`both`), `class`, and
`last-validated`; its body carries the required sections Purpose, Preconditions, Steps,
Pitfalls, Verification, and Rollback. Deterministic steps MUST reference meta-scripts rather
than restate them; AI MUST be invoked only where a step is genuine interpretation, narrowed
to an `unknown/other` fallback over an enumerated state list. Harness files (`CLAUDE.md`,
`AGENTS.md`, tool-specific skills) are adapters that point at the runbook and MUST NOT
duplicate it.

#### Scenario: runbook-lint validates a runbook
- **WHEN** `runbook-lint` runs on a `96-Runbooks/*.md` file
- **THEN** it exits 0 only if the required frontmatter keys and body sections are all present, and exits 1 otherwise

#### Scenario: A runbook is harness-agnostic
- **WHEN** the canonical runbook file is read
- **THEN** it contains no tool-specific invocation as its source of truth (any Claude Code / Hermes specifics live in adapter files that reference it)

---

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

