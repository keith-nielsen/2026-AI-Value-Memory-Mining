<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: swap-logbook-claims-order

**Change type:** `constitution-override`  
**Principle(s) affected:** CONST-04 (Folder Numbering — Touch-Frequency Order)  
**Tier:** 1  
**Proposer:** Keith Nielsen  
**Date:** 2026-06-15

---

## Why

CONST-04 mandates folder numbering "ordered from most frequently touched **(daily logs
at top)** to least." The implementation contradicts its own principle: `10-Claims` is at
the top and the daily logs sit at `20-Logbook` (second). In practice the daily note is
the orienting cockpit a user opens first each session — set intentions, log, decisions,
preview the inbox, resume open digs — while `10-Claims` is an unordered capture queue
that gets skimmed. This change makes the layout conform to CONST-04 rather than override
it: it is a **corrective amendment** that strengthens the principle, not a sacrifice of
it.

## What Changes

- **CONST-04 principle text: unchanged.** It already says "daily logs at top"; we are
  making reality match it.
- **Canonical Layer-2 ordering corrected:** `20-Logbook → 10-Logbook` and
  `10-Claims → 20-Claims`. The refine gate folders travel with Claims
  (`20-Claims/_refine-proposals/`, `20-Claims/_refine-approved/`,
  `20-Claims/_refine-queue.json`).
- **Scope:** intra-Layer-2 only. The three-layer model (CONST-02) is untouched — both
  folders are and remain Layer 2 — Workings.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle being overridden (restated):** CONST-04 says the file explorer should sort
by how often you touch each area, daily logs first. The current numbering puts the
capture inbox first instead, so the explorer does not open on the user's actual cockpit.
"What breaks" if numbering is arbitrary: at-a-glance workflow positioning is lost and
every script/spec/diagram that references the numbered paths must move in lockstep. This
change accepts that lockstep cost in exchange for an explorer that opens on the daily.

**Blast radius — every artifact referencing this principle (28 files):**

Mechanical string substitution (`10-Claims`↔`20-Claims`, `20-Logbook`↔`10-Logbook`):

- [ ] `vault-template/99-Operations/scripts/{daily-note,rollover,kanban-render,lint,refine-detect,refine-execute}.md` — hardcoded paths
- [ ] `vault-template/99-Operations/schemas/{frontmatter,refine-prompt}.md` — schema/contract path examples
- [ ] `vault-template/CLAUDE.md`, `vault-template/00-Docs/examples/{01-claim-example,README}.md` — path references
- [ ] `vault-template/.gitignore` — `10-Claims/_refine-queue.json` → `20-Claims/...`
- [ ] `.gitignore` (repo) — `vault-template/10-Claims/_refine-queue.json` → `vault-template/20-Claims/...`
- [ ] `openspec/specs/{access-control,agent-integration,maintenance,value-pipeline}/spec.md` — access matrix + path refs
- [ ] `openspec/constitution.md`, `openspec/project.md`, `openspec/adr/0004-deposit-not-merge.md` — gate path refs
- [ ] `AGENTS.md`, `docs/{glossary,method,obsidian}.md` — path refs
- [ ] `.github/scripts/validate-scripts.sh` — sandbox test paths

Structural (line-reorder + relabel by hand — sed is not sufficient):

- [ ] `openspec/specs/vault-structure/spec.md` — the canonical Folder Structure tree (see delta) + `daily` schema path
- [ ] `docs/diagrams.md` — Diagram 5 (Folder Stack): node IDs/labels + flow edges
- [ ] `README.md` — repo layout tree
- [ ] `vault-template/00-Docs/README.md` — Folder Layout tree

Filesystem renames:

- [ ] repo: `vault-template/10-Claims → 20-Claims`, `vault-template/20-Logbook → 10-Logbook`
- [ ] live vault: same renames under `~/Documents/Vault/`

Excluded by design:

- `CHANGELOG.md` — historical entries stay accurate to their release; a new `[0.1.3]`
  entry documents this change.

