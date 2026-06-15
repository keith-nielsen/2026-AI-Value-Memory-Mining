<!-- SPDX-License-Identifier: Apache-2.0 -->
# Agent Context — memory-mining

> **CONSTITUTIONAL HARD STOP — READ FIRST**
>
> An AI agent (Claude Code, Hermes, any model) **MUST NOT** propose, apply, or merge
> any change that touches a constitutional (Tier-0 / Tier-1) element without first
> (a) surfacing the principle, its rationale, and its "what breaks" consequences to
> the human, and (b) receiving explicit human confirmation of the sacrifice.
>
> Agents may *draft* the CHECK and PLAN sections of a `constitution-override` change.
> The SIGN-OFF gate is **human-only**. An agent that detects it is about to modify a
> `protects:`-tagged element **must stop and present the trade-off — never proceed silently**.
>
> Constitutional elements are defined in `openspec/constitution.md`.
> The `constitution-override` change template is at
> `openspec/changes/templates/constitution-override/proposal.md`.

---

## What this repository is

**memory-mining** is a reference-grade, Apache-2.0 OpenSpec SDD template for building
a local-first, Markdown-based personal knowledge system organized as a **Value Mining**
operation. It is both an exemplary implementation of spec-driven development *and* a
forkable template any adopter can run on their own vault.

**Two layers you need to understand:**

| Layer | Path | Role |
|---|---|---|
| SDD core | `openspec/` | The source of truth. Specs, constitution, ADRs, change lifecycle. |
| Implementation | `vault-template/` | The vault skeleton the specs govern. Scripts, templates, folder structure. |

---

## How this repo practises SDD

Every change to `vault-template/` or the vault's behavior originates as an OpenSpec
change in `openspec/changes/`. The lifecycle is:

```
/opsx:propose "what you want"   → creates proposal + specs + design + tasks
/opsx:apply                     → implement the tasks
/opsx:archive                   → sync delta specs into main specs; move to archive/
```

Do **not** edit `vault-template/` files directly without a corresponding OpenSpec change.
Do **not** edit `openspec/specs/` directly — changes come from `/opsx:archive`.

---

## Value Mining — the system this repo templates

Content flows through a pipeline modeled as ore extraction:

```
Capture → Prospect → Dig → Ore → Sort → Refine → Treasury → Polish (perpetual)

Side paths:
  Slagged → 70-Tailings  (retained, re-minable when economics shift)
  Spoil   → 71-Spoil     (terminal: spent husks + proven-false waste)

Downstream (future):
  Treasury → 50-Mint  (dated immutable editions)
  Treasury → 60-Forge (bespoke wares)

Special (rare, by-exception):
  80-Crucible — independent model/operator, direct Treasury inject with crucible: true
```

---

## Agent access rules (vault-template)

These are enforced by code, not trust. See `openspec/constitution.md` for the rationale.

| Area | Agent may | Agent may NOT |
|---|---|---|
| `30-Sites/<assigned>/` | Read + write | Touch other sites |
| `20-Claims/_refine-proposals/` | Write (deposit proposals) | Self-promote to `_refine-approved/` |
| `40-Treasury/` | Read only | Write directly (INV-4) |
| `99-Operations/` | — (no access) | Write (INV-5) |
| `80-Crucible/` | — (no access) | Enter (INV-8) |

Enforcement: the `vault-template/99-Operations/scripts/refine-execute.md` executor and
the `vault-template/99-Operations/hooks/pre-commit` hook are the real boundaries.

---

## Invariants (quick reference)

Full text and band groupings: `openspec/specs/access-control/spec.md` and PRD §5.

**Substrate** — INV-1 (Format) · INV-2 (One commit) · INV-3 (Layer-0 SSOT)
**Safety** — INV-4 (Bounded write) · INV-5 (Actor≠owner) · INV-6 (Offline scripts) · INV-7 (No secrets) · INV-8 (Crucible independence)
**Value** — INV-9 (Value never discarded) · INV-10 (Tailings retained)
**Consistency** — INV-11 (Name conformance) · INV-12 (Domain via metadata) · INV-13 (Wikilinks)

INV IDs are **frozen** — see `openspec/adr/0008-invariant-criticality-ordering.md`.

---

## Things never to do

- Edit `openspec/specs/` directly without an OpenSpec change.
- Write to `vault-template/40-Treasury/` or `vault-template/99-Operations/` as an agent.
- Rename or renumber INV IDs (they are frozen; see ADR-0008).
- Silently modify any file tagged `protects:` without the Informed-Upheaval Protocol.
- Vendor third-party tool source (Obsidian, n8n, Hermes, Ollama) into this repo.
- Add secrets, credentials, or tokens to any file.

---

## Pillar configuration

The default pillars (`mental health financial social technology calling`) are examples.
Every fork adopter is expected to replace them with their own durable life-domains.
See `docs/USING-THIS-TEMPLATE.md` for pillar candidacy criteria.

`calling` is the deliberate catch-all for personal pursuits that don't fit the universal
pillars — physical practices, devotions, games, craft disciplines, etc.
