<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution — value-memory-mining

This document defines the **protected principles and design metaphors** that give
the Value Mining system its intuitiveness, consistency, and cognitive flow. These
principles are **not immutable** — a future contributor may overturn them — but
they are **load-bearing**, and may be overturned only through a deliberate,
planned, regression-tested upheaval that explicitly states *what is being
sacrificed*.

> **An AI agent MUST NEVER alter a constitutional element without first surfacing
> the consequences to a human and obtaining explicit confirmation. See §5.**

---

## 1. Protected Principles

Each principle has: an **id**, a **tier**, the **principle or metaphor**,
its **rationale**, the **"what breaks"** clause, and an **ADR reference**.

Spec files and vault artifacts that embody a principle are tagged with
`protects: [<id>]` in their frontmatter. CI fails if a diff touches a
`protects:`-tagged element without the full Informed-Upheaval ceremony (§3).

---

### CONST-01 — The Value Mining Metaphor
`tier: 1` · `adr: ADR-0002`

**Principle:** The pipeline uses mining vocabulary throughout: Claim → Dig → Ore →
Sort → Refine → Bank → Treasury → Polish. Transition verbs: **dig** (Claim→Site),
**slag** (Site→Tailings), **dump** (Site→Spoil), **redig** (Tailings→Site), **refine**
(ore→bullion), **bank** (the human gate that authorizes bullion into the Treasury).
**Prospect** is the upstream human act that discovers Claims from the world (it produces
the inbox; it is not a Site state); **reprospect** is the bounded survey that re-evaluates
Tailings. Side paths: Slagged→Tailings (retained, re-minable), Spoil (terminal).
Downstream: Mint/Forge. Every stage name lets you infer the next stage and the
material's value-state.

**Rationale:** One coherent extraction-of-value frame where a stage's name predicts
the next stage and the material's current state. Inference replaces memorization;
the vocabulary is self-teaching.

**What breaks if you override this:** Mixing or abandoning the metaphor makes names
stop predicting structure. Newcomers must memorize an arbitrary taxonomy. The
vocabulary fragments and cognitive flow collapses. Every spec, script, template,
diagram, index name, and glossary entry references this frame — the blast radius is
the entire system.

---

### CONST-02 — The Three-Layer Model
`tier: 1` · `adr: ADR-0002`

