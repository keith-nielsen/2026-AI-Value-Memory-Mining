---
capability: access-control
protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: access-control

## Purpose

Define who may read and write each vault area, and which actions each actor class
may perform. Enforcement is structural (code + hooks + CI), never trust-based.
## Requirements
### Requirement: Actor Classes

The system SHALL recognize exactly three actor classes with distinct privileges:

- **Human (H)** — the operator; full read/write everywhere; the only actor that
  may approve a refine proposal (move to `_refine-approved/`) or sign off on a
  constitutional override.
- **Agent (A)** — an LLM/AI process (Hermes worker, Claude Code, etc.); constrained
  to a specific working area and the proposal deposit folder.
- **Script (S)** — a deterministic `[script]` process; no network/LLM calls (INV-6);
  may write Treasury only via the executor gate.

#### Scenario: Human is the only approving actor
- **WHEN** a refine proposal must be promoted to `_refine-approved/` or a constitutional override must be signed off
- **THEN** only a Human (H) actor may perform that action; Agent and Script actors cannot

### Requirement: Area Access Matrix

Each vault area SHALL grant the access shown below; any actor exceeding its cell is a violation.

| Area | H | A | S | Notes |
|---|---|---|---|---|
| `99-Operations/` | RW | — | R | INV-5: actor ≠ owner of definition |
| `97-Molds/` | RW | R | R | Templates; instantiation only |
| `98-Warehouse/` | RW | W¹ | RW | Reference stockroom: retained source material (binaries + digitized refs), shelved by media type |
| `00-Docs/` | RW | R | R | Deletable onboarding |
| `20-Claims/` | RW | RW² | RW | Capture zone — agent may capture directly |
| `20-Claims/_refine-proposals/` | R | W | R | Agent deposit point |
| `20-Claims/_refine-approved/` | W | — | R | **The gate.** Agent cannot self-promote. |
| `10-Logbook/` | RW | **RW**⁷ | RW | Working area — framework neither generates nor polices (ADR-0032, ADR-0033) |
| `30-Sites/<assigned>` | RW | RW¹ | RW | Agent writes only to its assigned Site |
| `30-Sites/<other>` | RW | — | RW | Agent cannot touch other Sites |
| `40-Treasury/` | RW | R³ | gated-W⁴ | Crown jewels — INV-4 |
| `40-Treasury/Catalog/` | RW | R | gated-W⁴ | indexes; human curates |
| `50-Mint/` | RW | —⁵ | RW | Future production (deferred) |
| `60-Forge/` | RW | —⁵ | RW | Future production (deferred) |
| `70-Tailings/` | RW | R | RW | Slagged; re-minable |
| `71-Spoil/` | RW | — | RW | Terminal discard; agent excluded |
| `80-Crucible/` | RW | —⁶ | RW | INV-8: independent operator only |

¹ Agent writes only within its assigned Site / attachment for that Site.  
² Agent may capture directly into `20-Claims/` (create Claim notes) — an operator decision recorded at
the ADR-0022 Gate-4 and formalized in ADR-0025 (essential capture efficiency / comfort-of-ride). This
relaxes the earlier proposals-only capture path; it does **not** touch the `_refine-approved/` gate
(Agent `—`), so promotion INTO `40-Treasury/` remains human-gated (INV-4). `20-Claims/` is a Layer-2
Workings area (CONST-02), the least-protected layer, so direct agent capture is consistent with the
layer model.  
³ Agent read of Treasury is restricted during cloud bootstrap; full read only under local/egress-controlled model.  
⁴ Script writes Treasury only when applying a human-approved proposal from `_refine-approved/`.  
⁵ Future agent access (Mint/Forge) to be scoped when those segments are designed.  
⁶ Crucible uses an independent model/operator by design; main agent excluded (INV-8).  
⁷ Agent write to `10-Logbook/` is permitted at both enforcement layers (ADR-0033): the framework owns no artifact there after ADR-0032 retired the daily cycle, and the silo is the write target for whatever external harness drives the effort cadence. INV-11 naming still applies at commit time — pre-action prevention is withdrawn, commit-time enforcement is not.

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

#### Scenario: Agent may capture directly into 20-Claims
- **WHEN** an agent process (at operator direction) writes a new Claim note under `20-Claims/`,
  outside `_refine-approved/`
- **THEN** the write is permitted and is not a violation — `20-Claims/` is a Layer-2 Workings area and
  no INV-4/INV-5 zone is touched
- **THEN** promotion of any resulting value into `40-Treasury/` still requires the human
  `_refine-approved/` gate

#### Scenario: The Logbook is agent-writable at both layers
- **WHEN** the Agent writes a file under `10-Logbook/` — via a harness file tool or via a shell command
- **THEN** the write succeeds: no permission deny rule matches the path, and the OS sandbox does not
  list the silo in `denyWrite`
