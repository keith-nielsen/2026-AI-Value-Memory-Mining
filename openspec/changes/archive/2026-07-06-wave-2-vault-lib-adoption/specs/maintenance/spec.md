<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

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
- **Scoped commits:** `commit_paths(vault, paths, message)` — scoped `git add` plus a
  **pathspec-scoped commit** of exactly the named paths (the INV-2 shape). It never sweeps:
  unrelated content that happens to be staged is left staged, not committed. An unchanged result
  is a **clean no-op** — an informative message, no commit, exit `0` — per the INV-2 clause that a
  silent no-op on unchanged state is acceptable while a failure is not.
- **Exit-code contract:** `0` success or clean no-op · `1` violation (lint/usage failure) ·
  `2` needs-input (a worklist was emitted) · `3` gate-blocked. A script whose run is refused by an
  operational gate (missing precondition, strict-order guard) SHALL exit `3` and print a
  `BLOCKED:` line — never `0`.

Adoption: the full Python fleet is adopted — the drive-path set (`daily-close`, `daily-note`,
`dig-rollover`, `kanban-render`, `bank-execute`) plus `knowledge-lint`, `treasury-orphan`,
`tailings-reprospect`, `ore-detect`, and the `naming-rules` mirror-writer (whose `vault_lib`
import is **lazy**, inside `__main__` only, so `--check` and module import stay dependency-free
for the hooks). The shell pair (`site-slag`, `spoil-dump`) remains env-requiring operator tooling
pending its own change. **Bootstrap exception:** `render-reconcile-script` deploys `vault_lib.py`
itself and therefore SHALL NOT import it; it carries an inline copy of the root-resolution
contract instead.

**The bare-drive guarantee extends through governance hooks:** a git hook fired by a drive-path
commit (the `core.hooksPath` commit-gate, and any future hook on that path) SHALL NOT require a
pre-sourced environment. A hook that needs the vault root SHALL derive it from its git context
(e.g. `git rev-parse --show-toplevel` — a hook always runs inside the repository), never from the
caller's environment.

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

#### Scenario: The commit-gate passes drive-path commits without environment
- **WHEN** a drive-path script commits its owned artifact and the `core.hooksPath` pre-commit
  naming gate fires in a process with no `VAULT_ROOT` set
- **THEN** the gate evaluates the staged names normally — INV-11 enforcement unchanged, a
  violating name is still `BLOCKED` — and does not fail on a missing environment variable

#### Scenario: A repeated render is a clean no-op
- **WHEN** a committing render script (e.g. kanban) runs twice in a row with no underlying state
  change, so the second render produces identical content
- **THEN** the second run prints an `unchanged — no commit needed` line, produces no commit, and
  exits `0` — it does not crash on an empty index

#### Scenario: A scoped commit ignores unrelated staged content
- **WHEN** unrelated files are already staged (e.g. by the operator) and a fleet script commits
  its owned artifact via `commit_paths`
- **THEN** the resulting commit contains exactly the script's named paths, and the unrelated
  staged content remains staged and uncommitted
