---
title: "Value Mining — Method Walkthrough"
---

# Value Mining — Method Walkthrough

A practical narrative of the methodology: what you do, in what order, and why each
stage exists.

---

## The Core Idea

Most knowledge systems fail at the same point: everything that enters also stays,
forever, at equal priority. The result is an ever-growing archive that becomes harder
to use as it grows. You stop trusting it because you can't tell the gold from the
gravel.

Value Mining inverts this. It treats knowledge like a mining operation: you stake
Claims, work Sites, sort the ore, and refine only the high-grade material into lasting
bullion. Everything else is either slagged for later re-evaluation or discarded as
waste. The Treasury — what you actually keep at full attention — stays curated and
trustworthy.

---

## Stage 1: Capture a Claim

Drop raw material into `10-Claims/` without ceremony. A Claim is anything that
catches your attention: a quote, a half-formed idea, a URL, an observation, a question
you don't have time to investigate now.

The only discipline here is capturing everything. Nothing gets evaluated at this stage.
The `10-Claims/` folder is deliberately unstructured — it is the inbox, not the
library.

---

## Stage 2: Prospect

When you're ready to work, pick a Claim and prospect it. Create a Site folder in
`30-Sites/<slug>/` and copy the effort mold (`97-Molds/effort.md`) in as `_effort.md`.
Set `status: prospect`.

Prospecting answers one question: *is this worth digging?* You're doing a first-pass
investigation — reading, skimming, cross-referencing. If the answer is no, move the
effort straight to `70-Tailings/` (slag it) or `71-Spoil/` (discard if proven
worthless). If yes, move to Dig.

---

## Stage 3: Dig

Set `status: dig`. Work in your Site folder — add notes, references, experiments,
drafts. The Site is your scratch space. Let it be messy.

At some point the digging produces something: a pattern, a synthesis, a technique, a
decision principle. When you have extractable value, you have ore.

---

## Stage 4: Ore — Assay and Grade

Set `status: ore`. Now estimate the grade:

| Grade | Meaning |
|-------|---------|
| `gold` | Rare durable insight; changes how you operate |
| `silver` | Solid finding; worth preserving and referencing |
| `bronze` | Marginal; maybe worth keeping, maybe not |
| `coal` | Low value; almost certainly slag or discard |

Grade is **pure value, never effort**. A three-minute observation can be gold. A
week-long deep dive can be coal. Separating grade from effort is the discipline that
makes the system work.

---

## Stage 5: Sort — 3-Way Triage

With ore in hand, you Sort. Four possible routes:

1. **Proven false / empty** → `71-Spoil/` as `waste`. You were wrong; there's nothing
   here. Document why (useful forensics) and move on.

2. **Ultravaluable or genuinely ambiguous** → `80-Crucible` (deferred; use human
   judgment now). Reserved for material so important or contested that it warrants
   independent verification with a separate model or operator.

3. **High-grade (silver / gold)** → Routine Refine pipeline. The refine detector
   picks it up; the agent (Phase 3) or human drafts a proposal; you approve; the
   executor writes bullion to `40-Treasury/`.

4. **Bronze or coal** → human judgment:
   - Bronze: evaluate. Worth extracting now? If yes, promote to Refine manually. If
     no, slag to `70-Tailings/`.
   - Coal: almost always slag, but you decide.

---

## Stage 6: Refine

Refining is verification-as-transformation. You (or an approved agent proposal)
distill the ore into a single durable knowledge note in `40-Treasury/`. In the
process, you confirm the grade — and if the material turns out to be lower-value than
estimated, you can downgrade it and re-route to Tailings rather than Treasury.

The **gate** is the chokepoint. A proposal JSON is placed in `_refine-proposals/`
(by you or an agent). You review it. If it passes, you move it to `_refine-approved/`.
The executor script writes the Treasury note and links it to the relevant Catalog MOCs.

Nothing enters `40-Treasury/` without a human approval.

---

## Stage 7: Treasury and Polish

The Treasury (`40-Treasury/`) holds your bullion — refined, verified knowledge.
Navigate it through the Catalog MOCs (`40-Treasury/Catalog/`): one front-door note
per pillar, plus the Home MOC.

Polish is perpetual incremental upkeep. Bullion is never "done." As your understanding
deepens, you return to Treasury notes to add cross-links, correct errors, sharpen
language, raise the grade. Polish is lightweight: five minutes of careful revision is
a valid Polish session.

---

## The Side Paths

### Tailings (`70-Tailings/`)

Tailings are retained, re-minable. When you slag an effort, set `status: slagged` and
write a `slag_reason` in the frontmatter before running `vault-slag.sh`. The reason is
critical: it tells you what would have to change for this effort to be worth re-mining.

Run `vault-reprospect.py` after any meaningful capability or economics shift — a
cheaper model, a new tool, a domain insight. It lists all slagged efforts with their
grade and reason. Some will have cleared.

### Spoil (`71-Spoil/`)

Spoil is terminal. Two kinds of material end up here:

- **Spent husks**: the Site folder after successful refining. The value is in
  Treasury; the husk is residue. Run `vault-dispose.sh <slug>`.
- **Waste**: ore proven false or empty. Stub it in Spoil as a tombstone so you don't
  re-dig the same dry hole.

Never re-mine Spoil. If you think something in `waste` was wrong, create a new Claim.

---

## Pillar Design

Pillars are your top-level life/knowledge domains. The default set ships with six:

| Pillar | Scope |
|--------|-------|
| `mental` | Cognition, psychology, mental models, philosophy |
| `health` | Physical and wellbeing practices |
| `financial` | Money, investing, economic reasoning |
| `social` | Relationships, communication, community |
| `technology` | Software, systems, tools, craft |
| `calling` | Personal pursuits, creative work, intrinsic motivations |

Pillars should be distinct (minimal overlap), top-level (not sub-categories of each
other), and durable (stable for years, not months). Rename, split, or collapse them as
your practice evolves — but do so deliberately via the Informed-Upheaval Protocol if
the change affects constitutional elements.

`calling` is intentionally the catch-all: anything that doesn't fit the other five
pillars belongs here. As patterns emerge in your vault, you may find a new top-level
pillar is warranted — that's healthy evolution.

---

## The Logbook

`20-Logbook/Daily/` holds your daily notes, created at midnight by the daily-note
cron. Use them for Intentions (what you plan to extract today), Log (what actually
happened), Decisions (choices made during the day), and Captured (raw material for
Claims).

The roll-over cron appends `## Carry-over` links to all active `dig` efforts in
today's daily note at 00:02, so you always know what Sites are open without a manual
check.

`20-Logbook/kanban.md` is a read-only Markdown projection of all effort frontmatter,
generated by `vault-kanban-render.py`. Columns: Prospect → Dig → Ore → Slagged.
Within each column, rows sort grade-descending. It gives you a dashboard view of
mining activity.

---

## Automation Philosophy

Three execution classes keep the system honest:

- **`[script]`**: Deterministic, no reasoning, no network, no LLM calls. Provably
  correct for the task it performs (INV-6). These are the workhorses: daily note,
  lint, refine detect, refine execute, dispose, slag, rollover, kanban.

- **`[agent]`**: Proposes only. Never writes to Treasury or Operations. The human gate
  is the only path from an agent's work into the protected zone (INV-4).

- **`[gate]`**: Human approval. The file-move from `_refine-proposals/` to
  `_refine-approved/` is the gate. It is the only action that allows a write into
  `40-Treasury/`.

This three-class model means the system is provably safe by construction, not by
policy. You could replace the agent with any model at any time — the gate is the
invariant, not the agent's behavior.
