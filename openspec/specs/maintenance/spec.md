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
runtime: cron | manual | git hook | harness hook
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

#### Scenario: render refuses a note that breaks the single-fence rule
- **WHEN** `vault-render.py render` (or `reconcile`) encounters a meta-script note with zero or
  more than one `python|bash` code fence
- **THEN** it prints `VIOLATION: <note> has N code fences (exactly 1 required)`, renders nothing
  for that note, and the run exits `1`

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

**Ownership:** the script that performs a mutation commits it, scoped to exactly the files it
mutated — no script relies on a later collector to sweep its writes into someone else's commit.
Uncommitted operator working-tree content is never captured by a script commit.

Commit message format: `<verb>: <subject>` (e.g., `bank: trustless-provenance-sealing`).

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

The vault does **not** project effort state. No fleet script renders a board, dashboard, or
carry-over list of outstanding efforts: the vault exists to distil insight, and tracking
outstanding effort is a distinct lens delegated outside it. A projection with no consumer is not a
neutral cost — it decays into a stale artifact that answers wrongly rather than admitting it cannot.

| Script note | Deploy target | Runtime | Purpose |
|---|---|---|---|
| `render-reconcile-script.md` | `~/bin/vault-render.py` | manual | Deploy Layer-0 code blocks to host targets; detect drift |
| `daily-note-script.md` | `~/bin/vault-daily-note.py` | manual | Create today's daily note from Mold; idempotent; commits the created note (`daily: opened <date>`) |
| `knowledge-lint-script.md` | `~/bin/vault-lint.py` | manual / pre-commit | Validate Treasury frontmatter and name conformance |
| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog index |
| `ore-detect-script.md` | `~/bin/vault-refine-detect.py` | manual | Queue ore whose grade cleared the Sort gate |
| `bank-execute-script.md` | `~/bin/vault-refine-execute.py` | manual | Apply approved proposals from `_refine-approved/`; writes Treasury; one atomic commit per banked proposal (`bank: <stem>`) |
| `spoil-dump-script.md` | `~/bin/vault-dump.sh` | manual | Move a spent husk to `71-Spoil/`; one commit |
| `site-slag-script.md` | `~/bin/vault-slag.sh` | manual | Move an uneconomic effort to `70-Tailings/`; one commit |
| `tailings-reprospect-script.md` | `~/bin/vault-reprospect.py` | manual | List slagged efforts for re-evaluation; detection only |
| `daily-close-script.md` | `~/bin/vault-close-day.py` | manual | Disposition every item of a daily, write the `## Close` manifest, set `closed:`; emits the `unknown/other` worklist; seals with a scoped commit (daily + consumed sidecar), never a sweep |
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

#### Scenario: Daily note creator is idempotent
- **WHEN** the daily-note creator runs twice on the same day
- **THEN** the note is created on the first run and `exists` is printed on the second; no duplicate is created

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
created unconditionally, and its creation is never gated. The deterministic engine
`vault-close-day.py` (`[script]`, INV-6, no LLM) classifies by rule and **emits an
`unknown/other` worklist** for an agent or human to resolve; it never calls a model itself.

#### Scenario: A closed day is fully dispositioned
- **WHEN** `vault-close-day.py` finalizes a day
- **THEN** the `## Close` manifest accounts for every item, `closed:` is set to the close date, and `close-lint` exits 0

#### Scenario: An open prior day is surfaced without gating capture
- **WHEN** the daily-note creator creates today's stub and the previous day is not `closed`
- **THEN** the stub is still created (capture is never gated) and carries a `⚠ BLOCKED: close <prev>`
  banner

#### Scenario: An empty day auto-closes
- **WHEN** `vault-close-day.py` runs on a day with no items
- **THEN** total-disposition is trivially satisfied and the day is marked `closed` without manual input

#### Scenario: close-lint flags an out-of-vocabulary disposition
- **WHEN** `vault-close-day.py --check` runs on a sealed day whose `## Close` manifest carries a
  disposition word not in the `DISPOSITIONS` vocabulary (e.g. a typo)
- **THEN** it prints `FAIL: disposition not in vocab: <word>` and exits `1`

### Requirement: Shared Fleet Plumbing and Exit-Code Contract (vault_lib)

