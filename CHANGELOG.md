<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

This changelog is generated from completed OpenSpec changes in
`openspec/changes/archive/`. Each entry corresponds to an archived change.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- **Template–live parity check** (`add-template-parity-check`): a repo-owned, stdlib-only,
  detection-only tool (`tools/template-parity.py` + `tools/template-sync-manifest.json`) that verifies
  a deployed vault's LOCKSTEP scaffold (`99-Operations/scripts/`, `99-Operations/schemas/`) is
  byte-identical to what `vault-template/` ships — the mirror-completeness axis `reconcile` never
  covered (`reconcile` is note → `~/bin`; this is template → live). Byte-exact and bidirectional per
  lockstep prefix, with a manifest `exclude` for vault-generated artifacts (`naming-rules.json`); it
  prints the count of files checked and never auto-fixes (INV-3 posture). Motivated by three unfinished
  applies caught by hand on 2026-07-17. Repo-only (the deployed vault stays standalone, F15); not a CI
  gate (CI has no live vault). `maintenance` spec: +1 Requirement.

## [0.1.26] - 2026-07-17

### Changed
- **The ≥3-token naming floor is now enforced, not merely documented** (`enforce-naming-token-floor`,
  ADR-0030, completing **ADR-0015**): `vault_naming.py` gains `--check-strict FILENAME` (exemption-aware:
  `is_exempt` → `validate_name` → `slug_pattern` → `has_min_hyphen_tokens`); the commit gate calls it on
  the basename; the refine executor pre-flights the floor **before any write**; the linter's staged
  `elif` is switched on and the floor extends to Treasury stems and effort folder slugs. `--check STEM`
  keeps its contract, so no existing caller moves implicitly. `min_hyphen_tokens: 3` and `slug_pattern`
  are **unchanged** — this adds no rule, it switches on ADR-0015's.

  ADR-0015 deferred enforcement in June "gated on full conformance" and named it *"a separate later
  change"* — **which was never written**. Until now the whole pending item was one ADR sentence and three
  commented-out lines; **`has_min_hyphen_tokens` had no production caller at all**, so the rule was
  enforced nowhere. The precondition is met: **118 live `.md`, 15 exempt, 103 subject, 0 failing**. Every
  family conformed by hand exactly as ADR-0015 predicted, and nobody flipped the switch, because the
  thing that would have noticed was a comment.

  **Live constraint:** newly *created* content names must carry ≥3 kebab tokens. No existing artifact is
  affected — 0 offenders, and the gate is `--diff-filter=AR` regardless.

### Fixed
- **Refine executor could be stranded half-applied** (ADR-0030, found by two *pre-existing* tests failing
  once the gate went live): the executor writes `40-Treasury/<stem>.md` and *then* commits, so a sub-3
  stem passing pre-flight would be written and then blocked at commit. Its pre-flight now rejects the
  floor violation at the boundary, keeping *"reject at the boundary, no Treasury write"* true.

## [0.1.25] - 2026-07-17

### Added
- **`PILLARS` tokens are validated as kebab slugs** (`enforce-pillar-slug-tokens`, ADR-0029): the linter
  validates the vocabulary at the point it resolves, before the frontmatter loop, using the existing
  `is_valid_slug()`. A malformed vocabulary exits immediately rather than cascading into a per-note
  pile-up. The ≥3-token floor is deliberately **not** applied — it governs `.md` stems, not name
  fragments, so `mental` stays valid.

### Changed
- **Pillar naming rule stated and demonstrated** (ADR-0029): each pillar is **one** lowercase kebab slug;
  whitespace separates. A multi-word pillar is one hyphenated token (`mental-health`), never two words.
  `config.defaults.env`, `config.env.example`, and `docs/USING-THIS-TEMPLATE.md` now show the
  two-words-vs-one-token contrast explicitly, label the example default as **six** pillars, and tell
  adopters to **pin `PILLARS` in their private `config.env`** — unpinned, they inherit the framework's
  *example* default and a public-repo edit would silently re-pillar their vault. **The pillar set did not
  change** (value verified byte-identical).

  Origin: an agent read the whitespace-delimited value during session bootstrap and reported six pillars
  as five, welding `mental` and `health` into one. `vocab()` was never wrong — the format let a *reader*
  invent a boundary the format forbids, and the prohibition lived in a comment enforced by nothing. The
  `;`-delimiter fix was rejected: a pillar is interpolated into `<pillar>-domain-index.md`, so literal
  spaces would need a slug transform in every consumer plus a permanent display/slug identity split.
  Demarcation comes from making the **token** self-delimiting instead.

  **Sacrifice:** literal spaces in pillar names are permanently unavailable. Display forms alias at the
  link — `[[mental-health-domain-index|Mental Health]]`, the pattern `home-master-index.md` already uses.

## [0.1.24] - 2026-07-17

