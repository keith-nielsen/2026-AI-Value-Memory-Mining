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

Drop raw material into `20-Claims/` without ceremony. A Claim is anything that
catches your attention: a quote, a half-formed idea, a URL, an observation, a question
you don't have time to investigate now.

The only discipline here is capturing everything. Nothing gets evaluated at this stage.
The `20-Claims/` folder is deliberately unstructured — it is the inbox, not the
library.

---

## Stage 2: Dig — open a Site

Prospecting — going out into the world to find what's worth a Claim — happens *upstream*,
before the system; by the time a nugget earns a Site you've already decided it's worth
digging. So **dig** it: pick a Claim, create `30-Sites/<slug>/`, copy the effort mold
(`97-Molds/effort-mold-blank.md`) in as `<slug>.md`, and set `status: dig`. A Site is born already
committed to work — there is no "prospect" state.

If first contact shows the nugget isn't worth it after all, `slag` it to `70-Tailings/`
(retained) or `dump` it to `71-Spoil/` (terminal).

---

## Promoting a Claim to a Site

This is the hinge between the inbox and active work, and getting it clean matters: a
half-promoted claim or a leftover fragment is how you end up editing the wrong copy a
week later.

**The rule: one in-progress effort = exactly one file, `30-Sites/<slug>/<slug>.md`.**
That Site is the *single source of truth* for the effort's state. `20-Claims/` is for
**un-prospected captures only** — the moment you start prospecting/digging, promote.

A claim that has grown a `status:` field (e.g. you typed `status: dig` onto an inbox
note) is the tell-tale signal it has outgrown the inbox: `status` is an *effort* field,
so promote it.

**The promotion, step by step:**

1. Create `30-Sites/<slug>/<slug>.md` from the `effort` mold (`97-Molds/effort-mold-blank.md`).
2. Fill the frontmatter: `type: effort`, `title`, `status: dig`, `pillars`,
   `started` (today), `grade:` blank (you estimate it at *ore*).
3. Migrate the claim's content into the body — its substance becomes the
   **Dig (working notes)**; add a one-line **Goal / definition of done**.
4. **Remove the original claim** from `20-Claims/`. Its content now lives in the Site;
   git history preserves the original, so you don't need a tombstone (a tombstone is
   just another fragment to wander into).
5. Repoint any `[[claim]]` wikilinks (e.g. in the daily note) to
   `[[30-Sites/<slug>/<slug>|<slug>]]`, and log the promotion in today's daily.
6. Commit as one structured change (the commit-gate hook validates every name).

**Where's my work? (on resume)** — `30-Sites/` is the index: each folder is a live effort.

The vault deliberately projects **no** effort dashboard (ADR-0028). It is a self-priming pump,
not a driven one: nothing ticks it, and nothing renders a board you would have to remember to
open. Tracking outstanding effort is a separate lens, delegated to the harness.

> A future `vault-promote.sh` will make this a single deterministic command (like
> `slag` / `dump`); for now it is a careful manual move. See the
> [Obsidian roadmap](obsidian.md#roadmap--deferred-ideas) for the inbox-button vision.

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
The executor script writes the Treasury note and links it to the relevant Catalog indexes.

Nothing enters `40-Treasury/` without a human approval.

---

## Stage 7: Treasury and Polish

The Treasury (`40-Treasury/`) holds your bullion — refined, verified knowledge.
Navigate it through the Catalog indexes (`40-Treasury/Catalog/`): one front-door note
per pillar, plus the Home index.

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
  Treasury; the husk is residue. Run `vault-dump.sh <slug>`.
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

`10-Logbook/Daily/` holds your daily notes, created at midnight by the daily-note
cron. Use them for Intentions (what you plan to extract today), Log (what actually
happened), Decisions (choices made during the day), and Captured (raw material for
Claims).

The vault projects no effort state (ADR-0028). There is no board and no daily carry-over
list: both existed, neither was read, and a projection you must remember to render *and*
remember to open decays into a stale artifact that answers wrongly rather than admitting it
cannot. Effort tracking is a distinct lens and lives outside the vault.

---

## Automation Philosophy

Three execution classes keep the system honest:

- **`[script]`**: Deterministic, no reasoning, no network, no LLM calls. Provably
  correct for the task it performs (INV-6). These are the workhorses: daily note,
  lint, refine detect, refine execute, dump, slag. Each is **run on demand** — the vault
  has no scheduler and installs none (ADR-0028).

- **`[agent]`**: Proposes only. Never writes to Treasury or Operations. The human gate
  is the only path from an agent's work into the protected zone (INV-4).

- **`[gate]`**: Human approval. The file-move from `_refine-proposals/` to
  `_refine-approved/` is the gate. It is the only action that allows a write into
  `40-Treasury/`.

This three-class model means the system is provably safe by construction, not by
policy. You could replace the agent with any model at any time — the gate is the
invariant, not the agent's behavior.
