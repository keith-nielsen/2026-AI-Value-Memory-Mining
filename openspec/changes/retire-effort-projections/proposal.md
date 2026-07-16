<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: retire-effort-projections

**Change type:** `constitution-override` (**conforming** — touches the `maintenance` spec
[`protects: [INV-2, INV-3, INV-6]`, MODIFIES four Requirements]; **no Tier-0/1 element is overridden
or weakened**. The `runtime: cron` / `schedule:` retractions are **Tier 2** by constitution §2
["cron schedules" → *ordinary change, no ceremony required*] and ride here only because they are the
same decision.)
**Principle(s) affected:** INV-3 (fleet **membership**, not the render/reconcile mechanism), INV-2
(worked examples only)
**Tier:** 0 (the spec is `protects:`-tagged; nothing in it is overridden)
**Proposer:** Claude (Opus 4.8), drafting Gates 1–2 per constitution §5
**Date:** 2026-07-17

---

## Why

The vault is a Value Mining operation: it exists to **distil insight**. Two fleet scripts project
**effort state** — a different lens entirely — and neither has a consumer.

- **`kanban-render`** writes `10-Logbook/kanban.md`. **Nothing reads it.** Verified 2026-07-17: no
  script reads it; it is not Obsidian-Kanban-plugin format; **no Obsidian plugins are installed at
  all**; the operator does not open it. Rendered **4 times in 32 days, consumed 0**. It was found 12
  days stale (dated 2026-07-05), reporting `Dig (14)` against a reality of 18 efforts — a stale
  projection answering the question *wrongly* rather than admitting it cannot. It is not free: its
  same-day re-render crash consumed a governed change (wave-2's `commit_paths` no-op guard) to repair
  an artifact nobody consumes.
- **`dig-rollover`** appends open-dig wikilinks under `## Carry-over` in the daily. Its last run
  (2026-07-03) wrote **12 unchanging links, no context, no delta**. A signal that never varies is
  noise; the operator learned to skip the section. It has been dead 14 days.
- Both sit beside a **cadence that has never existed**: there is no crontab and no systemd timer on
  the deployed host. `render` deploys code and marks it executable — **it does not install
  schedules**. `schedule:` has never been read by anything. `daily-note` has run **once**, by hand.

**Operator decision (2026-07-17):** retire both. Outstanding-effort tracking is delegated elsewhere
(Hermes — human + harness). The vault's daily cadence — *metering time into chunks, and whether that
should couple to insight discovery at all* — is **explicitly held open** pending operator design.
Retiring the projections parks them without foreclosing that decision.

The sacrifice is stated at Gate 4 and is real: after this, **nothing in the vault surfaces
outstanding efforts automatically.**

## What Changes

At the principle level: **nothing.** INV-3's mechanism (literate note → `render` → `reconcile`, drift
detected never auto-fixed) is untouched, and every surviving script still obeys it. What changes is
the fleet's **membership** and two false `runtime:`/`schedule:` declarations.

Four `maintenance` Requirements are MODIFIED, three of them only because they used the retired
scripts as **worked examples for rules that survive**:

1. **Script Inventory** — remove 2 rows; correct 2 `Runtime` cells (`cron …` → `manual`).
2. **One Mutation, One Commit (INV-2)** — the commit-format example and two scenarios are rollover's;
   the rule is unchanged, the exemplar moves.
3. **Daily Close Lifecycle** — the "advancing (rollover / carry-over) is gated" clause loses its
   subject. **Capture-always-has-a-home and strict-order close are unchanged**; the `⚠ BLOCKED`
   banner survives in `daily-note`.