### Removed
- **Effort projections retired** (`retire-effort-projections`, ADR-0028): `kanban-render-script`
  (`~/bin/vault-kanban-render.py`, `10-Logbook/kanban.md`) and `dig-rollover-script`
  (`~/bin/vault-rollover.py`, daily `## Carry-over`) leave the fleet — 17 scripts → 15. Neither had a
  consumer: the board was rendered 4 times in 32 days and read 0 (not Obsidian-Kanban format, no
  plugins installed); the carry-over wrote 12 unchanging links a day until it read as noise. The vault
  does not project effort state — that lens is delegated to the harness.

### Changed
- **Cadence retracted from the framework** (ADR-0028): no script declares `runtime: cron` or a
  `schedule:`; `cron`/`schedule` leave `note-frontmatter-schema.md`; `docs/USING-THIS-TEMPLATE.md`
  Step 5 no longer instructs installing a crontab. The vault is a **self-priming pump, not a driven
  one** — `render` deploys code and never installed schedules, so the declared cadence was a
  decoration nothing honoured. Scripts run bare, on demand, by an actor who chose to run them.
- `maintenance` spec: MODIFIED *Script Inventory* (+ a scenario recording that a retirement must
  delete its deploy target explicitly — `reconcile` iterates notes, so an orphaned `~/bin` artifact is
  invisible to drift detection), *One Mutation One Commit*, *Daily Close Lifecycle*, *Shared Fleet
  Plumbing* — re-exemplified with surviving fleet members; no rule weakened.
- `access-control` spec: MODIFIED *OS/Harness-Enforced Agent Write Scope* — `10-Logbook/kanban.md`
  drops from the structured-tool deny enumeration (the whole of `10-Logbook/` remains denied).

## [0.1.23] - 2026-07-14

### Added
- **GitHub Release object per version tag** (change `release-object-per-tag`; conforming override,
  additive — Gate-4 sign-off recorded in the proposal). The ship ceremony now documents and mandates
  tag → `gh release create --verify-tag --latest` → `gh release view` parity check → mirror, so a tag
  can never again strand without its Release (the drift that pinned the Releases page at v0.1.13 while
  tags ran to v0.1.22). Documented in `CONTRIBUTING.md` and `AGENTS.md`.

### Changed
- **INV-14 outbound guard made target-aware and gap-closed** (ADR-0027; conforming — the Safety band is
  tightened, nothing relaxed). `outbound-publish-guard.py` now judges "targets the vault" by the
  command's *effective target* (`cd` / `git -C` / `gh -R`), not the shell's reported cwd — removing the
  false HARD-DENY that blocked every legitimate publish to the sibling framework repo from a
  vault-rooted session. It also raises the ASK **hard stop** on **any** non-denied outward op (now
  including a plain `git push`, and `git -C <path> push`), closing a gap where a push could defer
  unprompted. Vault-outward commands are still hard-denied. Mirrored byte-identically across the hook's
  three homes (repo, vault-template, literate meta-script note).

## [0.1.22] - 2026-07-14

