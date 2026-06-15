---
title: "Value Mining — System Diagrams"
version: "1.1"
source: "source/vault-diagrams-draft.md"
---

# Value Mining — System Diagrams

Seven Mermaid diagrams covering the full system. Paste any code block into an Obsidian
note wrapped in a ```` ```mermaid ```` fence to render interactively.

**Suggested reading order (first encounter):**
1 Value Chain → 5 Folder Stack → 2 Lifecycle → 4 Sort Router → 3 Refine Pipeline → 7 Containment Boundary → 6 GitOps Loop

Orientation first, structure second, mechanics third, safety and infrastructure last.

---

## Diagram 1: Value Chain Overview

*What is the end-to-end flow of material through the system?*

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'primaryColor': '#42a5f5',
  'primaryTextColor': '#ffffff',
  'primaryBorderColor': '#1976d2',
  'lineColor': '#546e7a',
  'secondaryColor': '#f9a825',
  'tertiaryColor': '#9e9e9e'
}}}%%
flowchart LR
    CL([20-Claims]):::blue
    LB([10-Logbook]):::blue
    SI([30-Sites<br/>Prospect→Dig→Ore]):::blue
    SORT{Sort}:::blue
    REF[Refine]:::gold
    TR([40-Treasury]):::gold
    MN([50-Mint]):::teal
    FG([60-Forge]):::teal
    TL([70-Tailings]):::brown
    SP([71-Spoil]):::brown
    CR([80-Crucible]):::crucible

    CL -->|stake & prospect| SI
    SI -.->|records| LB
    TR -.->|records| LB
    SI -->|ore| SORT
    SORT -->|highgrade<br/>silver/gold| REF
    SORT -->|lowgrade / uneconomic| TL
    SORT -.->|ambiguous /<br/>ultravaluable| CR
    SORT -->|proven false| SP
    REF ==>|bullion| TR
    CR -.->|direct inject<br/>crucible:true| TR
    TR -->|draw| MN
    TR -->|draw| FG
    TL -.->|re-prospect<br/>economics shift| SORT

    classDef blue fill:#42a5f5,stroke:#1976d2,color:#fff
    classDef gold fill:#f9a825,stroke:#f57f17,color:#fff
    classDef teal fill:#00897b,stroke:#00695c,color:#fff
    classDef brown fill:#8d6e63,stroke:#5d4037,color:#fff
    classDef crucible fill:#e65100,stroke:#bf360c,color:#fff
```

**Reading guide:**
- Solid arrows → material flow (mandatory path)
- Dashed arrows `-.->` → rare / observing paths
- Thick arrow `==>` → the primary value deposit (ore becomes bullion)
- `10-Logbook` floats parallel, recording without transforming
- `80-Crucible` and `re-prospect` are dashed — rare/exceptional

---

## Diagram 2: Effort Lifecycle

*What states can an effort be in, and what transitions are valid?*

```mermaid
%%{init: {'theme': 'base'}}%%
stateDiagram-v2
    direction TB

    [*] --> prospect : Claim promoted to Site

    prospect --> dig : Operator begins investigation
    dig --> ore : Digging produces material<br/>grade estimated

    ore --> refining : Sort — highgrade clears gate
    ore --> slagged : Sort — uneconomic now
    ore --> waste : Sort — proven false → Dispose
    ore --> refining : Crucible — rare<br/>ambiguous/ultravaluable

    slagged --> ore : Re-prospect<br/>economics shifted

    refining --> spent : Bullion banked in Treasury<br/>husk disposed
    refining --> slagged : Refine downgrade<br/>confirmed lower than estimated

    spent --> [*]
    waste --> [*]

    note right of slagged
        70-Tailings<br/>Retained, re-minable
    end note

    note right of spent
        71-Spoil<br/>Terminal
    end note

    note right of waste
        71-Spoil<br/>Terminal
    end note
```

**Reading guide:**
- `slagged` is the only re-entrant state — it can return to `ore` via re-prospect
- `spent` and `waste` are true terminal states (no exit transition)
- `refining` is a process, not a folder — it bridges Sites → Treasury
- Grade values and actor handoff are in Diagrams 3 and 4

---

## Diagram 3: Refine Pipeline (Swimlane)

