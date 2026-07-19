<!-- SPDX-License-Identifier: Apache-2.0 -->
<!--
  Three Requirements below are REMOVED-then-ADDED rather than MODIFIED. That is deliberate and
  is the tool-sanctioned shape: the archiver's MODIFIED path refuses any block that does not
  restate every current scenario (it cannot express an intentional scenario removal), and each
  of these must genuinely lose a scenario whose subject ceases to exist — "A created daily note
  is committed by its creator", "A close seals with a scoped commit, never a sweep", "Daily note
  creator is idempotent", "The closed test is YAML-typed". Apply order is REMOVED → ADDED, so the
  name is free when re-added.
-->
## REMOVED Requirements

### Requirement: Daily Close Lifecycle

### Requirement: One Mutation, One Commit (INV-2)

### Requirement: Script Inventory

### Requirement: Shared Fleet Plumbing and Exit-Code Contract (vault_lib)

## ADDED Requirements

### Requirement: One Mutation, One Commit (INV-2)

Every automated mutation SHALL end in exactly one Git commit with a structured message.
No script produces zero commits (silent no-op on unchanged state is acceptable;
producing zero commits when a mutation occurred is not) or multiple commits.

**Ownership:** the script that performs a mutation commits it, scoped to exactly the files it
mutated — no script relies on a later collector to sweep its writes into someone else's commit.
Uncommitted operator working-tree content is never captured by a script commit.

Commit message format: `<verb>: <subject>` (e.g., `bank: trustless-provenance-sealing`).

#### Scenario: A banked proposal is one atomic commit
- **WHEN** the refine executor applies an approved proposal
- **THEN** it produces exactly one commit (`bank: <stem>`) containing the knowledge note, the
  appended Catalog index links, and the consumed proposal's deletion (when the proposal was
  tracked) — and nothing else

#### Scenario: A mover seals with a scoped commit, never a sweep
- **WHEN** `vault-slag.sh <slug>` moves an effort while unrelated uncommitted changes exist
  elsewhere in the working tree
- **THEN** the commit contains exactly the moved effort, and the unrelated changes remain
  uncommitted and untouched

### Requirement: Script Inventory

The following scripts SHALL be implemented as literate meta-script notes in Phase 1–2.
Each is offline and deterministic (INV-6).

The vault does **not** project effort state. No fleet script renders a board, dashboard, or
carry-over list of outstanding efforts: the vault exists to distil insight, and tracking
outstanding effort is a distinct lens delegated outside it. A projection with no consumer is not a
neutral cost — it decays into a stale artifact that answers wrongly rather than admitting it cannot.

The vault likewise generates **no dated note format**. Capture has a home in `20-Claims/`; the
framework engages downstream of capture, refining accumulated ore into banked value (ADR-0032). A
dated log that only a human could author, and that git already records, is a lossy duplicate of the
commit history rather than a second source.

| Script note | Deploy target | Runtime | Purpose |
|---|---|---|---|
| `render-reconcile-script.md` | `~/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to host targets; detect drift |
| `knowledge-lint-script.md` | `~/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog index |
| `ore-detect-script.md` | `~/bin/vault-refine-detect.py` | manual | Queue ore whose grade cleared the Sort gate |
| `bank-execute-script.md` | `~/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury; one atomic commit per banked proposal (`bank: <stem>`) |
| `spoil-dump-script.md` | `~/bin/vault-dump.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
| `site-slag-script.md` | `~/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
| `tailings-reprospect-script.md` | `~/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
| `naming-rules-script.md` | `~/bin/vault_naming.py` | manual | Naming validator SSOT; also emits `naming-rules.json` |
| `vault-lib-script.md` | `~/bin/vault_lib.py` | manual | Shared fleet plumbing: root resolution, config vocabulary, frontmatter access, scoped one-commit helper, fleet exit-code contract (ADR-0023) |
| `commit-gate-script.md` | `99-Operations/hooks/pre-commit` | git hook | Commit-gate: block non-conforming file names (INV-11) |
| `outbound-publish-guard-script.md` | `.claude/hooks/outbound-publish-guard.py` | harness hook | Claude Code `PreToolUse` guard (INV-14, ADR-0018): hard-deny vault-outward commands; loud ASK before public publishes — now render/reconcile-governed (R8) |
| `push-guard-script.md` | `99-Operations/hooks/pre-push` | git hook | Push-gate (INV-14): deny outbound push by default; permit a remote in `PUSH_ALLOWLIST` (full vault); for a remote in `PUBLIC_REMOTE_ALLOWLIST`, permit **only** paths matched by `99-Operations/schemas/publish-manifest.json` (`public_allow`), else refuse |

No script declares a `cron` runtime or a `schedule:`. `render` deploys code and marks it executable;
it does **not** install schedules, and nothing reads a `schedule:` field. A cadence a script cannot
install is a decoration, not a configuration (ADR-0028).

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

#### Scenario: Retiring a script removes its deploy target in lockstep
- **WHEN** a script note is removed from the inventory
- **THEN** its deploy target is deleted from the host in the same apply — `reconcile` iterates
  **notes**, so a deployed artifact whose note no longer exists is invisible to drift detection and
  would persist as operational code outside the render inventory (the R8 gap)