### Added
- **Scope-review CI gate** (change `add-overreach-scope-review`; conforming override, additive —
  Gate-4 sign-off recorded in the proposal). Every PR now declares its authorized surface as a
  fenced ```scope block (for ceremony changes: the Gate-1 blast radius, machine-checked); a new
  `scope-review` CI job compares the diff against the declaration deterministically — offline, no
  LLM in the decision path — and fails on any undeclared file (medium), workflow env var, or
  manifest dependency (high). Phase-A burn-in (report-only); the blocking flip follows as its own
  change. The gate is **self-contained**: two stdlib-only Python scripts, zero runtime
  dependencies (a supply-chain audit rejected the initial `npx` form — a 113-package floating
  transitive tree resolved per run).
  *Concept credit:* the declared-scope gate pattern, scope-JSON schema, and severity taxonomy
  were learned from **OverReach** ([Naveja00/OverReach](https://github.com/Naveja00/OverReach),
  MIT) — reimplemented clean-room with stricter matching; no code copied.
  *Provenance hat-tip:* from the 2026-07-14 competitive landscape analysis, which also evaluated
  (with thanks): BRACE (CC BY 4.0 — its self-assessment checklist was run against the live
  deployment), statewright, microsoft/agent-governance-toolkit, eqtylab/cupcake,
  falcosecurity/prempti, ThumbGate, mori, elephantasm-core, traceguard, Terminalcontrol
  (FleetView), and nousresearch/hermes-agent.

## [0.1.21] - 2026-07-13

### Changed
- **Relocated the constitution-override ceremony template out of the OpenSpec change tree and adopted
  OpenSpec 1.6.0** (change `relocate-override-template-openspec-16`; ADR-0026; `constitution-override`,
  procedural — touches the `protects:`-tagged `maintenance` spec and pointer text in `constitution.md`,
  no Tier-0/1 element overridden). OpenSpec 1.6.0's stricter default discovery enumerated the blank
  template at `openspec/changes/templates/constitution-override/proposal.md` as a delta-less change and
  failed it; the template now lives at `openspec/templates/constitution-override/proposal.md` (outside
  the scanned `changes/`/`specs/` tree), with all 7 references and the CI `test -f` guard repointed in
  lockstep. The `@fission-ai/openspec` pin advances `1.4.1 → 1.6.0` (supersedes Dependabot #18). A new
  `maintenance` requirement codifies that governance tooling is version-pinned and ceremony templates
  live outside the change tree, so this cannot recur. The ceremony and every constitutional principle are
  unchanged.

## [0.1.20] - 2026-07-13

### Changed
- **Agent may capture directly into `20-Claims/`** (change `permit-agent-claims-capture`; ADR-0025;
  `constitution-override` touching `access-control`). The Area Access Matrix Agent cell for `20-Claims/`
  moves from `—` to `RW` and footnote 2 is reworded: the agent may create Claim notes directly (operator
  efficiency / comfort-of-ride decision from the ADR-0022 Gate 4). The `_refine-approved/` Treasury gate
  is untouched (Agent `—`), so promotion into `40-Treasury/` stays human-gated (INV-4). `20-Claims/` is
  Layer-2 Workings (CONST-02); no Tier-0 invariant is weakened. Also: README ADR count corrected
  (18 -> 25) and a CI guard added so the README ADR count must equal the actual `openspec/adr/` file count.

## [0.1.19] - 2026-07-13

### Added
- **OS/harness-enforced agent write scope — burn-in stage** (change: `os-enforced-agent-write-scope` —
  ADR-0022; enforcement for INV-4/INV-5, no new invariant). `vault-template/.claude/settings.json` now
  ships pre-action enforcement of the Area Access Matrix's Agent column: an OS sandbox
  (bubblewrap/Seatbelt) denies agent shell writes — all child processes, all interpreters — to
  `40-Treasury/ 99-Operations/ .claude/ 96-Runbooks/ 97-Molds/ 10-Logbook/`, and `permissions.deny`
  Edit-rules block structured-tool writes to the same scope plus script-owned Logbook artifacts
  (`Daily/*.md`, `kanban.md`); the disposition sidecar (`Daily/*.resolutions.json`) stays writable by
  pattern disjointness. Rendered scripts remain drivable via bare exact invocations
  (`sandbox.excludedCommands`). Ships burn-in only — the strict flip (`failIfUnavailable`,
  `allowUnsandboxedCommands: false`) is a deliberate later stage. `access-control` ADDED Requirement;
  AGENTS.md drive contract; USING-THIS-TEMPLATE Step 4c.

## [0.1.18] - 2026-07-13

### Added
- **Refine executor: empty `index_links` defaults to a pending-catalog holding index** (change
  `bank-execute-pending-catalog`; ADR-0024; `constitution-override` touching `maintenance`). An
  explicit empty `index_links` is no longer a silent orphan nor a hard block — the executor links the
  banked note into `40-Treasury/Catalog/pending-catalog-index.md` (a new template Catalog index), so
  every banked note stays reachable via ≥1 Catalog index (INV-12) and un-cataloged notes form a
  visible "awaiting-catalog" queue. Missing / non-list `index_links` remains a schema rejection.
  Surfaced by the Crucible prove-out dig (Qwen dry-run #10). `maintenance`: MODIFIED pre-flight requirement.

## [0.1.17] - 2026-07-06

### Added
- **Runbooks + declared floors** (change `runbooks-and-floors`; fleet-review B6/B7).
  New `render-reconcile-runbook` (the INV-3 deploy/drift loop) and `refine-pipeline-runbook`
  (detect → propose → human gate → atomic bank, with B4 reject semantics). `maintenance` gains
  "Platform and Dependency Floors": Python ≥ 3.12, `python-frontmatter` as the sole third-party
  dependency (hook paths stdlib-only), Linux/POSIX floor — new dependencies become governed
  decisions. `USING-THIS-TEMPLATE` documents the floors.
- **Render fence lint + publish-guard inventory** (change `reconcile-fence-lint-guard-inventory`;
  fleet-review B5/R8). `vault-render.py` refuses a note with ≠1 `python|bash` fence (VIOLATION,
  exit 1 — the extractor no longer silently takes the first); `outbound-publish-guard.py` (the
  INV-14 PreToolUse rail) gains a literate source note (`runtime: harness hook`, enum extended)
  so `reconcile` finally guards it against drift.

### Changed
- **Shell pair conformance** (change `shell-pair-conformance`). `vault-slag.sh`/`vault-dump.sh`
  join the fleet contract: env-free root resolution (inline bash copy), INV-11 slug validation
  via `vault_naming.py --check`, usage/source/destination gates (exit 1/3), and pathspec-scoped
  commits of exactly the moved effort — the last `add -A` sweeps in the fleet are gone.

### Fixed
- **Fleet hygiene bundle** (change `fleet-hygiene-bundle`). `runtime:` enum gains `git hook`
  (commit-gate note aligned; rendered hook unchanged); close-lint `--check` now validates every
  manifest disposition against `DISPOSITIONS` (typos FAIL — the old guard was near-tautological,
  R7); bootstrap-runbook clean-ops line updated for the env-free hook/fleet reality (template;
  live copy operator-applied).

### Added
- **Refine executor pre-flight + batch isolation** (change `bank-execute-pre-flight`; fleet-review
  B4). The sole automated Treasury writer now validates every proposal whole before any write:
  schema, path containment (target in `40-Treasury/`, links in `40-Treasury/Catalog/`), INV-11
  stem, **create never overwrites (INV-9)**, append-target existence, `GRADES`/`PILLARS` vocab,
  link-target existence. Rejections print all reasons, write nothing, and don't stop the batch;
  any reject exits 1. `maintenance`: ADDED Requirement.

### Changed
- **Commit ownership + close de-sweep** (change `commit-ownership-de-sweep`; operator decision
  B3-(a)). Every mutation now owns its scoped commit: daily-note commits the note it creates
  (`daily: opened <date>`); the refine executor banks each proposal atomically (`bank: <stem>` —
  note + Catalog links + consumed proposal); close-day replaces its load-bearing `git add -A`
  sweep with a scoped seal (daily + consumed sidecar) — the last Python sweep is gone, and a
  close never captures unrelated working-tree content. `commit_paths` tolerates consumed
  (deleted, never-tracked) paths. INV-2 requirement gains the ownership clause + scenarios.
- **Wave-2 `vault_lib` adoption + `commit_paths` hardening** (change `wave-2-vault-lib-adoption`;
  extends ADR-0023). `commit_paths` now no-ops cleanly on unchanged state (fixes the kanban
  same-day empty-index crash fleet-wide) and commits with an explicit pathspec so unrelated
  pre-staged content stays staged (closes the F3/F4/F5 sweep class structurally). Adopted in
  `knowledge-lint`, `treasury-orphan`, `tailings-reprospect`, `ore-detect`, and the
  `naming-rules` mirror-writer (lazy, `__main__`-only; `--check`/hook path dependency-free) —
  the full Python fleet now runs bare with no pre-sourced environment. Shell pair
  (`site-slag`/`spoil-dump`) deferred to the B3-era change.

### Fixed
- **Commit-gate hook is now environment-free** (change `fix-commit-gate-env-guard`). Deleted the
  vestigial `VAULT_ROOT` guard (set but never used) that broke bare-exact drive-path commits at
  their final step — the last blocker found by the Phase-1a live acceptance. INV-11 enforcement
  unchanged. `push-guard` audited: already self-locates, no change.

---

## [0.1.16] - 2026-07-05

Shared fleet plumbing `vault_lib` + drive-path adoption. (change: `add-shared-vault-lib` — ADR-0023)

### Added
- **Shared fleet plumbing `vault_lib`** (ADR-0023 Accepted; change `add-shared-vault-lib` —
  Gate 4 signed 2026-07-05).
  New `vault-lib-script.md` → `~/bin/vault_lib.py`: vault-root resolution (env-first, config-marker
  walk — makes the ADR-0022 bare-exact drive invocations work with no pre-sourced environment,
  closing burn-in probe P5), config vocabulary precedence (process env > `config.env` >
  `config.defaults.env` > code default), YAML-typed `is_closed`, scoped `commit_paths` (INV-2
  shape), fleet exit-code contract (`0` ok · `1` violation · `2` needs-input · `3` gate-blocked).
  `maintenance` spec: ADDED Requirement + Script Inventory row.

### Changed
- Drive-path scripts adopt `vault_lib` (`daily-close`, `daily-note`, `dig-rollover`,
  `kanban-render`, `bank-execute`; `render-reconcile` carries an inline bootstrap copy).
  Behavioral deltas (enumerated in ADR-0023): rollover and close-day gate refusals now exit 3
  (were 0 / 1); `closed: false` uniformly reads as open; kanban grades/statuses come from the
  config SSOT; `DISPOSITIONS` gains a config-file source below the environment.

---

## [0.1.15] - 2026-07-02

Publication boundary (path-level default-deny manifest) + special-file naming exemptions. (changes: `publication-boundary-manifest` — ADR-0020; `naming-special-file-exemptions` — ADR-0021)

### Added
- **Publication boundary — path-level default-deny manifest** (ADR-0020; extends ADR-0018/INV-14). `99-Operations/schemas/publish-manifest.json` is a default-deny allowlist of publishable framework paths; `push-guard-script` refuses a push to a `PUBLIC_REMOTE_ALLOWLIST` remote whose diff touches any non-allowlisted (private) path, path-by-path. Layers on the existing remote-level INV-14 gate; both allowlists empty by default. `access-control` (ADDED Requirement) + `maintenance` (MODIFIED Script Inventory) specs.
- **Special-file naming exemptions** (ADR-0021; extends ADR-0015/INV-11). `naming-rules` gains `exempt_names` / `exempt_globs` (basename-matched) so tool-mandated / convention filenames (`README.md`, `CLAUDE.md`, dailies, `*.example`, …) are skipped by the kebab / ≥3-token rules; `is_exempt` is honored by the linter now (mechanical rejection still deferred per ADR-0015). `docs/naming-exemptions-rationale.md` documents each by dependency class.
- **Framework/instance config split** — `99-Operations/config.defaults.env` (public defaults, sourced first) + `config.env.example` (stub); the live `config.env` is now a gitignored private instance. New `PUBLIC_REMOTE_ALLOWLIST` guard key.

### Changed
- `docs/obsidian.md` — prominent "turn OFF *Automatically update internal links*" warning (governed renames conflict with auto-relinking; INV-3).
- `docs/USING-THIS-TEMPLATE.md` — config defaults/instance setup (`cp config.env.example config.env`) + `PUBLIC_REMOTE_ALLOWLIST` / publish-manifest.
- `vault-template/` mirror of the push-guard path-gate, the two naming meta-scripts, `publish-manifest.json`, and the config split.

### Fixed
- Config-split blast radius: `.github/scripts/validate-scripts.sh` (sandbox now instantiates `config.env` from `config.env.example`) and `.github/workflows/ci.yml` `vocabulary-lint` (reads `config.defaults.env`) — both would otherwise break on the removed `config.env`.

---

## [0.1.14] - 2026-06-30

`98-Warehouse` re-chartered as the **reference stockroom**. (change: `warehouse-reference-stockroom`; ADR-0019)

### Added
- **`98-Warehouse/` reference stockroom** — retained source/reference material the operation draws on repeatedly (binaries *and* digitized references), organized into media shelves `Books/`, `Music/`, `Art/`, `Pictures/`, `Audio/`. Re-classified from generic "binary attachments / infrastructure" in `vault-structure` (*Three-Layer Model* + *Folder Structure*) and `access-control` (*Area Access Matrix*); both retain `protects:`.
- **Shelf-naming scope scenario** — Warehouse shelf *folders* take human-friendly names under the universal path-component rule only; the kebab-case / ≥3-token convention is scoped to `.md` stems and `30-Sites/`/`70-Tailings/` effort folders + `40-Treasury/` stems, so it does not reach them.
- `vault-template/98-Warehouse/{Books,Music,Art,Pictures,Audio}/.gitkeep`.

### Changed
- `vault-template/00-Docs/README.md` — `98-Warehouse/` charter line.

### Fixed
- Completed ADR-0016 propagation: `vault-structure` spec + `vault-template/99-Operations/schemas/refine-prompt-contract.md` `index_links` example `<pillar>-index.md` → `<pillar>-domain-index.md` (the pre-v0.1.9 straggler; `agent-integration` was already correct).

---

## [0.1.13] - 2026-06-29

Private by default — **INV-14** (Tier-0) + the outbound publish guard. (change: `private-by-default-publish-guard`; ADR-0018)

### Added
- **`INV-14` — private by default; no unbid publication** (Tier-0, Safety band; appended per ADR-0008, INV-1–13 unchanged). A deployed vault never publishes outward: no automated actor may push/mirror vault content except to an operator-allowlisted remote, and public publication requires deliberate human confirmation — never an agent's unprompted suggestion. Carried by the `access-control` spec; defined in `project.md`; listed Tier-0 in `constitution.md`.
- **`push-guard-script`** → `99-Operations/hooks/pre-push`: deny-by-default, `PUSH_ALLOWLIST`-gated (deterministic, INV-6).
- **Portable Claude Code `PreToolUse` guard** (`.claude/`, repo + vault-template): hard-denies vault-outward commands; loud ASK before any public repo creation / distribution-hub publish.
- **`config.env`** keys `VAULT_PUBLISH_GUARD`, `PUSH_ALLOWLIST` (empty = deny all pushes).

### Changed
- Docs: README ("Private by default" + counts → 18 ADRs / 14 invariants), `AGENTS.md`, `docs/USING-THIS-TEMPLATE.md` (Step 4b).

### Fixed
- `config.env` comment `close-daily` → `daily-close` (v0.1.12 straggler; non-`.md`, missed by the earlier `.md`-scoped grep).

**Honest limit (ADR-0018):** Tier-0 guarantees *safe-by-default + governed + loud-to-remove*, not a physical impossibility — git hooks don't clone, `--no-verify` bypasses, an owner can opt out. OS-level egress control is deferred.

---

## [0.1.12] - 2026-06-29

Runbook naming brought to the ≥3-token convention; the daily-close / provenance-seal vocabulary
unified. Plus a moc→index residual sweep. (change: `runbook-naming-3token`; ADR-0017)

### Changed
- **Runbooks → ≥3-token `silo-section-descriptor`** (constitution-override, conforming amendment;
  ADR-0017): `close-daily.md` → `daily-close-runbook.md`, `seal-provenance.md` →
  `provenance-seal-runbook.md` (last grandfathered system-artifact family). The ritual vocabulary is
  unified on one stem family per ritual: `close-daily` → `daily-close`, `seal-provenance` →
  `provenance-seal` — coherent with the already-renamed `daily-close-script`. `session-bootstrap-loader`
  unchanged (already conforms). Spec deltas: `maintenance` (Daily Close Lifecycle), `vault-structure`
  (Folder Structure + Frontmatter Schemas). References repointed across AGENTS.md, CLAUDE.md, scripts,
  and schema. No principle weakened; INV-11 reinforced.
- **Upgrade (forks/vaults):** `git mv` the 2 runbook files + repoint references; no re-render
  (runbooks have no deploy target).

### Fixed
- **moc→index residual cleanup** — purged stale "MOC" wording left over from the `moc → index`
  rename (v0.1.6 / ADR-0013) in four non-protected vault-template files: `bank-execute-script`
  prose, `treasury-orphan-script` (`moc_text` → `index_text`), `home-master-index` heading
  ("Pillar MOCs" → "Pillar indexes"), and `config.env` comment. Terminology-only; no behavior change.

---

## [0.1.11] - 2026-06-29

`/vmm-session-rebooted` slash command — explicit cold-start prime trigger.

### Added
- **`/vmm-session-rebooted`** Claude Code command (`.claude/commands/`, repo + vault-template) — a thin
  adapter that invokes the `session-bootstrap-loader` runbook (env + the four gates + JIT pointers).
  The most reliable prime trigger (it makes *engaging* the bootstrap the agent's explicit task). No
  spec change; points at the runbook SSOT (no duplication).

---

## [0.1.10] - 2026-06-29

Session bootstrap loader — the cold-start prime mechanism (minimum bootstrap, maximum confidence).

### Added
- **`96-Runbooks/session-bootstrap-loader`** runbook (harness-agnostic SSOT): at session start, source
  env, engage the four gates (governance-first · re-read-before-acting · autonomy-bans · clean-ops),
  and know the just-in-time pointers (the `llm-context-reboot` load-list, the deferred-not-built list,
  other runbooks, the memories). A Claude Code **SessionStart hook** (`.claude/settings.json`, in-repo)
  surfaces it automatically; `AGENTS.md` + `CLAUDE.md` point at it. No spec change (conforms to the
  existing Runbook-Format).

---

## [0.1.9] - 2026-06-29

System-artifact naming (Informed-Upheaval Protocol, conforming amendment) — scripts, schemas, and Catalog indexes brought to the `silo-section-descriptor` convention.

### Changed
- **Scripts** → `<domain>-<action>-script` (`.md` notes only; deploy targets unchanged — `.py` rename deferred; canonical mining verbs): e.g. `close-daily`→`daily-close-script`, `dump`→`spoil-dump-script`, `refine-execute`→`bank-execute-script`, `pre-commit`→`commit-gate-script` (deployed hook stays `pre-commit`).
- **Schemas** → `note-frontmatter-schema`, `runbook-format-schema`, `refine-prompt-contract`.
- **Catalog indexes** → `<pillar>-domain-index` + `home-master-index` (the scope token anticipates future sub-sector indexes).
- Specs synced: `maintenance`, `vault-structure`, `agent-integration`. See ADR-0016.

---

## [0.1.8] - 2026-06-28

Token-minimum naming (Informed-Upheaval Protocol, conforming amendment) — the ≥3-token naming rule, codified as convention.

### Added
- **Token-Minimum Naming requirement** in `naming-rules`: every `.md` stem carries **≥3 hyphen-tokens
  — the floor, not the ceiling** (use *more* where the extra tokens add human-meaningful specificity).
  System-artifact families use `silo-section-descriptor` (silo first); content stems are ≥3-token
  slugs; dailies exempt. Existing sub-3 names grandfathered; **mechanical enforcement is deferred** to
  a later change (after the families conform). Agent guidance noted in `AGENTS.md`. See ADR-0015.

---

## [0.1.7] - 2026-06-27

Mold naming (Informed-Upheaval Protocol, conforming amendment) — self-identifying molds.

### Changed
- **Molds → `<note-type>-mold-blank.md`** — the four `97-Molds/` templates (`daily`, `effort`,
  `index`, `knowledge`) are renamed on the `silo-section-descriptor` convention so each mold is
  self-identifying in any flat / search / migrated view, and `index` no longer collides with the
  Catalog `<pillar>-index.md` notes. The `daily-note` script's mold path and the docs are repointed;
  the `vault-structure` Folder Structure listing is updated. No principle weakened (CONST-01 /
  INV-11 reinforced). See ADR-0014.

---

## [0.1.6] - 2026-06-19

Naming & identity (Informed-Upheaval Protocol, conforming amendment) — intuitive names + self-identifying artifacts.

### Changed
- **`moc → index`** — Catalog overview notes are now `<pillar>-index.md` (`type: index`); the mold,
  the `index_links` proposal field, and CONST-05's label "(MOCs)" → "(indexes)" follow. "MOC" (Map
  of Content) was opaque PKM jargon; "index" is self-teaching. The *principle* (domain via metadata
  + Catalog, never folders) is unchanged.
- **`_effort → <slug>/<slug>.md`** — a Site/Tailings/Spoil effort note is now the **folder-note**
  (stem == folder), self-identifying in any flat view (graph/search/migration) instead of an
  anonymous `_effort.md`. Maintenance scripts locate it as "the file whose stem equals its folder."
  See ADR-0013.

### Migration (existing forks/vaults)
- `git mv 40-Treasury/Catalog/<pillar>-moc.md → -index.md` (+ `home`); `git mv 30-Sites/<slug>/_effort.md → <slug>/<slug>.md`
  (and Tailings/Spoil); repoint wikilinks (`/_effort|` → `/<slug>|`, `-moc` → `-index`); re-render scripts.

### Process
- Constitution-override `naming-and-identity` (CONST-05 label, Tier 1), **authorized** by Keith Nielsen; ADR-0013.

---

## [0.1.5] - 2026-06-17

Spec-as-code runbooks + the daily close lifecycle (Informed-Upheaval Protocol, conforming amendment).

### Added
- **`96-Runbooks/` band** — operational procedures as harness-agnostic *spec-as-code* (schema:
  `99-Operations/schemas/runbook.md`; CI `runbook-lint`). Two charter runbooks: **`seal-provenance`**
  (forensic sealing) and **`close-daily`** (daily disposition sweep).
- **Daily close lifecycle** — `vault-close-day.py` assigns every daily item a disposition from a
  controlled vocabulary (`DISPOSITIONS`), writes an **append-only `## Close` manifest**, and sets
  `closed:`. Invariants: append-only, total-disposition, strict-order close, gated advance (capture
  is never gated). Deterministic (INV-6); AI invoked only at `unknown/other`. See ADR-0011, ADR-0012.
- Daily mold `closed:` field; `rollover` gated on the prior close; `daily-note` capture-home
  `⚠ BLOCKED` banner.
- `AGENTS.md` runbook pointer + agent operating notes; `CLAUDE.md` adapter.

### Changed
- `vault-structure` Folder Structure adds `96-Runbooks/` (reserved band `90–96 → 90–95`); CONST-04/02 upheld.
- `maintenance` spec: **Runbook Format** + **Daily Close Lifecycle** requirements.

### Process
- Constitution-override `spec-as-code-runbooks` (conforming amendment, Tier 1), **authorized** by
  Keith Nielsen; ADR-0011, ADR-0012.

---

## [0.1.4] - 2026-06-15

Lifecycle vocabulary refinement (Informed-Upheaval Protocol, CONST-01) + the project rename.

### Changed
- **Retired `prospect` as a Site status.** Prospecting is the *upstream, human* act that
  discovers Claims from the world — it is not a Site state. Sites are born at `dig`; the
  effort status set is now `dig | ore | slagged`. Updated `EFFORT_STATUSES`, the effort
  mold default, the kanban columns, the frontmatter schema, and the `value-pipeline` spec.
- **Locked the transition verbs:** `dig` (Claim→Site), `slag` (Site→Tailings),
  **`dump`** (Site→Spoil, renamed from `dispose` → `vault-dump.sh`), `redig`
  (Tailings→Site), `refine` (ore→bullion), **`bank`** (the human gate that authorizes
  bullion into the Treasury; state `authorized`). `reprospect` reclassified as the lone
  automatable read-only survey.
- New **Lifecycle Vocabulary** table in `docs/glossary.md`; CONST-01 chain updated to
  `Claim → Dig → Ore → Sort → Refine → Bank → Treasury → Polish`. See ADR-0010.
- **Renamed:** GitHub repo `memory-mining` → **`2026-AI-Value-Memory-Mining`** (year-prefixed
  Title-Kebab); internal project identity **`value-memory-mining`** (lower-kebab).

### Migration (existing forks/vaults)
- Drop `prospect` from `EFFORT_STATUSES` and set the effort mold default to `dig`;
  `git mv ~/bin/vault-dispose.sh` usage → `vault-dump.sh` (re-`render`).

### Process
- Constitution-override change `lifecycle-vocabulary` (CONST-01, Tier 1), **authorized**
  by Keith Nielsen; ADR-0010. CONST-01's principle is sharpened, not sacrificed.

---

## [0.1.3] - 2026-06-15

Constitutional correction (Informed-Upheaval Protocol) — Layer-2 folder ordering.

### Changed
- **Swapped `10-Claims` ↔ `20-Logbook`** so the daily logs sort to the top of the
  file explorer, conforming to CONST-04 ("daily logs at top"). The layout previously
  contradicted its own numbering principle. Result: `10-Logbook/` (the daily cockpit)
  now precedes `20-Claims/` (the capture inbox). The refine gate travels with Claims:
  `20-Claims/_refine-proposals/`, `20-Claims/_refine-approved/`, `20-Claims/_refine-queue.json`.
- Updated every path reference in lockstep — scripts, specs, the access-control matrix,
  schemas, molds paths, diagrams (Folder Stack), and the layout trees.

### Migration (for existing forks/vaults)
- `git mv 20-Logbook 10-Logbook` and `git mv 10-Claims 20-Claims`, then re-`render` the
  scripts. Anything pinned to the old paths (cron lines, external tooling) must update.

### Process
- Recorded as constitution-override change `swap-logbook-claims-order` (CONST-04, Tier 1)
  with human sign-off; see `openspec/adr/0009-layer2-ordering-correction.md`. CONST-04's
  principle text is unchanged — this is a corrective amendment, not an override.

---

## [0.1.2] - 2026-06-15

Documentation fills from dogfooding the live vault — Obsidian setup and the
Claim→Site promotion workflow.

### Added
- `docs/obsidian.md` — recommended Obsidian setup: core plugins; the
  **default-new-note-location → `10-Claims`** setting that keeps accidental/dangling-link
  notes out of the vault root; native Templates / Daily Notes for note creation; the
  Shell Commands + `flatpak-spawn --host` recipe for running maintenance scripts from
  the sandbox; and the Flatpak install + NVIDIA GL-extension matching note.
- `docs/method.md` → **"Promoting a Claim to a Site"** — the manual Claim→Site
  procedure, the single-source-of-truth cleanup discipline, and the three
  "where's my work?" indices (`30-Sites/`, the kanban board, the daily carry-over).

### Changed
- `vault-template/00-Docs/README.md` — clarified the two in-vault READMEs and noted that
  the full fork guide (`docs/USING-THIS-TEMPLATE.md`) and Obsidian guide (`docs/obsidian.md`)
  live in the template repo and do not copy into a forked vault; added pointers.
- `README.md` and `docs/USING-THIS-TEMPLATE.md` link the new Obsidian guide.

### Deferred (captured in docs, not built)
- A `vault-promote.sh` + an Obsidian "promote-from-inbox" punch-list button, a
  stray-fragment lint, and a `99-Operations` index MOC.

---

## [0.1.1] - 2026-06-15

Adopter-friction fixes found by performing a real install of the template into a
live Obsidian vault.

### Added
- `vault-template/.gitignore` — a forked vault now ignores `.venv/`, `__pycache__`,
  the generated `10-Claims/_refine-queue.json`, and Obsidian per-machine UI state
  (`.obsidian/workspace*`, `.obsidian/cache`) out of the box. The template previously
  shipped without a vault-level `.gitignore`.

### Changed
- Setup now installs `python-frontmatter` into a **vault-local venv** at
  `$VAULT_ROOT/.venv` rather than the system Python, which modern distros block under
  PEP 668. `config.env` (and `config.env.example`) prepend `$VAULT_ROOT/.venv/bin` to
  `PATH`, so `source 99-Operations/config.env` activates the right interpreter for both
  manual ops and cron. Updated `README.md`, `docs/USING-THIS-TEMPLATE.md`, and
  `vault-template/00-Docs/README.md` accordingly.

---

## [0.1.0] - 2026-06-15

First validated release. The deterministic engine (Phases 0–2) is proven against
the full PRD acceptance suite; Phase 3 (agent operations) remains spec-only/deferred.

### Added
- Initial repository structure: OpenSpec SDD scaffold, vault-template skeleton,
  constitution, 6 capability specs, 8 ADRs, 2 archived teaching changes,
  1 live change stub (add-telemetry-segment), CI pipeline, docs layer.
- Worked end-to-end example in `vault-template/00-Docs/examples/` (Claim → Treasury).
- `.github/scripts/validate-scripts.sh` — renders all 13 meta-scripts and runs
  `py_compile` + `shellcheck` + a fresh-vault pipeline smoke + the INV-11 executor
  boundary test. Wired as a CI matrix job (Python 3.12, 3.13).

### Fixed
- `config.env` used an HTML comment (`<!-- SPDX -->`) on line 1, which broke
  `source 99-Operations/config.env`. Changed to a shell comment (`# SPDX`).
- The literate-script render extractor used a non-line-anchored regex that
  truncated any script whose body contains a triple-backtick (notably
  `render-reconcile` itself). Anchored the closing fence to line start
  (`^``` ` with `re.MULTILINE`) in the script and both documented bootstrap
  snippets (`README.md`, `docs/USING-THIS-TEMPLATE.md`).
- The in-vault bootstrap (`00-Docs/README.md`) instructed running a `.md`
  meta-script note directly as Python; replaced with the code-block extraction step.
- Cron and ongoing-ops invocations set only `VAULT_ROOT`, so `vault-refine-detect.py`
  (needs `REFINE_GATE_GRADES`) and `vault-lint.py` (needs `PILLARS`/`GRADES`/
  `KNOWLEDGE_STAGES`) would `KeyError`. All documented invocations now source
  `config.env`.

### Changed
- Aligned proposal-schema MOC path examples with the kebab-case filenames
  (`<pillar>-moc.md`) used by the actual template (INV-11).
- Supported Python floor set to **3.12+** (was advertised as 3.10+, which the
  version matrix showed was not actually met).

### Validated
- Full PRD Phase 0→2 acceptance suite (A0.1–A2.6, plus orphan detector) against a
  sandboxed vault: 19/19 checks pass. All 13 operational scripts deploy via
  `render`, `reconcile` reports zero drift, and the refine pipeline
  (detect → propose → gate → execute), dispose, slag, rollover, kanban, linter,
  naming validator, and commit-gate hook all behave per spec.
- The documented onboarding was dogfooded literally end-to-end on a fresh vault.

[0.1.6]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.6
[0.1.5]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.5
[0.1.4]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.4
[0.1.3]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.3
[0.1.2]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.2
[0.1.1]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.1
[0.1.0]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.0
