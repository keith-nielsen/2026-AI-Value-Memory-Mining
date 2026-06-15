---
title: "Value Mining — Glossary"
source: "vault-system-PRD.md §2"
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

**Prospect** — the first investigation of a Claim; validate whether it's worth
digging. (Effort lifecycle stage.)

**Dig** — actively extract raw material from a prospected candidate. (Effort lifecycle
stage.)

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

**Re-prospect** — re-evaluate slagged tailings when extraction economics change,
promoting any that now clear the grade gate. Detection-only script; human gates the
file-move back to Sites.

---

## Structural Terms

**Vault** — the top-level Obsidian container (root directory); also a Git repository.

**Note** — one `.md` file with YAML frontmatter.

**Pillar** — a top-level life/knowledge domain. Expressed as metadata + tags + a
Catalog entry (MOC), *never* as a knowledge subfolder. Configured in
`99-Operations/config.env`.

**Catalog** — the collection of Maps of Content (MOCs) inside the Treasury; each MOC
is a human-curated "front door" to a pillar. Lives in `40-Treasury/Catalog/`.

**MOC (Map of Content)** — a curated index note that organises links to related
knowledge notes within a pillar. One per pillar plus a Home MOC.

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
