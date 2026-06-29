<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0019 — 98-Warehouse: binary attachments → reference stockroom

**Status:** Accepted
**Date:** 2026-06-30
**Relates:** `vault-structure` · `access-control` specs · change `warehouse-reference-stockroom` · naming scope from ADR-0015/0016

## Context

`98-Warehouse/` was chartered as "binary attachments / general binary storage" and sat empty
(`.gitkeep` only). The operation needed a home for **retained source/reference material it draws on
repeatedly** — not mined value (Treasury), not a working dig (Site), not machinery (Operations). The
triggering case: an owned-hardcopy *The Elements of Style* digitized to Markdown, kept for daily
reference. Binary media (images, audio) want the same home.

## Decision

- Re-charter `98-Warehouse/` as the **reference stockroom**: retained source/reference material,
  binaries *and* digitized references, organized into **media shelves** — `Books/`, `Music/`, `Art/`,
  `Pictures/`, `Audio/` (created on demand; this is the default set).
- Shelf **folder** names are human-friendly Title-Case labels under the universal path-component rule
  only. The kebab-case / ≥3-token convention is scoped (per `naming-rules`, ADR-0015/0016) to `.md`
  stems and to `30-Sites/`/`70-Tailings/` effort folders and `40-Treasury/` stems — a Warehouse shelf
  is none of those, so the convention does not reach it. A scenario records this so it is not
  mis-flagged later.
- Access privileges are unchanged (H RW · A W-within-assignment · S RW). Binaries remain confined to
  `98-Warehouse/` (Format Invariant unchanged); a digitized `.md` reference is still Markdown (INV-1).

## Options considered

1. **New top-level `Library` silo vs. repurpose `98-Warehouse`** — chose **repurpose**: a "warehouse"
   already connotes stored stock drawn on repeatedly; a new silo is a heavier structural change
   (numbering, CONST-04 order, ripple) for the same outcome. `98-Warehouse` was empty and purpose-adjacent.
2. **Kebab the shelves (`books`, `pictures`) vs. human Title-Case** — chose **Title-Case**: the rule
   does not apply to these folders, and the OS media-folder idiom is more legible; forcing kebab would
   add a rule where none exists.
3. **Forbid `.md` in Warehouse vs. allow digitized references** — chose **allow**: a transcribed book
   is Markdown (INV-1 holds) and is reference material, not a typed note; co-locating it with its
   eventual binary scan keeps the source together.

## Consequences

- `98-Warehouse/` has a clear charter and a shelf convention; reference material has an unambiguous home.
- Adopters/forks inherit 5 empty shelf folders by default (deletable).
- **Sacrifice:** none structural — no invariant, access cell, numbering, or workflow is weakened, and
  no existing file moves. The only standing cost is the 5 default shelf folders. (Folded in: the
  v0.1.9 `<pillar>-index.md` → `<pillar>-domain-index.md` template straggler, completing ADR-0016.)