- **THEN** the `core.hooksPath` pre-commit gate still applies INV-11 naming to the staged filename —
  withdrawing pre-action prevention does not withdraw commit-time enforcement

### Requirement: Bounded Write Scope (INV-4)

No agent/LLM process SHALL write to `40-Treasury/` or `99-Operations/`. An agent may
write only to (a) its assigned Site working area in `30-Sites/<slug>/` and (b)
`20-Claims/_refine-proposals/`.

A script may write to `40-Treasury/` only when applying a proposal that a
human has approved by moving it into `20-Claims/_refine-approved/`. Presence in
`_refine-approved/` is the gate.

*Runtime reality:* Hermes Agent workers execute with the operator's uid and full
filesystem access — the runtime does not sandbox to the assigned Site. INV-4 is
therefore enforced by the deterministic boundary: the refine executor and the
commit-gate hook (INV-11), plus OS-level ACLs when built (deferred, §14.1).

#### Scenario: Script writes Treasury only through the gate
- **WHEN** the refine executor runs
- **THEN** it writes to `40-Treasury/` only for proposals present in `_refine-approved/`
- **THEN** a proposal still in `_refine-proposals/` is never applied

### Requirement: Actor ≠ Owner of Its Own Definition (INV-5)

No automated process (script, agent, CI) SHALL have write access to `99-Operations/`.
The Layer-0 machinery cannot modify its own operating procedures. This is enforced
by design (no script writes `99-Operations/`) and backstopped by the commit-gate hook.

#### Scenario: Automation cannot modify Layer 0
- **WHEN** any script, agent, or CI process attempts to write under `99-Operations/`
- **THEN** the write is rejected; only a Human (H) actor may modify Layer-0 definitions

### Requirement: Secrets Prohibition (INV-7)

No credentials, API keys, tokens, or passwords SHALL appear in any vault file.
Scripts read secrets from the environment (`os.environ`), not from vault files.
Structural configuration is split into a **public defaults** file and a **private instance**:
`99-Operations/config.defaults.env` (tracked, framework defaults — vocabularies, guard defaults) is
sourced first; `99-Operations/config.env` (gitignored, personal/machine overrides — absolute
`VAULT_ROOT`, `PATH`, any customized `PILLARS`) is sourced last and never published. Neither contains
credentials.

#### Scenario: No secrets in config; private instance is gitignored
- **WHEN** `config.defaults.env` and `config.env` are inspected
- **THEN** they contain only structural configuration (`VAULT_ROOT`, `PILLARS`, `GRADES`, `REFINE_GATE_GRADES`, `KNOWLEDGE_STAGES`, `EFFORT_STATUSES`, `SPOIL_STATUSES`, `VAULT_PUBLISH_GUARD`, `PUSH_ALLOWLIST`, `PUBLIC_REMOTE_ALLOWLIST`) — no credentials
- **THEN** the live `config.env` is gitignored (private instance); only `config.defaults.env` + `config.env.example` are tracked/publishable

### Requirement: Crucible Independence (INV-8)

The Crucible (`80-Crucible/`) SHALL use an independent model/operator, distinct from the
main process agent, as a diversity/fresh-eyes play to catch blindspots. The main
agent (Hermes or any equivalent) is excluded from `80-Crucible/`. The Crucible
produces a direct injection into Treasury with `crucible: true` provenance flag.

Build of the Crucible apparatus is deferred (§14.1); the exclusion is enforced by
the access matrix above from day one.

#### Scenario: Main agent excluded from Crucible
- **WHEN** the main process agent attempts to read or write `80-Crucible/`
- **THEN** access is denied; only the independent Crucible operator may act there

### Requirement: Private by Default — No Unbid Publication (INV-14)

A deployed vault SHALL be private by default. No automated actor (Agent or Script) may push,
mirror, or otherwise replicate vault content to any remote or external/third-party destination,
**except** a destination the operator has explicitly listed in `PUSH_ALLOWLIST` (`config.env`).
With `PUSH_ALLOWLIST` empty (the default), every outbound push is refused.

Creating a public repository, or publishing to an external distribution hub, from within the vault
SHALL require explicit, deliberate **human** confirmation — and SHALL never be initiated as an
agent's unprompted suggestion.

Enforcement is **structural**, never trust-based:
- a deterministic `pre-push` hook (`push-guard-script`, INV-6) that denies by default and permits only
  an allowlisted remote; and
- the agent harness guard (`.claude` `PreToolUse`) that hard-denies any outward command whose
  **effective target** is the deployed vault, and raises a loud ASK **hard stop** before **any** other
  outward-replication or public-facing publication.