New ADR required (Gate 4): `openspec/adr/0009-layer2-ordering-correction.md`.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan — authoritative repo (one atomic commit):**

1. `git mv vault-template/20-Logbook vault-template/10-Logbook` and
   `git mv vault-template/10-Claims vault-template/20-Claims`.
2. Two-pass substitution across the mechanical-set files (excluding `CHANGELOG.md` and
   `source/`): `10-Claims`→`20-Claims`, then `20-Logbook`→`10-Logbook`.
3. Hand-edit the 4 structural files so listings/diagrams show `10-Logbook` before
   `20-Claims` and flow edges originate from the correct nodes.
4. Add the `vault-structure` spec delta (this change) to the live spec; add
   `openspec/adr/0009-layer2-ordering-correction.md`; add `CHANGELOG.md [0.1.3]`.
5. Regression (below); commit; push; tag `v0.1.3`; archive this change.

**Migration plan — live vault (`~/Documents/Vault`, separate repo):**

1. Backup: `tar czf ~/Documents/Vault.pre-swap-backup.tar.gz -C ~/Documents Vault`.
2. `git mv` the two directories (same as repo).
3. Re-render scripts from the updated template into the vault's `99-Operations/scripts/`
   (copy the changed meta-script notes), then `vault-render.py render`.
4. `reconcile` (zero drift), `lint` (clean), and grep for any stale `10-Claims`/
   `20-Logbook` references in user content (fix the daily-note links, which currently
   point at `30-Sites/...` and are unaffected, but verify).
5. One structured commit in the vault.

**Regression tests that MUST pass before Gate 3 is marked complete:**

- [ ] `openspec validate --all --strict` passes
- [ ] `constitution-lint`, `vocabulary-lint`, `spec-lint` pass
- [ ] `link-check` passes (no broken doc links after the tree edits)
- [ ] `validate-scripts.sh` (Py 3.12/3.13): render, reconcile zero-drift, daily-note,
      lint, refine-detect, kanban, **INV-11 executor boundary** — all green with the new paths
- [ ] PRD A0.1 (folder tree complete), A1.x/A2.x acceptance behaviors unaffected
- [ ] No file (excl. CHANGELOG history) references the old paths: `grep -r '10-Claims\|20-Logbook'` returns only the new-correct usages

---

## Gate 3 — EXECUTE + REGRESSION TEST

Migration executed 2026-06-15: directories renamed, 24 path-referencing files
substituted, 4 structural files (vault-structure tree, Folder Stack diagram, two layout
trees) hand-corrected, `vault-structure` spec updated, ADR-0009 added, CHANGELOG `[0.1.3]`
added. CHANGELOG history and the change records intentionally retain old-path mentions.

**Implementation complete:** ☑  
**All regression tests green:** ☑ — `openspec validate --all --strict` 8/8; link-check clean; `validate-scripts.sh` OK (render, reconcile zero-drift, daily-note, lint, refine-detect, kanban, INV-11 executor boundary) with the new paths; no stray old paths outside CHANGELOG/change-records.  
**CI green on this PR:** ☑ (confirmed on the v0.1.3 push before tag/archive)  

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

<!-- Human-only. Agents may not sign. -->

**Second review confirms blast radius was fully addressed:** ☑  
**Consequences explicitly accepted:**

> The specific numbering `10=Claims / 20=Logbook` is retired. Anyone with muscle memory
> or external tooling pinned to the old paths (and any existing fork) must migrate; the
> refine gate moves to `20-Claims/_refine-*`. In exchange, the explorer opens on the
> daily cockpit, conforming to CONST-04. No constitutional principle is sacrificed — the
> three-layer model and CONST-04's touch-frequency rule are both preserved/strengthened.

**ADR created:** `openspec/adr/0009-layer2-ordering-correction.md` ☑  
**ADR captures:** context / options / choice / consequence / sacrifice ☑  

**SIGN-OFF** (human only — agents may not sign):  
Name: **Keith Nielsen** — authorized in session ("authorized", 2026-06-15); recorded by agent per the proposer's explicit instruction.  
Date: **2026-06-15**  
