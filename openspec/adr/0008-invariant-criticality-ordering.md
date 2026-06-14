<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0008 — Invariant Criticality Ordering (INV-1 through INV-13 are Frozen)

**Status:** Accepted (LOCKED)  
**Date:** 2026-06-14

## Context

The original PRD assigned INV numbers in the order invariants were discovered during
design, not in order of criticality. This produced an ordering where a Consistency
convention (INV-2: domain via metadata) had a lower number than a Safety invariant
(INV-7: no secrets) — the opposite of their actual blast-radius relationship.

This ordering was visible to consumers (scripts, comments, CLAUDE.md, diagrams)
and would have created confusion as the codebase grew. A reordering was proposed
before any implementation artifacts were created.

## Decision

Renumber INV-1 through INV-13 by **criticality band** (Substrate → Safety →
Value → Consistency), so lower numbers reflect more fundamental invariants:

| Band | INVs | Rationale |
|---|---|---|
| Substrate | INV-1–3 | Touched in every operation; foundational to what the system is |
| Safety | INV-4–8 | Highest blast radius if violated; access control and containment |
| Value | INV-9–10 | Preservation guarantees for the output of the system |
| Consistency | INV-11–13 | Structural conventions; important but narrower blast radius |

The **mapping from old to new IDs** is recorded here as the authoritative translation:

| Old | New | Name |
|-----|-----|------|
| INV-1 | INV-1 | Format |
| INV-5 | INV-2 | One mutation, one commit |
| INV-6 | INV-3 | Layer 0 is source of truth |
| INV-4 | INV-4 | Bounded write scope |
| INV-11 | INV-5 | Actor ≠ owner of its own definition |
| INV-10 | INV-6 | Deterministic layer is offline |
| INV-9  | INV-7 | No secrets in vault |
| INV-12 | INV-8 | Crucible independence |
| INV-7  | INV-9 | Refined value is never discarded |
| INV-8  | INV-10 | Tailings are retained |
| INV-13 | INV-11 | Name conformance, enforced at the boundary |
| INV-2  | INV-12 | Domain via metadata, not folders |
| INV-3  | INV-13 | Wikilinks |

## INV IDs are now frozen

The constitution forbids further renumbering. New invariants append at the end
with the next free number (INV-14, INV-15, …). Renumbering existing IDs is a
Tier-0 constitutional override — it touches every script, spec, diagram, and
comment that cites an INV number.

## Consequences

- The invariant list now reads as a priority order: if two rules conflict, the
  lower-numbered one wins.
- All scripts, acceptance tests, diagrams, and CLAUDE.md were updated to the new
  numbering before any implementation artifacts were created — no migration needed.
- Future contributors must not renumber; they may only append.
- Sacrifice: the original PRD's numbering is no longer valid; external references
  to the old numbers are incorrect after this ADR.
