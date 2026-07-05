<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Shared Fleet Plumbing and Exit-Code Contract (vault_lib)

The maintenance fleet SHALL include a shared, deterministic library module — `~/bin/vault_lib.py`,
rendered from `vault-lib-script.md` — providing the five concerns every script previously
improvised:

- **Vault-root resolution:** `$VAULT_ROOT` is honored when it marks a vault; otherwise the root is
  found by walking up from the working directory to the first directory whose `99-Operations/`
  holds `config.defaults.env` or `config.env`. A drive-path script (one listed in the harness's
  exact-invocation exclusion list) SHALL therefore work when invoked **bare, with no pre-sourced
  environment**, from any working directory inside the vault.
- **Config vocabulary:** controlled vocabularies resolve with the precedence the shell sourcing
  order establishes — process environment > `config.env` (instance) > `config.defaults.env`
  (framework) > declared code default. Values are read as raw strings; no shell evaluation (INV-6).
- **Frontmatter access:** one YAML-typed accessor (`fm`, `is_closed`); `closed: false` or an absent
  `closed:` key is **not closed**, fleet-wide.
- **Scoped commits:** `commit_paths(vault, paths, message)` — `git add` of exactly the named paths
  plus one commit (the INV-2 shape); it never sweeps.
- **Exit-code contract:** `0` success or clean no-op · `1` violation (lint/usage failure) ·
  `2` needs-input (a worklist was emitted) · `3` gate-blocked. A script whose run is refused by an
  operational gate (missing precondition, strict-order guard) SHALL exit `3` and print a
  `BLOCKED:` line — never `0`.

Adoption is incremental: the drive-path set (`daily-close`, `daily-note`, `dig-rollover`,
`kanban-render`, `bank-execute`) and `render-reconcile` adopt in this change; remaining scripts
SHOULD adopt as they are next modified. **Bootstrap exception:** `render-reconcile-script` deploys
`vault_lib.py` itself and therefore SHALL NOT import it; it carries an inline copy of the
root-resolution contract instead.

#### Scenario: A drive-path script runs bare with no pre-sourced environment
- **WHEN** a rendered drive-path script is invoked by its bare exact form (e.g.
  `~/bin/vault-kanban-render.py`) from a shell with no `VAULT_ROOT` set, cwd inside the vault
- **THEN** it resolves the vault root via the config marker walk and completes normally
- **WHEN** the same invocation happens with no `VAULT_ROOT` and cwd outside any vault
- **THEN** it prints a `BLOCKED:` line and exits `3`

#### Scenario: A gate refusal is machine-distinguishable from success
- **WHEN** the rollover script runs and the previous day is not `closed`
- **THEN** it prints `BLOCKED: previous day <date> not closed — run daily-close first` and exits `3`
- **WHEN** the rollover script runs and there is nothing to carry over
- **THEN** it exits `0`

#### Scenario: The closed test is YAML-typed and fleet-wide
- **WHEN** a prior daily note carries `closed: false` (or no `closed:` value)
- **THEN** the daily-note creator applies the `⚠ BLOCKED` banner and the rollover gate refuses —
  both via the same `vault_lib.is_closed`, with no divergence between the two scripts

#### Scenario: The shared library self-check is read-only
- **WHEN** `vault_lib.py` is executed bare inside a vault
- **THEN** it prints the resolved root and a vocabulary summary, mutates nothing, and exits `0`

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
