<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: warehouse-reference-stockroom

**Change type:** `constitution-override`
**Principle(s) affected:** `vault-structure` spec — `protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12]`; `access-control` spec — `protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`. **Conforming amendment** — re-classifies the charter of an existing infrastructure silo and clarifies a naming scope; weakens no invariant.
**Tier:** 0/1 (touches `protects:`-tagged specs) — additive/clarifying
**Proposer:** Keith Nielsen (drafted by Claude Code; authorized by Keith)
**Date:** 2026-06-30

---

## Why

`98-Warehouse/` was chartered narrowly as "binary attachments / general binary storage" and sat
empty. In practice the operation needs a home for **retained source/reference material it draws on
repeatedly** — material that is *not* mined value (so not Treasury), *not* a working dig (so not a
Site), and *not* operations machinery. A warehouse is exactly that: low-traffic stock you keep out
of the way and reach for when needed (e.g. an owned-hardcopy *The Elements of Style* digitized to
Markdown, plus binary media). This change re-charters `98-Warehouse/` as the **reference stockroom**,
shelved by media type, and clarifies that shelf *folder* names are out of the kebab/≥3-token scope.

## What Changes

- **MODIFY** `vault-structure` → *Three-Layer Model*: re-classify `98-Warehouse/` from generic
  "infrastructure" to the **reference stockroom** (retained source/reference material; binaries +
  digitized references).
- **MODIFY** `vault-structure` → *Folder Structure*: show the default **media shelves**
  (`Books/`, `Music/`, `Art/`, `Pictures/`, `Audio/`); add the charter paragraph; add a scenario
  asserting shelf folders take human-friendly names under the **universal** path-component rule only
  (kebab/≥3-token is scoped to `.md` stems + `30-Sites/`/`70-Tailings/`/`40-Treasury/` — a Warehouse
  shelf is none of those). **Also** corrects a leftover `<pillar>-index.md` → `<pillar>-domain-index.md`
  (completing ADR-0016 propagation).
- **MODIFY** `access-control` → *Area Access Matrix*: the `98-Warehouse/` row Notes
  "General binary storage" → "Reference stockroom …". Privileges (H RW · A W¹ · S RW) unchanged.
- **Template:** scaffold `vault-template/98-Warehouse/{Books,Music,Art,Pictures,Audio}/.gitkeep`;
  update `vault-template/00-Docs/README.md` charter line; fix the v0.1.9 index straggler in
  `vault-template/99-Operations/schemas/refine-prompt-contract.md` (`<pillar>-index.md` →
  `<pillar>-domain-index.md`, matching `agent-integration`).
- **No** invariant changed: binaries remain confined to `98-Warehouse/` (Format Invariant unchanged);
  digitized `.md` reference material is still Markdown (INV-1 holds); access privileges unchanged.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `vault-structure`: MODIFY *Three-Layer Model* + *Folder Structure* (charter + shelves + naming-scope clarification + ADR-0016 straggler fix).
- `access-control`: MODIFY *Area Access Matrix* (Warehouse row note).

## Impact

- **Spec delta:** `vault-structure` (2 MODIFIED requirements), `access-control` (1 MODIFIED requirement).
- **Template:** `98-Warehouse/` shelves, `00-Docs/README.md`, `99-Operations/schemas/refine-prompt-contract.md`.
- **Docs:** README charter line. Diagram node unchanged (still the folder name).
- New ADR (Gate 4). Mirror to live vault is minimal (shelves + README already present live).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** `vault-structure` is the authority for where things live and
what shape they take on disk (protecting CONST-02 plaintext-canonical, CONST-04 touch-frequency order,
CONST-05, INV-1 Markdown+YAML, INV-12 no-pillar-folders). `access-control` defines who may read/write
each area (INV-4/5 bounded writes, etc.). This change **re-classifies one infra silo's charter and
adds organizing subfolders** to it, plus a naming-scope clarification. It does **not** move any silo,
change the numbering/order (CONST-04 intact), permit binaries outside `98-Warehouse/` (Format
Invariant unchanged), add pillar folders to Treasury (INV-12 intact), or alter any actor's access
cell. Digitized references are Markdown, so INV-1 holds. Both specs are *reinforced* (clearer charter),
not weakened.

**Blast radius (checked off in Gate 3):**

- [x] `openspec/specs/vault-structure/spec.md` — MODIFIED *Three-Layer Model* + *Folder Structure*
- [x] `openspec/specs/access-control/spec.md` — MODIFIED *Area Access Matrix*
- [x] `vault-template/98-Warehouse/{Books,Music,Art,Pictures,Audio}/.gitkeep`
- [x] `vault-template/00-Docs/README.md` — charter line
- [x] `vault-template/99-Operations/schemas/refine-prompt-contract.md` — ADR-0016 straggler fix
- [x] ADR-0019 (new)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** additive + clarifying. Adopters gain 5 shelf folders (empty `.gitkeep`); no existing
file moves or renames (other than the one-token straggler-text fix). The live vault already holds the
shelves + the README charter line (applied 2026-06-30), so the live mirror is a no-op beyond parity.

**Regression that MUST pass before Gate 3:** `openspec validate --all --strict`; `constitution-lint`
(both specs retain `protects:`); `vocabulary-lint`; CI green.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — spec deltas + template shelves + README + straggler fix + ADR draft
**All regression tests green (local suite):** ☑ — `openspec validate --all --strict` (8/8) · both specs retain `protects:`
**CI green on this PR:** ☐ (runs on push)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> Sacrifice: none structural — `98-Warehouse/` gains a defined charter + media shelves and a naming-scope
> clarification; no invariant, access cell, or workflow is weakened, and no existing file is moved.
> The only ongoing cost is that adopters carry 5 empty shelf folders by default (deletable).

**ADR created:** `openspec/adr/0019-warehouse-reference-stockroom.md` ☑ (Accepted)
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: **Keith Nielsen** — "Authorized." (transcribed by Claude Code at Keith's explicit instruction; the decision is the human's)
Date: 2026-06-30