Fleet scripts SHALL resolve the vault root, controlled vocabularies, frontmatter access, and
scoped commits through the shared `vault_lib` module rather than improvising each. The fleet
exit-code contract is: `0` ok · `1` violation · `2` needs-input (a worklist was emitted) ·
`3` gate-blocked. A script whose run is refused by an operational gate (missing precondition,
strict-order guard) SHALL exit `3` and print a `BLOCKED:` line — never `0`.

Adoption: the full Python fleet is adopted — the drive-path set (`daily-close`, `daily-note`,
`bank-execute`) plus `knowledge-lint`, `treasury-orphan`, `tailings-reprospect`, `ore-detect`, and
the `naming-rules` mirror-writer (whose `vault_lib` import is **lazy**, inside `__main__` only, so
`--check` and module import stay dependency-free for the hooks). The shell pair (`site-slag`,
`spoil-dump`) conforms via an inline bash copy of the root-resolution contract (bash cannot import
the Python module), INV-11 slug validation through `vault_naming.py --check`, source/destination
gates (`BLOCKED`, exit 3), and pathspec-scoped commits of exactly the moved effort — never `add -A`.
**Bootstrap exception:** `render-reconcile-script` deploys `vault_lib.py` itself and therefore SHALL
NOT import it; it carries an inline copy of the root-resolution contract instead.

**The bare-drive guarantee extends through governance hooks:** a git hook fired by a drive-path
commit (the `core.hooksPath` commit-gate, and any future hook on that path) SHALL NOT require a
pre-sourced environment. A hook that needs the vault root SHALL derive it from its git context
(e.g. `git rev-parse --show-toplevel` — a hook always runs inside the repository), never from the
caller's environment.

#### Scenario: A drive-path script runs bare with no pre-sourced environment
- **WHEN** a rendered drive-path script is invoked by its bare exact form (e.g.
  `~/bin/vault-daily-note.py`) from a shell with no `VAULT_ROOT` set, cwd inside the vault
- **THEN** it resolves the vault root via the config marker walk and completes normally
- **WHEN** the same invocation happens with no `VAULT_ROOT` and cwd outside any vault
- **THEN** it prints a `BLOCKED:` line and exits `3`

#### Scenario: A gate refusal is machine-distinguishable from success
- **WHEN** `vault-close-day.py` runs for a day whose earlier day is still open (strict-order guard)
- **THEN** it prints a `BLOCKED:` line and exits `3`
- **WHEN** `vault-close-day.py` runs for a day that is already closed
- **THEN** it exits `0`

#### Scenario: The closed test is YAML-typed
- **WHEN** a prior daily note carries `closed: false` (or no `closed:` value)
- **THEN** the daily-note creator treats the day as **open** and applies the `⚠ BLOCKED` banner, via
  `vault_lib.is_closed` — a bare `closed:` key is not truthiness

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

### Requirement: Refine Executor Pre-Flight and Batch Isolation

The refine executor SHALL validate every approved proposal whole, before any write. It is the
sole automated writer of `40-Treasury/` (`bank-execute-script` → `~/bin/vault-refine-execute.py`),
and its pre-flight MUST cover:

- **Schema:** required fields present with correct types (`target_note`, `mode`, `insight_md`,
  `provenance_md`, `index_links`; `frontmatter` for `create`); unparseable JSON is a rejection,
  not a crash.
- **Containment:** the target resolves inside `40-Treasury/`; every index link resolves inside
  `40-Treasury/Catalog/`. Path escapes are rejected.
- **INV-11 boundary:** the target stem is a valid kebab slug.
- **INV-9 pre-action:** `create` SHALL NOT overwrite an existing note — a collision is a
  rejection; `append` requires the target to exist.
- **Vocabularies:** `grade` and `pillars` validate against the config SSOT (`GRADES`, `PILLARS`).
- **Link targets:** every named Catalog index file exists.
- **Catalog reachability (INV-12):** an **empty** `index_links` (a well-formed but zero-length list)
  is NOT a rejection — the executor defaults it to the holding index
  `40-Treasury/Catalog/pending-catalog-index.md` before the Containment and Link-targets checks, so
  every banked note is reachable via ≥1 Catalog index and never a silent orphan. The holding index is
  the visible *awaiting-catalog* queue (its backlog is outstanding curation work, surfaced by
  `treasury-orphan`). It is an ordinary Catalog index that MUST exist (a deployed vault ships it from
  the template); if it is absent the empty-`index_links` proposal is rejected by the Link-targets
  check like any other missing target. A *missing* or *non-list* `index_links` remains a Schema
  rejection — only an explicit empty list is defaulted.

