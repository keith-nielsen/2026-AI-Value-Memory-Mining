<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: OS/Harness-Enforced Agent Write Scope (INV-4/INV-5 enforcement)

The Agent column of the Area Access Matrix SHALL be enforced **before the write occurs**, structurally,
at two complementary layers — closing the gap the matrix previously left to convention and the
post-hoc commit-gate ("OS-level enforcement is deferred per §14.1" is hereby un-deferred):

- **Shell layer (OS sandbox):** every Agent shell command and all of its child processes — including
  arbitrary interpreters (`python3 -c`, `perl -e`, …) invisible to command-text inspection — run inside
  an OS-enforced sandbox (bubblewrap on Linux, Seatbelt on macOS) whose filesystem policy denies writes
  to `40-Treasury/`, `99-Operations/`, `.claude/`, `96-Runbooks/`, `97-Molds/`, and `10-Logbook/`.
  Out-of-vault writes are denied by default and re-allowed only for operator-listed paths.
- **Structured-tool layer (harness permission rules):** the harness's file tools (Edit/Write and
  equivalents), which bypass the shell sandbox by design, are bound by declarative deny rules covering
  the same protected areas plus the script-owned Logbook artifacts (`10-Logbook/Daily/*.md`,
  `10-Logbook/kanban.md`). The sole agent-writable close artifact — the disposition sidecar
  `10-Logbook/Daily/*.resolutions.json` — remains writable by **pattern disjointness** (deny rules
  carry no carve-outs) and SHALL be written via the structured Write tool only, never via shell.

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
  attempts to create, modify, or delete a file under a denied area (e.g. `40-Treasury/`, `10-Logbook/`)
- **THEN** the operating-system sandbox refuses the write before it occurs; no commit-gate or agent
  cooperation is involved

#### Scenario: Structured-tool write to a script-owned artifact is denied
- **WHEN** the Agent invokes a harness file tool against `10-Logbook/Daily/<date>.md`, `kanban.md`, or
  any protected area
- **THEN** the harness permission layer denies the call pre-action
- **AND** a Write-tool call targeting `10-Logbook/Daily/<date>.resolutions.json` is permitted (the
  disposition sidecar is the one agent-owned close artifact)

#### Scenario: Driving a script is permitted only by exact invocation
- **WHEN** the Agent runs a rendered vault script exactly as listed in the exclusion list (e.g.
  `~/bin/vault-daily-note.py`)
- **THEN** the script runs outside the sandbox and writes its owned artifacts normally
- **WHEN** the same script is invoked in any other form (e.g. `python3 ~/bin/vault-daily-note.py`, or
  chained after another command)
- **THEN** it runs sandboxed and any write to a protected area fails closed

#### Scenario: Strict mode is a separate, ordered step
- **WHEN** the operator moves from burn-in to strict enforcement
- **THEN** sandbox dependencies are verified present first, and the strict settings
  (`failIfUnavailable`, no unsandboxed fallback) are applied as their own deliberate change — never
  bundled into the initial adoption
