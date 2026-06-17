<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: spec-as-code-runbooks

**Change type:** `constitution-override`
**Principle(s) affected:** CONST-02 (Three-Layer Model), CONST-04 (Folder Numbering) — via the `protects:`-tagged `vault-structure` and `maintenance` specs. **Conforming amendment** (additive; no principle text changes).
**Tier:** 1
**Proposer:** Keith Nielsen (drafted by Claude Code; Gate 4 authorized by Keith only)
**Date:** 2026-06-17

---

## Why

Two high-value, error-prone, *repeatable* processes — **closing a daily** and **sealing a gold artifact's provenance** — currently live only in conversation and prose-memory. After a context clear, or under a model/harness swap, an agent re-improvises them and hallucinates variations. We need them codified as **model-/harness-agnostic spec-as-code runbooks**, each a thin orchestration over deterministic `.py` (INV-6), AI invoked only at `unknown/other`. Their canonical home is a numbered vault band — which requires touching the `protects:`-tagged `vault-structure` spec, hence this ceremony.

## What Changes

- **CONST-04 and CONST-02 principle text: unchanged.** The new `96-Runbooks` band *conforms* to CONST-04 (zero-padded, gapped, infra-region) and sits inside the already-reserved `90–96 future-system` range; the three layers are untouched (runbooks are operational, Layer-0-adjacent like `97-Molds`/`99-Operations`).
- **`vault-structure` spec:** add `96-Runbooks/` to the Folder Structure tree (narrow the reserved note to `90–95`); add the `runbook` schema and a `closed:` field on the `daily` frontmatter schema.
- **`maintenance` spec:** add a **Runbook Format** requirement and a **Daily Close Lifecycle** requirement; add `vault-close-day` to the Script Inventory.
- **Scope:** purely additive. No existing requirement is removed or weakened.

---

## Gate 1 — CHECK (Impact Analysis)

**Principles being overridden (restated):** CONST-04 says the explorer must sort by touch-frequency (daily at top, infra at bottom), zero-padded and gapped; CONST-02 says the vault is exactly three layers (Operations / Treasury / Workings). "What breaks" if violated: arbitrary numbering destroys at-a-glance positioning and forces cascading renames; collapsing layers re-couples churn with durable value and voids the access-control rationale. **This change triggers neither failure** — it adds one conforming band in the reserved infra range and adds two requirements to an operational spec. It is a corrective/additive amendment that *uses* the principles, not a sacrifice of them.

**Blast radius — every artifact (checked off as completed in Gate 3):**

- [x] `openspec/specs/vault-structure/spec.md` — Folder Structure tree + reserved note; Frontmatter Schemas (`runbook`, daily `closed:`)
- [x] `openspec/specs/maintenance/spec.md` — Runbook Format + Daily Close Lifecycle requirements; Script Inventory
- [x] `vault-template/96-Runbooks/{seal-provenance,close-daily}.md` — the two charter runbooks (new band)
- [x] `vault-template/99-Operations/schemas/runbook.md` — runbook meta-schema (new)
- [x] `vault-template/99-Operations/schemas/frontmatter.md` — daily `closed:`
- [x] `vault-template/99-Operations/scripts/close-daily.md` — `vault-close-day.py` (new); `rollover.md` + `daily-note.md` gate updates
- [x] `vault-template/99-Operations/config.env` — `DISPOSITIONS` controlled vocab
- [x] `vault-template/97-Molds/daily.md` — `closed:` + `## Close` / `## Carry-over` slots
- [x] `openspec/adr/0011-spec-as-code-runbooks.md`, `openspec/adr/0012-daily-close-lifecycle.md` — new ADRs
- [x] `.github/scripts/{runbook-lint,close-lint}` + `.github/workflows/ci.yml` — new lint jobs; `validate-scripts.sh` adds `vault-close-day`
- [x] `AGENTS.md` (Runbooks pointer + agent footguns), `CLAUDE.md` (pointer)
- [x] `CHANGELOG.md` — `[0.1.5]`

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. Author the `vault-structure` + `maintenance` deltas (this change), then apply them to the live specs.
2. Build the band, schemas, runbooks, scripts, config vocab, mold, ADRs, lints, CI, adapters (Gate 3).
3. **Existing forks/vaults:** `mkdir 96-Runbooks/` and copy the two runbooks; the daily mold gains `closed:` going forward — pre-existing dailies without `closed:` are treated as legacy/open and exempted by `close-lint` (only dailies created after adoption are gated). Re-render `vault-close-day`, `rollover`, `daily-note`.

**Regression tests that MUST pass before Gate 3 → 4:**

- [x] `openspec validate --all --strict` (incl. this change)
- [x] `constitution-lint` passes (specs keep `protects:`; constitution intact; IUP template present)
- [x] `vocabulary-lint` passes
- [x] `runbook-lint` passes on both charter runbooks
- [x] `close-lint` passes on the already-closed `2026-06-15` daily
- [x] `validate-scripts.sh` (Python 3.12 + 3.13): `vault-close-day.py` renders, `py_compile`s, shellcheck-clean, close-daily smoke green
- [x] link-check clean; CI green

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All regression tests green:** ☑ (OpenSpec 8/8 · runbook-lint · link-check · validate-scripts 3.12+3.13)
**CI green on this PR:** ☑ (all 10 jobs)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> Sacrifice: one more top-level band in every vault (mild structural surface); forks must `mkdir` it on upgrade. The reserved `90–96` range shrinks to `90–95`. No principle, invariant, or existing workflow is weakened.

**ADR created:** `openspec/adr/0011-spec-as-code-runbooks.md`, `openspec/adr/0012-daily-close-lifecycle.md` ☑
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**AUTHORIZE** (human only — agents may not sign):
Name: **Keith Nielsen** — "Authorized."
Date: 2026-06-17