A proposal failing any check is REJECTed with all reasons printed and **no partial write** — the
note, the index links, and the proposal file are all untouched. Rejection is **batch-isolated**:
remaining proposals are still processed. A run with any rejection exits `1` (`EXIT_VIOLATION`,
fleet contract); a fully applied (or empty) batch exits `0`. Rejected proposals remain in
`_refine-approved/` for correction — the executor never deletes what it did not bank.

#### Scenario: A malformed proposal is rejected without stopping the batch
- **WHEN** the executor runs over a batch containing an unparseable or schema-incomplete proposal
  followed by a valid one
- **THEN** the bad proposal is REJECTed with reasons, nothing of it is written, and the valid
  proposal is still banked with its atomic commit; the run exits `1`

#### Scenario: Create never overwrites refined value
- **WHEN** a `create` proposal targets a note that already exists in `40-Treasury/`
- **THEN** the proposal is REJECTed (`INV-9`) and the existing note is byte-identical afterwards

#### Scenario: A missing Catalog target rejects the whole proposal pre-write
- **WHEN** a proposal names an `index_links` entry that does not exist
- **THEN** the proposal is REJECTed and the knowledge note is NOT created — no half-applied state

#### Scenario: An empty index_links defaults to the pending-catalog holding index
- **WHEN** an approved proposal's `index_links` is an explicit empty list and
  `40-Treasury/Catalog/pending-catalog-index.md` exists
- **THEN** the executor does NOT reject it; it banks the note and links it into
  `pending-catalog-index.md` so the note is reachable (INV-12), and the note appears in the
  awaiting-catalog queue for later re-homing into its pillar index

#### Scenario: A path escape is rejected
- **WHEN** a proposal's `target_note` resolves outside `40-Treasury/` (e.g. via `..`) or an index
  link resolves outside `40-Treasury/Catalog/`
- **THEN** the proposal is REJECTed with a containment reason and nothing is written

### Requirement: Platform and Dependency Floors

The fleet SHALL declare and honor explicit floors, so implementers and future models never guess:

- **Python ≥ 3.12** (CI exercises 3.12 and 3.13); language features beyond the floor are not used.
- **Sole third-party dependency: `python-frontmatter`**, installed in the vault-local venv. The
  hook-critical paths — the git hooks, `vault_naming.py --check`, and `vault_lib`'s root/config
  helpers — MUST remain stdlib-only so they run on the system Python without the venv.
- **Platform floor: Linux/POSIX.** Bash hooks, executable bits, and POSIX path semantics are
  assumed; Windows is an explicit non-goal (documented, not silently broken).

#### Scenario: Hook-critical paths run without the venv
- **WHEN** the pre-commit naming gate or `vault_naming.py --check` runs on a system Python with
  no third-party packages installed
- **THEN** it completes normally — no `frontmatter` (or other third-party) import is reached on
  that path

#### Scenario: A new third-party dependency is a governed decision
- **WHEN** a change proposes any import beyond the standard library and `python-frontmatter`
- **THEN** it names the dependency in its proposal and updates this requirement — silent
  dependency growth is a violation

### Requirement: Governance Tooling Is Pinned and Ceremony Templates Live Outside the Change Tree

The OpenSpec CLI (`@fission-ai/openspec`) SHALL be pinned to an exact version in `package.json` so that
`openspec validate` is reproducible across contributors and CI. A weekly canary MAY validate the corpus
against `@latest` to surface incompatibilities before the pin advances.

Ceremony scaffolds — blank templates such as the constitution-override proposal template — SHALL live
**outside** `openspec/changes/` and `openspec/specs/` (the directories the validator scans), because a
template has no spec deltas and the validator treats every folder under `changes/` as a change. The
constitution-override ceremony template SHALL exist at `openspec/templates/constitution-override/proposal.md`,
and CI SHALL assert its presence at that path.

#### Scenario: The pinned CLI makes validation reproducible
- **WHEN** a contributor or CI runs `openspec validate --all --strict` after `npm install`
- **THEN** the `@fission-ai/openspec` version resolved is exactly the one pinned in `package.json`
- **THEN** the pin advances only through a change that re-proves the corpus validates green under the new version

