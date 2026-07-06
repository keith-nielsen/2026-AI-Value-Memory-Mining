---
type: runbook
id: refine-pipeline-runbook
title: Refine pipeline — detect, propose, approve, bank
trigger: "ore has cleared the Sort grade gate and durable value should be banked into the Treasury"
applies-to: vault
class: procedure
last-validated: 2026-07-06
---
# Runbook — Refine Pipeline

## Purpose

Move refined value into `40-Treasury/` through the only sanctioned write path: deterministic
detection → agent-drafted proposals → **human approval** (INV-4) → pre-flighted, atomic banking.
No other actor or path writes the Treasury.

## Preconditions

- `[script]` Fleet rendered (`render-reconcile-runbook`); `20-Claims/_refine-proposals/` and
  `_refine-approved/` exist.
- Efforts to refine carry `status: ore` and a grade that clears `REFINE_GATE_GRADES`.

## Steps

1. `[script]` `~/bin/vault-refine-detect.py` — writes the queue to
   `20-Claims/_refine-queue.json` (gitignored); prints `queued N`.
2. `[agent]` For each queued Site: author a proposal JSON into `20-Claims/_refine-proposals/`
   per `99-Operations/schemas/refine-prompt-contract.md` (`target_note` under `40-Treasury/`,
   kebab stem, `mode`, `insight_md`, `provenance_md`, `index_links` under `Catalog/`,
   `frontmatter` with vocab-valid `pillars`/`grade`). This is the interpretation step — the only
   AI in the pipeline.
3. `[gate]` **Human review**: move accepted proposals from `_refine-proposals/` to
   `_refine-approved/`. The move *is* the approval — no agent may perform it.
4. `[script]` `~/bin/vault-refine-execute.py` — pre-flights each proposal whole (schema,
   containment, INV-11 stem, INV-9 create-never-overwrites, vocab, link targets); banks each
   pass as **one atomic commit** (`bank: <stem>` — note + Catalog links + consumed proposal);
   REJECTs print all reasons, write nothing, and leave the proposal in place; any reject → exit 1.
5. `[human]` Dispose the husk: verify the Treasury entry, then `~/bin/vault-dump.sh <slug>`
   (→ `71-Spoil/`) — or `~/bin/vault-slag.sh <slug>` if the effort was uneconomic instead.

## Pitfalls

- An agent must never write `_refine-approved/` — not even a test file; that directory IS the
  human gate.
- Rejected proposals stay put for correction — fix and re-run; do not hand-write the Treasury
  note to "help".
- `create` collisions are rejected (INV-9): a re-bank of an existing note is an `append`
  proposal, not a second `create`.
- Exit 1 means at least one reject — read every `REJECT` reason; the rest of the batch was
  still processed.

## Verification

- `git log` shows one `bank: <stem>` commit per applied proposal, containing exactly the note,
  its Catalog indexes, and the consumed proposal.
- `~/bin/vault-lint.py` exits 0; `~/bin/vault-orphans.py` reports no new orphan.

## Rollback

- Before dump/slag: `git revert <bank-commit>` reopens cleanly (one atomic commit per bank).
  Reverting banked value is a **human-only** decision — automation never deletes refined value
  (INV-9).
