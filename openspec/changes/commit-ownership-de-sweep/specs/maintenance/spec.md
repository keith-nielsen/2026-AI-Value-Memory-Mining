<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: One Mutation, One Commit (INV-2)

Every automated mutation SHALL end in exactly one Git commit with a structured message.
No script produces zero commits (silent no-op on unchanged state is acceptable;
producing zero commits when a mutation occurred is not) or multiple commits.

**Ownership:** the script that performs a mutation commits it, scoped to exactly the files it
mutated — no script relies on a later collector to sweep its writes into someone else's commit.
Uncommitted operator working-tree content is never captured by a script commit.

Commit message format: `<verb>: <subject>` (e.g., `rollover: 2 open dig(s) → 2026-06-14`).

#### Scenario: rollover produces exactly one commit when digs exist
- **WHEN** the rollover script runs with at least one `status: dig` effort in `30-Sites/`
- **THEN** it appends wikilinks to today's daily note and produces exactly one commit

#### Scenario: rollover produces no commit when nothing changed
- **WHEN** the rollover script runs and all current digs are already in the carry-over heading
- **THEN** it exits cleanly with no commit produced

#### Scenario: A created daily note is committed by its creator
- **WHEN** the daily-note creator creates today's note
- **THEN** it produces exactly one commit (`daily: opened <date>`) containing only that note
- **WHEN** the note already exists
- **THEN** no commit is produced

#### Scenario: A banked proposal is one atomic commit
- **WHEN** the refine executor applies an approved proposal
- **THEN** it produces exactly one commit (`bank: <stem>`) containing the knowledge note, the
  appended Catalog index links, and the consumed proposal's deletion (when the proposal was
  tracked) — and nothing else

#### Scenario: A close seals with a scoped commit, never a sweep
- **WHEN** `vault-close-day.py` seals a day while unrelated uncommitted changes exist elsewhere
  in the working tree
- **THEN** the close commit contains exactly the sealed daily note (plus the consumed worklist
  sidecar when git tracked it), and the unrelated changes remain uncommitted and untouched

### Requirement: Script Inventory

The following scripts SHALL be implemented as literate meta-script notes in Phase 1–2.
Each is offline and deterministic (INV-6).

| Script note | Deploy target | Runtime | Purpose |
|---|---|---|---|
| `render-reconcile-script.md` | `~/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to host targets; detect drift |
| `daily-note-script.md` | `~/bin/vault-daily-note.py` | cron `1 0 * * *` | Create today's daily note from Mold; idempotent; commits the created note (`daily: opened <date>`) |
| `knowledge-lint-script.md` | `~/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog index |
| `ore-detect-script.md` | `~/bin/vault-refine-detect.py` | cron daily | Queue ore whose grade cleared the Sort gate |
| `bank-execute-script.md` | `~/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury; one atomic commit per banked proposal (`bank: <stem>`) |
| `spoil-dump-script.md` | `~/bin/vault-dump.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
| `site-slag-script.md` | `~/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
| `tailings-reprospect-script.md` | `~/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
| `dig-rollover-script.md` | `~/bin/vault-rollover.py` | cron `2 0 * * *` | Append open dig carry-overs to today's daily note; gated on prior day `closed` |
| `daily-close-script.md` | `~/bin/vault-close-day.py` | manual | Disposition every item of a daily, write the `## Close` manifest, set `closed:`; emits the `unknown/other` worklist; seals with a scoped commit (daily + consumed sidecar), never a sweep |
| `kanban-render-script.md` | `~/bin/vault-kanban-render.py` | manual | Render read-only Markdown Kanban board |
| `naming-rules-script.md` | `~/bin/vault_naming.py` | manual | Naming validator SSOT; also emits `naming-rules.json` |
| `vault-lib-script.md` | `~/bin/vault_lib.py` | manual | Shared fleet plumbing: root resolution, config vocabulary, frontmatter access, scoped one-commit helper, fleet exit-code contract (ADR-0023) |
| `commit-gate-script.md` | `99-Operations/hooks/pre-commit` | git hook | Commit-gate: block non-conforming file names (INV-11) |
| `push-guard-script.md` | `99-Operations/hooks/pre-push` | git hook | Push-gate (INV-14): deny outbound push by default; permit a remote in `PUSH_ALLOWLIST` (full vault); for a remote in `PUBLIC_REMOTE_ALLOWLIST`, permit **only** paths matched by `99-Operations/schemas/publish-manifest.json` (`public_allow`), else refuse |

The **note filenames** follow the `silo-section-descriptor` naming convention (silo first, `script`
trailing). **Deploy targets are unchanged.** The `commit-gate` and `push-guard` hooks are deterministic
(INV-6): they read git state, `config.env`, and (for `push-guard`) the language-neutral
`publish-manifest.json` schema only — no network, no LLM.

The **`publish-manifest.json`** schema (`99-Operations/schemas/`) is a language-neutral, default-deny
allowlist of publishable framework paths, consumed by `push-guard-script` and by any future
public-export/mirror tool.

Sibling scripts import the shared modules (`vault_naming`, `vault_lib`) from `~/bin` via
`sys.path.insert(0, str(pathlib.Path.home() / "bin"))`; the underscore module names mark
importable libraries (the `vault_naming` precedent).

#### Scenario: Daily note creator is idempotent
- **WHEN** the daily-note creator runs twice on the same day
- **THEN** the note is created on the first run and `exists` is printed on the second; no duplicate is created

#### Scenario: Push-guard denies an un-allowlisted push
- **WHEN** `git push` runs from a deployed vault and the target remote URL is not listed in `PUSH_ALLOWLIST` or `PUBLIC_REMOTE_ALLOWLIST`
- **THEN** the `pre-push` hook aborts the push (non-zero) with an INV-14 message

#### Scenario: Push-guard applies the path-level manifest to a public remote
- **WHEN** `git push` targets a remote in `PUBLIC_REMOTE_ALLOWLIST` and the diff includes a path not in `publish-manifest.json` `public_allow`
- **THEN** the `pre-push` hook aborts with an INV-14 path-boundary violation; a push whose paths are all allowlisted is permitted