#### Scenario: A ceremony template is not enumerated as a change
- **WHEN** `openspec validate --all` runs against the repository
- **THEN** the constitution-override template at `openspec/templates/constitution-override/proposal.md` is
  NOT enumerated as a change and cannot fail the "change must have ≥1 delta" rule
- **THEN** no blank scaffold resides under `openspec/changes/`

#### Scenario: CI asserts the ceremony template exists at its fixed path
- **WHEN** the constitution-lint CI job runs
- **THEN** it fails if `openspec/templates/constitution-override/proposal.md` is absent
- **THEN** every reference to the template across specs, docs, and workflows points at that same path

### Requirement: Scope-Review CI Gate (Declared Scope)

Every pull request SHALL declare its authorized change surface as a fenced ```scope block in the
PR body — root-relative paths, one per line, directories with a trailing `/`, no glob syntax; the
non-file surfaces the checker inspects are declared with prefixed entries (`env: NAME`,
`dep: package`, `endpoint: /route`); for ceremony changes the declaration mirrors the Gate-1
blast radius. CI SHALL enforce the declaration
deterministically (INV-6 posture at the CI layer — offline, no LLM in the decision path):

- **Extraction is fail-closed:** a missing, empty, or malformed declaration fails the job with an
  instructive message. The PR body reaches the extractor via environment variable, never shell
  interpolation. Entries containing glob characters, or lacking both `/` and `.`, are rejected
  (the pinned checker matches directory prefixes and exact paths only).
- **Comparison is deterministic and self-contained:** the diff against the merge base is compared
  to the declared scope by a repo-owned, stdlib-only comparator — exact-path / directory-prefix
  matching, no fuzzy branches, no third-party runtime dependency, no registry fetch, no network.
  The gate SHALL NOT depend on external packages at run time (the declared-scope concept and
  schema were informed by an evaluated external tool, credited in the CHANGELOG).
- **The threshold is repo-owned:** the job fails on any finding — undeclared file (medium) or
  undeclared workflow env var / dependency (high). Malformed inputs fail closed.
- **Two-stage adoption:** Phase A runs report-only (`continue-on-error`) as burn-in; the flip to
  blocking is its own governed change after clean burn-in. Dependabot PRs are exempt by actor.

#### Scenario: PR without a Declared-scope block fails extraction
- **WHEN** a pull request is opened whose body contains no fenced ```scope block
- **THEN** the `scope-review` job fails at the extraction step, naming the fix (add the block per
  the PR template), and no checker invocation occurs

#### Scenario: Diff touching an undeclared path is a failing finding
- **WHEN** the PR diff modifies a file matched by no declared entry (e.g. an undeclared
  `docs/` file riding along with a scripts change)
- **THEN** the checker reports a `scope.file` finding and the threshold step exits non-zero,
  listing the offending path(s) — the author either shrinks the diff or amends the declaration
  deliberately

#### Scenario: Declared-only diff passes
- **WHEN** every path in the PR diff is matched by a declared entry (exact path or directory
  prefix) and no undeclared dependencies/endpoints/env-vars are introduced
- **THEN** the threshold step exits 0 and reports PASS with any low-severity advisories

#### Scenario: Checker crash fails closed
- **WHEN** the comparator receives a missing or malformed scope file or diff
- **THEN** it exits non-zero (fail-closed); the gate never passes by silence

### Requirement: GitHub Release Object Per Version Tag

Every published version tag `vX.Y.Z` SHALL have a corresponding GitHub **Release object**, created as a
mandatory, verified step of the ship ceremony. A git tag and a GitHub Release are distinct objects:
pushing a tag does NOT create a Release, and the "latest release" surfaces (the repository Releases page
and any profile mirror) reflect the newest Release object, not the newest tag. The ship ceremony
therefore SHALL, after a change is merged to `main`:

- create an annotated tag `vX.Y.Z`;
- create the GitHub Release for that tag (`gh release create <tag> --verify-tag --latest`) with a title
  and notes derived from the tag/CHANGELOG; and
- **verify parity** (`gh release view <tag>` resolves and is marked Latest) as an explicit ceremony
  step before the ship is considered complete.

