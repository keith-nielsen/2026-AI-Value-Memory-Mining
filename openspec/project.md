<!-- SPDX-License-Identifier: Apache-2.0 -->
# Project — memory-mining

## Purpose

Build and maintain a reference-grade, Apache-2.0 OpenSpec SDD template repository
for a local-first, Markdown-based personal knowledge system organized as a
**Value Mining** operation. The repository must be exemplary in its own right *and*
serve as a "done right" template any implementer can fork to run the same
spec-driven process on their own vault.

## Standing Goals

1. **Framework correctness over minimum-to-ship.** Every decision reflects the
   methodology at its best, not at its quickest.
2. **Decompose, don't paste.** Source artifacts are decomposed into their
   canonical locations; no monolithic PRD survives into the specs.
3. **Teaching through example.** Archived changes are first-class teaching
   artifacts demonstrating the full propose → apply → archive lifecycle.
4. **Constitutional integrity.** Tier-0 and Tier-1 elements may only be altered
   via the Informed-Upheaval Protocol (see `constitution.md`).
5. **Broad adoption.** Apache-2.0 license; no CLA requirement at launch; third-party
   tools orchestrated, never vendored.

## Architectural Principles (INV-1 – INV-13)

These are extracted from the PRD and are the authoritative invariant list.
INV IDs are **frozen** — see ADR-0008.

### Substrate — fundamental to every operation

- **INV-1 — Format.** All content files are Markdown (`.md`) with YAML
  frontmatter, UTF-8. No proprietary formats.
- **INV-2 — One mutation, one commit.** Every automated mutation ends in exactly
  one Git commit with a structured message. All automated changes are diffable
  and revertible.
- **INV-3 — Layer 0 is source of truth.** Host runtime artifacts are produced
  FROM `99-Operations/` via `render` and verified via `reconcile` (drift
  detection only — never auto-enforced). Host artifacts are never the authority.

### Safety — highest blast radius if violated

- **INV-4 — Bounded write scope.** No agent/LLM process may write to
  `40-Treasury/` or `99-Operations/`. An agent may write only to its assigned
  Site (`30-Sites/<slug>/`) and `10-Claims/_refine-proposals/`. A script may
  write to `40-Treasury/` only when applying a human-approved proposal from
  `10-Claims/_refine-approved/`.
- **INV-5 — Actor ≠ owner of its own definition.** No automated process has
  write access to `99-Operations/`.
- **INV-6 — Deterministic layer is offline.** `[script]` operations make no
  network calls and no LLM calls; they are model-agnostic.
- **INV-7 — No secrets in vault.** No credentials, keys, tokens, or passwords in
  any vault file. Scripts read secrets from the environment only.
- **INV-8 — Crucible independence.** The Crucible uses an independent
  model/operator, distinct from the main process agent. The main agent is
  excluded from `80-Crucible/`.

### Value — preservation guarantees

- **INV-9 — Refined value is never discarded.** Bullion in `40-Treasury/` is
  never moved to `71-Spoil/` or deleted by automation. Only effort husks are
  disposed. Only waste (proven false) is discarded.
- **INV-10 — Tailings are retained.** Slagged efforts are never auto-purged;
  they keep their Dig metadata for re-prospecting.

### Consistency — structural conventions

- **INV-11 — Name conformance, enforced at the boundary.** Every vault path
  component must satisfy the naming ruleset: cross-platform-safe characters, no
  reserved device names, NFC-normalised, no leading dot / trailing space or dot.
  Machine-generated names must additionally be kebab-case slugs. Enforced
  deterministically at the refine executor and the commit-gate hook.
- **INV-12 — Domain via metadata, not folders.** Pillar membership is expressed
  only through the `pillars` frontmatter field, tags, and Catalog (MOC) links.
  `40-Treasury/` must not contain pillar subfolders.
- **INV-13 — Wikilinks.** Internal links use `[[wikilink]]` form.

## Directional Preferences

- Prefer deterministic, offline scripts over agent operations wherever possible.
- Prefer explicit human gates over automated promotion between lifecycle stages.
- Prefer the smallest pillar set that cleanly covers a life (default: 6).
- Prefer kebab-case slugs for all machine-generated identifiers.
- Prefer literate meta-scripts (code inside Markdown notes) over bare script files.

## Stack

| Concern | Choice | Notes |
|---|---|---|
| SDD framework | OpenSpec v1.4.1+ | `spec-driven` schema; ADRs as project convention |
| Vault UI | Obsidian | Local-first; wikilinks native |
| Script language | Python 3.10+ | `python-frontmatter` for YAML |
| Git wrappers | Bash | Thin wrappers only |
| Agent runtime | Hermes Agent v0.15.2 | Phase 3, deferred |
| Orchestration | n8n | Deferred |
| Local inference | Ollama / llama.cpp | Deferred |
| License | Apache-2.0 | See ADR-0007 |
