<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0028 — Retire the effort projections (kanban board, dig carry-over) and the decorative cron cadence

**Status:** Proposed (Gate-4 pending — human sign-off; agents may not sign)
**Date:** 2026-07-17
**Change:** `retire-effort-projections` (`constitution-override`, **conforming** — touches the
`maintenance` spec [`protects: [INV-2, INV-3, INV-6]`, MODIFIES four Requirements]; **no Tier-0/1
element overridden or weakened**. The `runtime: cron` / `schedule:` retractions are Tier 2 per
constitution §2 and ride here as the same decision.)
**Relates / extends:** ADR-0023 (shared `vault_lib` — the no-op clause whose lesson came from the
kanban re-render crash); ADR-0018/B5 (R8 — operational code outside the render inventory)

## Context

The vault is a Value Mining operation: it exists to **distil insight**. Two fleet scripts project
**effort state** — a different lens — and an audit on 2026-07-17 found neither has a consumer.

**`kanban-render` → `10-Logbook/kanban.md`.** Nothing reads it. Verified: no script reads it; it is
not Obsidian-Kanban-plugin format; **no Obsidian plugins are installed at all**; the operator does
not open it. **Rendered 4 times in 32 days, consumed 0.** It was found dated 2026-07-05 — 12 days
stale — reporting `Dig (14)` against a reality of 18 efforts. And it was not free: its same-day
re-render crash consumed a governed change (wave-2's `commit_paths` no-op guard) to repair an
artifact nobody consumes.

**`dig-rollover` → daily `## Carry-over`.** Its last run (2026-07-03) wrote **12 unchanging
wikilinks**, no context, no delta. A signal that never varies is noise; the operator learned to skip
the section. Dead 14 days.

**The cadence never existed.** There is no crontab and no systemd timer on the deployed host.
`render` deploys code and marks it executable — **it does not install schedules**, and nothing reads
`schedule:`. `daily-note` (`schedule: "1 0 * * *"`) has run **once**, by hand. Three scripts have
declared a cadence since inception that no mechanism has ever honoured.

The deeper finding: **both artifacts were built to answer "what is outstanding?" and both failed —
while the question went unanswered.** 18 Sites sat open for weeks and nobody noticed, *with* a board
and a carry-over list nominally covering exactly that. A projection you must remember to render and
remember to open is two acts of remembering; it decays to the same place as no projection, but leaves
a worse artifact behind — one that answers **wrongly** instead of admitting it cannot.

The operator's decision (2026-07-17) is framed by a question deliberately left open: **decoupling
effort spent from insight discovered.** Whether the vault should meter time into chunks at all, and
whether outstanding-effort tracking belongs in it, is being designed. Outstanding effort moves to
Hermes (human + harness). Retiring the projections **parks** them without foreclosing that design.

## Decision

**The organising principle (operator, 2026-07-17): the state machine is a *self-priming pump, not a
driven one*.** Nothing outside the vault ticks it. Each operation primes itself at the point of need
— which is what the fleet was already built for and had never been allowed to be: `vault_lib`'s
root-marker walk means every script runs bare, from any cwd, with no pre-sourced environment
(ADR-0023). A declared cadence contradicted that design; it implied an external driver the vault does
not have and should not want. Extracting cadence out of the framework makes the design coherent:
**self-locating scripts, run on demand, by an actor who decided to run them.** Cadence for effort
tracking is later embedded in the Hermes harness, where the driver actually lives.

This also reframes what is being retired. It is not "delete two dead scripts" — it is **remove the
framework's pretence of being driven.** The kanban and the carry-over were the two artifacts that only
made sense under a driver: something had to tick, so that something could be rendered, so that
something could be read. None of that was true.

- **Retire `kanban-render` and `dig-rollover`** from the fleet: notes deleted, Script Inventory rows
  removed, deploy targets deleted from the host **explicitly and in lockstep**. The spec gains a
  clause stating the vault does not project effort state, and a scenario recording *why the deletion
  must be explicit*: **`reconcile` iterates notes**, so a deployed artifact whose note no longer
  exists is invisible to drift detection and would persist as operational code outside the render
  inventory — the R8 gap, re-opened by a careless retirement.
- **Retract the decorative cadence.** `daily-note` and `ore-detect` become `runtime: manual`;
  `schedule:` leaves both notes and the `runtime` enum drops `cron` from
  `note-frontmatter-schema.md`. **A cadence a script cannot install is a decoration, not a
  configuration.** The correct fix for a declaration nothing honours is to delete the declaration,
  not to build machinery that makes it true.
- **Requirements that used the retired scripts as worked examples are re-exemplified, not weakened.**
  INV-2's commit format, the bare-drive guarantee, the gate-refusal contract, and the no-op clause
  all survive intact with surviving fleet members as their examples.
- **The `closed`-test scenario is narrowed, not preserved.** It asserted `is_closed` was honoured
  "fleet-wide … with no divergence between the two scripts" — the two being `daily-note` and
  `rollover`. With rollover retired, `daily-note` is the sole conforming subject (`daily-close` still
  carries a hand-rolled `split_fm`, tracked separately). Narrowing states what is true; retaining the
  old wording would assert what is not.

## Options considered

- **(a) Retire both; retract the cadence (chosen).** Removes two consumers-of-nothing and two false
  declarations. Honest: the spec afterwards describes the system that exists.
- **(b) Force the projections — cron the kanban, ritualize the render.** Rejected: this automates the
  *production of an artifact nothing reads*. It was the first proposal made and it was wrong; it
  treats "the check is stale" as a scheduling defect rather than asking whether anyone wanted the
  output. Cron'ing `daily-note` would additionally have manufactured 12 empty dailies, each requiring
  a strict-order close — automating a punch list, in a vault whose named disease is the punch-list
  trap.
- **(c) Install the crontab to make `schedule:` true.** Rejected for the same reason: it makes reality
  obey a declaration nobody justified. **Retract > reconcile > build.**
- **(d) Keep the scripts, drop only the cadence.** Rejected: leaves two scripts in the fleet that
  nothing runs and nothing reads — dead machinery kept warm, still costing render/reconcile surface,
  CI time, spec scenarios, and reviewer attention.
- **(e) Make the kanban Obsidian-Kanban-plugin format and install the plugin.** Rejected: it is still
  **pull** — you must remember to render and remember to open. The failure was not the format.

## Consequence / sacrifice

- **The vault loses every automatic surface for outstanding effort state.** Nothing in it answers
  "what am I working on?" That question moves to Hermes, or goes unanswered until designed. This is
  deliberate — both surfaces existed and both went unread — but the **need is real and was proven**:
  18 stranded Sites went unnoticed *with* the surfaces nominally in place. **Retiring them removes
  the false comfort, not the need.** The gap is now honest and visible instead of nominally covered.
- **Forks inherit a fleet of 15 scripts, not 17**, and no `10-Logbook/kanban.md` or daily
  `## Carry-over`. Existing dailies and boards are untouched — provenance is append-only; only future
  generation stops.
- **Not sacrificed:** capture always has a home; strict-order close; the `⚠ BLOCKED` banner; every
  INV-2/INV-3/INV-6 rule. The strict-order gate survives independently in `daily-note` and
  `daily-close` — rollover held a third copy of a check for a behaviour that will no longer exist.
- **Reversal is cheap, and that matters.** Both scripts are ~40 lines, recoverable from git history,
  and their Requirements are re-addable as an ordinary change. This is not a one-way door — which is
  why retiring *now*, while the effort/insight coupling is still being thought through, costs less
  than keeping dead machinery warm and calling it optionality.
- **Sacrifice, stated plainly:** the vault gives up the *appearance* of effort visibility it has had
  since inception, and accepts a period with none at all, rather than keep two artifacts that
  answered the question wrongly. A stale projection is more dangerous than no projection.
- **Automation retracted means the operator manages their own time.** That is accepted deliberately,
  not regretted: a pump that primes itself is only started by someone who intends to start it. The
  framework stops asserting a cadence it cannot keep, and the human keeps the cadence they actually
  have — until Hermes carries it.
- **Doing less is the point.** Two scripts, two false declarations, four spec scenarios and a CI check
  leave; nothing of value goes with them. The vault's focus is value distilled from ideas, and every
  artifact that is not that competes for the same attention — reviewer, operator, and model alike.
  Focus is the deliverable here, not tidiness.
