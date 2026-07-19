<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0032 — Retire the daily note and its close cycle; the framework is a refinery, not a driver

**Status:** **Proposed** (Gate-4 pending — human-only sign-off, constitution §5)
**Date:** 2026-07-18
**Change:** `retire-daily-close-cycle` (`constitution-override`, **conforming** — touches the
`maintenance` spec [`protects: [INV-2, INV-3, INV-6]`] and the `access-control` spec
[`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`]; **no Tier-0/Tier-1 element is
overridden or weakened**. CONST-02 protects `10-Logbook/` as a **Layer-2 silo**, which this change
retains; only the daily *note format* and its scripts retire.)
**Relates / extends:** ADR-0028 (retired the effort projections and the decorative cadence — this is
the same audit applied one silo over); ADR-0023 (`vault_lib` — `is_closed()` loses its last caller
here); ADR-0025 (`permit-agent-claims-capture` — the model for the write-scope widening this change
deliberately does **not** perform)

## Context

ADR-0028 retracted the framework's pretence of being driven: *"the state machine is a self-priming
pump, not a driven one."* It retired the kanban and the carry-over, and deleted the `schedule:`
declarations no mechanism honoured. It **kept** the daily note as the capture surface.

An audit on 2026-07-18, prompted by the operator asking why a daily close exists at all once the
cadence is gone, found the daily surface in the same condition the kanban was in — and by a wider
margin.

**The daily is not consumed.** 12 dailies were minted in the 32 days to 2026-07-05, then **zero in
the following 13 days** — a period covering **70 commits**, releases v0.1.24 through v0.1.30, ADRs
0027–0031, and an entire multi-item fix program. The vault's most productive recorded stretch ran
with no daily note at all, and nothing was lost. The last two dailies (`2026-07-03`, `2026-07-05`)
are **empty in every section**; `2026-07-03`'s only content is a `## Carry-over` list, the artifact
ADR-0028 already retired. **No Site, Claim, or Treasury note cites a daily as a source** — every
inbound reference in the vault is machinery describing the daily *path* (the frontmatter schema, the
harness probes, the Obsidian config), never content drawing on a daily's record.

**The record it kept already existed elsewhere.** `2026-06-29.md` states plainly that it is a
*"Gap-day backfill (reconstructed from git 2026-06-29)"* — when the calendar drifted past the open
daily, the log was rebuilt **from git**. Git was already the real meta-corpus; the daily was a lossy
duplicate of it, and the one time the duplicate lapsed it was regenerated from the original.

**Nothing automated could ever fill it.** The harness denies agents write access to
`10-Logbook/Daily/*.md` at the tool layer and to `10-Logbook/` at the kernel. The only actor that
could write `Intentions` / `Log` / `Decisions` / `Captured` was a human typing into Obsidian outside
the harness. There is exactly **one** `daily:` commit in the vault's entire history. When the human
ritual lapsed, the surface went dark the same week — it had no other possible author.

**The operating frame this sits inside (operator, 2026-07-18).** An external self-improving,
memory-resident harness (Hermes or equivalent) owns the effort cadence: it populates `20-Claims`,
promotes seeds into `30-Sites`, drives the digging, and writes the effort audit trail into
`10-Logbook`. **This framework engages downstream of that** — when a Site has accumulated enough ore,
it harvests bullion into `40-Treasury` and discards husks to `71-Spoil`. VMM is a refinery with a
defined intake, not an end-to-end operating system. Recorded in
`30-Sites/vmm-strategy-roadmap/vmm-strategy-roadmap.md`.

Under that frame the daily note is not merely unused — it is the **wrong shape for the silo's
intended tenant**, and a hand-authored ceremonial artifact competing for the same space.

## Decision

**Retire the `daily-note` / `daily-close` pair and the daily note type**, in lockstep with their
deploy targets (ADR-0028's R8 scenario: `reconcile` iterates *notes*, so a deployed artifact whose
note no longer exists is invisible to drift detection and would persist as ungoverned operational
code).

The excision is **clean, not a disentanglement** — established by audit, not assumed:

> No pipeline script (`ore-detect`, `bank-execute`, `site-slag`, `spoil-dump`, `tailings-reprospect`,
> `treasury-orphan`, `knowledge-lint`) imports `is_closed`, reads a daily, or tests close state. The
> single occurrence across the entire pipeline fleet is one prose clause in
> `bank-execute-script.md` noting that the close-day sweep no longer collects Treasury writes.
> **The coupling runs the other way**: `daily-close`'s `LINK_RULES` observe the pipeline silos;
> nothing in the pipeline reaches back. `Sites → Ore → Bullion → Treasury → Spoil` already runs
> standalone today.

What retires:

- **`daily-note-script.md` / `daily-close-script.md`** and their targets `~/bin/vault-daily-note.py`
  / `~/bin/vault-close-day.py`; 2 Script Inventory rows.
- **The `Daily Close Lifecycle` Requirement**, whole — the `DISPOSITIONS` sweep, the `## Close`
  manifest, `closed:`, strict-order close, close-lint. Its subject ceases to exist.
- **`vault_lib.is_closed()`** — zero callers remain. `closed:` is a daily concept; efforts use
  `status:`/`EFFORT_STATUSES`.
- **The `DISPOSITIONS` vocabulary** from `config.defaults.env`, the `vault_lib` self-check, and the
  access-control config-key scenario. It is daily-owned in practice; the pipeline carries its own
  `EFFORT_STATUSES` / `SPOIL_STATUSES`.
