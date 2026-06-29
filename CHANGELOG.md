<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

This changelog is generated from completed OpenSpec changes in
`openspec/changes/archive/`. Each entry corresponds to an archived change.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

<!-- New entries are added here as changes land. -->

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
