<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0009 — Layer-2 Ordering Correction: Logbook Before Claims

**Status:** Accepted  
**Date:** 2026-06-15  
**Amends:** ADR-0002 (Value Mining metaphor + folder numbering) · **Principle:** CONST-04

## Context

CONST-04 mandates folder numbering "ordered from most frequently touched **(daily logs
at top)** to least." The original implementation placed `10-Claims` first and the daily
logs at `20-Logbook` (second) — contradicting CONST-04's own stated example.

Dogfooding the live vault made the tension concrete: the daily note is the orienting
**cockpit** a user opens first each session (set intentions, log, decisions, preview the
inbox, resume open digs), while `10-Claims` is an unordered capture queue that gets
skimmed. The file explorer therefore opened on the wrong surface.

This was raised as a workflow question and routed through the **Informed-Upheaval
Protocol** because folder numbering is a Tier-1 constitutional element (CONST-04).

## Decision

Swap the two Layer-2 folders so the layout conforms to CONST-04:

- `20-Logbook → 10-Logbook` (the daily cockpit, now at the top)
- `10-Claims → 20-Claims` (the capture inbox), carrying the refine gate
  (`_refine-proposals/`, `_refine-approved/`, `_refine-queue.json`)

CONST-04's principle text is **unchanged** — it already said "daily logs at top." This is
a **corrective amendment** that makes the implementation conform to the constitution, not
an override of it.

## Options considered

1. **Swap the folders (chosen).** Conforms to CONST-04; one-time wide-but-mechanical
   migration across ~24 path-referencing files + 4 structural diagrams/trees.
2. **Leave the structure, fix ergonomics in Obsidian** (pin the daily / start page /
   hotkey). Cheaper, but leaves CONST-04 saying "daily logs at top" while the vault does
   not — eroding the constitution's authority. Rejected as papering over a real bug.
3. **Rewrite CONST-04** to bless "capture inbox at top." Rejected: the cockpit-first
   principle is sound; the implementation was the error.

## Consequences

- The explorer now opens on `10-Logbook/` — the daily cockpit — by default.
- The three-layer model (CONST-02) is untouched: both folders remain Layer 2, so this is
  an intra-layer correction.
- **Sacrifice / cost:** the `10=Claims / 20=Logbook` numbering is retired. Anyone (or any
  fork) with muscle memory or tooling pinned to the old paths must migrate, and the refine
  gate moves to `20-Claims/_refine-*`. The migration is one-time and mechanical.
- No constitutional principle is sacrificed; CONST-04 is strengthened.

Recorded under change `swap-logbook-claims-order` (constitution-override, signed off
2026-06-15).
