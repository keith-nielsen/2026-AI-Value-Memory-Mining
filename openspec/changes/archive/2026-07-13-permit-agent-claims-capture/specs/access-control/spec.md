<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: Area Access Matrix

Each vault area SHALL grant the access shown below; any actor exceeding its cell is a violation.

| Area | H | A | S | Notes |
|---|---|---|---|---|
| `99-Operations/` | RW | — | R | INV-5: actor ≠ owner of definition |
| `97-Molds/` | RW | R | R | Templates; instantiation only |
| `98-Warehouse/` | RW | W¹ | RW | Reference stockroom: retained source material (binaries + digitized refs), shelved by media type |
| `00-Docs/` | RW | R | R | Deletable onboarding |
| `20-Claims/` | RW | RW² | RW | Capture zone — agent may capture directly |
| `20-Claims/_refine-proposals/` | R | W | R | Agent deposit point |
| `20-Claims/_refine-approved/` | W | — | R | **The gate.** Agent cannot self-promote. |
| `10-Logbook/` | RW | R | RW | Daily logs + reviews |
| `30-Sites/<assigned>` | RW | RW¹ | RW | Agent writes only to its assigned Site |
| `30-Sites/<other>` | RW | — | RW | Agent cannot touch other Sites |
| `40-Treasury/` | RW | R³ | gated-W⁴ | Crown jewels — INV-4 |
| `40-Treasury/Catalog/` | RW | R | gated-W⁴ | indexes; human curates |
| `50-Mint/` | RW | —⁵ | RW | Future production (deferred) |
| `60-Forge/` | RW | —⁵ | RW | Future production (deferred) |
| `70-Tailings/` | RW | R | RW | Slagged; re-minable |
| `71-Spoil/` | RW | — | RW | Terminal discard; agent excluded |
| `80-Crucible/` | RW | —⁶ | RW | INV-8: independent operator only |

¹ Agent writes only within its assigned Site / attachment for that Site.  
² Agent may capture directly into `20-Claims/` (create Claim notes) — an operator decision recorded at
the ADR-0022 Gate-4 and formalized in ADR-0025 (essential capture efficiency / comfort-of-ride). This
relaxes the earlier proposals-only capture path; it does **not** touch the `_refine-approved/` gate
(Agent `—`), so promotion INTO `40-Treasury/` remains human-gated (INV-4). `20-Claims/` is a Layer-2
Workings area (CONST-02), the least-protected layer, so direct agent capture is consistent with the
layer model.  
³ Agent read of Treasury is restricted during cloud bootstrap; full read only under local/egress-controlled model.  
⁴ Script writes Treasury only when applying a human-approved proposal from `_refine-approved/`.  
⁵ Future agent access (Mint/Forge) to be scoped when those segments are designed.  
⁶ Crucible uses an independent model/operator by design; main agent excluded (INV-8).

#### Scenario: Agent cannot write Treasury directly
- **WHEN** an agent process attempts to write any file under `40-Treasury/`
- **THEN** the commit-gate hook blocks the commit with an INV-4 violation message
- **THEN** the refine executor is the only permitted write path

#### Scenario: Agent cannot write Operations
- **WHEN** an agent process attempts to write any file under `99-Operations/`
- **THEN** the commit-gate hook blocks the commit with an INV-5 violation message

#### Scenario: Agent cannot self-promote a proposal
- **WHEN** an agent process moves a file from `_refine-proposals/` to `_refine-approved/`
- **THEN** this is treated as an INV-4 violation (the gate is human-only by convention;
  OS-level enforcement is deferred per §14.1)

#### Scenario: Agent may capture directly into 20-Claims
- **WHEN** an agent process (at operator direction) writes a new Claim note under `20-Claims/`,
  outside `_refine-approved/`
- **THEN** the write is permitted and is not a violation — `20-Claims/` is a Layer-2 Workings area and
  no INV-4/INV-5 zone is touched
- **THEN** promotion of any resulting value into `40-Treasury/` still requires the human
  `_refine-approved/` gate
