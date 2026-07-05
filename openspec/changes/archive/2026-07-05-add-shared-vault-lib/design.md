<!-- SPDX-License-Identifier: Apache-2.0 -->

# Design — add-shared-vault-lib

## Module boundary: why a second module beside `vault_naming`

`vault_naming` is a governed SSOT with its own ceremony cadence (ADR-0013/0015/0016/0021): its
content changes when *naming policy* changes. `vault_lib` is plumbing: its content changes when
*mechanics* change. Merging them would couple naming-policy review to plumbing review and give the
naming SSOT an import surface it doesn't need. Two small modules, one precedent import pattern
(`sys.path.insert(0, ~/bin)`), underscore names marking both as importable libraries.

## Root resolution: env-first, marker-walk fallback, hard-block on a bad env

- `$VAULT_ROOT` valid → use it (CI and interactive shells keep exact current behavior).
- `$VAULT_ROOT` set but not a vault → `BLOCKED` + exit 3, **no silent fallback** — when the
  operator points somewhere explicitly, guessing is worse than stopping.
- No env → walk up from cwd to the first directory whose `99-Operations/` contains
  `config.defaults.env` **or** `config.env`. Both are accepted because a fresh template checkout
  has only the defaults file (the instance `config.env` is gitignored and created by the operator),
  while a hardened instance vault must keep working even if the defaults file is ever absent.
  The marker is a *file inside* `99-Operations/`, not the directory name alone, so a stray
  `99-Operations` folder elsewhere cannot spoof a vault root.

This is what closes burn-in probe P5: the exclusion list requires the bare exact invocation
(`~/bin/vault-kanban-render.py` — any prefix, including `VAULT_ROOT=… `, breaks the match and
silently demotes the run into the sandbox, sharp edge SE-5), and the bare form starts in a shell
with no sourced environment. cwd is the vault root in the agent harness, so the walk terminates
immediately in practice.

## Config precedence: mirror the shell, don't re-implement it

`config.env` sources `config.defaults.env` first and then overrides (bash last-write-wins).
`load_config` reproduces exactly that: read defaults, overlay instance. `vocab()` puts the process
environment above both — an exported variable must keep winning, or CI (`set -a; source config.env`)
and every existing interactive flow would change meaning. Values are raw strings — deliberately no
shell evaluation, no `${VAR}` expansion (INV-6: deterministic, no surprise indirection; the only
consumers are whitespace-separated word lists). `VAULT_ROOT` itself is **never** taken from
`load_config` for this reason — root comes from env or the walk, nothing else.

## `is_closed`: one YAML-typed answer

Three parsers existed; two disagreed on `closed: false` (regex: closed; frontmatter lib: open).
The lib standardizes on YAML-typed truthiness — `false`, `null`, and absence are open. This is the
semantic rollover already had; daily-note converges to it. `daily-close-script`'s internal
`split_fm` machinery is *not* replaced in this change (its parser also feeds `set_closed` and the
manifest writer — replacing it is B2/B3 territory); its string-truthy `is_closed` gives the same
verdict on every value the close flow actually writes (a date string).

## Exit codes: 0 / 1 / 2 / 3

`0` ok/no-op · `1` violation · `2` needs-input · `3` gate-blocked. Close-day already used 2 for
"worklist emitted, resolve and re-run" — that meaning is kept and named. `3` is new and reserved
for *refusals by design* (strict-order, missing precondition): the states a driver must react to
differently from both success and failure. Rollover's refusal exiting 0 was the concrete defect —
under driver-owned control flow (ADR-0022 direction), a runbook driver literally could not see the
gate hold.

## Bootstrap exception

`render` deploys `vault_lib.py`; importing it would make first-install order-dependent (and CI's
bootstrap does exactly that first render from the note). So `render-reconcile-script` carries an
inline ~10-line copy of the resolution contract, marked as such. Cost: one deliberate duplication,
visible in both files. Alternative rejected: `render` keeping the raw `environ["VAULT_ROOT"]`
(stays broken bare); vendoring vault_lib import with try/except fallback (two code paths, worse).

## Lazy `frontmatter` import

`find_vault_root`/`load_config`/`vocab` must work in contexts without the venv (git hooks run with
system python). Only `fm`/`is_closed` need `python-frontmatter`, so the import lives inside `fm()`.

## Deliberately out (with reasons)

- **B3 de-sweep of close-day's `git add -A`:** the sweep currently launders `daily-note`'s and
  `bank-execute`'s uncommitted writes into the close commit — removing it without first assigning
  those scripts their own commits would break INV-2 coverage. Needs its own decision + change.
- **B4 `bank-execute` hardening** (schema validation, pre-flight, transactional apply, commit):
  Treasury-writing behavior change; separate review.
- **B2 full skeleton (argparse/`main()`/docstrings fleet-wide):** large mechanical diff; riding it
  on this change would bury the behavioral deltas that need Gate-4 eyes.
- **Wave-2 adoption:** each remaining script adopts when next touched — keeps every diff reviewable.