#### Scenario: Push-guard denies an un-allowlisted push
- **WHEN** `git push` runs from a deployed vault and the target remote URL is not listed in `PUSH_ALLOWLIST` or `PUBLIC_REMOTE_ALLOWLIST`
- **THEN** the `pre-push` hook aborts the push (non-zero) with an INV-14 message

#### Scenario: Push-guard applies the path-level manifest to a public remote
- **WHEN** `git push` targets a remote in `PUBLIC_REMOTE_ALLOWLIST` and the diff includes a path not in `publish-manifest.json` `public_allow`
- **THEN** the `pre-push` hook aborts with an INV-14 path-boundary violation; a push whose paths are all allowlisted is permitted

### Requirement: Shared Fleet Plumbing and Exit-Code Contract (vault_lib)

Fleet scripts SHALL resolve the vault root, controlled vocabularies, frontmatter access, and
scoped commits through the shared `vault_lib` module rather than improvising each. The fleet
exit-code contract is: `0` ok · `1` violation · `2` needs-input (a worklist was emitted) ·
`3` gate-blocked. A script whose run is refused by an operational gate (missing precondition,
source/destination guard) SHALL exit `3` and print a `BLOCKED:` line — never `0`.

Adoption: the full Python fleet is adopted — `bank-execute` plus `knowledge-lint`,
`treasury-orphan`, `tailings-reprospect`, `ore-detect`, and the `naming-rules` mirror-writer (whose
`vault_lib` import is **lazy**, inside `__main__` only, so `--check` and module import stay
dependency-free for the hooks). The shell pair (`site-slag`, `spoil-dump`) conforms via an inline
bash copy of the root-resolution contract (bash cannot import the Python module), INV-11 slug
validation through `vault_naming.py --check`, source/destination gates (`BLOCKED`, exit 3), and
pathspec-scoped commits of exactly the moved effort — never `add -A`. **Bootstrap exception:**
`render-reconcile-script` deploys `vault_lib.py` itself and therefore SHALL NOT import it; it carries
an inline copy of the root-resolution contract instead.

**The bare-drive guarantee extends through governance hooks:** a git hook fired by a drive-path
commit (the `core.hooksPath` commit-gate, and any future hook on that path) SHALL NOT require a
pre-sourced environment. A hook that needs the vault root SHALL derive it from its git context
(e.g. `git rev-parse --show-toplevel` — a hook always runs inside the repository), never from the
caller's environment.

#### Scenario: A drive-path script runs bare with no pre-sourced environment
- **WHEN** a rendered drive-path script is invoked by its bare exact form (e.g.
  `~/bin/vault-refine-detect.py`) from a shell with no `VAULT_ROOT` set, cwd inside the vault
- **THEN** it resolves the vault root via the config marker walk and completes normally
- **WHEN** the same invocation happens with no `VAULT_ROOT` and cwd outside any vault
- **THEN** it prints a `BLOCKED:` line and exits `3`

#### Scenario: A gate refusal is machine-distinguishable from success
- **WHEN** `vault-slag.sh <slug>` runs for an effort whose source directory does not exist
- **THEN** it prints a `BLOCKED:` line and exits `3`
- **WHEN** the same mover runs for a valid effort
- **THEN** it completes and exits `0`

#### Scenario: The shared library self-check is read-only
- **WHEN** `vault_lib.py` is executed bare inside a vault
- **THEN** it prints the resolved root and a vocabulary summary, mutates nothing, and exits `0`

#### Scenario: The commit-gate passes drive-path commits without environment
- **WHEN** a drive-path script commits its owned artifact and the `core.hooksPath` pre-commit
  naming gate fires in a process with no `VAULT_ROOT` set
- **THEN** the gate evaluates the staged names normally — INV-11 enforcement unchanged, a
  violating name is still `BLOCKED` — and does not fail on a missing environment variable

#### Scenario: A repeated committing run is a clean no-op
- **WHEN** a committing fleet script runs twice in a row with no underlying state change, so the
  second run's named paths are unchanged
- **THEN** `commit_paths` prints an `unchanged — no commit needed` line, produces no commit, and
  exits `0` — it does not crash on an empty index

#### Scenario: A scoped commit ignores unrelated staged content
- **WHEN** unrelated files are already staged (e.g. by the operator) and a fleet script commits
  its owned artifact via `commit_paths`
- **THEN** the resulting commit contains exactly the script's named paths, and the unrelated
  staged content remains staged and uncommitted

#### Scenario: A shell mover is env-free, validated, and scoped
- **WHEN** `vault-slag.sh <slug>` runs bare with no `VAULT_ROOT`, cwd inside the vault
- **THEN** it resolves the root via the config marker walk; an invalid slug exits `1`
  (`INVALID` from the naming SSOT); a missing source or existing destination prints `BLOCKED:`
  and exits `3`; on success it produces exactly one commit containing only the moved effort,
  and unrelated staged content remains staged and uncommitted
