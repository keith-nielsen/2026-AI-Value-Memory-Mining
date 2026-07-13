<!-- SPDX-License-Identifier: Apache-2.0 -->
# Agent Context — value-memory-mining

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
> `openspec/templates/constitution-override/proposal.md`.

---

## What this repository is

**value-memory-mining** is a reference-grade, Apache-2.0 OpenSpec SDD template for building
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
Capture → Dig → Ore → Sort → Refine → Treasury → Polish (perpetual)

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
| `20-Claims/` | Capture directly (create Claim notes) | Self-promote to `_refine-approved/` |
| `20-Claims/_refine-proposals/` | Write (deposit proposals) | Self-promote to `_refine-approved/` |
| `40-Treasury/` | Read only | Write directly (INV-4) |
| `99-Operations/` | — (no access) | Write (INV-5) |
| `80-Crucible/` | — (no access) | Enter (INV-8) |

Enforcement: the `vault-template/99-Operations/scripts/bank-execute-script.md` executor and
the `vault-template/99-Operations/hooks/pre-commit` hook are the real boundaries — plus, since
`os-enforced-agent-write-scope` (ADR-0022), **pre-action enforcement in the agent harness**:
an OS sandbox denies shell writes (any child process, any interpreter) to
`40-Treasury/ 99-Operations/ .claude/ 96-Runbooks/ 97-Molds/ 10-Logbook/`, and permission deny
rules block structured-tool writes to the same scope plus script-owned Logbook artifacts
(`Daily/*.md`, `kanban.md`). The disposition sidecar (`Daily/*.resolutions.json`) is the one
agent-writable close artifact — written via the Write tool only, never via shell.

**Drive contract:** to run a `[script]` step, invoke the rendered script by its **bare exact
invocation** (e.g. `~/bin/vault-daily-note.py`) — that form is sandbox-excluded so the script can
write what it owns. An interpreter-prefixed (`python3 ~/bin/…`), chained, or relative invocation runs
*sandboxed* and its protected writes fail closed. The sandbox is a fence you operate inside, not a
gate you acknowledge; a kernel denial means *surface it to the operator*, never route around it.

---

## Invariants (quick reference)

Full text and band groupings: `openspec/specs/access-control/spec.md` and PRD §5.

**Substrate** — INV-1 (Format) · INV-2 (One commit) · INV-3 (Layer-0 SSOT)
**Safety** — INV-4 (Bounded write) · INV-5 (Actor≠owner) · INV-6 (Offline scripts) · INV-7 (No secrets) · INV-8 (Crucible independence)
**Value** — INV-9 (Value never discarded) · INV-10 (Tailings retained)
**Consistency** — INV-11 (Name conformance) · INV-12 (Domain via metadata) · INV-13 (Wikilinks)

INV IDs are **frozen** — see `openspec/adr/0008-invariant-criticality-ordering.md`.

**Naming (INV-11):** every `.md` stem carries **≥3 hyphen-tokens — the floor, not the ceiling**; use
*more* where the extra tokens add human-meaningful specificity. System-artifact families use
`silo-section-descriptor` (silo first; e.g. molds `<note-type>-mold-blank`); content stems are
≥3-token slugs; dailies (`YYYY-MM-DD`) are exempt. Convention today (existing sub-3 names
grandfathered); mechanical enforcement is sequenced later. SSOT: `openspec/specs/naming-rules/spec.md`.

---

## Runbooks — repeatable operations live in `96-Runbooks/`

High-value, error-prone, repeatable procedures are codified as **spec-as-code runbooks** in
`vault-template/96-Runbooks/` (schema: `99-Operations/schemas/runbook-format-schema.md`) — the single,
harness-agnostic source of truth. **To perform one, open and follow the runbook; do not improvise:**

- `session-bootstrap-loader` — **cold-start prime**: source env, engage the gates, know the JIT pointers (a SessionStart hook surfaces it). Run it first each session.
- `daily-close-runbook` — close a daily note (full disposition sweep) before advancing to the next day.
- `provenance-seal-runbook` — forensically seal a gold artifact (hash + signature + OTS/Bitcoin + signed tag).

This file (and `CLAUDE.md`, Claude Code skills, etc.) are **adapters** — they point at the
runbooks; the runbooks hold the procedure. Determinism first: prefer the `.py`/`.sh` meta-scripts a
runbook references; invoke AI only at an explicit `unknown/other` step (see ADR-0011).

## Operating notes (footguns this repo has hit)

- `grep -rl PATTERN .` emits paths **without** the `./` prefix — an exclusion anchored `^\./…`
  silently fails to match. Use `grep -v 'openspec/changes/'` (no `^./`).
- `vault-kanban-render.py` and `vault-close-day.py` **auto-commit**; a prior `git add` can let
  their commit sweep in unrelated staged changes. Stage/commit deliberately around them.
- Vault scripts need `VAULT_ROOT` exported (the pre-commit hook fails loudly without it).
- The operator's SSH signing key is theirs — **never sign/stamp/tag as them** (`provenance-seal-runbook`
  steps 3–4 and 6 are human `[gate]`s).
- Never self-authorize a `constitution-override` — Gate 4 is human-only.
- The deployed vault is **PRIVATE (INV-14)**. Never push / mirror it outward or create a public repo
  from it, and **never even _propose_** outbound publication — the suggestion itself is the hazard.
  Publishing is deliberate, human-initiated, and `PUSH_ALLOWLIST`-gated (deny-by-default `pre-push`).

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
