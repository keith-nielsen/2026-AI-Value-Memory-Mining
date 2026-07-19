<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

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
  the same protected areas.

**On `10-Logbook/`:** the silo remains denied at the shell layer. With the daily-close cycle retired
(ADR-0032) there is no script-owned artifact within it and no agent-writable sidecar; the former
tool-layer rule for `10-Logbook/Daily/*.md` and the disposition-sidecar carve-out are both removed
because their subjects no longer exist. Whether `10-Logbook/` should become an agent-writable working
area is a **widening of write scope** and a separate governed decision on the ADR-0025 model — it is
deliberately NOT taken here.

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
- **WHEN** the Agent invokes a harness file tool against a script-owned or protected artifact
  (e.g. `99-Operations/scripts/<script>.md`, `97-Molds/<mold>.md`, `40-Treasury/<note>.md`)
- **THEN** the harness permission layer denies the call pre-action
- **AND** no carve-out exists inside `10-Logbook/`: the disposition sidecar was retired with the
  daily-close cycle (ADR-0032), so the silo has no agent-writable path at either layer

#### Scenario: Driving a script is permitted only by exact invocation
- **WHEN** the Agent runs a rendered vault script exactly as listed in the exclusion list (e.g.
  `~/bin/vault-refine-execute.py`)
- **THEN** the script runs outside the sandbox and writes its owned artifacts normally

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
