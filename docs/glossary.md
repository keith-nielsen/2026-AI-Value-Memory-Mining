---
title: "Value Mining — Glossary"
source: "openspec/ corpus — constitution, capability specs, ADRs"
---

# Value Mining — Glossary

---

## Value Mining Terms

**Value Mining** — the methodology: the staged extraction of durable knowledge value
from raw inputs. Every term below maps to a stage or artifact in this pipeline.

**Claim** — a staked, unprospected area of interest; raw capture ear-marked for
investigation. Lives in `20-Claims/`.

**Site** — an active working where extraction happens; one per effort. Lives in
`30-Sites/<slug>/`.

**Prospect** — the upstream, human act of going into the world and discovering value
worth a Claim. It *produces* the inbox; it is **not** a Site state and has no script (the
search space is unbounded — human agency only). Surfaces as a Daily intention; skippable
when the Claims backlog is deep.

**Dig** — the move that lifts a Claim into a Site and begins active extraction
(`status: dig`). A Site is born here, already committed to work. (Verb: `dig`.)

**Ore** — the raw extracted material: digging has produced something, and its grade
has been *estimated* (assay). This is the Sort/refine-gate decision point. (Effort
lifecycle stage.)

**Sort** — the 3-way triage of ore: clear high-grade → routine Refine; ambiguous /
ultravaluable → Crucible; juice-not-worth-squeeze → Tailings; proven false → Spoil.

**Refine** — verify and structure the durable value into bullion (a knowledge note),
*confirming (and possibly revising) the grade* in the process. The act of refining is
verification; a confirmed downgrade may route the material back to slag. (Knowledge
stage; also the name of the promotion pipeline.)

**Polish** — perpetual incremental upkeep of high-value bullion. Never "finished."
(Knowledge stage.)

**Bullion** — refined, verified knowledge deposited in the Treasury. The Value Mining
output.

**Grade** — the value tier of material: `coal < bronze < silver < gold`. Estimated at
`ore`, confirmed at `refine`. Pure value to the operator's goals — never a measure of
effort.

**Crucible** — the rare, by-exception heavy-validation apparatus: independent
model/operator, steelman harnesses, synthetic QA, math labs. Invoked for ambiguous or
ultravaluable ore. Produces a direct injection into Treasury with `crucible: true`
provenance flag. Carries dual meaning: smelting vessel and trial-by-fire. (Build
deferred.)

**Mint** — strike dated, immutable editions (coinage) from Treasury bullion for
repeatable, reusable value. (Build deferred.)

**Forge** — smith Treasury bullion into complex, custom, bespoke wares. (Build
deferred.)

**Slagged / Tailings** — ore with real value that is not economic to extract *now*.
Retained, not discarded; re-evaluated when extraction economics shift (a cheaper model,
a new tool, a capability jump). Lives in `70-Tailings/`.

**Spoil** — the terminal discard heap. Contains *spent* husks (value already banked in
Treasury; the residue of a successful refine) and *waste* (proven false or empty — a
dry hole, not ore). Never re-mined. Lives in `71-Spoil/`.

**Reprospect** — the read-only **survey** that re-evaluates slagged Tailings when
extraction economics shift. A *bounded, closed-world* problem (a finite known set against
the known pipeline state), so it is **automatable** — unlike prospecting the open world.
Surfaces candidates; the move back to a Site (verb: **redig**) is a separate human-gated step.

**Bank** — the human gate that authorizes refined bullion into the Treasury (state:
`authorized`). The agent *deposits* a proposal; the human *banks* it; the script writes it.

---

## Lifecycle Vocabulary

The verbs, surveys, and states of the effort lifecycle. *Verbs are actions; surveys read,
moves write; folders are authentic place-nouns; `refine`+`bank` are the gated exception.*

| Phase | Verb | Kind | Move | Status | Agency |
|-------|------|------|------|--------|--------|
| inflow | **prospect** | survey · *no script* | world → `20-Claims` | (raw) | human, **unbounded** |
| start | **dig** | move | Claim → `30-Sites` | `dig` | human |
| assay | — | in-place | — | `dig → ore` | — |
| set aside | **slag** | move | Site → `70-Tailings` | `slagged` | human/script |
| discard | **dump** | move | Site → `71-Spoil` | `spent` \| `waste` | human/script |
| recycle-scan | **reprospect** | survey · *script* | `70-Tailings` | `slagged` | AI, **bounded** |
| recycle | **redig** | move | Tailings → `30-Sites` | `dig` | human |
| smelt | **refine** | gated transform | ore → proposal | (refined) | agent/script |
| gate | **bank** | human gate | proposal → `40-Treasury` | **`authorized`** | human |
| upkeep | polish | in-place | `40-Treasury` | `refined → polished` | human |

**Agency gradient:** prospecting the open world is unbounded → human-only; reprospecting a
known Tailings set is bounded → automatable. That's why `reprospect` earns a script and
`prospect` doesn't.

---

## Structural Terms

**Vault** — the top-level Obsidian container (root directory); also a Git repository.

**Note** — one `.md` file with YAML frontmatter.

**Pillar** — a top-level life/knowledge domain. Expressed as metadata + tags + a
Catalog entry (index), *never* as a knowledge subfolder. Configured in
`99-Operations/config.env`.

**Catalog** — the collection of Maps of Content (indexes) inside the Treasury; each index
is a human-curated "front door" to a pillar. Lives in `40-Treasury/Catalog/`.

**index (Map of Content)** — a curated index note that organises links to related
knowledge notes within a pillar. One per pillar plus a Home index.

**Layer 0 / Operations** — the self-describing operational partition
(`99-Operations/`): scripts, config, rationale (literate meta-scripts). Source of
truth for operational artifacts. Outside the mining metaphor — it is the mine's
machinery, not ore.

**Layer 1 / Treasury** — refined and polished bullion (`40-Treasury/`). Never deleted
by automation.

**Layer 2 / Workings** — capture, logs, active and slagged sites, spent husks:
`20-Claims/`, `10-Logbook/`, `30-Sites/`, `70-Tailings/`, `71-Spoil/`.

**Render / Reconcile** — extract operational artifacts from Layer 0 to host targets
(user-invoked); detect drift between deployed and source without overwriting (INV-3).

**Gate** — a required human approval before a write executes. In the Refine pipeline,
the gate is the act of moving a proposal from `20-Claims/_refine-proposals/` to
`20-Claims/_refine-approved/`.

**Deposit-not-merge** — the cardinal rule of agent integration: an agent's definition
of done is a schema-valid proposal JSON deposited in `_refine-proposals/`. The worker
calls `kanban_complete` on deposit. The human gate and the executor run outside the
kanban flow. A kanban `done` is not a Treasury write.

**Literate meta-script** — an operational artifact stored as a Markdown note in
`99-Operations/scripts/` with YAML frontmatter and a single fenced code block.
`render` extracts the code block to the host; `reconcile` detects drift.

---

## Actor Classes

| Class | Symbol | Scope |
|-------|--------|-------|
| Human | H | Operator; owns all gates and Layer 0 |
| Agent | A | Assigned Site + `_refine-proposals/` only |
| Script | S | Deterministic; applies approved proposals; no network/LLM |

---

## Execution Classes

| Class | Meaning |
|-------|---------|
| `[script]` | Deterministic — no reasoning, no network, no LLM calls |
| `[agent]` | Reasoning — proposes only; never writes to Treasury or Operations |
| `[gate]` | Human approval required before any write executes |