4. **Shared Fleet Plumbing (vault_lib)** — the adoption list names both retired scripts; three
   scenarios use them as exemplars.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) being overridden (restated in the proposer's own words):**

> **INV-3** says operational code does not live on the host — it lives as a literate note in
> `99-Operations/scripts/`, reaches the host **only** through `render`, and any divergence between
> the two is detected by `reconcile` and **never** auto-fixed. The *Script Inventory* Requirement is
> the enumeration of that fleet. Removing a member does not weaken the rule: the mechanism is
> untouched and every survivor still obeys it. **What breaks if this is done carelessly:** a note
> deleted from the inventory while its deployed artifact stays at `~/bin/` becomes **operational
> code outside the render inventory** — precisely the R8 gap that B5/ADR-0018 closed. And
> `reconcile` **cannot catch this**: it iterates *notes* and compares each to its target, so an
> orphaned `~/bin/vault-kanban-render.py` with no note is **invisible** to it. The deploy targets
> must therefore be deleted **explicitly and in lockstep**; drift detection will not do it for us.
> This is the whole risk of the change.
>
> **INV-2** says every automated mutation ends in exactly one scoped commit. Rollover is only its
> *worked example* (`rollover: 2 open dig(s) → …`). Removing the script removes the example, not the
> rule — but the rule must keep an exemplar, or the requirement becomes abstract.

**Blast radius — every artifact referencing these scripts:**

- [ ] `openspec/specs/maintenance/spec.md` — MODIFY 4 Requirements (Script Inventory; One Mutation
      One Commit; Daily Close Lifecycle; Shared Fleet Plumbing)
- [ ] `openspec/constitution.md` — **no change** (no principle text is touched; cron schedules are
      already Tier 2 there)
- [ ] `vault-template/99-Operations/scripts/dig-rollover-script.md` — **DELETE**
- [ ] `vault-template/99-Operations/scripts/kanban-render-script.md` — **DELETE**
- [ ] `vault-template/99-Operations/scripts/daily-note-script.md` — frontmatter `runtime: cron` +
      `schedule:` → `runtime: manual`, drop `schedule:`; Rationale drops the "runs one minute before
      the roll-over script" coupling
- [ ] `vault-template/99-Operations/scripts/ore-detect-script.md` — same frontmatter retraction
- [ ] `vault-template/99-Operations/scripts/daily-close-script.md` — Rationale enumerates "rollover
      links, kanban" as commit owners
- [ ] `vault-template/99-Operations/scripts/vault-lib-script.md` — Rationale cites "the kanban
      same-day re-render lesson, 2026-07-05" (**historical attribution — the lesson stands; keep the
      citation, it is provenance, not a dependency**)
- [ ] `vault-template/96-Runbooks/daily-close-runbook.md` — "Parked `ore` does not carry over (the
      kanban / refine-queue is its home)"
- [ ] `vault-template/99-Operations/schemas/note-frontmatter-schema.md` — `runtime` enum
      `cron | manual`; with no cron member left, **`cron` and the `schedule:` field leave the schema**
      (also closes the enum half of the known `runtime:` drift)
- [ ] `vault-template/99-Operations/schemas/refine-prompt-contract.md` — mentions `kanban_block(...)`
      → **VERIFY-ONLY, expected no change**: that is the **Hermes** kanban (Phase-3 harness), a
      different primitive the script note explicitly says is "never merged" with this one
- [ ] `vault-template/.claude/settings.json` — permission entries for `~/bin/vault-rollover.py`,
      `~/bin/vault-kanban-render.py`, `Edit(/10-Logbook/kanban.md)`
- [ ] `vault-template/00-Docs/README.md` — fleet description
- [ ] `.github/scripts/validate-scripts.sh` — CI **executes** the kanban render as a smoke check
      (line ~77); it would fail hard post-retirement
- [ ] `docs/method.md` — 4 sites (dashboard bullet, carry-over bullet, kanban projection section,
      fleet enumeration)
- [ ] `docs/USING-THIS-TEMPLATE.md`, `docs/obsidian.md`, `docs/naming-exemptions-rationale.md`,
      `README.md`, `AGENTS.md` — references to sweep
- [ ] `docs/glossary.md` — **DO NOT TOUCH.** Its `kanban` entries are the **Hermes** kanban
      (`kanban_complete`, "the human gate and the executor run outside the kanban flow"). The
      controlled vocabulary term survives; only the Markdown board leaves. Confirm `vocabulary-lint`
      still passes with the term retained.
- [ ] `README.md` ADR count **27 → 28** (in **two** places, lines ~29 and ~100) — the `adr-count` CI
      guard asserts README count == `openspec/adr/` file count and will fail otherwise
- [ ] `CHANGELOG.md` — entry under `[Unreleased]`
- [ ] ADR reference — **new `openspec/adr/0028-retire-effort-projections.md`** (see Gate 4)
- [ ] **Live vault (operator, post-merge apply — agent-write-denied):** delete
      `~/bin/vault-rollover.py`, `~/bin/vault-kanban-render.py`, `10-Logbook/kanban.md`; remove the
      two script notes from live `99-Operations/scripts/`; `cp` the modified notes; `render`;
      `reconcile` → expect **15/15 `ok:`**, zero drift

**Explicitly NOT in the blast radius (verified, recorded so a reviewer need not re-derive):**

- Existing dailies keep their `## Carry-over` sections (10 of 12). **Provenance is append-only** —
  this is a retirement, not a rewrite.
- The **strict-order close gate survives**: it lives independently in `daily-note` (`⚠ BLOCKED`
  banner) and `daily-close` (refuses to seal while an earlier day is open). Rollover held the third
  copy, and it gated a behaviour that will no longer exist.
- `tests/test_fleet.py` — **no references** to either script (verified by grep).
- Hermes kanban — a separate primitive; untouched.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan** (every artifact updated in lockstep; no artifact left referencing a retired script):