Because release creation and verification are part of the same ceremony that cuts the tag, a tag can
never accumulate without its Release. This is a ceremony action (agent- or operator-run, gated by the
INV-14 outbound guard), **not** part of the deterministic offline script fleet — it legitimately calls
the authenticated `gh` CLI, so INV-6 (no network in the deterministic fleet) is not engaged. No CI job
performs a networked GitHub call to enforce parity; the guarantee is the mandatory verified ceremony
step.

#### Scenario: Shipping a version creates and verifies its Release
- **WHEN** a merged change is shipped as `vX.Y.Z`
- **THEN** the ceremony creates the annotated tag, creates the GitHub Release for it, and verifies with
  `gh release view vX.Y.Z` that the Release exists and is marked Latest before the ship is complete

#### Scenario: A tag without a Release is an incomplete ship
- **WHEN** a `vX.Y.Z` tag exists on the remote but `gh release view vX.Y.Z` does not resolve
- **THEN** the ship is not complete; the release-creation step is performed (backfilled) so tag/Release
  parity holds

#### Scenario: Release creation passes through the outbound hard stop
- **WHEN** the agent runs `gh release create` (or the tag push) during a ship
- **THEN** the INV-14 outbound guard raises the ASK hard stop, and the agent first presents an overview
  summary plus the absolute path to the governing `proposal.md`; the step proceeds only on explicit
  human approval

### Requirement: Pillar Vocabulary Tokens Are Kebab-Case Slugs

Every token in the `PILLARS` vocabulary MUST be a valid kebab-case slug as defined
by the `naming-rules` `slug_pattern` (`^[a-z0-9]+(?:-[a-z0-9]+)*$`) and MUST pass
the cross-platform-safety and reserved-name checks of `validate_name()` — i.e. the
token MUST satisfy `is_valid_slug()`.

The ≥3-hyphen-token floor (`has_min_hyphen_tokens`, INV-11) does **NOT** apply to
pillar tokens. That floor governs `.md` stems; a pillar token is a name *fragment*
that is interpolated into a stem (`<pillar>-domain-index`), and the resulting stem
satisfies the floor on its own.

A multi-word pillar is expressed as a single hyphenated token (`mental-health`),
never as two whitespace-separated words. The `PILLARS` delimiter remains whitespace.

Rationale: a pillar token is interpolated directly into the machine-generated
Catalog index filename `40-Treasury/Catalog/<pillar>-domain-index.md`. Constraining
the token to the slug grammar makes the vocabulary and the filename agree by
construction, with no pillar→slug transform and no display/slug identity split.

#### Scenario: Well-formed pillar vocabulary passes

- **WHEN** the linter runs with `PILLARS="mental health financial social technology calling"`
- **THEN** each token is validated with `is_valid_slug()`
- **THEN** all six tokens pass and no violation is recorded

#### Scenario: Multi-word pillar as a single kebab token passes

- **WHEN** `PILLARS` contains the token `mental-health`
- **THEN** `is_valid_slug("mental-health")` is true and no violation is recorded
- **THEN** the derived index filename is `mental-health-domain-index.md`, which
  satisfies the INV-11 ≥3-token floor

#### Scenario: Malformed pillar token fails the lint

- **WHEN** `PILLARS` contains a token that fails `is_valid_slug()` — e.g.
  `Mental_Health` (uppercase + underscore), `CON` (reserved name), or `-lead`
  (leading hyphen)
- **THEN** the linter records a violation naming the offending token and the
  `PILLARS` key
- **THEN** the linter exits `EXIT_VIOLATION`
- **THEN** no Catalog index is derived from the malformed token

#### Scenario: Pillar vocabulary is validated before frontmatter is checked

- **WHEN** the linter runs
- **THEN** `PILLARS` well-formedness is validated before Treasury `pillars`
  frontmatter is validated against it
- **THEN** a malformed vocabulary is reported as a vocabulary violation, not as a
  cascade of per-note frontmatter violations

### Requirement: The Linter Applies The Token Floor To Content Stems

The knowledge linter SHALL apply the ≥3-hyphen-token floor (`has_min_hyphen_tokens`) in
addition to the kebab rule, to every non-exempt content name it already checks:

- Treasury note stems (`40-Treasury/*.md`)
- Effort folder slugs (`30-Sites/*/`, `70-Tailings/*/`)
- Other content stems (`20-Claims`, `10-Logbook`, `40-Treasury/Catalog`)

The previously staged branch for this rule SHALL be enabled, not left commented. Special-file
exemptions (`is_exempt`) continue to be applied first.

