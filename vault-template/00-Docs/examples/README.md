# Worked Example: A Claim Becomes Bullion

This folder is a narrated, end-to-end walkthrough of the Value Mining pipeline using
one realistic insight: discovering that **`git bisect` turns regression hunting into a
binary search**. Read the files in order; each is a real stage in the pipeline.

> These are **illustrative artifacts**, not live pipeline files. They live in
> `00-Docs/examples/` (the deletable onboarding sandbox), so the linter and the refine
> scripts ignore them. In a real vault each would live in its pipeline folder — noted
> at each step below. Delete this whole folder once the flow makes sense.

---

## The pipeline at a glance

```
Capture ──► Dig ──► Ore ──► Sort ──► Refine ──► Treasury ──► Polish
  (1)                  (2: the effort)        (3: proposal)  (4: bullion)
```

See [`../README.md`](../README.md) (the onboarding overview) and the diagrams in the
template repo's `docs/diagrams.md` for the full picture.

---

## Step 1 — Capture a Claim → [`01-claim-example.md`](./01-claim-example.md)

**Lives in:** `20-Claims/` (in a real vault)

A raw, unstructured capture. No grade, no schema, no commitment — just the thought,
written down before it evaporates. The only discipline here is *capturing*. Notice the
claim is casual and a little messy; that is correct for this stage.

## Step 2 — Dig → Ore → [`02-site-walkthrough/02-site-walkthrough.md`](./02-site-walkthrough/02-site-walkthrough.md)

**Lives in:** `30-Sites/<slug>/<slug>.md` (in a real vault)

The Claim was promoted to a Site and worked through three effort statuses:
`dig` (active extraction) → `ore` (material
extracted, grade **estimated**). The `<slug>.md` shows the **Dig notes** — long,
exploratory, redundant. That is their job. The durable value is *not* here yet.

The estimated grade is **gold** — not because the work was hard (it wasn't), but
because the insight permanently changes how every future regression is handled.
**Grade is value, never effort.**

## Step 3 — Sort + Refine proposal → [`03-refine-proposal.json`](./03-refine-proposal.json)

**Lives in:** `20-Claims/_refine-proposals/` (deposited by an agent or written by you)

At **Sort**, the gold ore cleared the refine gate. A refine proposal was produced —
a JSON object matching the proposal schema (see the `agent-integration` spec). It
distills the durable insight into `insight_md`, records what was tried in
`provenance_md`, and names the Catalog index to link. Crucially, the proposal
**distills, it does not transcribe**: the raw `git bisect` command reference is left
out (it lives in `man git-bisect`); only the *reframe* and the non-obvious
preconditions are kept.

> **The gate:** a proposal in `_refine-proposals/` is only a *suggestion*. Nothing
> reaches the Treasury until a human moves it to `_refine-approved/`. That move is the
> single human approval gate (deposit-not-merge). Then the refine executor script
> writes the bullion.

## Step 4 — Bullion in the Treasury → [`04-treasury-bullion.md`](./04-treasury-bullion.md)

**Lives in:** `40-Treasury/git-bisect-regression-hunting.md` (in a real vault)

The refined knowledge note: short, dense, verified. Compare it side-by-side with the
Dig notes in step 2 — same subject, but the bullion has shed all the exploratory mess.
It carries the full `knowledge` frontmatter schema (`type`, `title`, `pillars`,
`grade`, `stage`, `crucible`, dates, `tags`) and a `## Provenance / Changelog`
section. It is linked from
[`technology-domain-index.md`](../../40-Treasury/Catalog/technology-domain-index.md).

From here the note enters **Polish** — perpetual, lightweight upkeep. It is never
"finished."

---

## What happened to the husk?

After the bullion was banked, the Site husk in `30-Sites/` was dumpd to `71-Spoil/`
(`status: spent`) via `vault-dump.sh`. The husk is residue; its value is already in
the Treasury. The bullion is **never** moved or deleted by automation (INV-9).

Had the ore turned out to be low-value or uneconomic instead, it would have been
**slagged** to `70-Tailings/` with a `slag_reason` (retained, re-minable) rather than
refined — see the Sort router in `docs/diagrams.md`.

---

## Try it / clean up

These example files are safe to read, copy, and delete. When you're ready to start
your own vault with a clean slate, delete the entire `00-Docs/` folder (it is the
deletable onboarding sandbox). For the full fork-and-bootstrap flow, see the template
repo's `docs/USING-THIS-TEMPLATE.md`.
