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
| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual | Report Treasury notes not linked from any Catalog index (INV-12); detection only |
| `secret-scan-script.md` | `~/bin/vault_secrets.py` | manual / pre-commit | Credential-format scanner (INV-7, ADR-0036): tiered patterns over staged content, a path set, or the object DB; `--selftest` proves the patterns fire |
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
- **The gate is BLOCKING (Phase B, complete).** The job SHALL NOT carry `continue-on-error`; a
  finding fails the job and the run. Phase A's report-only burn-in is discharged. Dependabot PRs
  remain exempt by actor, and the job does not run on the `push` trigger.
- **Where the block binds SHALL be stated, not assumed.** A failing job blocks a merge through the
  lifecycle driver, which refuses to emit a merge command while any check is failing. Adding this
  job to the branch ruleset's required contexts is a **separate** decision, because the job reports
  `skipped` on the `push` trigger and on dependabot PRs, and whether a `skipped` conclusion
  satisfies a required context cannot be dry-run on this plan.

#### Scenario: PR without a Declared-scope block fails extraction
- **WHEN** a pull request is opened whose body contains no fenced ```scope block
- **THEN** the `scope-review` job fails at the extraction step, naming the fix (add the block per
  the PR template), and no checker invocation occurs
- **THEN** the failure is not suppressed — the job has no `continue-on-error`

#### Scenario: Diff touching an undeclared path is a failing finding
- **WHEN** the PR diff modifies a file matched by no declared entry (e.g. an undeclared
  `docs/` file riding along with a scripts change)
- **THEN** the checker reports a `scope.file` finding and the threshold step exits non-zero,
  listing the offending path(s) — the author either shrinks the diff or amends the declaration
  deliberately
- **THEN** the lifecycle driver refuses to emit a merge command while that check is failing

#### Scenario: Declared-only diff passes
- **WHEN** every path in the PR diff is matched by a declared entry (exact path or directory
  prefix) and no undeclared dependencies/endpoints/env-vars are introduced
- **THEN** the threshold step exits 0 and reports PASS with any low-severity advisories

#### Scenario: Checker crash fails closed
- **WHEN** the comparator receives a missing or malformed scope file or diff
- **THEN** it exits non-zero (fail-closed); the gate never passes by silence

#### Scenario: The job is renamed only while its context is unrequired
- **WHEN** the job's `name` is changed, since the name is the check-context identity
- **THEN** the change is made while the context is absent from the ruleset's required contexts
- **THEN** any later addition to required contexts uses the new name, so no required context is
  ever renamed out from under a merge

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

### Requirement: Operator-Only Paths Fail Legibly

A fleet script SHALL fail legibly when its write target lies in an area the Area Access Matrix
withholds from the agent: on a write refused by the OS sandbox (`OSError` with `errno == EROFS`), it
SHALL exit with a distinct status of **4** and a message that names the path, states the denial is
**by design**, and directs the reader to run the step as the operator. It SHALL NOT emit a bare
traceback for this case, and SHALL re-raise any other `OSError` unchanged.

The denial itself is correct and is not relaxed: `vault-render.py render` writes only
`deploy_target`s (`~/bin/`, `99-Operations/hooks/`, `.claude/hooks/`) and `vault_naming.py` in emit
mode writes only `99-Operations/schemas/naming-rules.json` — all areas the matrix marks `A: —` or
places outside the vault. What changes is legibility. A bare traceback carries no signal that the
failure is intentional, so the reader's first hypothesis is a broken deploy, a missing dependency, or a
misconfigured sandbox, and time is spent debugging a fault that does not exist. This is strictly worse
after the Stage-B strict flip, which removes the burn-in fallback that currently makes such failures
survivable.

Exit **4** is reserved for "denied by design" so that a caller can distinguish it from a genuine fault
(exit 1). Read-only modes are unaffected and MUST remain available: `vault-render.py reconcile` still
reports drift, and `vault_naming.py --check` / `--check-strict` still gate commits.

#### Scenario: Render refused by the sandbox explains itself
- **WHEN** `vault-render.py render` attempts a `deploy_target` write and the OS sandbox refuses it with
  `EROFS`
- **THEN** it prints the blocked path, states that render is an operator-only path denied by design,
  notes that this is not a broken deploy, directs the reader to run it as the operator, and points at
  `reconcile` as the still-available read-only mode
- **THEN** it exits **4**, and no traceback is printed

#### Scenario: Schema regeneration refused by the sandbox explains itself
- **WHEN** `vault_naming.py` is run in emit mode and the write to
  `99-Operations/schemas/naming-rules.json` is refused with `EROFS`
- **THEN** it prints an equivalent operator-only message and exits **4**
- **THEN** `--check` and `--check-strict` are unaffected, so the commit gate continues to function

#### Scenario: A genuine I/O fault is not swallowed
- **WHEN** either script's write fails with an `OSError` whose `errno` is **not** `EROFS` — a full disk,
  a permission error, a missing parent
- **THEN** the exception propagates unchanged, so a real fault is never disguised as a governance denial

### Requirement: Template→Live Mirror (Repo→Live Apply)

The framework repo SHALL provide a deterministic, offline mirror tool that APPLIES the repo's
LOCKSTEP scaffold onto a deployed vault in the single direction governance allows — `vault-template/`
→ live, one way, never the reverse, never a delete — so a post-merge mirror is performed by one
reviewed invocation instead of a hand-composed `cp`. It is the write-capable counterpart to the
detection-only Template–Live Parity Check: parity ANSWERS "is the mirror complete?", this tool MAKES
it complete. It is a maintainer/mirror-time tool — NOT part of the deployed vault (which is standalone
and never references the repo), NOT a fleet script (no `deploy_target`, never rendered), and NOT a CI
gate.

- **Same manifest, no second source of truth.** The tool reads the existing
  `tools/template-sync-manifest.json` unmodified — the same `lockstep` prefixes and `exclude` list the
  parity check uses. The detector and the fixer MUST agree on one definition of "governed scaffold";
  a divergent manifest is a coordination hazard for no benefit. The shared tree-walk and comparison
  logic live in one module both tools call, never a forked second copy.
- **Direction is strictly repo → live, and the diff is computed, not enumerated.** The tool walks
  both trees itself and acts on what it finds — never on a file list typed from memory. For each
  LOCKSTEP file (excluding the manifest's `exclude`): `MISSING-IN-LIVE` → copy repo → live (creating
  parent directories); `DIFFERS` → overwrite live with the repo's bytes.
- **A live-only file is reported, never resolved.** A file present under a LOCKSTEP prefix in the
  live vault but absent from the template (`MISSING-IN-TEMPLATE`) means something happened outside
  governance; the tool prints it under its own header and leaves it untouched. Deleting it or adopting
  it as canonical is a human's decision, not a silent default.
- **Non-destructive by construction; recovery is git.** The tool never writes to the repo and never
  deletes; the worst case is overwriting a live file with the repo's already-reviewed bytes,
  recoverable from `git status` on the live vault. It never `git add`/commits — committing the mirrored
  change stays the operator's explicit INV-2 step (one commit, structured message).
- **Ends by re-deriving parity; evidence, not assertion.** After acting the tool re-walks both trees
  and prints the identical denominator'd tally the parity check prints (files checked, prefixes,
  excluded, drift) — never a bare success word. A second run against an already-mirrored state copies
  nothing and reports `0 drift` (idempotent).
- **Stdlib-only, offline, no LLM** — the INV-6 determinism posture at the mirror-time maintenance
  layer. Exit contract: `0` mirror complete (0 drift and no `MISSING-IN-TEMPLATE`) · `2` one or more
  `MISSING-IN-TEMPLATE` files found and left untouched (a human decides — distinct from a clean
  success) · `3` blocked (no resolvable live vault, or a manifest with no LOCKSTEP prefixes).

#### Scenario: An already-mirrored vault is a no-op
- **WHEN** `tools/template-mirror.py <VAULT_ROOT>` runs against a vault already byte-identical to the
  template's LOCKSTEP scaffold
- **THEN** it copies nothing, the filesystem is unchanged, it prints the denominator'd tally with
  `0 drift`, and exits `0`

#### Scenario: A missing lockstep file is mirrored forward
- **WHEN** a LOCKSTEP file exists in `vault-template/` but is absent from the live vault
- **THEN** the tool copies it repo → live (creating parent directories), re-derives parity showing
  `0 drift`, and exits `0`

#### Scenario: A differing lockstep file is overwritten with the repo's bytes
- **WHEN** a LOCKSTEP file exists in both trees with differing content (an incomplete or hand-edited
  mirror)
- **THEN** the tool overwrites the live copy with the template's bytes, re-verifies byte-identical,
  and exits `0` — it never writes to the repo

#### Scenario: A live-only lockstep file is reported, not deleted
- **WHEN** a file exists under a LOCKSTEP prefix in the live vault only, with no counterpart in the
  template
- **THEN** the tool does NOT delete or modify it, prints it under a distinct `MISSING-IN-TEMPLATE`
  header, and exits `2` — success and "found something needing a human" are visibly different states

#### Scenario: An excluded generated artifact is never touched
- **WHEN** a file listed in the manifest `exclude` (e.g. `naming-rules.json`, generated into the live
  vault by `vault_naming.py`) differs between the two trees
- **THEN** the tool leaves it untouched and does not count it in the checked/drift tally, matching the
  parity check's behavior exactly

#### Scenario: No resolvable live vault is a blocked run, not a false pass
- **WHEN** the tool is invoked with neither a live-vault argument nor `$VAULT_ROOT`, or against a path
  that is not a vault
- **THEN** it prints a `BLOCKED:` line and exits `3` — it never reports a mirror by silence

### Requirement: INV-6 Is Enforced by Static and Dynamic Checks

INV-6 SHALL be enforced by two complementary mechanisms rather than asserted in prose. Neither is
sufficient alone, and the incompleteness of each SHALL be stated wherever the result is reported.

**Static half.** `tools/inv6-offline-check.py` SHALL analyse every Layer-0 fleet note's code fence
and report any statically visible network call. Python SHALL be analysed by **AST**, not by text
search: an import of a network module or a `subprocess`/`os` invocation of a network binary or a
remote-contacting `git` subcommand is a violation, while a string literal *naming* such a verb is
not. Bash SHALL be analysed by a conservative command-position scan, which is the weaker half and
SHALL NOT be claimed as complete.

**The naming-versus-calling distinction is load-bearing, not a nicety.** The `outbound-publish-guard`
and `push-guard` notes implement the INV-14 rail, and their function is to *name* outward verbs
inside regex literals. A text-matching checker flags them — measured at 6 and 2 hits respectively —
and a control that fails the two most security-relevant scripts in the fleet on every run will be
disabled rather than obeyed.

**Indirection SHALL be reported, never ignored.** A dynamic import with a computed name, or a
`subprocess` call with a non-literal argv, SHALL be reported as **UNRESOLVED** and SHALL fail the
check. Silence there would be a claim the tool cannot support.

**Dynamic half.** CI SHALL run the fleet behaviour suite inside an unprivileged **network
namespace**, and SHALL prove the isolation before believing the result: the network MUST be shown
reachable outside the namespace and unreachable inside it, in the same run. If isolation cannot be
established the job SHALL **fail closed** — an unisolated run is not a weaker result, it is no
result.

**Scope.** The Layer-0 fleet only (`99-Operations/scripts/`). Repo-side maintainer tools are not
`[script]` operations; `ship-release.py` legitimately performs authenticated reads and INV-6 is not
engaged for it. Applying this check to `tools/` would manufacture violations out of correct
behaviour.

**Bound on what a pass means.** A green result means *no statically visible network call, and none
on the paths the suite exercises*. It does **not** mean the fleet is offline. Coverage is the limit
of the dynamic half, and it is thinnest where the network verbs live — the two INV-14 guards
currently have no tests. This bound SHALL NOT be dropped when the result is summarised.

#### Scenario: A fleet script that calls the network fails the static check

- **WHEN** a fleet note's Python imports a network module, or invokes a network binary or a
  remote-contacting `git` subcommand via `subprocess`/`os`
- **THEN** `inv6-offline-check.py` reports a VIOLATION naming the note, line, and reason, and exits non-zero

#### Scenario: A guard that names an outward verb is not flagged

- **WHEN** a fleet note contains an outward verb such as `git push` or `gh repo create` only as a
  string or regex literal — as the INV-14 guards necessarily do
- **THEN** the check reports no violation for it

#### Scenario: Indirection is reported rather than passed

- **WHEN** a fleet note performs a dynamic import with a computed name, or a `subprocess` call whose
  argv is not a literal
- **THEN** the finding is reported as UNRESOLVED and the check exits non-zero

#### Scenario: The dynamic check refuses when it cannot isolate

- **WHEN** the network is unreachable outside the namespace, or the namespace fails to block traffic,
  or no unprivileged network namespace is available
- **THEN** the job exits non-zero with an explicit "INVALID instrument" message and reports no verdict
  about INV-6

#### Scenario: The fleet suite completes with no network available

- **WHEN** the fleet behaviour suite runs inside a proven-isolated network namespace
- **THEN** it completes successfully, evidencing that the exercised paths make no network call
- **AND** the reported result carries its coverage bound

### Requirement: Pull Request Lifecycle Is Driven, Not Composed

The framework repo SHALL provide a guarded, **level-triggered** driver (`tools/pr-flow.py`) that
mechanizes the branch → push → pull request → checks → merge → branch-deletion lifecycle, and
contributors
SHALL walk it rather than hand-composing the sequence. The driver SHALL hold no state file,
re-deriving state from the world on every invocation, so that a missed step or a lost session is
corrected by the next pass rather than remembered. It SHALL NOT execute any outward mutation: it
SHALL emit the next single command verbatim and exit `2`, so that the invariant INV-14 outbound
guard — which
text-matches the command the caller runs — keeps firing on every outward step. The contract is
**challenge and response**: the driver challenges, the caller responds by running exactly the emitted
command, and the driver verifies on re-invocation that the action actually completed.

#### Scenario: The branch does not contain the base tip
- **WHEN** the driver runs on a branch that is not a descendant of the base's remote tip
- **THEN** it emits a rebase command and exits `2`
- **THEN** it does not emit any push, pull-request-create, or merge command
- **THEN** the emitted reason states that a pull request opened on a stale base reports checks that
  are not
  about its own change

#### Scenario: The base ref could not be refreshed
- **WHEN** the fetch of the base ref fails
- **THEN** the driver reports the base as UNVERIFIED and refuses to advance
- **THEN** it does not evaluate base-currency against the stale remote-tracking ref

#### Scenario: A local operation is still in progress
- **WHEN** `.git/rebase-merge`, `.git/rebase-apply`, `.git/MERGE_HEAD`, or `.git/CHERRY_PICK_HEAD`
  is present
- **THEN** the driver refuses with exit `1` and names the marker it found
- **THEN** the refusal states that a half-finished rebase silently blocks branch deletion later

#### Scenario: The remote branch has diverged from local
- **WHEN** the remote branch exists and its commit SHA (secure hash algorithm value, the identifier
  of a commit) differs from the local branch SHA
- **THEN** the emitted push command uses `--force-with-lease` and never a bare `--force`

#### Scenario: A local command is emitted while another branch is checked out
- **WHEN** the branch under test needs a local mutation and is not the checked-out branch
- **THEN** the driver emits the branch switch first and does not emit the mutation

#### Scenario: An emitted command is not executable as written
- **WHEN** a required input for the next command is absent
- **THEN** the driver refuses with exit `1` and names the missing input
- **THEN** it does not emit a command containing a placeholder

#### Scenario: A merge reports success but the branch survives
- **WHEN** the pull request is merged and the remote branch still resolves on origin
- **THEN** the driver emits the branch-deletion command rather than reporting the lifecycle complete
- **THEN** the emitted reason states that the deletion is not implied by the merge's success report

#### Scenario: The lifecycle has already completed
- **WHEN** the branch is absent both locally and on origin and its pull request is merged
- **THEN** the driver reports the lifecycle complete and exits `0`

### Requirement: The Remaining Route Is Shown Before The Next Step

The driver SHALL make the whole remaining route visible before any step is taken, so that planning
does not have to be reconstructed from recall. Every invocation SHALL print a route header naming
each step, its completion state, the current position, and the owner of the next step. The driver
SHALL additionally provide a `--plan` mode that reports every step with its executor, its authority,
its guard, and whether that guard was **measured** now or is **projected**. Command text SHALL be
emitted for the current step only; the driver SHALL NOT compose command text for a step whose
preconditions have not been reached, because an unreached step's command is a prediction and would be
indistinguishable in the output from a verified one.

#### Scenario: A route is requested before the lifecycle begins
- **WHEN** `--plan` is invoked
- **THEN** every remaining step is listed with its executor and its authority
- **THEN** each step is marked as measured or projected
- **THEN** no command text appears for any projected step

#### Scenario: A step is emitted
- **WHEN** the driver emits the next command
- **THEN** the output also carries the route header showing position and remaining steps

### Requirement: Authority Is Distinguished From Execution

The driver SHALL state, for every step, both **who executes it** and **whose authority permits it**,
and SHALL NOT conflate the two. Execution SHALL NOT be assigned to the operator wherever the agent is
measured capable of performing it; in that case the operator's role is **consent**, discharged
through the INV-14 outbound ask at the moment of execution. The consent mechanism SHALL be measured
by evaluating the outbound guard against the command in question, not declared from a stored table.
For any step whose authority rests with the operator, the driver SHALL print what is being authorized
in reviewable terms, and SHALL keep that statement short enough to be read rather than skipped.

#### Scenario: A command the agent can run requires the operator's authority
- **WHEN** the next command is a `git` push that the capability probe reports as runnable
- **THEN** the driver names the agent as executor and the operator as authority
- **THEN** it names the outbound ask as the mechanism by which that authority is discharged
- **THEN** it does not instruct the operator to run the command themselves

#### Scenario: A command the agent cannot run
- **WHEN** the next command requires a credential this process does not hold
- **THEN** the driver names the operator as executor
- **THEN** the reason states both the technical cause and the policy that keeps it so

#### Scenario: A push is emitted from a session whose working directory is a deployed vault
- **WHEN** any push command is emitted
- **THEN** it carries an explicit effective-target redirect
- **THEN** the emitted command is not a bare push that the outbound guard would resolve to the vault

### Requirement: Preconditions Are Re-Asserted At The Moment Of Mutation

Because an operator-executed command may be run long after the driver measured the state that
justified it, preconditions SHALL be re-asserted at the moment of mutation rather than only at the
moment of emission — the **time-of-check-to-time-of-use (TOCTOU)** gap SHALL NOT be left open. Where the
platform offers a server-side precondition, it SHALL be used in preference to a client-side check:
the merge SHALL be requested with the head SHA that the pull request must still match, so that a
raced merge is refused by the server rather than detected afterwards. A saved plan SHALL carry an
expiry and SHALL refuse to execute once stale, and consent recorded against one state SHALL NOT carry
over to a different one.

#### Scenario: The head moved between emission and execution
- **WHEN** a merge is requested with a head SHA that no longer matches the pull request
- **THEN** the merge is refused by the platform and does not occur
- **THEN** the driver reports the refusal as a raced state rather than a failure of the change

#### Scenario: A saved plan is run after the state changed
- **WHEN** a generated command file is executed and the asserted preconditions no longer hold
- **THEN** the assertion fails and the mutation does not run
- **THEN** the output states which precondition moved

#### Scenario: A saved plan is run after it expires
- **WHEN** a generated command file is executed past its stated expiry
- **THEN** it refuses and directs the caller to re-derive the plan

### Requirement: Asynchronous Platform State Is Awaited, Never Assumed

Platform state that is computed asynchronously SHALL be treated as **not yet ready** rather than as a
verdict. Absence of check runs SHALL NOT be read as checks passing, and an uncomputed mergeability
result SHALL NOT be read as mergeable. The driver SHALL provide a readiness probe that answers a
single named condition in one request with a meaningful exit code, so that a wait is testable rather
than described. The driver SHALL NOT itself block or sleep; waiting SHALL be expressed as
re-invocation. Polling SHALL respect the channel's published rate budget, SHALL honour the retry and
reset headers the platform returns, and the driver SHALL report the remaining budget before it is
exhausted, because a channel that runs out mid-lifecycle blinds every guard that depends on it.

Where a mutation's own response asserts the state it produced, that response SHALL take precedence
over a subsequent read of an eventually-consistent view. A write response is the answer of the
endpoint that performed the work; a read view is a weaker, later signal, and SHALL NOT be permitted to
overrule it. Two reads of the same fact through different endpoints MAY disagree, so the driver SHALL
NOT treat whichever endpoint it happens to consult first as authoritative.

While the driver is verifying a mutation, a read that returns no data SHALL be treated as **no answer
yet**, never as evidence that the mutation did not occur. A failed read, an empty result and a result
carrying data are three distinct outcomes and SHALL be distinguishable at the point of decision.

While the driver is verifying a **merge**, it SHALL NOT emit the command for any step that precedes
the merge in the lifecycle. Once a pull request has merged, the pre-merge guards describe a state the
branch has left, so the only correct outcomes are to confirm the merge or to report that it is not yet
visible. This restriction SHALL be scoped to the verification of a merge and SHALL be released as soon
as the merge is observed to have landed, so that the cleanup steps which legitimately follow are never
suppressed.

#### Scenario: No check runs have registered yet
- **WHEN** the head commit has zero check runs
- **THEN** the driver reports NOT READY and exits `2`
- **THEN** it does not report the checks as green and does not emit a merge

#### Scenario: Mergeability has not been computed
- **WHEN** the mergeability of the pull request is reported as uncomputed
- **THEN** the driver reports NOT READY and exits `2`
- **THEN** it does not treat an uncomputed result as mergeable

#### Scenario: A wait is required
- **WHEN** the driver reports that it is waiting on a platform condition
- **THEN** it names a probe that tests that condition and returns an exit code
- **THEN** it does not describe a wait that has no way to be tested

#### Scenario: The read budget is nearly exhausted
- **WHEN** the remaining rate budget falls below the cost of a further invocation
- **THEN** the driver reports the remaining budget and the time until it resets

#### Scenario: The mutation's response asserts a state the read view does not yet show
- **WHEN** the driver is verifying a merge and the captured response of that merge asserts it landed
- **THEN** the driver routes to the post-merge path on the strength of that response
- **THEN** it confirms against the read view with bounded lag tolerance rather than requiring the read
  view to agree before it will proceed

#### Scenario: Two endpoints disagree about the same fact
- **WHEN** one read reports a pull request merged and another read of the same pull request does not
- **THEN** the driver does not treat the endpoint it consulted first as authoritative
- **THEN** it reports the disagreement rather than silently adopting either answer

#### Scenario: A read returns nothing while a mutation is being verified
- **WHEN** the driver is verifying a mutation and the read returns an empty result
- **THEN** the driver treats the result as no answer yet
- **THEN** it does not conclude that the mutation did not occur

#### Scenario: A merge is being verified and the read view has not caught up
- **WHEN** the driver is verifying a merge and no read confirms it within the retry ladder
- **THEN** the driver reports WAITING and exits `2`
- **THEN** it emits no command belonging to any step that precedes the merge, including local commands
  such as a rebase

#### Scenario: The merge is confirmed and cleanup remains
- **WHEN** the driver observes that the merge has landed while verifying it
- **THEN** the restriction on emitting earlier steps is released
- **THEN** the cleanup steps that follow the merge are emitted normally

### Requirement: A Body-Derived Check Is Re-Triggered By A Push, Not A Re-Run

Where a required check reads the pull request body from the event payload, the driver SHALL state
that the payload is a snapshot taken at push time, and that a re-run replays the original payload.
Correcting the body SHALL therefore be followed by a push rather than a re-run. The pull request
title and body SHALL be brought current **before** the merge is emitted, and the correction SHALL be
made through the REST (Representational State Transfer) endpoint, because the convenience command
for editing a pull request can fail
silently behind a deprecated layer.

#### Scenario: A body-derived check is failing after the body was corrected
- **WHEN** the failing check derives its input from the pull request body
- **THEN** the driver prescribes a push and states that a re-run would replay the stale payload

#### Scenario: The body is corrected
- **WHEN** the pull request body or title requires correction
- **THEN** the emitted command uses the REST endpoint
- **THEN** the driver re-reads the field afterwards to confirm the change landed

### Requirement: Platform Capability Is Probed, Not Recalled

The driver SHALL provide a `--capabilities` mode that MEASURES, at invocation time, which channels
this process can actually use — state reads, `git` mutations, `gh` mutations, and the remaining read
budget — and reports the resulting division of labour. Ownership of a command SHALL NOT be asserted
from a stored table or from recollection, because the environment that determines it varies between
sessions and a stored answer preserves a wrong one.

#### Scenario: Capabilities are reported without network access
- **WHEN** a probe cannot reach its endpoint
- **THEN** the probe reports that capability as failed and exits `0`
- **THEN** it does not raise, because a probe that crashes teaches its caller to skip probing

#### Scenario: gh is unavailable but git is not
- **WHEN** `gh` cannot authenticate while `git` push and anonymous reads succeed
- **THEN** the report attributes `gh` mutations to the operator and `git` mutations to the agent
- **THEN** the report states the mechanism, not merely the verdict

### Requirement: GitHub Reads Degrade To An Unauthenticated Channel

Read-only GitHub tooling in this repo SHALL attempt the unauthenticated REST API (application
programming interface) before requiring
`gh`, and SHALL report the channel that answered alongside the data. A read that cannot be served by
any channel SHALL be reported as UNAVAILABLE and SHALL NOT be synthesised from another layer.

#### Scenario: A sandboxed agent reads pull request state
- **WHEN** `gh` cannot reach the operating system (OS) keyring and reports an authentication failure
- **THEN** `tools/pr-state.py` continues over the anonymous channel instead of exiting blocked
- **THEN** the output marks the report DEGRADED and names the channel that answered

#### Scenario: A GraphQL-only layer cannot be read
- **WHEN** the reporter is running on the degraded channel
- **THEN** the GraphQL-only layers are reported as UNAVAILABLE
- **THEN** no line attributes REST-sourced data to GraphQL

### Requirement: Branches Not Owned By This Repo Are Never Rewritten

The driver SHALL distinguish a branch that exists locally from one that exists only on the remote,
and SHALL NOT emit a rebase, a push, or a branch deletion for a remote-only branch. Bot branches are
maintained by the automation that created them, and rewriting or deleting one detaches it from that
automation or causes the pull request to be recreated. Locality SHALL be determined by an explicit
`refs/heads/` lookup, because a bare revision parse resolves a remote-tracking ref and reports a
foreign branch as local.

#### Scenario: A Dependabot pull request is driven
- **WHEN** the branch exists on origin but not under `refs/heads/`
- **THEN** the driver reports the branch as not local and skips the rebase and push guards
- **THEN** after the merge it leaves the remote branch in place

### Requirement: Stacked Pull Requests Are Retargeted Before The Parent Merges

The driver SHALL detect open pull requests whose base is the branch being merged, and SHALL refuse to
emit a merge while any exists, naming each child and prescribing the retarget. The driver SHALL NOT
couple branch deletion to the merge command: the convenience flag that does so both defeats the
platform's own retargeting of dependent pull requests and reports success when the deletion did not
occur. Branch deletion SHALL be a separate step whose effect is verified. Where the branch under test
is itself stacked, the driver SHALL say so.

#### Scenario: A pull request has children stacked on it
- **WHEN** an open pull request targets the branch being merged as its base
- **THEN** the driver refuses with exit `1` and names each child pull request
- **THEN** the refusal prescribes retargeting each child before this merge

#### Scenario: A merge is emitted
- **WHEN** the driver emits a merge command
- **THEN** that command does not also delete the branch
- **THEN** branch deletion is emitted separately and confirmed by a subsequent read

#### Scenario: The pull request under test is itself a stacked child
- **WHEN** the base is not the default branch
- **THEN** the driver reports that the pull request is stacked

### Requirement: Ambiguous Or Unmergeable Pull Request State Is Refused, Not Guessed

The driver SHALL query pull requests in every state rather than open ones alone, SHALL refuse when
more than one open pull request shares the head branch, SHALL refuse to advance a draft, and SHALL
refuse when the platform reports the pull request as not mergeable. A closed-unmerged pull request
SHALL be reported when a new one is proposed for the same branch, so that creating a replacement is a
stated consequence rather than an accident.

#### Scenario: Two open pull requests share a head branch
- **WHEN** more than one open pull request has the same head
- **THEN** the driver refuses with exit `1` and names each
- **THEN** it does not select one

#### Scenario: The pull request cannot be merged
- **WHEN** the platform reports the pull request as not mergeable
- **THEN** the driver refuses with exit `1`

#### Scenario: The pull request is a draft
- **WHEN** the pull request is marked draft
- **THEN** the driver refuses with exit `1`

#### Scenario: A closed-unmerged pull request exists for the branch
- **WHEN** no open pull request exists but a closed-unmerged one does
- **THEN** the driver reports it before emitting a create command

### Requirement: The Session Prime Measures Capability Before Asserting It

The cold-start prime SHALL run a capability probe and report its layers before the session makes any
claim about what it can read, write, or reach. A capability limit SHALL NOT be asserted from
recollection, from a stored path list, or from a single command's failure — a denial is evidence about
the command that failed, never about the class of channels it belongs to.

Write scope, `gh` credential, `git` credential, and network reachability are **independent layers**:
they SHALL be reported separately and none SHALL be inferred from another. The prime SHALL reference
the existing capability reporter rather than restate its checks, so that one system owns the criterion
and every consumer imports it.

Capability SHALL be distinguished from authority: a channel the agent can execute may still require
operator authorization (INV-14), and measuring the former never confers the latter.

#### Scenario: A credential error is not reported as a network verdict
- **WHEN** a `git` operation fails with a credential-storage-lock error naming a read-only filesystem
- **THEN** the prime reports a write-channel failure
- **THEN** it does not report the network, the remote, or any other credential channel as unavailable

#### Scenario: Capability is measured before it is asserted
- **WHEN** the session is asked what it can write or reach and the probe has not yet run
- **THEN** the probe is run and the answer is derived from its output
- **THEN** no capability claim is issued from a stored path list or from a previous session's memory

#### Scenario: A changed write scope contradicts recollection
- **WHEN** the configured write scope has changed since the claim was last true
- **THEN** the probe reports the current scope
- **THEN** the probed scope governs and the conflicting recollection is discarded, because a stored
  answer preserves a wrong one

#### Scenario: One channel fails while another succeeds
- **WHEN** `gh` mutations are unavailable because the operator credential is unreadable by the session
- **THEN** the report still attributes `git` mutations and anonymous reads to the channels that serve them
- **THEN** the session continues on the working channels instead of reporting itself blocked

### Requirement: A Change Is Archived On Its Own Branch

An OpenSpec change SHALL be archived on the feature branch that carries it, within the same pull
request that merges it. Archiving moves `openspec/changes/<slug>/` to
`openspec/changes/archive/<YYYY-MM-DD>-<slug>/`, applies the change's delta into the corresponding
`openspec/specs/` capability spec, and records the CHANGELOG entry. The archive step SHALL precede
opening the pull request.

Archiving is part of the change, not follow-up work. A change that merges unarchived leaves
`openspec/specs/` describing a state the repository has already left, and owes a second pull request to
close the gap.

Where another in-flight change carries a delta against the **same** capability spec, the archive SHALL
be deferred and applied in merge order. Applying two deltas to one spec file from independently
prepared branches allows the later archive to overwrite the earlier one's requirements without conflict
— the changes touch the same file but need not touch the same lines. This exception SHALL be recorded
with the name of the concurrent change it defers to, so that a second pull request is a stated
consequence rather than an unexplained one.

The convention SHALL be discoverable from the contributor documentation and SHALL NOT rest solely in
per-change task files, which are not read at the moment the decision is made.

Where this convention is restated or re-derived, the derivation SHALL be a pasted command transcript
over the merge history, not an inference from commit subjects: a dedicated archive commit does not
imply a separate pull request.

#### Scenario: A change is ready to merge
- **WHEN** a change's tasks are complete and its pull request has not yet been opened
- **THEN** the change directory is moved into the archive, its delta is applied to the capability spec,
  and the CHANGELOG entry is recorded on that same branch
- **THEN** the pull request that merges the change also carries its archive

#### Scenario: A concurrent change touches the same capability spec
- **WHEN** another in-flight change carries a delta against the same capability spec
- **THEN** the archive is deferred and applied in merge order
- **THEN** the deferral names the concurrent change, and the resulting second pull request is recorded
  as the accepted cost of the exception

#### Scenario: A change merged without being archived
- **WHEN** a change reaches `main` with no archive
- **THEN** a second pull request to archive it is owed and is tracked as owed
- **THEN** the capability spec is understood to be lagging the repository until that pull request lands

### Requirement: An Architecture Decision Record Citation Resolves

Architecture Decision Records (ADRs) SHALL be numbered contiguously from `0001` with no gap and no
duplicate. Continuous integration (CI) SHALL derive the expected set from the records present rather
than from a literal range, because a hardcoded range is correct only on the day it is written and
passes silently thereafter while validating a shrinking fraction of the corpus.

Every ADR identifier cited anywhere in the repository SHALL resolve to a record that exists. A
citation is an assertion that a decision was recorded; where the record does not exist, the citation
documents a deliberation that no reader can inspect and cannot be distinguished from one that never
happened.

A citation to a record that does not yet exist SHALL be permitted **only** within a change directory
under `openspec/changes/`, excluding its archive. A change directory is a proposal and is forward-looking
by nature; specifications, workflow configuration, README, contributor documentation, and archived
changes are records, and a record SHALL resolve. An archived change is a record for this purpose:
a forward reference that was permitted while the change was live SHALL fail once it is archived,
because by then the record it promised is owed.

The check SHALL report the citing file and line for each unresolved identifier, because an identifier
alone does not locate the assertion that must be corrected.

#### Scenario: An identifier is cited in workflow configuration but no record exists
- **WHEN** CI configuration cites an ADR identifier that resolves to no file
- **THEN** the check fails and names the citing file and line
- **THEN** the failure is reported as an unresolved citation, distinctly from a numbering gap

#### Scenario: A live change declares a record it owes
- **WHEN** a change directory outside the archive cites an ADR identifier that does not yet exist
- **THEN** the check passes for that citation
- **THEN** no annotation is required on the citation, because its location establishes that it is a proposal

#### Scenario: A change carrying a forward reference is archived
- **WHEN** a change directory containing an unresolved ADR citation is moved into the archive
- **THEN** the check fails for that citation
- **THEN** the failure names the record that is now owed

#### Scenario: A record is added out of sequence
- **WHEN** a new ADR is added whose number leaves an earlier number unused
- **THEN** the contiguity check fails and names the missing number
- **THEN** the result does not depend on any literal range held in the check itself

### Requirement: The Route Is Pre-Flighted Before A Mutation

The driver SHALL answer, before any outward mutation, every route step that is decidable from
repository state, and SHALL report those answers together. A question the repository can already
answer about itself SHALL NOT be deferred to the platform, because the platform answers it only after
a push has been spent and, for a body-derived gate, only after a further push.

A pre-flight SHALL judge each step with the **shipped** check rather than a restatement of it: the
check's own text SHALL be executed. A second copy of a rule drifts from the first, and the pre-flight
must move when the rule moves rather than preserving an answer the rule no longer gives.

A step whose outcome is held by the platform — the existence of a pull request, pull requests stacked
on the branch, the merge itself, and any decision made by a repository ruleset the session cannot
read — SHALL be reported as not locally decidable, and SHALL NOT be predicted.

A check that **could not run** in the current environment SHALL be reported distinctly from a check
that **failed**, and SHALL NOT be counted as a finding. Reporting an environment limitation as a
defect is the same non-result-as-a-result error the pre-flight exists to catch, and a pre-flight that
raises false findings will be disregarded, taking its true findings with it.

The pre-flight SHALL determine whether each live change can be archived on its own branch by
**simulating** the archive and running the archive-sensitive checks against the simulated state,
rather than by reasoning about the change's contents. Where a change cannot archive, the pre-flight
SHALL name the artifact that blocks it.

Where more than one live change carries a delta against the same capability spec, the pre-flight SHALL
report that the archives are ordered, and SHALL name the changes involved, because two deltas applied
to one spec file can overwrite each other without ever conflicting.

#### Scenario: A declared scope does not cover the diff
- **WHEN** a pre-flight runs against a branch whose diff exceeds the scope declared in its body
- **THEN** the undeclared paths are named before the branch is pushed
- **THEN** the report distinguishes the removed and added sides of a rename, both of which the diff carries

#### Scenario: A change cites a record it does not ship
- **WHEN** a live change's archived form would fail an archive-sensitive check
- **THEN** the pre-flight reports that the change must defer its archive
- **THEN** it names the artifact that must exist first, rather than reporting only that the check failed

#### Scenario: Two live changes touch one capability spec
- **WHEN** more than one live change carries a delta against the same capability spec
- **THEN** the pre-flight reports the archives as ordered and names the changes
- **THEN** the later change is directed to rebase before archiving

#### Scenario: A check cannot run in this environment
- **WHEN** a check fails because the environment cannot execute it rather than because the repository is wrong
- **THEN** the pre-flight reports it as not runnable here and names the limitation
- **THEN** the result is excluded from the findings and does not fail the pre-flight

#### Scenario: A step is decided by the platform
- **WHEN** a route step's outcome is held by the platform rather than by repository state
- **THEN** the pre-flight reports it as not locally decidable
- **THEN** it does not report a predicted outcome for that step

### Requirement: The Capability Probe Measures A Declared Estate

The capability probe SHALL take its subjects from **declared roots**, and SHALL NOT derive its subject
from the working directory. The estate has known members whose locations are configuration, not
discoveries: the vault (`VAULT_ROOT`) and the framework repository (`FRAMEWORK_ROOT`). A probe that
infers its subject from where the shell happens to be will silently measure the wrong thing and
report the result with the same confidence as a correct one.

Each member SHALL be evaluated against **that member's expected state**, not against a single
repository-shaped template. A finding SHALL be a deviation from what that member is supposed to be.

The vault is private by default and holds no remote (INV-14). Absence of a remote in the vault SHALL
be reported as the invariant **holding**, and SHALL NOT be reported as a failed channel. Where a
remote is **present** on the vault, the probe SHALL report a **violation** naming it, because that is
the condition INV-14 exists to prevent.

The trigger SHALL be presence, not demonstrated pushability. Establishing that a remote accepts a push
means attempting one from the vault — the act INV-14 forbids, and which the outbound guard refuses. A
probe may not commit the breach it is checking for. Presence is also the earlier signal: a remote that
lacks credentials today is one credential away from being pushable, and the invariant is already
broken at the moment the remote exists.

Where `FRAMEWORK_ROOT` is not declared, the estate SHALL be reported as one member: the vault layers
measured as normal, and every framework-repository layer reported `UNDECLARED`, distinctly from
`FAILED`. A deployed vault without the framework repository alongside it is a supported configuration,
not an error state.

The probe SHALL report which roots it measured, so that its output cannot be read as describing a
subject it did not examine.

The probe SHALL verify that the vault's protected subtrees are actually protected, by **attempting a
write** into each subtree governed by an autonomy ban (INV-4, INV-5) and reporting whether that write
was refused. A protection that is assumed rather than exercised is not evidence, and the guard is
enforced outside the vault's own filesystem, so it can lapse with no event the vault can observe. This
attempted write is operator-specified startup verification, and is therefore not an autonomous write.

A refused write SHALL be reported as the protection holding. A write that **succeeds** SHALL be
reported as a protection failure, because the subtree is writable and the invariant is resting on
nothing for the remainder of the session.

Where the probe's own write succeeds, the probe SHALL attempt to remove the artifact it created and
SHALL check the result of that removal. Where removal fails, the probe SHALL report the absolute path
of the residue distinctly from the protection failure itself, because an artifact left inside a
protected subtree is a second and separate defect.

Every failing outcome of this verification SHALL be reported together with the operator action it
calls for. A protection check that reports only a verdict obliges its reader to derive the remedy at
exactly the moment the governing assumption has been shown false.

Modes that operate on a single repository — pull-request routing, readiness, and precondition
assertion — SHALL continue to derive their subject from the working directory, which is correct for
them.

#### Scenario: The probe is run from the vault
- **WHEN** the capability probe runs with the working directory inside the vault
- **THEN** it measures the declared estate roots rather than the working directory
- **THEN** the framework-repository channels are measured against `FRAMEWORK_ROOT`, not against the vault

#### Scenario: A remoteless vault is reported
- **WHEN** the vault has no configured remote
- **THEN** the probe reports INV-14 as holding
- **THEN** it does not report a failed remote read, a failed push, or an unresolved repository slug

#### Scenario: A vault has acquired a remote
- **WHEN** the vault has any configured remote
- **THEN** the probe reports an INV-14 violation naming the remote
- **THEN** the violation is reported as a finding, not as a working capability
- **THEN** the probe does not attempt a push to establish whether the remote would accept one

#### Scenario: The framework repository is not declared
- **WHEN** `FRAMEWORK_ROOT` is unset
- **THEN** every framework-repository layer is reported `UNDECLARED`
- **THEN** no layer is reported `FAILED`, because an absent declaration is not a measured failure

#### Scenario: A protected subtree refuses the probe's write
- **WHEN** the probe attempts a write into a subtree under an autonomy ban and the write is refused
- **THEN** the protection is reported as holding for that subtree
- **THEN** no operator action is prescribed, because this is the expected result

#### Scenario: A protected subtree accepts the probe's write
- **WHEN** the write into a subtree under an autonomy ban succeeds
- **THEN** the probe reports a protection failure naming the subtree
- **THEN** the report states that the invariant is unenforced for the session and names the operator
  action, because the guard is enforced outside the vault and cannot be repaired from within it

#### Scenario: The probe cannot remove the artifact it created
- **WHEN** the probe's write succeeds and the removal of that artifact fails
- **THEN** the probe reports the residue and its absolute path separately from the protection failure
- **THEN** the report names the removal the operator must perform and the check confirming the residue
  was never committed

### Requirement: A Probe Reports Diagnoses, Not Internal Errors

A probe SHALL report, in its state column, a diagnosis of the channel it measured. Text produced by
the language runtime — exception messages, formatting errors, tracebacks — SHALL NOT be presented as a
channel's state, because a reader cannot distinguish a broken channel from a broken probe, and will
attribute the defect to the environment.

A failed precondition SHALL be reported as a precondition failure and SHALL NOT be routed through the
path that reports channel results. Where a guard substitutes a placeholder for an unavailable value,
that placeholder SHALL NOT reach code that assumes the value was obtained.

Where a probe quotes the output of a subprocess it invoked, it SHALL attribute the quotation to that
subprocess and SHALL select the line by relevance to the cause. Selecting a line by position yields
trailing remediation boilerplate in place of the diagnosis, and an unattributed fragment reads as
corrupted output.

#### Scenario: A required value could not be resolved
- **WHEN** an identifier a channel depends on cannot be resolved
- **THEN** the probe reports the unresolved precondition and names it
- **THEN** it does not attempt the dependent channel and does not report that channel as failed

#### Scenario: The probe's own code raises
- **WHEN** an exception is raised inside the probe rather than by the channel under test
- **THEN** the report distinguishes a probe defect from a channel result
- **THEN** no runtime exception text appears in a state column

#### Scenario: A subprocess error is quoted
- **WHEN** the probe quotes stderr from a command it ran
- **THEN** the quotation is attributed to that command
- **THEN** the line quoted is the one naming the cause, not the last line of the output

### Requirement: A Diff Touching A Protected Element Declares Its Constitutional Impact

A change whose diff modifies a specification file carrying a `protects:` frontmatter tag SHALL carry
an explicit declaration of that change's constitutional impact, and continuous integration SHALL
refuse a change that supplies none.

The subject set SHALL be determined by reading **YAML frontmatter**, and SHALL NOT be determined by
matching the string `protects:` anywhere in a file's contents. Documentation, changelogs, workflow
definitions, architecture decision records and the constitution itself all quote the tag in prose; a
substring match refuses them all, including the file that implements the gate and the constitution the
gate exists to protect.

The declaration SHALL enumerate the protected identifiers that the touched files carry, and SHALL
state which of those identifiers, if any, the change **overrides**. Where the declaration states that
no identifier is overridden, the gate SHALL pass.

The gate SHALL NOT evaluate whether a declaration is correct. Determining whether a change overrides a
principle is the human judgement the Informed-Upheaval Protocol reserves, and a gate that guessed at it
would refuse legitimate work while lending false authority to its own verdict. The gate establishes
that the question was answered in writing and that the answer is in version control; it establishes
nothing further, and its reporting SHALL NOT imply otherwise.

Where the declaration names one or more overridden identifiers, the gate SHALL require a
`constitution-override` change directory in the same diff, carrying the four gate sections the
protocol mandates, and SHALL refuse the change where it is absent.

The gate SHALL NOT refuse a change that carries a complete `constitution-override`. A guard that
refuses the ceremony it demands teaches its reader to bypass it, and would discredit the protocol it
serves.

A change that synchronises a delta into a specification file as part of archiving SHALL pass where the
declaration is present in the change directory being archived, whether that directory is read at its
live path or at its archived path. Archiving moves a directory and applies its delta, so it touches
protected specifications by construction and is a routine ceremony step rather than a constitutional act.

A refusal SHALL name the protected files the diff touched, the identifiers those files carry, and the
declaration the change is missing. A guard that reports only a verdict obliges its reader to derive the
remedy, which is the condition under which readers learn to route around guards.

#### Scenario: A protected specification is modified with no declaration
- **WHEN** a diff modifies a specification file carrying a `protects:` frontmatter tag
- **AND** the change supplies no constitutional-impact declaration
- **THEN** the gate refuses the change
- **THEN** the refusal names the touched file, the identifiers it carries, and the declaration required

#### Scenario: A declaration states that nothing is overridden
- **WHEN** a diff modifies a protected specification
- **AND** the declaration names no overridden identifier
- **THEN** the gate passes
- **THEN** the gate does not evaluate whether the declaration is accurate

#### Scenario: A declaration names an overridden identifier
- **WHEN** a declaration names one or more overridden identifiers
- **AND** the diff carries no `constitution-override` change directory
- **THEN** the gate refuses the change
- **THEN** the refusal names the identifiers claimed as overridden

#### Scenario: A constitution-override change is evaluated by the gate
- **WHEN** a diff carries a `constitution-override` change directory with its four gate sections present
- **THEN** the gate passes
- **THEN** the gate does not refuse the change on account of the protected files that change touches

#### Scenario: A file quotes the protects tag in prose
- **WHEN** a diff modifies a file that contains the string `protects:` in its body but carries no
  `protects:` frontmatter tag
- **THEN** the gate does not fire
- **THEN** the constitution, the changelog, the contributing guide and the workflow definitions are
  outside the subject set on this basis

#### Scenario: An archive synchronises a delta into a protected specification
- **WHEN** a diff moves a change directory into the archive and applies its delta into a protected
  specification
- **AND** the archived change directory carries a constitutional-impact declaration
- **THEN** the gate passes
- **THEN** the declaration is located whether the change directory is read at its live or archived path

### Requirement: A Constitutional Declaration Is Read From The Tree, Not The Pull-Request Body

The constitutional-impact declaration SHALL be read from a file in the change's own diff, and SHALL
NOT be read from pull-request metadata.

A pull-request body may be edited after its checks have reported, and editing it does not re-evaluate
them. A declaration held there can therefore be made to say something other than what was verified,
while the verification remains green. For a claim about constitutional impact this is disqualifying:
the record and the check must be the same object, and that object must be versioned.

The declaration SHALL be discoverable without network access and without a pull request in existence,
so that the gate can be evaluated locally before a change is pushed.

#### Scenario: The declaration is present only in the pull-request body
- **WHEN** a change places its constitutional-impact declaration in the pull-request body alone
- **THEN** the gate refuses the change
- **THEN** the refusal states that the declaration must be committed to the tree

#### Scenario: The gate is evaluated locally before any pull request exists
- **WHEN** the gate runs against a local branch with no pull request open
- **THEN** it reaches the same verdict it would reach in continuous integration
- **THEN** it requires no network access to do so

#### Scenario: A declaration is amended after review
- **WHEN** a committed declaration is amended
- **THEN** the amendment appears in the diff under review
- **THEN** continuous integration re-evaluates the gate against the amended declaration

### Requirement: An Outward Command Is Checked Against The Driver's Emission

Where a lifecycle driver emits a command for execution, it SHALL record that command, together with
the step and branch it was derived for and an expiry, in a location the outbound guard can read
without network access.

The outbound guard SHALL classify an outward command by its **effective target**, resolved from the
command text as it already resolves a leading directory change, an explicit repository argument, and
an explicit remote-repository selector. Three zones SHALL be distinguished: the deployed vault, a
repository whose lifecycle a driver governs, and everywhere else.

Where the effective target is the deployed vault, the existing refusal SHALL apply unchanged. Where
the effective target is elsewhere, the existing confirmation SHALL apply unchanged, so that a one-off
outward command against an ungoverned repository remains possible without a driver.

Where the effective target is a governed repository and the command is **byte-identical** to a live
recorded emission for the current branch, the guard SHALL allow it without a confirmation prompt.
Where it is not, the guard SHALL raise the existing confirmation and SHALL additionally report the
difference between the command presented and the command recorded.

**The record SHALL only ever downgrade a confirmation to an allowance. It SHALL NOT create a
refusal.** Every failure of the mechanism — an absent record, an expired record, a record written for
another branch, an unparseable record, or a fault in the comparison — SHALL fall through to the
confirmation that is raised today. A control that can only relax an existing prompt cannot make the
system stricter than it was, and this property is what permits it to ship without a burn-in period.

A recorded emission SHALL expire, and SHALL be discarded when the lifecycle it belongs to completes.
A record that outlives its step is an authorisation left lying where a later, different command can
match it.

Reporting a difference SHALL name what differs rather than merely stating that something does.
Mangled commands differ in ways the author cannot see by re-reading — an unexpanded variable, a
prefix that displaces a leading directory change — and a guard that reports only a mismatch obliges
its reader to find the cause at the moment they have already demonstrated they cannot.

#### Scenario: The emitted command is run verbatim
- **WHEN** an outward command targets a governed repository
- **AND** it is byte-identical to a live recorded emission for the current branch
- **THEN** the guard allows it without raising a confirmation
- **THEN** it reports which recorded step authorised it

#### Scenario: The emitted command is run with modifications
- **WHEN** an outward command targets a governed repository
- **AND** a live emission exists but the command text differs from it
- **THEN** the guard raises the confirmation that is raised today
- **THEN** it reports the difference between the presented and recorded commands

#### Scenario: No emission has been recorded
- **WHEN** an outward command targets a governed repository
- **AND** no live recorded emission exists
- **THEN** the guard raises the confirmation that is raised today
- **THEN** it does not refuse the command

#### Scenario: An outward command targets an ungoverned repository
- **WHEN** an outward command's effective target is neither the vault nor a governed repository
- **THEN** the guard behaves exactly as it does today
- **THEN** no recorded emission is required for it to proceed

#### Scenario: An outward command targets the vault
- **WHEN** an outward command's effective target is the deployed vault
- **THEN** the guard refuses it
- **THEN** the presence or absence of a recorded emission does not change that outcome

#### Scenario: The record is expired or written for another branch
- **WHEN** a recorded emission exists but has expired, or names a branch other than the current one
- **THEN** the guard treats it as absent
- **THEN** the confirmation raised today is raised

### Requirement: A Downgrade Record Is Forgeable And Says So

The recorded emission SHALL be writable by the same agent whose commands it governs, and this
limitation SHALL be documented wherever the mechanism is described.

The mechanism therefore protects against **error**, not against **intent**. A mistaken or mangled
command does not also produce a matching record, which is the property the mechanism relies on; an
agent that chose to write its own record could authorise its own command. This is consistent with the
outbound rail's stated posture — a safe default and a governed guarantee, not a physical
impossibility, and a tripwire for a cooperating agent.

It is stated as a requirement rather than left as a remark because an unstated limitation on a control
is indistinguishable from a control that does not have it. This repository has previously had to
retract enforcement claims that described protection it did not possess, and the correction is to
record the gap where the mechanism is described, not to describe the mechanism more favourably.

An allowance granted by this mechanism SHALL therefore be reported as a match against a record, and
SHALL NOT be reported as an authorisation, an approval, or a verification.

#### Scenario: The mechanism is described in documentation
- **WHEN** the emission record is described in a specification, decision record, or script note
- **THEN** the description states that the record is writable by the agent it governs
- **THEN** it states that the mechanism addresses error rather than intent

#### Scenario: An allowance is reported to the reader
- **WHEN** the guard allows a command because it matched a recorded emission
- **THEN** the report states that the command matched a record
- **THEN** the report does not claim the command was authorised or verified

### Requirement: A Capability State Is A Single Word Naming What Was Found

Every state a capability report emits SHALL be a single word containing no whitespace, so that a
consumer can compare it without parsing prose.

Every such state SHALL be declared as a named constant in one place. States inlined at their print
sites have no discoverable legal set, and a new state can then be introduced by a typo without any
check observing it. An automated check SHALL assert that every state the report emits belongs to the
declared set.

A state SHALL name **what was found in this process**, and SHALL NOT name what is possible in the
world. The test is whether the token could be falsified by something outside the process that emitted
it: a state that could be is the wrong word. A capability report is read at the moment its reader has
no other information, so a token that overstates its own scope is not merely imprecise — it is the
specific error such a report exists to prevent.

Where a row reports a credential, the states SHALL distinguish three conditions: a usable credential,
the absence of a usable credential, and the absence of the tool itself. The first two describe the
credential; the third describes the tool, and SHALL be understood to leave the credential state
**unknown** rather than negative. A report that collapses the third condition into the second obliges
its reader to distinguish two different remedies from one token.

A row SHALL be named for what it measures rather than what may be inferred from it. Where a check
inspects a credential, the row names the credential; whether an operation is thereby possible is a
conclusion, and belongs in the column that already records who may run the operation.

Retiring a state token SHALL be preferred to narrowing one. A token reused with a tighter meaning
makes every previously-emitted transcript ambiguous, because nothing in the older output records which
meaning was in force.

#### Scenario: A state is emitted as a single word
- **WHEN** the capability report emits any state
- **THEN** that state contains no whitespace
- **THEN** it is one of the declared state constants

#### Scenario: An undeclared state is introduced
- **WHEN** a state is emitted that is not in the declared set
- **THEN** the automated check fails
- **THEN** the failure names the offending state

#### Scenario: A credential row reports three distinguishable conditions
- **WHEN** the tool is present and its credential is usable
- **THEN** the state reports the credential as usable
- **WHEN** the tool is present and no usable credential exists
- **THEN** the state reports the credential as absent
- **WHEN** the tool itself is not present
- **THEN** the state reports the tool as absent, distinctly from the credential case

#### Scenario: A row is named for its measurement
- **WHEN** a row is produced by inspecting a credential
- **THEN** the row is named for the credential
- **THEN** it is not named for an operation whose possibility is inferred from it

#### Scenario: A state token would be falsified from outside the process
- **WHEN** a candidate state asserts what is possible rather than what was found
- **THEN** it is rejected as a state name
- **THEN** the finding is expressed as what this process observed

### Requirement: A Capability Report Distinguishes Inspection From Attempt

For every channel it reports, the capability report SHALL record whether the channel was **attempted**
or whether a **precondition was inspected**, and SHALL make that distinction visible to its reader.

Where a channel was attempted, the report SHALL name the channel actually exercised. Two mechanisms
may carry the same label while traversing different paths — an operation invoked as a subprocess does
not necessarily cross a guard that inspects a shell command line — and a report that names only the
outcome cannot expose that divergence. Naming the exercised channel makes a future divergence visible
in the output rather than discoverable only by reading the source.

The report SHALL NOT encode evidence, channel, or reason inside a state token. A state answers what was
found; how it was found is a separate fact, and combining them produces a value that is neither
readable as a word nor parseable as a field.

The report SHALL offer a machine-readable form. A fixed-width table is a presentation, and a consumer
that parses it binds to column widths, so every cosmetic change becomes a breaking one. With a
machine-readable form available, the human table remains free to change.

#### Scenario: A channel that was exercised is reported as attempted
- **WHEN** the report includes a channel it actually exercised
- **THEN** the evidence records that the channel was attempted
- **THEN** the evidence names the channel that was exercised

#### Scenario: A channel whose precondition was inspected is not reported as attempted
- **WHEN** the report includes a channel for which only a precondition was read
- **THEN** the evidence records an inspection rather than an attempt
- **THEN** the reader can distinguish it from a channel that was exercised

#### Scenario: A consumer reads the report without parsing the table
- **WHEN** the report is requested in its machine-readable form
- **THEN** each channel is emitted with its state, its runner, its authority, and its evidence as
  separate fields
- **THEN** no field requires splitting a human-formatted line to recover