The floor SHALL NOT be applied to pillar tokens, which are name *fragments* interpolated into
a stem rather than stems themselves (ADR-0029).

#### Scenario: A sub-3-token Treasury stem fails the lint

- **WHEN** the linter encounters a non-exempt `40-Treasury/short-note.md`
- **THEN** it records `Treasury stem not >=3-token kebab (INV-11)`
- **THEN** it exits `EXIT_VIOLATION`

#### Scenario: A sub-3-token effort folder fails the lint

- **WHEN** the linter encounters `30-Sites/sample/`
- **THEN** it records `effort folder not >=3-token kebab (INV-11)`

#### Scenario: The live corpus passes with the rule enabled

- **WHEN** the linter runs over a conforming vault
- **THEN** no floor violation is recorded, because enforcement was switched on only after
  full conformance was measured (0 of 103 non-exempt names failing)

### Requirement: Template–Live Parity Check (Mirror Completeness)

The framework repo SHALL provide a deterministic, offline, detection-only tool that verifies a
deployed vault's LOCKSTEP scaffold is byte-identical to what the repo's `vault-template/` ships, so
a post-merge mirror can be proven complete rather than assumed. It answers the axis `reconcile`
cannot: `reconcile` compares a script note to its deployed `~/bin` target (note → host); this
compares repo-shipped scaffold to live-deployed scaffold (template → vault). It is a
maintainer/mirror-time check — NOT part of the deployed vault (which is standalone and never
references the repo) and NOT a CI gate (CI has no live vault to compare against).

- **Lockstep scope is an explicit manifest.** A repo-owned `tools/template-sync-manifest.json`
  declares `lockstep` directory prefixes — the INV-3 source-of-truth scaffold (`99-Operations/scripts/`,
  `99-Operations/schemas/`) — and an `exclude` list for files under a lockstep prefix that the live
  vault legitimately GENERATES (the template ships the generator, not its output; e.g.
  `99-Operations/schemas/naming-rules.json`, emitted by `vault_naming.py`). Everything outside a
  lockstep prefix is per-instance seed (CLAUDE.md, config, `40-Treasury/`, Catalog indexes, README)
  and SHALL NOT be compared.
- **Comparison is byte-exact and bidirectional.** For each prefix the union of files under the prefix
  in BOTH trees is compared: a file present in one tree but absent from the other is drift
  (`MISSING-IN-LIVE` / `MISSING-IN-TEMPLATE`); a differing file is drift (`DIFFERS`). Directory-prefix
  scope means a newly-shipped file under a lockstep prefix is compared automatically — it cannot go
  silently unchecked.
- **Detection only, never auto-fix.** Like `reconcile` (INV-3) the tool reports drift and exits
  non-zero; it never writes. A human re-runs the mirror to resolve drift.
- **Evidence, not assertion.** The tool prints the count of files actually compared (the denominator)
  alongside the drift count, so an empty drift list cannot be mistaken for a broken comparison.
- **Stdlib-only, offline, no LLM** — the INV-6 determinism posture applied at the mirror-time
  maintenance layer. Exit contract mirrors the fleet: `0` in parity · `1` drift · `3` blocked
  (no resolvable live vault, or a manifest with no lockstep prefixes).

#### Scenario: A clean mirror reports zero drift
- **WHEN** `tools/template-parity.py <VAULT_ROOT>` runs after a complete mirror
- **THEN** every non-excluded file under each lockstep prefix is byte-identical between
  `vault-template/` and the live vault, it prints the count of files checked with `0 drift`, and
  exits `0`

#### Scenario: A hand-edited or unmirrored lockstep file is drift
- **WHEN** a deployed lockstep file differs from the template it was shipped from (an incomplete
  mirror, or a local edit)
- **THEN** the tool prints `DIFFERS: <path>` and exits `1` — the incomplete apply is surfaced, and
  the tool does not modify either tree

#### Scenario: A lockstep file present in only one tree is drift
- **WHEN** a file under a lockstep prefix exists in the template but not the live vault (or the
  reverse)
- **THEN** the tool prints `MISSING-IN-LIVE: <path>` (or `MISSING-IN-TEMPLATE: <path>`) and exits `1`

#### Scenario: A generated artifact under a lockstep prefix is excluded, not flagged
- **WHEN** a file listed in the manifest `exclude` (e.g. `naming-rules.json`) exists only in the live
  vault because the vault generates it
