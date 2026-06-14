<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0003 — Bronze-Not-Copper: The Grade System

**Status:** Accepted  
**Date:** 2026-06-10  
**Constitution:** CONST-03

## Context

The value pipeline needs a grade system that:
1. Measures **value only**, never effort (conflating the two is the classic PKM
   failure mode — high-effort low-value work gets over-promoted)
2. Provides an at-a-glance ranking without requiring a lookup
3. Has a clear threshold between "refine automatically" and "human decides"

Options for the grade names:
- **coal / copper / silver / gold** — familiar metals, but "copper" doesn't carry
  an unambiguous relative ranking intuition
- **coal / bronze / silver / gold** — Olympic medal system: bronze = recognizable
  third-place, instant relative ranking (bronze < silver < gold), coal = the
  pre-valuable baseline
- **low / medium / high / critical** — explicit but no intuitive visual anchor;
  doesn't compose well with the mining metaphor

The threshold choice:
- Auto-refine at `bronze` and above → too aggressive; bronze is marginal
- Auto-refine at `silver` and above → human decides bronze; coal auto-slags
- Auto-refine at `gold` only → under-automated

## Decision

Use **`coal < bronze < silver < gold`** as the four value grades (CONST-03).
Auto-queue for routine refine at `silver` and `gold`. Bronze is marginal: the
operator may override or slag, but bronze does not auto-refine.

Grade is **estimated** at `ore` (by human or agent assay) and **confirmed** at
`refine` (the act of refining is verification; a confirmed downgrade may route
material back to Tailings).

## Consequences

- The Olympic medal anchor gives instant at-a-glance value ranking without a
  reference card; newcomers understand the scale immediately.
- "Bronze, not copper" is a deliberate, memorable choice — it is its own mnemonic.
- `vocabulary-lint` enforces the exact terms; introducing "copper" or renaming
  grades is a Tier-2 change but must update all scripts, docs, and lint rules.
- Sacrifice: contributors expecting a 1–5 numeric scale must learn the medal system.
