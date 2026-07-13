<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: bank-execute-pending-catalog

**Change type:** `constitution-override`
**Principle(s) affected:** `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`); strengthens INV-12
**Tier:** 0 (edits a spec that protects Tier-0 invariants)
**Proposer:** Claude (agent draft — human Gate-4 required)
**Date:** 2026-07-11

---

## Why

The refine executor's pre-flight (`Refine Executor Pre-Flight and Batch Isolation`) validates that
`index_links` is a list, but not that it is **non-empty**. A proposal with `"index_links": []`
therefore banks a Treasury note that is wired into **no** Catalog index — an *orphan*, reachable only
by full-text search or an incidental backlink, invisible at every pillar front door. This silently
undercuts INV-12 (notes are surfaced via Catalog links, never folders). It is also internally
inconsistent: a proposal naming a *broken* index link is hard-REJECTed ("A missing Catalog target
rejects…"), while a proposal naming *no* link sails through.

Surfaced by the Crucible prove-out dig (Qwen dry-run, finding #10) and confirmed against the live vault.
Rather than block progress (hard-reject) or permit a silent orphan (warn-only), we adopt the
industry-standard **inbox pattern**: facilitate the bank, but route un-cataloged notes to a *visible*
holding queue so the outstanding curation work is impossible to lose.

## What Changes

The `Refine Executor Pre-Flight` requirement currently permits an empty `index_links`, producing an
orphan. After this override it **defaults an explicit empty `index_links` to a holding index**
(`40-Treasury/Catalog/pending-catalog-index.md`) before the containment/link-target checks — so every
banked note is reachable via ≥1 Catalog index (INV-12 upheld), nothing is blocked, and the holding
index is the visible *awaiting-catalog* queue. A *missing* or *non-list* `index_links` is still a
Schema rejection; only an explicit empty list is defaulted. No Tier-0/1 principle is weakened; INV-12
reachability is strengthened.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) being overridden (restate in your own words):**

> The `maintenance` spec is `protects: [INV-2, INV-3, INV-6]` — the atomic-commit, render/reconcile,
> and determinism invariants — so *any* edit to it must run this ceremony, even a purely additive one.
> This change does not relax INV-2/3/6: the bank stays one atomic scoped commit, the executor stays
> deterministic, no network/LLM enters. What it changes is the executor *contract*: an empty
> `index_links` stops being a legal way to produce an un-navigable note and instead becomes a defaulted,
> tracked, reachable one. The consequence I accept (Gate 4) is that a proposal can no longer bank a
> Treasury note with zero Catalog links in a single step — it is always linked somewhere.

**Blast radius — every artifact referencing this principle:**

- [x] `openspec/specs/maintenance/spec.md` — MODIFY "Refine Executor Pre-Flight and Batch Isolation"
      (add the Catalog-reachability bullet + the empty-`index_links` default scenario)
- [ ] `openspec/constitution.md` — no principle text change (additive; INV text unchanged)
- [x] `vault-template/99-Operations/scripts/bank-execute-script.md` — add `PENDING_CATALOG` constant +
      the empty-list normalization before `check()`
- [x] `vault-template/40-Treasury/Catalog/pending-catalog-index.md` — NEW holding index (shipped in template)
- [ ] `vault-template/97-Molds/` — no mold change
- [ ] `docs/diagrams/` — none
- [ ] `docs/glossary.md` / `vocabulary-lint` glossary — no new controlled terms ("pending-catalog" /
      "holding index" are descriptive, not off-metaphor)
- [ ] `AGENTS.md` — no agent-instruction change
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [x] `tests/test_fleet.py` — new case: empty `index_links` defaults to the holding index (banked, linked)
- [x] ADR required — `openspec/adr/0024-bank-execute-pending-catalog.md`

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. Ship `pending-catalog-index.md` in the template Catalog so fresh deployments have the holding index.
2. Add `PENDING_CATALOG` + the normalization to the executor source note; render deploys it to
   `~/bin/vault-refine-execute.py` (INV-3 loop — operator-run on the live host).
3. MODIFY the `maintenance` pre-flight requirement (bullet + scenario) in lockstep with the code.
4. Add the pytest case; extend the changelog; write ADR-0024.
5. **Live vaults (operator):** create `40-Treasury/Catalog/pending-catalog-index.md` (Treasury is
   autonomy-banned, INV-5) — until it exists, an empty-`index_links` proposal rejects (safe: no orphan).

**Regression tests that MUST pass before Gate 3:**

- [ ] `openspec validate bank-execute-pending-catalog --strict` and `openspec validate --all --strict`
- [ ] `constitution-lint` passes (ceremony artifacts + ADR present)
- [ ] `vocabulary-lint` passes (no glossary change)
- [ ] `pytest tests/` — existing bank cases still green + the new default-to-holding case
- [ ] Existing scenario intact: a *named* non-existent index link still hard-rejects

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ (code + template index + spec delta + test + ADR + changelog)
**All regression tests green:** ☑ — `openspec validate --all --strict` = 8/8; `pytest tests/` = 25 passed
(incl. the new default-to-holding case + the unchanged named-missing-target reject)
**CI green on this PR:** ☑ — PR #19, all checks green on head `114929c` (2026-07-13)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> The system loses the (currently legal) ability to bank a Treasury note with **zero** Catalog links in
> one step — every banked note is now linked into at least the holding index. If any future workflow
> genuinely wanted "bank now, decide reachability never," this forbids it. Judged a feature, not a loss:
> an un-navigable deposit contradicts INV-12 and the pre-flight's own "reject broken links" rule. Forks
> gain a `pending-catalog-index.md` holding index they must keep (or curate empty).

**ADR created:** `openspec/adr/0024-bank-execute-pending-catalog.md` ☑
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen (operator)
Date: 2026-07-13
Authorization: Gate-4 approved by the operator in session ("Approved", 2026-07-13); recorded by the
agent at the operator's explicit standing direction — the human made the decision, the agent only
transcribed it.