**Principle:** Layer 0 = Operations (`99-Operations/`, the mine's machinery — *how*).
Layer 1 = Treasury (`40-Treasury/`, durable value — *what*). Layer 2 = Workings
(`20-Claims/`, `10-Logbook/`, `30-Sites/`, temporal — *now*).

**Rationale:** Separates stable crown-jewels from high-churn temporal work and from
infrastructure. Each layer has a distinct stability profile and touch frequency.
The access-control model is layer-aware; the safety invariants (INV-4, INV-5, INV-9)
derive their meaning from layer membership.

**What breaks if you override this:** Collapsing layers re-couples churn with durable
value. The stability guarantees and the entire access-control rationale lose their
basis. INV-4 (bounded write scope) becomes incoherent without Layer 1/Layer 0
as the protected zones.

---

### CONST-03 — Grades = Value Only (`coal | bronze | silver | gold`)
`tier: 1` · `adr: ADR-0003`

**Principle:** Grade answers "how valuable," status answers "how far along." They are
orthogonal. The four grades use the Olympic medal intuition (bronze = recognizable
third-place, not "copper"). Grade is estimated at `ore`, confirmed at `refine`.

**Rationale:** Conflating value with effort is the classic PKM failure mode — it
produces incoherent prioritization. The medal anchor gives instant at-a-glance
value ranking without a lookup. "Bronze, not copper" is the specific choice that
preserves the intuition.

**What breaks if you override this:** Conflating value with effort makes Sort
decisions incoherent. Swapping the medal names (e.g., introducing "copper") forfeits
the at-a-glance ranking and breaks every reference in scripts, docs, and the
vocabulary lint.

---

### CONST-04 — Folder Numbering: Zero-Padded, Gapped, Touch-Frequency Order
`tier: 1` · `adr: ADR-0002`

**Principle:** Two-digit zero-padded numbers, gapped by 10s, ordered from most
frequently touched (daily logs at top) to least (infra at bottom). Explorer becomes
a frequency-ordered workspace without configuration.

**Rationale:** The file explorer is the primary navigation UI. Frequency order puts
today's work at the top by default. Zero-padding ensures correct lexicographic sort
in every interface. 10s gaps allow insertion without cascading renames.

**What breaks if you override this:** Alphabetic or arbitrary order destroys
at-a-glance workflow positioning. Ungapped numbering forces cascading renames when
bands are added. Every script, spec, and diagram references the numbered paths.

---

### CONST-05 — Domain via Metadata + Catalog (indexes), Never Folders
`tier: 1` · `adr: ADR-0002` · `protects: [INV-12]`

**Principle:** Pillar membership is expressed through the `pillars` frontmatter field,
tags, and index links inside `40-Treasury/Catalog/`. The Treasury root contains no
pillar subfolders.

**Rationale:** Knowledge is many-to-many — a note belongs to multiple pillars.
Folders enforce a single parent, breaking multi-domain membership and portability.
Tags + indexes preserve flexible membership while Obsidian's graph and search remain
accurate.

**What breaks if you override this:** Folder taxonomy forces false single-classification.
Multi-pillar notes become impossible or duplicated. Portability breaks because the
classification is encoded in the path, not the content. INV-12 and the linter's
pillar-validation logic both assume a flat Treasury.

---

## 2. Tier Classification

Two lenses classify constitutional elements. Keep them distinct.

**The criticality bands** (PRD §5) order INVs by how fundamental they are:
Substrate → Safety → Value → Consistency.

**The tiers below** classify by overridability and required ceremony:

| Tier | Elements | Override path |
|------|----------|---------------|
| **Tier 0 — Inviolable** | INV-1 through INV-8, INV-11, INV-14 | Change the enforcing code/hooks/CI. The friction is structural. |
| **Tier 1 — Foundational frame** | CONST-01 through CONST-05 + INV-12 | Full Informed-Upheaval Protocol (§3). This is what the constitution most exists to protect. |
| **Tier 2 — Conventions** | INV-13 (wikilinks), cron schedules, kebab specifics, pillar names | Ordinary OpenSpec change — no ceremony required. |

---

## 3. The Informed-Upheaval Protocol

An override of any **Tier-0 or Tier-1** element is a first-class OpenSpec change
of type **`constitution-override`**. It must pass four gates **in order**.
Doc-only edits to `protects:`-tagged elements are rejected by CI without the ceremony.

Use the template: `openspec/templates/constitution-override/proposal.md`

### Gate 1 — CHECK (impact analysis)
- Name the principle ID(s) being overridden.
- Restate the "what breaks" consequences **in the proposer's own words**.
- Enumerate the full blast radius: every spec, script, template, diagram, and
  vocabulary term that references the element.

### Gate 2 — PLAN (migration + regression)
- A written migration plan covering every artifact in the blast radius.
- The explicit set of regression tests that must pass: acceptance tests,
  naming/vocabulary lints, `openspec validate`.
- How every dependent artifact is updated in lockstep.

### Gate 3 — EXECUTE + REGRESSION-TEST
- Implement the change.
- All named tests and CI pass green before Gate 4.

### Gate 4 — RE-CHECK + HUMAN SIGN-OFF
- A second review confirming the blast radius was fully addressed.
- Consequences are explicitly accepted.
- **Explicit human sign-off recorded** (not agent-delegatable).
- An ADR captures context / options / choice / consequence / **sacrifice**.
- The change is archived as a permanent, discoverable record.

---

## 4. Enforcement Mechanism

| Mechanism | What it does |
|---|---|
| `protects:` frontmatter tag | Marks spec files and vault artifacts as constitutionally protected |
| `constitution-lint` (CI) | Fails if a diff touches a `protects:`-tagged element without a complete `constitution-override` (acknowledgment + ADR present) |
| `vocabulary-lint` (CI) | Validates the Value Mining controlled glossary; off-metaphor terms (e.g., *garden*, *evergreen*, *harvest*) fail the build |
| Branch protection | Require CI green + human review on PRs touching `openspec/constitution.md` or `protects:`-tagged paths |
| Change template | `constitution-override/proposal.md` has mandatory CHECK/PLAN/RE-CHECK/SIGN-OFF sections; missing any → change is invalid |

---

## 5. AI-Agent Hard Stop

> **An AI agent (Claude Code, Hermes, any model) MUST NOT propose, apply, or merge
> any change that touches a constitutional (Tier-0 / Tier-1) element without first
> (a) surfacing the principle, its rationale, and its "what breaks" consequences to
> the human, and (b) receiving explicit human confirmation of the sacrifice.**
>
> Agents may *draft* the CHECK and PLAN sections of a `constitution-override` change.
> The SIGN-OFF gate (§3, Gate 4) is **human-only**.
>
> An agent that detects it is about to modify a `protects:`-tagged element must
> **stop and present the trade-off — never proceed silently**.

This protocol is the selected mechanism because it is simultaneously **explicit**
(consequences documented), **planned** (override is a first-class change, not an
edit), **regression-tested** (Gates 2–3), **mechanically enforced** (CI fails
without the ceremony), and **AI-safe** (human-only sign-off + agent hard-stop).

It mirrors the same propose → surface → consciously-approve → record pattern the
vault uses at the object level (`_refine-proposals/` → `_refine-approved/`),
applied to the spec layer itself.
