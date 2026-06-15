---
capability: value-pipeline
protects: [CONST-01, CONST-03, INV-9, INV-10]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: value-pipeline

## Purpose

Define the Value Mining extraction pipeline: stage definitions, grade-gate logic,
the Sort triage, and the Tailings/Spoil disposal model. This spec is the authority
for how material moves from raw capture to refined bullion.

## Requirements

### Requirement: Pipeline Stages

Every piece of content SHALL have a defined position on the value chain. Stage names
predict the next stage and the material's current value-state (CONST-01).

| Stage | Location | Object | Key field | Meaning |
|---|---|---|---|---|
| Capture | `20-Claims/` | loose note | — | Raw, unsorted input |
| Prospect | `30-Sites/<slug>/` | effort | `status: prospect` | Staked, under initial validation |
| Dig | `30-Sites/<slug>/` | effort | `status: dig` | Active extraction in progress |
| Ore | `30-Sites/<slug>/` | effort | `status: ore` + `grade` | Raw material extracted; grade **estimated** |
| Sort | (process, not folder) | decision | — | 3-way triage |
| Refine | `40-Treasury/` | knowledge note | `stage: refined` | Grade confirmed; verified + structured into bullion |
| Polish | `40-Treasury/` | knowledge note | `stage: polished` | Perpetual upkeep of bullion |
| Slagged | `70-Tailings/<slug>/` | effort | `status: slagged` + `slag_reason` | Real value, not economic now; retained, re-minable |
| Spent husk | `71-Spoil/<slug>/` | husk | `status: spent` | Residue of a successful refine; terminal |
| Waste | `71-Spoil/<slug>/` | stub | `status: waste` | Proven false or empty; terminal |

#### Scenario: Effort progresses through active statuses
- **WHEN** an operator promotes a Claim to a Site
- **THEN** the effort's `_effort.md` is created with `status: prospect`
- **WHEN** work begins
- **THEN** the operator sets `status: dig`
- **WHEN** material is extracted and assay'd
- **THEN** the operator sets `status: ore` and sets an estimated `grade`

---

### Requirement: Grade System

Grade SHALL measure value only — never effort. Grade and status are orthogonal (CONST-03).

| Grade | Meaning | Auto-refine? |
|---|---|---|
| `gold` | Highest value | Yes (auto-queued at Sort) |
| `silver` | High value | Yes (auto-queued at Sort) |
| `bronze` | Marginal value | No — operator decides: override or slag |
| `coal` | Low value | No — slags to Tailings |

Grade is **estimated** at `ore` (by human or agent assay) and **confirmed** at
`refine`. Refining is verification: a confirmed downgrade may route material back
to Tailings rather than completing the refine.

#### Scenario: Grade gate queues silver and gold only
- **WHEN** the refine detector runs
- **THEN** it queues efforts with `status: ore` and `grade` in `{silver, gold}`
- **THEN** it omits efforts with `grade: bronze` or `grade: coal`

#### Scenario: Grade confirmed at refine may route back to Tailings
- **WHEN** the refine executor processes a proposal and the confirmed grade is below the gate
- **THEN** the operator may route the effort to `70-Tailings/` instead of completing the Treasury write

---

### Requirement: Sort Triage

Sort SHALL be applied as a decision point at `ore`, after grade estimation, routing material one of four ways:

1. **Routine refine** — grade ∈ {silver, gold}: auto-queue for the refine pipeline.
2. **Crucible** — rare, by exception: ambiguous or ultravaluable ore sent to the
   independent validation apparatus (INV-8; build deferred).
3. **Slag to Tailings** — grade ∈ {bronze, coal}, or not economic now: move to
   `70-Tailings/` with a `slag_reason`.
4. **Waste to Spoil** — proven false or empty: move to `71-Spoil/` with `status: waste`.

#### Scenario: Coal always slags
- **WHEN** an effort reaches `status: ore` with `grade: coal`
- **THEN** Sort routes it to `70-Tailings/` (not auto-refined, not discarded as waste)

---

### Requirement: Tailings Retention (INV-10)

Slagged efforts in `70-Tailings/` MUST NOT be auto-purged. They retain their
full Dig metadata (grade estimate, `slag_reason`) for re-prospecting when extraction
economics shift (a cheaper model, a new tool, a capability jump).

The re-prospect script (`vault-reprospect.py`) is detection-only: it lists slagged
efforts with their grade and reason. Promotion back to `30-Sites/` is always a
human-gated move.

#### Scenario: Re-prospect lists slagged efforts without writing
- **WHEN** the re-prospect script runs against `70-Tailings/`
- **THEN** it prints each slagged effort's slug, grade, and `slag_reason`
- **THEN** it writes nothing (detection only)

---

### Requirement: Value Preservation (INV-9)

Bullion in `40-Treasury/` MUST NOT be moved to `71-Spoil/` or deleted by automation.
Only effort husks (the residue of a completed refine in `30-Sites/`) are disposed
to `71-Spoil/`. Waste (proven-false content) is the only material discarded.

#### Scenario: Dispose moves husk, not bullion
- **WHEN** the dispose script runs for a completed effort
- **THEN** the `30-Sites/<slug>/` directory moves to `71-Spoil/<slug>/`
- **THEN** the corresponding Treasury note is untouched
- **THEN** exactly one Git commit is produced (INV-2)

#### Scenario: Dispose is cleanly revertible
- **WHEN** `git revert` is applied to the dispose commit
- **THEN** the prior state is cleanly restored