1. **Spec deltas** — `specs/maintenance/spec.md`: MODIFY the four Requirements. Re-exemplify rather
   than delete rules: the INV-2 commit-format example becomes `bank: <stem>`; its two rollover
   scenarios are replaced by the surviving `daily-note` idempotence pair; the bare-drive scenario's
   exemplar moves from `~/bin/vault-kanban-render.py` to `~/bin/vault-daily-note.py`; the
   gate-refusal scenario's exemplar moves from rollover to `vault-close-day.py` (which exits `3` on
   strict-order and on a missing note).
2. **The `closed`-test scenario needs care.** It currently asserts `is_closed` is honoured
   "fleet-wide … with no divergence between the two scripts" — the two being `daily-note` and
   `rollover`. With rollover retired, `daily-note` is the sole conforming subject
   (`daily-close` carries a known hand-rolled `split_fm`, tracked separately in the live vault's
   `vmm-functional-rationalization` Site). **Narrow the scenario to `daily-note` rather than restate
   a claim the fleet no longer supports.** Do **not** silently keep the "no divergence" wording.
3. **Delete the two script notes** from `vault-template/99-Operations/scripts/`.
4. **Retract the false declarations** — `daily-note` and `ore-detect` frontmatter → `runtime: manual`,
   `schedule:` removed; drop `cron`/`schedule` from `note-frontmatter-schema.md`.
5. **CI** — remove the kanban smoke check from `.github/scripts/validate-scripts.sh`.
6. **Docs sweep** — `method.md`, `USING-THIS-TEMPLATE.md`, `obsidian.md`,
   `naming-exemptions-rationale.md`, `README.md`, `AGENTS.md`, `vault-template/00-Docs/README.md`,
   `daily-close-runbook.md`, `.claude/settings.json`. Verify `glossary.md` untouched.
7. **ADR-0028** (Proposed) + README ADR count 27 → 28 (both sites) + CHANGELOG.
8. **Live apply is operator-only** (post-merge): delete deploy targets **explicitly** — `reconcile`
   cannot see an orphaned `~/bin` artifact (Gate 1).

**Regression tests that MUST pass before Gate 3:**

- [ ] `openspec validate --all --strict` passes
- [ ] `constitution-lint` passes
- [ ] `vocabulary-lint` passes **with `kanban` retained in the glossary** (Hermes term survives)
- [ ] `adr-count` CI guard passes (README 28 == 28 ADR files)
- [ ] `.github/scripts/validate-scripts.sh` → `VALIDATION OK` **with the kanban check removed**
- [ ] `pytest` (`tests/test_fleet.py`) green
- [ ] `scope-review` CI gate green — PR body carries a ```scope block, exact paths, no globs
- [ ] **Post-apply, live vault (operator):** `~/bin/vault-render.py reconcile` → **15/15 `ok:`**,
      exit 0; `~/bin/vault-lint.py` exit 0; no orphaned `~/bin/vault-rollover.py` or
      `~/bin/vault-kanban-render.py` remains; `10-Logbook/kanban.md` gone

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☐
**All regression tests green:** ☐
**CI green on this PR:** ☐

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☐
**Consequences explicitly accepted:**

> **The vault loses every automatic surface for outstanding effort state.** After this, nothing in
> the vault answers "what am I working on?" — not a board, not the daily. That question moves to
> Hermes, or goes unanswered until it is designed. This is deliberate: both surfaces existed, and
> both went unread — the kanban 4 renders / 0 reads, the carry-over 12 unchanging links learned into
> invisibility. **But the need is real and was proven this session:** 18 stranded Sites went
> unnoticed for weeks, and the artifacts that should have surfaced them did not, because a projection
> you must remember to render *and* remember to open is two acts of remembering. Retiring them
> removes the false comfort, not the need.
>
> **Forks/users affected:** any deployed vault inherits a fleet of **15 scripts, not 17**, and loses
> `10-Logbook/kanban.md` and daily `## Carry-over`. Existing dailies and boards are untouched
> (append-only); only future generation stops.
>
> **What is explicitly NOT sacrificed:** capture always has a home; strict-order close; the `⚠
> BLOCKED` banner; every INV-2/INV-3/INV-6 rule. Only two consumers-of-nothing and two false
> declarations leave.
>
> **The reversal cost is low and should be stated honestly:** both scripts are ~40 lines, fully
> recoverable from git history, and their Requirements are re-addable as an ordinary change. This is
> not a one-way door — which is part of why retiring now, while the effort/insight coupling is still
> being thought through, is cheaper than keeping dead machinery warm.

**ADR created:** `openspec/adr/0028-retire-effort-projections.md` ☐
**ADR captures:** context / options / choice / consequence / **sacrifice** ☐

**SIGN-OFF** (human only — agents may not sign):
Name: ___________________________
Date: ___________________________
