<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

This changelog is generated from completed OpenSpec changes in
`openspec/changes/archive/`. Each entry corresponds to an archived change.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Changed
- **Renamed:** GitHub repo `memory-mining` → **`2026-AI-Value-Memory-Mining`** (owner's
  year-prefixed Title-Kebab convention; GitHub redirects the old URL). Internal project
  identity is **`value-memory-mining`** (lower-kebab, matching the project's own INV-11
  slug philosophy). URLs/clone-dir use the repo name; titles/prose use the project name.

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

[0.1.3]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.3
[0.1.2]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.2
[0.1.1]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.1
[0.1.0]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.0
