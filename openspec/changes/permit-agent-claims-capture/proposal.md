<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: permit-agent-claims-capture

**Change type:** `constitution-override`  
**Principle(s) affected:** CONST-02 (Three-Layer Model) — refined, NOT overridden; touches the
`access-control` spec (`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`)  
**Tier:** 1 (spec-level access refinement; no Tier-0 invariant weakened)  
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-13)  
**Date:** 2026-07-13

---

## Why

The Area Access Matrix granted the agent no general `20-Claims/` write (footnote 2: "only drops proposals
into `_refine-proposals/`"), but live practice routinely has the agent capturing Claims directly at
operator direction — an essential efficiency and comfort-of-ride requirement. The
`os-enforced-agent-write-scope` change (ADR-0022) surfaced this at Gate 4; the operator decided direct
capture is permitted. The shipped OS/harness enforcement already matches (20-Claims is denied at neither
the sandbox nor the permission layer), so the matrix footnote is the sole remaining inconsistency. This
change closes it.

## What Changes

`20-Claims/` is a **Layer-2 Workings** area under CONST-02 (temporal "now" — the least-protected layer).
The matrix Agent cell for `20-Claims/` moves from `—` to `RW`, and footnote 2 is reworded to permit
direct capture. Nothing else moves: the `_refine-approved/` gate stays Agent `—`, so promotion INTO
`40-Treasury/` remains human-gated (INV-4). CONST-02 is refined to make explicit what its own logic
already implies — Layer-2 Workings is agent-writable working space — not overridden.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle being refined (in my own words):**

> CONST-02 separates the vault into three layers by stability: Operations (Layer 0), Treasury (Layer 1),
> and Workings (Layer 2 — `20-Claims/`, `10-Logbook/`, `30-Sites/`). The safety invariants INV-4/INV-5
> protect Layers 1 and 0 specifically; Layer 2 is the high-churn temporal zone where agents already
> work (they write their assigned Sites freely). Permitting direct `20-Claims/` capture keeps capture
> inside Layer 2 and touches no Layer 0/1 protection — so no invariant loses its basis.

**Blast radius — every artifact referencing this rule:**

- [x] `openspec/specs/access-control/spec.md` — MODIFY "Area Access Matrix": `20-Claims/` Agent
      `—` -> `RW`, footnote 2 reworded, +1 scenario (spec delta in this change)
- [ ] `openspec/constitution.md` — no principle text change (CONST-02 refined by illustration, not edited)
- [x] `AGENTS.md` — add a `20-Claims/` capture row to the access table
- [ ] `vault-template/.claude/settings.json` — NO change (20-Claims already denied at neither layer;
      verified 2026-07-13)
- [ ] `vault-template/97-Molds/` — none
- [ ] `docs/glossary.md` / `vocabulary-lint` — no new controlled terms
- [x] `README.md` — ADR count fix (18 -> 25; `ADR-0001–0025`) + latest-ADR reference
- [x] `.github/workflows/ci.yml` — NEW guard: the README ADR count MUST equal the actual
      `openspec/adr/*.md` count (prevents the drift that made this fix necessary)
- [x] ADR-0025 (new; implements the ADR-0022 Gate-4 decision)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. Spec delta: `access-control` MODIFY the Area Access Matrix requirement.
2. `AGENTS.md`: add the `20-Claims/` capture row.
3. `README.md`: correct the ADR count in all three spots to 25 / `ADR-0001–0025`.
4. `.github/workflows/ci.yml`: add the ADR-count consistency guard (in the spec-lint job).
5. ADR-0025 (Proposed). CHANGELOG `[Unreleased]` (drafted with the change, F10 lesson).
6. No live-vault or enforcement change — the shipped config already permits 20-Claims capture.

**Regression:**

- `openspec validate permit-agent-claims-capture --strict` + `openspec validate --all --strict`.
- `pytest tests/`.
- The new ci.yml ADR-count guard passes (25 == 25) on this branch.
- No `settings.json` diff (enforcement unchanged).

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — spec delta; AGENTS.md; README count; ci.yml guard; ADR-0025; CHANGELOG.
**All regression tests green:** ☑ — `openspec validate --all --strict`; `pytest tests/`.
**CI green on this PR:** ☑ (PR #21, 24/24 green on 43c03d5, 2026-07-13)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> The agent gains routine direct-capture write to `20-Claims/` (Layer-2 Workings, CONST-02). No Tier-0
> invariant is weakened: INV-4/INV-5 protect Layers 1/0, and the human `_refine-approved/` Treasury gate
> is unchanged (Agent `—`). The sacrifice: a direct `20-Claims/` write is no longer a violation, so
> capture is no longer forced through the proposal path. Accepted as an essential efficiency /
> comfort-of-ride gain with the load-bearing Treasury gate intact.

**ADR created:** `openspec/adr/0025-permit-agent-claims-capture.md` (Proposed) ☑ — flips to Accepted at sign-off
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen (operator)
Date: 2026-07-13
Authorization: Gate-4 approved by the operator in session ("Approved", 2026-07-13); recorded by the agent at the operator's standing direction -- the human decided; the agent transcribed.
