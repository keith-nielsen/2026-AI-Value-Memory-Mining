---
capability: access-control
protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: access-control

Who may read and write each vault area, and which actions each actor class may
perform. Enforcement is structural (code + hooks + CI), never trust-based.

---

## Requirement: Actor Classes

Three actor classes with distinct privileges:

- **Human (H)** — the operator; full read/write everywhere; the only actor that
  may approve a refine proposal (move to `_refine-approved/`) or sign off on a
  constitutional override.
- **Agent (A)** — an LLM/AI process (Hermes worker, Claude Code, etc.); constrained
  to a specific working area and the proposal deposit folder.
- **Script (S)** — a deterministic `[script]` process; no network/LLM calls (INV-6);
  may write Treasury only via the executor gate.

---

## Requirement: Area Access Matrix

| Area | H | A | S | Notes |
|---|---|---|---|---|
| `99-Operations/` | RW | — | R | INV-5: actor ≠ owner of definition |
| `97-Molds/` | RW | R | R | Templates; instantiation only |
| `98-Warehouse/` | RW | W¹ | RW | General binary storage |
| `00-Docs/` | RW | R | R | Deletable onboarding |
| `10-Claims/` | RW | —² | RW | Capture zone |
| `10-Claims/_refine-proposals/` | R | W | R | Agent deposit point |
| `10-Claims/_refine-approved/` | W | — | R | **The gate.** Agent cannot self-promote. |
| `20-Logbook/` | RW | R | RW | Daily logs + reviews |
| `30-Sites/<assigned>` | RW | RW¹ | RW | Agent writes only to its assigned Site |
| `30-Sites/<other>` | RW | — | RW | Agent cannot touch other Sites |
| `40-Treasury/` | RW | R³ | gated-W⁴ | Crown jewels — INV-4 |
| `40-Treasury/Catalog/` | RW | R | gated-W⁴ | MOCs; human curates |
| `50-Mint/` | RW | —⁵ | RW | Future production (deferred) |
| `60-Forge/` | RW | —⁵ | RW | Future production (deferred) |
| `70-Tailings/` | RW | R | RW | Slagged; re-minable |
| `71-Spoil/` | RW | — | RW | Terminal discard; agent excluded |
| `80-Crucible/` | RW | —⁶ | RW | INV-8: independent operator only |

¹ Agent writes only within its assigned Site / attachment for that Site.  
² Agent has no general `10-Claims/` write; only drops proposals into `_refine-proposals/`.  
³ Agent read of Treasury is restricted during cloud bootstrap; full read only under local/egress-controlled model.  
⁴ Script writes Treasury only when applying a human-approved proposal from `_refine-approved/`.  
⁵ Future agent access (Mint/Forge) to be scoped when those segments are designed.  
⁶ Crucible uses an independent model/operator by design; main agent excluded (INV-8).

#### Scenario: Agent cannot write Treasury directly
- **WHEN** an agent process attempts to write any file under `40-Treasury/`
- **THEN** the commit-gate hook blocks the commit with an INV-4 violation message
- **THEN** the refine executor is the only permitted write path

#### Scenario: Agent cannot write Operations
- **WHEN** an agent process attempts to write any file under `99-Operations/`
- **THEN** the commit-gate hook blocks the commit with an INV-5 violation message

#### Scenario: Agent cannot self-promote a proposal
- **WHEN** an agent process moves a file from `_refine-proposals/` to `_refine-approved/`
- **THEN** this is treated as an INV-4 violation (the gate is human-only by convention;
  OS-level enforcement is deferred per §14.1)

---

## Requirement: Bounded Write Scope (INV-4)

No agent/LLM process may write to `40-Treasury/` or `99-Operations/`. An agent may
write only to (a) its assigned Site working area in `30-Sites/<slug>/` and (b)
`10-Claims/_refine-proposals/`.

A script may write to `40-Treasury/` **only** when applying a proposal that a
human has approved by moving it into `10-Claims/_refine-approved/`. Presence in
`_refine-approved/` **is** the gate.

*Runtime reality:* Hermes Agent workers execute with the operator's uid and full
filesystem access — the runtime does not sandbox to the assigned Site. INV-4 is
therefore enforced by the deterministic boundary: the refine executor and the
commit-gate hook (INV-11), plus OS-level ACLs when built (deferred, §14.1).

---

## Requirement: Actor ≠ Owner of Its Own Definition (INV-5)

No automated process (script, agent, CI) has write access to `99-Operations/`.
The Layer-0 machinery cannot modify its own operating procedures. This is enforced
by design (no script writes `99-Operations/`) and backstopped by the commit-gate hook.

---

## Requirement: Secrets Prohibition (INV-7)

No credentials, API keys, tokens, or passwords may appear in any vault file.
Scripts read secrets from the environment (`os.environ`, not from vault files).
`config.env` contains only structural configuration (paths, pillar names, grade sets).

#### Scenario: No secrets in config.env
- **WHEN** `config.env` is inspected
- **THEN** it contains only `export VAULT_ROOT`, `PILLARS`, `GRADES`, `REFINE_GATE_GRADES`,
  `KNOWLEDGE_STAGES`, `EFFORT_STATUSES`, `SPOIL_STATUSES` — no credentials

---

## Requirement: Crucible Independence (INV-8)

The Crucible (`80-Crucible/`) uses an independent model/operator, distinct from the
main process agent, as a diversity/fresh-eyes play to catch blindspots. The main
agent (Hermes or any equivalent) is excluded from `80-Crucible/`. The Crucible
produces a **direct injection** into Treasury with `crucible: true` provenance flag.

Build of the Crucible apparatus is deferred (§14.1); the exclusion is enforced by
the access matrix above from day one.