- **THEN** the tool does NOT report it as drift; it is counted as excluded and the run can still exit
  `0`

#### Scenario: No resolvable live vault is a blocked run, not a false pass
- **WHEN** the tool is invoked with neither a live-vault argument nor `$VAULT_ROOT`, or against a
  path that is not a vault
- **THEN** it prints a `BLOCKED:` line and exits `3` — it never reports parity by silence

### Requirement: Catalog Linking Is Idempotent

When the refine executor banks a proposal, it SHALL append a Catalog index link
(`- [[<stem>]]`) to an `index_links` target only if that index does not already carry the link.
`create` mode is unaffected (a new note is in no index yet); `append` mode extends a note that is
usually already catalogued, so an unconditional write would duplicate the note's existing bullet.
Idempotent linking lets `append` extend a note without polluting its Catalog index, while a
genuinely new index named in `index_links` is still linked. INV-12 reachability is preserved: every
banked note remains reachable via ≥1 Catalog index.

#### Scenario: Appending to an already-catalogued note does not duplicate its link
- **WHEN** an `append` proposal names an `index_links` index that already contains `- [[<stem>]]`
- **THEN** the executor extends the note and leaves that index unchanged — the bullet appears once,
  not twice — and the bank still produces its one atomic commit

#### Scenario: A new index is still linked
- **WHEN** a proposal names an `index_links` index that does NOT yet contain `- [[<stem>]]`
- **THEN** the executor appends `- [[<stem>]]` to that index, so the note is reachable from it

### Requirement: Ship-Release Driver (Guarded, Re-Entrant, Never Outbound Itself)

The framework repo SHALL provide a ship-release driver (`tools/ship-release.py`) that mechanizes
the "Shipping a version" ceremony as a guarded, re-entrant state machine, so the ceremony's
documented hazards are guard clauses at their point of action instead of per-session
recollections. Each invocation re-derives the ship's state from the world (git refs, the remote,
the Release object) — the driver holds no state file and is safe to re-run at any point.

- **Merge-ancestor proof before any tag exists.** The driver SHALL refuse (exit `1`) to create or
  accept a tag whose target commit is not an ancestor of `origin/<base>` — never tag before merge.
- **CHANGELOG proof.** The driver SHALL refuse when `CHANGELOG.md` carries no `## [X.Y.Z]` section
  for the version being shipped; that section is the source of the emitted release notes.
- **Stale tags are refused with the true cause named.** A local or remote tag for the version that
  points at a different commit than the target is a refusal that prints BOTH commits and names the
  actual cause (a stale tag), never a mis-report of a different failure (e.g. "not merged").
  Resolving a stale tag — especially a published one — is a deliberate human action the driver
  SHALL NOT perform.
- **The driver SHALL NOT execute outward mutations.** `git push` and `gh release create` are
  ASK-gated by the INV-14 outbound guard, which text-matches the command being run; a wrapper that
  ran them internally would bypass that rail. The driver performs exactly one mutation itself — the
  local annotated tag, created only after both guards pass and verified by re-read — and otherwise
  EMITS the next single outward command verbatim, exiting `2` (needs-input). The caller runs that
  one command through the normal gated channel and re-invokes the driver.
- **Post-mutation verification, per layer.** On re-invocation the driver SHALL verify the previous
  step actually landed (the remote tag peels to the target; the Release object exists and is not a
  draft) before emitting the next step — a silent success is never trusted. Layer reads are printed
  one per line with the layer named (`local-tag` / `remote-tag` / `release-object`).
- **Tag↔Release parity tally closes the ship.** Once the Release exists, the driver SHALL tally all
  `vX.Y.Z` tags on origin against all Release objects and print the counts with their denominators
  (`N version tags / M releases — K tags without a release, J releases without a tag`), naming each
  parity miss. Exit `0` only on a clean tally; any miss (or a draft / a newest-version Release not
  marked Latest) exits `1`.
- **Network posture.** This is a ceremony tool, not a deterministic fleet script: it legitimately
  performs authenticated reads (`git fetch`/`ls-remote`, `gh release view/list`) per the
  "GitHub Release Object Per Version Tag" requirement, so INV-6 is not engaged. It is repo-only —
  not part of the deployed vault, not a CI gate. Exit contract: `0` ship complete · `1` refused ·
  `2` next gated command emitted · `3` blocked.