- **`97-Molds/daily-mold-blank.md`**, **`96-Runbooks/daily-close-runbook.md`**, the `daily` type in
  `note-frontmatter-schema.md`, and the runbook's JIT pointer in `session-bootstrap-loader.md`.
- **Four dead `.claude/settings.json` references** — `Edit(/10-Logbook/Daily/*.md)` and the
  `excludedCommands` entries `~/bin/vault-close-day.py *`, `~/bin/vault-daily-note.py`,
  `~/bin/vault-daily-note.py *`. Note that `vault-close-day.py` contains neither "daily" nor
  "logbook": a literal word search misses it.

**Requirements that used the retired scripts as worked examples are re-exemplified, not weakened**
(ADR-0028's rule, applied again). INV-2's commit-ownership scenarios, the bare-drive guarantee, and
the gate-refusal contract all survive intact with surviving fleet members as their subjects. **The
YAML-typed `closed` scenario is removed rather than narrowed**: ADR-0028 already narrowed it once to
`daily-note` as its *"sole conforming subject"*; with `daily-note` retired it has no subject at all,
and narrowing a second time would assert what is not true.

**Provenance is retained.** The 12 existing dailies and their `## Close` manifests are untouched —
append-only history stands; only future generation stops.

**Deliberately NOT in this change: the `10-Logbook` kernel write-block.** `./10-Logbook` remains in
`sandbox.filesystem.denyWrite`. Removing it is a **widening of agent write scope** — a governed
decision on the ADR-0025 model with its own Gate-4 — not cleanup, and it must not ride in as a side
effect of a retirement. The operator's stated intent is that it comes out later; it is parked in
`vmm-strategy-roadmap` as a low-priority correction. Note the interaction: dropping the tool-layer
`Edit(/10-Logbook/Daily/*.md)` rule (which this change does, because its target format ceases to
exist) is **cosmetic while the kernel block stands** — the silo remains agent-unwritable either way.

## Options considered

- **(a) Retire the pair; keep the silo; defer the write-scope question (chosen).** Removes an
  artifact with no consumer and no possible author, while leaving the strategic decision about the
  silo's future to its own governed change.
- **(b) Build the close-cycle driver as originally specced** (program item 4, RC-1a — a deterministic
  driver owning the daily close state machine). **Rejected: it automates the operation of an artifact
  nobody produces or reads.** This is ADR-0028's rejected option (b) exactly — treating "the cycle
  isn't being run" as a control-flow defect rather than asking whether anyone wanted the output. The
  driver would have been well-built machinery for a dead cycle.
- **(c) Keep the pair; retire only the close ceremony.** Rejected: leaves a stub-minting script whose
  output nothing fills and nothing reads, and re-opens the "obligation without a consumer" trap —
  every minted daily would still be an un-closable open day.
- **(d) Re-point the daily at Hermes now** — define a Logbook schema for the incoming driver.
  Rejected: **retract > reconcile > build.** Hermes is not built; the bootstrap runbook lists it under
  *do not assume available*. Designing a format for a driver that does not exist is ADR-0028's
  rejected option (c) — making reality obey a declaration — and would bind the future tenant to
  guesses made before it existed.
- **(e) Keep it as optional/manual, unused.** Rejected on ADR-0028's finding: dead machinery kept warm
  still costs render/reconcile surface, CI time, spec scenarios, harness rules, and reviewer
  attention — and a stale surface answers *wrongly* rather than admitting it cannot.

## Consequence / sacrifice

- **The vault loses its dated capture surface and its total-disposition guarantee over days.** The
  guarantee — *nothing un-actioned silently vanishes* — was real, and it is being given up **at the
  daily granularity**. Stated plainly: this change removes a safety net that was, in practice,
  stretched under an empty stage. The need it served is genuine and now formally unmet at that level.
- **The guarantee was aimed at the wrong object, and that is the deeper finding.** Total-disposition
  exhaustively swept a *day* while the vault's actual leak — stranded Sites, "digs never close," 18
  open and unnoticed — ran unchecked. ADR-0028 recorded the same mismatch. Re-aiming it at the
  **Sites harvest/discard cycle** is the successor work, and is **not** performed here.
- **RC-1a (control-flow inversion) loses its reference implementation.** The daily-close loop —
  script owns the state machine, agent confined to one typed sidecar the deny patterns deliberately
  miss — is the vault's only working instance of the pattern, and the one protocol class with no
  recorded breach. **The pattern is extracted before deletion** to
  `30-Sites/determinism-failure-modes-claude/sidecar-typed-slot-pattern.md` (the four-layer
  enforcement shape, plus what does not transfer). The principle survives; its vehicle must be rebuilt
  at the harvest cycle. Program item 4 is superseded, not completed.
- **Forks inherit a fleet of 13 scripts, not 15**, no daily mold, no daily-close runbook, and no
  `daily` note type. Existing dailies in any deployed vault are untouched.
- **`10-Logbook/` becomes an empty silo** until its intended tenant arrives. This is deliberate and
  is the honest state: an empty room reserved for a named occupant, rather than a furnished room
  nobody enters. `10-Logbook/Reviews/` is already empty.
- **Reversal is cheap.** Both scripts are recoverable from git history and their Requirements are
  re-addable as an ordinary change — the same not-a-one-way-door reasoning ADR-0028 relied on.
- **Sacrifice, stated plainly:** the vault gives up the *appearance* of a complete daily meta-corpus
  it has had since inception, and accepts having no dated log at all, on the evidence that git was
  always the real one and the duplicate was reconstructed from it the only time it mattered.
