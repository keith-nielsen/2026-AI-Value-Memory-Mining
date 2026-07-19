<!-- SPDX-License-Identifier: Apache-2.0 -->
<!--
  Plain MODIFIED: no scenario is removed or renamed, so every current scenario name reappears below
  (the archiver's drop-guard is name-matched — see the retire-daily-close-cycle proposal for why that
  matters). Two scenario BODIES change because `10-Logbook/` moves from the denied set to the
  writable set; one is added for the new guarantee.
-->
## MODIFIED Requirements

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