#### Scenario: An unmerged target is refused before any tag exists

- **WHEN** the driver runs for `vX.Y.Z` with a target commit that is not an ancestor of
  `origin/main`
- **THEN** it refuses with the ancestor proof named and exits `1`, and no tag for `vX.Y.Z` exists
  anywhere afterwards

#### Scenario: The driver walks the ceremony one gated command at a time

- **WHEN** the driver runs with both guards passing and no tag or Release yet
- **THEN** it creates the local annotated tag, verifies it by re-read, emits exactly
  `git push origin refs/tags/vX.Y.Z` as the next command, and exits `2`
- **WHEN** the caller has run that command and re-invokes the driver
- **THEN** the driver verifies the remote tag peels to the target, emits the
  `gh release create vX.Y.Z --verify-tag --latest …` command with notes derived from the CHANGELOG
  section, and exits `2`
- **WHEN** the Release exists and every version tag has its Release
- **THEN** the driver prints the parity tally with its denominators and exits `0`

#### Scenario: A stale tag is named as the true cause

- **WHEN** a tag for the version already exists (locally or on origin) pointing at a commit other
  than the target
- **THEN** the driver refuses, printing both commits and naming the stale tag as the cause — it
  does not report a merge problem, and it does not delete the tag itself

#### Scenario: A tag without a Release fails the closing tally

- **WHEN** the parity tally finds a version tag on origin with no corresponding Release object
- **THEN** the driver prints the miss (`parity-miss … tag vA.B.C has no Release`) and the tally
  with denominators, and exits `1` — an incomplete ship is never reported as complete

### Requirement: PR State Is Reported Per Layer

The framework repo SHALL provide a read-only PR-state reporter (`tools/pr-state.py <PR#>`) that
prints a pull request's state with the answering layer named on every line, because GitHub is a
stack of layers — event payload · workflow run · check aggregation · REST · GraphQL · branch/PR
state machine — that answer different questions and can disagree while all being correct.
Collapsing them into one oracle is the documented failure mode; the reporter keeps them apart.

- **Layers reported:** the PR state machine (state, draft, mergeable, `mergeStateStatus`); the
  branch layer read from origin refs (base and head existence and SHAs, diffed against the PR's
  recorded head oid); check-level aggregation (per-check verdicts with a tally and its
  denominator); run-level aggregation (per-run conclusions for the head commit); and the event
  payload as a standing advisory — it is not re-readable, a rerun replays the snapshot from the
  triggering event, and an amended PR body is seen only by a new push or an API read at job time.
- **Disagreement is a named signal, not an error.** When the run layer and the check layer
  disagree (e.g. a `continue-on-error` job), the reporter SHALL print a `LAYERS-DISAGREE:` line
  naming both layers and both tallies. The reporter exits `0` — the finding is the deliverable.
- **Known irreversible hazards are printed at the point of observation:** a deleted base branch
  (a closed stacked PR can be neither reopened nor retargeted — retarget the child before merging
  its parent) and a stale head oid (two layers out of sync) are flagged as `HAZARD [branch]:`
  lines.
- **Post-mutation verifier.** The reporter is the designated re-read after any `gh`/GraphQL
  mutation (a mutation can fail silently where REST succeeds); its output, not a silent success,
  is the evidence the state changed.
- **Read-only and repo-only.** Every call it makes is a read; it emits no outward command, so it
  sits below the INV-14 rail. Exit contract: `0` report delivered · `3` blocked.

#### Scenario: Every layer is named in the report

- **WHEN** the reporter runs against an open PR with checks and workflow runs
- **THEN** its output carries one or more lines for each of `pr-state-machine`, `branch`,
  `check-aggregation`, `workflow-run`, and `event-payload`, each prefixed with the layer name, and
  the check tally shows its denominator

#### Scenario: Disagreeing aggregation layers are surfaced as a signal

- **WHEN** the check layer reports a failing check while every workflow run for the same head
  commit concluded success (or vice versa)
- **THEN** the reporter prints a `LAYERS-DISAGREE:` line naming both layers and both tallies, and
  still exits `0`

#### Scenario: A deleted base branch is a printed hazard

- **WHEN** the PR's base branch no longer exists on origin
- **THEN** the reporter prints a `HAZARD [branch]:` line stating the retarget-before-merge rule
  for stacked PRs

