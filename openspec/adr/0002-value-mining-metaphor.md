<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0002 — Value Mining Metaphor, Three-Layer Model, and Folder Numbering

**Status:** Accepted  
**Date:** 2026-06-10  
**Constitution:** CONST-01, CONST-02, CONST-04

## Context

A personal knowledge system needs an organizing frame that:
1. Makes the pipeline self-teaching (stage names predict the next stage and current
   material state)
2. Distinguishes stable crown-jewels from high-churn work and from infrastructure
3. Puts the most frequently used areas at the top of any file explorer

Alternatives considered for the frame:
- **Garden/Evergreen** (Zettelkasten-adjacent) — broad cultural familiarity, but
  stage names don't predict material state; "evergreen" doesn't tell you where
  something came from or where it's going
- **Inbox/Project/Archive** (GTD-derived) — familiar, but conflates capture with
  processing; no grade system; no retained "not-ready-yet" category
- **Value Mining** — extraction metaphor where every stage name answers "what is
  this material, and what happens next": Claim (staked) → Prospect (investigated) →
  Dig (extracted) → Ore (raw, graded) → Sort (triaged) → Refine (confirmed value) →
  Treasury (durable bullion) → Polish (perpetual upkeep)

## Decision

Adopt the **Value Mining metaphor** as the constitutional frame (CONST-01), the
**three-layer model** as the structural organizing principle (CONST-02), and
**zero-padded, gapped, touch-frequency folder numbering** as the navigation
convention (CONST-04).

The vocabulary is treated as a controlled glossary enforced by `vocabulary-lint` CI.

## Consequences

- Stage names are self-teaching: the vocabulary is the documentation.
- The three layers give the access-control model a principled basis (INV-4, INV-5,
  INV-9 all derive from layer membership).
- Touch-frequency ordering means the most-used folders (Logbook, Claims, Sites) are
  at the top of the file explorer by default.
- Sacrificed: familiar alternatives (garden, GTD) cannot be used without a
  constitutional override; contributors must learn the mining vocabulary.
- `vocabulary-lint` will reject garden/evergreen/harvest terminology if introduced.
