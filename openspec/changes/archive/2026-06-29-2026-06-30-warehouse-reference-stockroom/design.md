<!-- SPDX-License-Identifier: Apache-2.0 -->
# Design — warehouse-reference-stockroom

## The gap

Three "homes" already exist for content the operation produces: Treasury (mined value), Sites
(active digs), Operations (machinery). None fits **retained source material the operation
consumes** — a reference book, a media asset — kept and re-read but never refined into bullion.
`98-Warehouse/` existed but was chartered as bare "binary attachments" and sat empty. This change
gives it the obvious role: a **reference stockroom**.

## Why shelves, and why their names are exempt

Stock is easier to keep "out of the way" when binned by kind, so the Warehouse is organized into
media shelves (`Books/`, `Music/`, `Art/`, `Pictures/`, `Audio/`) — the familiar OS media-folder
idiom, which is what makes them legible at a glance.

Their **Title-Case names are intentional and conformant**. The `naming-rules` spec has two tiers:
1. **Universal** — every path component (folder or `.md` stem) must use cross-platform-safe
   characters and avoid reserved device names. The shelves satisfy this.
2. **Kebab / ≥3-token** — applies only to *machine-generated* `.md` stems and to effort folders in
   `30-Sites/`/`70-Tailings/` and Treasury stems in `40-Treasury/`.

A Warehouse shelf is none of (2)'s targets, so the kebab/≥3-token rule simply does not reach it —
there is **nothing to exempt**. The added scenario records this so a future reviewer or linter does
not mis-flag `Books` as a sub-3-token violation.

## Digitized references and INV-1

A digitized reference (e.g. *The Elements of Style* → Markdown) lives in `Books/` as a `.md` file.
It is still Markdown, so INV-1 holds; it is *reference material*, not a typed vault note, so it is
outside the linter's typed-note globs (Treasury/Claims/Logbook/etc.) by location. Binary media
(Music/Art/Pictures/Audio) remain confined to `98-Warehouse/` per the unchanged Format Invariant.

## Folded-in fix

`vault-template/99-Operations/schemas/refine-prompt-contract.md` still showed the pre-v0.1.9
`<pillar>-index.md` `index_links` example while `agent-integration/spec.md` already says
`<pillar>-domain-index.md`. Corrected here to complete ADR-0016 propagation (the spec is the source
of truth; the template example simply lagged). The same fix was applied live on 2026-06-30.