*Who does what, in what order — and where is the human gate?*

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {
  'primaryColor': '#42a5f5',
  'lineColor': '#546e7a'
}}}%%
flowchart TB
    subgraph SCRIPT["🔧  Script (S — deterministic)"]
        direction TB
        DET[Detect ore at gate]:::script
        Q>_refine-queue.json]:::script
        EXEC[Write bullion<br/>+ link Catalog]:::script
        ARCH[Dispose husk<br/>→ 71-Spoil]:::script
        COM[git commit]:::script
    end

    subgraph AGENT["🤖  Agent (A — Hermes)"]
        direction TB
        PROP[Generate proposal]:::agent
        PJ>_refine-proposals/*.json]:::agent
    end

    subgraph HUMAN["👤  Human (H — operator)"]
        direction TB
        REV[Review proposal]:::human
        GATE{Approve?}:::gate
        AJ>_refine-approved/*.json]:::human
        REJ[Reject / revise]:::human
    end

    DENIED(["✕  40-Treasury<br/>DENIED — INV-4"]):::denied

    DET -->|queued ore<br/>silver/gold| Q
    Q -->|effort path| PROP
    PROP -->|proposal JSON| PJ
    PJ --> REV
    REV --> GATE
    GATE -->|yes| AJ
    GATE -->|no| REJ
    REJ -.->|revised / re-propose| PJ
    AJ ==>|approved proposal| EXEC
    EXEC --> ARCH
    ARCH --> COM
    PROP -. "DENIED (INV-4)" .-> DENIED

    classDef script fill:#42a5f5,stroke:#1976d2,color:#fff
    classDef agent fill:#90caf9,stroke:#1976d2,color:#333
    classDef human fill:#66bb6a,stroke:#388e3c,color:#fff
    classDef gate fill:#66bb6a,stroke:#1b5e20,color:#fff,font-weight:bold
    classDef denied fill:#ef9a9a,stroke:#c62828,color:#c62828,stroke-dasharray:5 5
```

**Reading guide:**
- The `Approve?` gate (green diamond) is the single chokepoint — nothing reaches the Treasury without it
- The red dashed denial node shows the structurally impossible path: agent cannot write directly to Treasury (INV-4)
- Handoff boundaries: Agent→Human = proposal JSON only; Human→Script = approved JSON only
- `git commit` closes every automated mutation (INV-2)

---

## Diagram 4: Sort Router

*How does ore get triaged — what goes where and why?*

```mermaid
%%{init: {'theme': 'base'}}%%
flowchart TD
    ORE([Ore<br/>grade estimated]):::blue

    ORE --> PF{Proven false<br/>or empty?}
    PF -->|yes → waste| WASTE
    PF -->|no| UV

    UV{Ultravaluable<br/>or ambiguous?}
    UV -->|yes → direct Crucible| CRUC
    UV -->|no| HG

    HG{Highgrade?<br/>silver / gold}
    HG -->|silver/gold<br/>→ routine refine| SMELT
    HG -->|bronze / coal| JW

    JW{Juice worth<br/>the squeeze?}
    JW -->|bronze:<br/>maybe worth it| BRONZE
    JW -->|coal:<br/>defer to tailings| SLAG

    BRONZE[Bronze: marginal<br/>evaluate]:::marginal
    BRONZE -->|operator override| SMELT
    BRONZE -->|not worth it now| SLAG

    SMELT[Routine Refine pipeline<br/>detect→propose→gate→execute]:::gold
    CRUC[80-Crucible<br/>direct inject, human-attended]:::crucible
    SLAG[[70-Tailings<br/>slagged]]:::brown
    WASTE[[71-Spoil<br/>waste]]:::brown

    classDef blue fill:#42a5f5,stroke:#1976d2,color:#fff
    classDef gold fill:#f9a825,stroke:#f57f17,color:#fff
    classDef crucible fill:#e65100,stroke:#bf360c,color:#fff
    classDef brown fill:#8d6e63,stroke:#5d4037,color:#fff
    classDef marginal fill:#ffcc02,stroke:#f9a825,color:#333
```

**Reading guide:**
- First decision: discard or keep? (proven false → Spoil)
- Second: does it need special handling? (ultravaluable/ambiguous → Crucible)
- Third: grade-gate check (silver/gold auto-refine; coal/bronze need manual decision)
- `Bronze` is the only marginal case — neither auto-refines nor auto-slags; operator decides
- `70-Tailings` and `71-Spoil` shown with double borders — terminal/retained states

---

## Diagram 5: Folder Stack + Layers

*What is the physical folder structure, grouped by layer and ordered by touch frequency?*

```mermaid
%%{init: {'theme': 'base'}}%%
flowchart TD
    subgraph ONBOARD["🟦  Onboarding — deletable after familiarisation"]
        D00["00-Docs"]:::onboard
    end

    subgraph DAILY["🔵  Daily Touch — Layer 2 · touch: daily"]
        D10["10-Logbook"]:::blue
        D20["20-Claims"]:::blue
        D30["30-Sites"]:::blue
    end

    subgraph VALUE["🟡  Crown Jewels — Layer 1 · touch: weekly"]
        D40["40-Treasury"]:::gold
        CAT["  └─ Catalog (MOCs)"]:::gold
    end

    subgraph PRODUCE["🟢  Production — future · touch: occasional"]
        D50["50-Mint"]:::teal
        D60["60-Forge"]:::teal
    end

    subgraph DISPOSE["🟫  Disposal · touch: occasional"]
        D70["70-Tailings"]:::brown
        D71["71-Spoil"]:::brown
    end

    subgraph SPECIAL["🔴  Special Ops · touch: rare"]
        D80["80-Crucible"]:::crucible
    end

    subgraph INFRA["⚙️  Infrastructure — Layer 0 · touch: set-and-forget"]
        D97["97-Molds"]:::infra
        D98["98-Warehouse"]:::infra
        D99["99-Operations"]:::infra
    end

    D20 -->|prospect| D30
    D30 -->|refine| D40
    D40 -->|draw| D50
    D40 -->|draw| D60
    D30 -->|slag| D70
    D30 -->|dispose| D71

    classDef onboard fill:#e0e0e0,stroke:#9e9e9e,color:#333
    classDef blue fill:#42a5f5,stroke:#1976d2,color:#fff
    classDef gold fill:#f9a825,stroke:#f57f17,color:#fff
    classDef teal fill:#00897b,stroke:#00695c,color:#fff
    classDef brown fill:#8d6e63,stroke:#5d4037,color:#fff
    classDef crucible fill:#e65100,stroke:#bf360c,color:#fff
    classDef infra fill:#9e9e9e,stroke:#616161,color:#fff
```

**Reading guide:**
- Top-to-bottom = touch frequency order (daily areas first, infrastructure last)
- Folder number prefix = sort order in any file explorer
- Subgraph colour = layer membership
- Spine edges show material flow only; internal detail is in other diagrams
- `00-Docs` is deletable once the operator is familiar

---

## Diagram 6: Layer 0 GitOps Loop

*How does the self-describing Operations layer work?*

```mermaid
%%{init: {'theme': 'base'}}%%
flowchart LR
    SRC>99-Operations/scripts/*.md<br/>literate meta-script notes]:::infra
    REN[render<br/>user-invoked]:::human
    HOST>~/bin/vault-*.py<br/>deployed artifacts]:::infra
    REC[reconcile]:::script
    OK([✓ ok<br/>in sync]):::ok
    DRIFT([⚠ DRIFT<br/>alert]):::drift
    FIX[Human fixes<br/>source in Layer 0]:::human
    BLOCK(["✕  NEVER auto-fix<br/>INV-3"]):::denied

    SRC -->|extract code block| REN
    REN -->|deploy to target| HOST
    HOST -->|compare| REC
    SRC -->|compare| REC
    REC -->|match| OK
    REC -->|mismatch| DRIFT
    DRIFT -->|human resolves| FIX
    FIX -->|edit source<br/>Layer 0 only| SRC
    HOST -. "NEVER auto-fix (INV-3)" .-> BLOCK

    classDef infra fill:#9e9e9e,stroke:#616161,color:#fff
    classDef human fill:#66bb6a,stroke:#388e3c,color:#fff
    classDef script fill:#42a5f5,stroke:#1976d2,color:#fff
    classDef ok fill:#a5d6a7,stroke:#388e3c,color:#333
    classDef drift fill:#ef9a9a,stroke:#c62828,color:#c62828
    classDef denied fill:#ef9a9a,stroke:#c62828,color:#c62828,stroke-dasharray:5 5
```

**Reading guide:**
- `render` is always user-invoked — no automation deploys to host without a human command
- `reconcile` detects drift; it never overwrites (INV-3)
- The dashed denial node: host artifacts are never authoritative and must never auto-update the source
- The only correction path: human sees DRIFT → edits the Layer-0 source → re-runs `render`

---

## Diagram 7: Containment Boundary

*What can each actor touch, and what paths are structurally impossible?*

This diagram tells the containment story, not the full permission grid. The exhaustive
per-area R/W/— matrix lives in the build PRD §6.1 — this diagram complements it by
making the boundary visible: the agent's reachable set, the single human gate, and the
protected zone it cannot enter.

```mermaid
%%{init: {'theme': 'base'}}%%
flowchart LR
    subgraph AGENT["AGENT — Hermes · writes ONLY inside this box"]
        AS["Assigned Site<br/>(30-Sites)"]:::agent
        PROP["_refine-proposals/"]:::agent
    end

    HUMAN(["Human reviews<br/>the proposal"]):::human
    GATE{{"_refine-approved/<br/>GATE — human only"}}:::gate
    EXEC["Script applies<br/>approved proposal"]:::script

    subgraph PROTECTED["PROTECTED ZONE — agent cannot enter"]
        TR["40-Treasury<br/>+ Catalog"]:::gold
        OPS["99-Operations"]:::infra
        CR["80-Crucible"]:::crucible
        SP["71-Spoil"]:::brown
        OS["Other Sites<br/>(30-Sites)"]:::blue
    end

    AS -->|distill insight| PROP
    PROP -->|H reads| HUMAN
    HUMAN ==>|approves| GATE
    GATE ==>|approved JSON| EXEC
    EXEC ==>|gated write only| TR

    AGENT -. "✕ INV-4: no direct write" .-> TR
    AGENT -. "✕ INV-5: actor ≠ owner" .-> OPS
    AGENT -. "✕ cannot self-promote" .-> GATE
    AGENT -. "✕ no agent disposal" .-> SP
    AGENT -. "✕ INV-8: independent operator only" .-> CR
    AGENT -. "✕ assigned site only" .-> OS

    linkStyle 0,1,2,3,4 stroke:#388e3c,stroke-width:3px
    linkStyle 5,6,7,8,9,10 stroke:#c62828,stroke-width:1.5px

    classDef agent fill:#42a5f5,stroke:#1976d2,color:#fff
    classDef human fill:#66bb6a,stroke:#388e3c,color:#fff
    classDef gate fill:#66bb6a,stroke:#1b5e20,color:#fff,font-weight:bold
    classDef script fill:#90caf9,stroke:#1976d2,color:#333
    classDef gold fill:#f9a825,stroke:#f57f17,color:#fff
    classDef infra fill:#9e9e9e,stroke:#616161,color:#fff
    classDef crucible fill:#e65100,stroke:#bf360c,color:#fff
    classDef brown fill:#8d6e63,stroke:#5d4037,color:#fff
    classDef blue fill:#42a5f5,stroke:#1976d2,color:#fff

    style AGENT fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style PROTECTED fill:#ffebee,stroke:#c62828,stroke-width:2px
```

**Reading guide:**
- **Green thick path** is the only route into the protected zone: assigned Site → proposal → human → gate → script → Treasury. Every link passes through the human.
- **Red thin dashed lines** are not rules the agent follows — they are capabilities it does not have. Each is annotated with the invariant that makes it structurally impossible.
- The agent box (blue tint) and the protected zone (red tint) never touch except through the gate.
- Agent read access (not drawn): R on `10-Logbook`, `70-Tailings`, restricted R on `40-Treasury` during cloud bootstrap. Reads do not threaten containment; writes do.

| Denied path | Invariant |
|---|---|
| Agent → Treasury (write) | INV-4 |
| Agent → Operations | INV-5 |
| Agent → `_refine-approved/` | cannot self-promote |
| Agent → Spoil | no agent disposal |
| Agent → Crucible | INV-8 |
| Agent → other Sites | bounded scope |