The harness guard SHALL judge "targets the vault" from the command's **effective target** — honoring a
leading `cd <path>`, `git -C <path>`, or `gh -R <owner/repo>` redirect, and treating a command that
names the vault path as an outward operand as vault-outward — **not** from the shell's reported working
directory alone (which, in a live agent session, is always the vault even when the command operates on
a sibling repository). Every outward-replication or distribution-publish command that is **not**
vault-denied — including a plain `git push` — SHALL raise the ASK hard stop; no outward command may
silently defer. The ASK is a structural stop: it cannot proceed without an explicit human confirmation
in any permission mode. Before triggering it, the agent SHALL present an overview summary and the
absolute path to the governing `proposal.md`.

This invariant is **additive** to the Safety band and weakens nothing: INV-4/5 bound *writes within*
the vault; INV-14 bounds *replication outward*. INV-14 is appended per the frozen-ID rule (ADR-0008);
INV-1–13 are unchanged.

#### Scenario: Automated push to a non-allowlisted remote is denied
- **WHEN** an Agent or Script triggers `git push` from the vault to a remote not in `PUSH_ALLOWLIST`
- **THEN** the `pre-push` hook aborts with an INV-14 violation; nothing is transmitted

#### Scenario: Agent must not propose outbound publication
- **WHEN** a task could be "helped" by pushing/mirroring vault content outward or creating a public repo
- **THEN** the agent does not suggest or perform it; the harness `PreToolUse` guard denies the vault-outward command and requires deliberate human action for any public publication

#### Scenario: Operator opt-in is explicit and deliberate
- **WHEN** the operator wants an off-machine backup
- **THEN** it is permitted only after the operator deliberately adds that (private) remote to `PUSH_ALLOWLIST`; a tired or quick assent solicited by an agent does not satisfy this

#### Scenario: A publish to a sibling repo from a vault-rooted session is asked, not denied
- **WHEN** the agent runs `gh release create` or `git push` whose effective target is a non-vault
  sibling repository (e.g. `cd <framework-repo> && gh release create …`, or `-R <owner/repo>`) from a
  session where `VAULT_ROOT` is set to the deployed vault
- **THEN** the harness guard does NOT hard-deny it as vault-outward; it raises the ASK hard stop, and the
  command proceeds only on explicit human approval

#### Scenario: A plain git push never defers silently
- **WHEN** the agent runs a `git push` (including `git -C <path> push`) whose effective target is not the
  deployed vault
- **THEN** the harness guard raises the ASK hard stop rather than deferring; the push cannot execute
  without explicit human confirmation, in any permission mode

#### Scenario: Vault-outward push is still hard-denied
- **WHEN** the agent runs any outward command whose effective target is inside the deployed vault (by
  cwd, by `git -C`/`cd` into the vault, or by naming the vault path as an operand)
- **THEN** the harness guard HARD-DENIES it — unchanged; the ASK relaxation applies only to non-vault targets

### Requirement: Publication Boundary — Path-Level Manifest for Public Remotes (INV-14)

Under INV-14, a deployed vault SHALL enforce publication **at the path level** for any remote the
operator designates public. The publishable surface is a **default-deny allowlist**:
`99-Operations/schemas/publish-manifest.json` lists the `public_allow` path globs (framework machinery
only — e.g. `CLAUDE.md`, `96-Runbooks/**`, `97-Molds/**`, `99-Operations/{scripts,schemas,hooks}/**`,
`config.defaults.env`, `00-Docs/**`, `**/.gitkeep`). Any path not matched is **private by default**
(fail-safe: a new or forgotten path stays private).

A remote listed in `PUBLIC_REMOTE_ALLOWLIST` (`config.env`) MAY receive **only** manifest-allowlisted
paths; a push to such a remote whose diff touches any non-allowlisted path SHALL be refused. This layer
is **additive** to — never a replacement for — the remote-level deny-by-default rule (a remote not in
`PUSH_ALLOWLIST` and not in `PUBLIC_REMOTE_ALLOWLIST` is still refused outright). `PUBLIC_REMOTE_ALLOWLIST`
empty (the default) ⇒ the path-gate is inert and posture is unchanged. Enforced structurally by the
deterministic `push-guard-script` (`pre-push`, INV-6); the same manifest MUST be honored by any future
public-export/mirror tool. Principle: *publish the machine, never the ore.*

#### Scenario: Private path to a public remote is refused
- **WHEN** a push targets a remote in `PUBLIC_REMOTE_ALLOWLIST` and the pushed diff touches a path not matched by `publish-manifest.json` `public_allow` (e.g. `30-Sites/…`, `98-Warehouse/…`, `99-Operations/config.env`)
- **THEN** the `pre-push` hook aborts with an INV-14 path-boundary violation naming the offending path; nothing is transmitted

#### Scenario: Framework-only push to a public remote is permitted
- **WHEN** a push targets a `PUBLIC_REMOTE_ALLOWLIST` remote and every path in the diff matches `public_allow`
- **THEN** the push is permitted

#### Scenario: Default-deny is fail-safe for new paths
- **WHEN** a new top-level path exists that is not listed in `publish-manifest.json`
- **THEN** it is treated as private and cannot be pushed to a public remote until deliberately added to `public_allow`

### Requirement: OS/Harness-Enforced Agent Write Scope (INV-4/INV-5 enforcement)

The Agent column of the Area Access Matrix SHALL be enforced **before the write occurs**, structurally,
at two complementary layers — closing the gap the matrix previously left to convention and the
post-hoc commit-gate ("OS-level enforcement is deferred per §14.1" is hereby un-deferred):

- **Shell layer (OS sandbox):** every Agent shell command and all of its child processes — including
  arbitrary interpreters (`python3 -c`, `perl -e`, …) invisible to command-text inspection — run inside
  an OS-enforced sandbox (bubblewrap on Linux, Seatbelt on macOS) whose filesystem policy denies writes
  to `40-Treasury/`, `99-Operations/`, `.claude/`, `96-Runbooks/`, and `97-Molds/`.
  Out-of-vault writes are denied by default and re-allowed only for operator-listed paths.
- **Structured-tool layer (harness permission rules):** the harness's file tools (Edit/Write and
  equivalents), which bypass the shell sandbox by design, are bound by declarative deny rules covering
  the same protected areas.

**On `10-Logbook/` (ADR-0033):** the silo is **not** in the denied set at either layer, and carries no
tool-layer `Edit(...)` rule. This is deliberate and is the second recorded widening of agent write
scope (after ADR-0025's `20-Claims/` capture permission). The justification is that the framework owns
**no artifact** there: ADR-0032 retired the daily note, its close cycle and the disposition sidecar,
leaving a silo the framework neither generates into nor reads from. A deny rule requires a subject; a
narrower tool-layer rule would assert an ownership that no longer exists. **A widening is only ever
made by a governed change** — a protected area is never opened as a side effect of another change, and
never by editing a deployed `.claude/settings.json` alone.

**Re-establishing protection is a deliberate act.** Should a future governed artifact live under
`10-Logbook/`, the four-layer shape that previously protected it (tool-layer deny · kernel deny ·
exact-form command exclusion · one disjoint typed slot) MUST be re-established explicitly by its own
change. It does not return by default.

**Script drive path:** the Agent MAY drive an owning script (the F13 "drive, never reproduce" rule) via
an operator-maintained exclusion list of **exact rendered-script invocations**; an excluded command
runs outside the sandbox so the script can write its owned artifacts. Any other invocation form
(interpreter-prefixed, chained, relative) runs sandboxed and its protected writes fail closed.

**Two-stage adoption:** *burn-in* first — sandbox enabled with the escape-hatch fallback retained
(a command that fails under the sandbox falls back to the regular permission prompt; every fallback is
an observation), then *strict* — `failIfUnavailable` plus no unsandboxed fallback — as a separate,
deliberate operator action after clean burn-in. Strict mode SHALL NOT be enabled before sandbox
dependencies are verified present (lockout hazard).

**Honest bound:** this enforcement requires the agent runtime to expose OS sandboxing and pre-action
permission rules. A runtime lacking them provides detection, not prevention; operating there is
reduced-trust and must be declared, not assumed equivalent.

#### Scenario: Shell write to a protected area is denied at the kernel
- **WHEN** an Agent shell command — directly, via redirection, or via any child process or interpreter —
  attempts to create, modify, or delete a file under a denied area (e.g. `40-Treasury/`,
  `99-Operations/`, `.claude/`)
- **THEN** the operating-system sandbox refuses the write before it occurs; no commit-gate or agent
  cooperation is involved

#### Scenario: Structured-tool write to a script-owned artifact is denied
- **WHEN** the Agent invokes a harness file tool against a script-owned or protected artifact
  (e.g. `99-Operations/scripts/<script>.md`, `97-Molds/<mold>.md`, `40-Treasury/<note>.md`)
- **THEN** the harness permission layer denies the call pre-action
- **AND** the same call against a path under `10-Logbook/` succeeds — the silo carries no deny rule
  at either layer (ADR-0033)

#### Scenario: Driving a script is permitted only by exact invocation
- **WHEN** the Agent runs a rendered vault script exactly as listed in the exclusion list (e.g.
  `~/bin/vault-refine-execute.py`)
- **THEN** the script runs outside the sandbox and writes its owned artifacts normally

#### Scenario: Opening a protected area requires a governed change
- **WHEN** an area is removed from the denied set at either enforcement layer
- **THEN** the removal is carried by its own governed change with an ADR stating what protection is
  withdrawn and what is accepted in exchange — a deployed vault's `.claude/settings.json` edit alone
  does NOT constitute the decision, because instance config is SEED and does not propagate to forks

