<!-- SPDX-License-Identifier: Apache-2.0 -->
# Design — os-enforced-agent-write-scope

## Shape of the solution

Two native enforcement layers replace the v0.1 hand-built guard (the live-vault Site
`protocol-harness-framework` DRAFT: a custom PreToolUse Python scanner + JSON ACL). Decision rationale
and the full research record live in the Site's `harness-remediation-executive-summary` (2026-07-04);
this design records what the repo needs to know.

| Layer | Mechanism | Covers | Why native beats v0.1 |
|---|---|---|---|
| Shell | `sandbox.filesystem.denyWrite` (bubblewrap/Seatbelt) | every Bash child process, incl. arbitrary interpreters | closes v0.1's self-documented "Bash hole" at the kernel; no scanner false-positives |
| Structured tools | `permissions.deny` `Edit(...)` rules | Edit/Write/MultiEdit/NotebookEdit | declarative, harness-maintained; evaluated deny-first in every mode |

The v0.1 draft's actor-typing insight is preserved: the agent *drives* owning scripts, never
reproduces their effects. The drive path is `sandbox.excludedCommands` — exact rendered-script
invocations that run unsandboxed. Everything else the agent does in a shell is fenced.

## Sharp edges that shaped this configuration

(Numbering follows the Site's `harness-remediation-executive-summary` "Sharp edges"; the ones with
config consequences here:)

- **SE-1 — two path dialects in one file.** `sandbox.filesystem` paths: `./x` = project-root-relative
  *only in project settings*. `permissions.deny` rules: gitignore-style, `/x` anchors at the settings
  source. Both blocks therefore live in the **project** `.claude/settings.json` and nowhere else.
- **SE-2 — lockout ordering.** `failIfUnavailable` before dependencies are installed prevents Claude
  Code from starting at all. Hence burn-in ships **without** it; the strict flip is Stage B.
- **SE-3 — burn-in before strict.** The escape hatch stays on during burn-in; a sandbox-failed command
  falls back to the regular permission prompt. Fallbacks are observations, not failures.
- **SE-4 — deny-overrides-CWD is proven, not assumed.** The vault root is the working directory, which
  the sandbox allows writes to by default; `denyWrite` must carve the protected subtrees out of that
  default. The live acceptance probes prove this empirically **before** any further phase builds on it;
  if a probe write succeeds, the response is stop-and-escalate, never adapt-around.
- **SE-5 — exclusion matching is the drive contract.** `~/bin/vault-daily-note.py` matches;
  `python3 ~/bin/vault-daily-note.py` does not (runs sandboxed, writes fail closed — safe but
  confusing). Both zero-arg and `*`-arg pattern forms are listed for each script because the matcher's
  treatment of trailing arguments is version-dependent; the bare-exact-invocation contract is
  documented in AGENTS.md.
- **SE-8 — Edit-rule coverage is self-checked.** The probes exercise the real Write tool against a
  denied path; if any structured tool slips an `Edit(...)` deny, `Write(...)` twin rules are added.

## Decisions and their reasons

1. **No new invariant.** INV-4/5 already state the rule; this change is enforcement. Appending an
   "INV-15" would duplicate INV-4/5's meaning and dilute the frozen-ID list (ADR-0008). The spec delta
   is an ADDED Requirement inside `access-control`.
2. **`10-Logbook/` denied whole at the shell layer; surgically at the tool layer.** Shell: the agent
   has no legitimate Bash write anywhere in the Logbook (the sidecar is Write-tool-only by rule).
   Structured tools: only `Daily/*.md` + `kanban.md` are denied, because deny rules cannot express
   "deny the silo except the sidecar" — disjoint patterns are the only carve-out mechanism.
3. **Enumerated-deny residual accepted (structured tools).** Native permission rules have no
   default-deny mode; unlisted paths stay tool-editable. Every script-owned artifact class is
   enumerated; the shell layer *is* default-deny outside the working directory. Recorded in ADR-0022.
4. **Template ships `sandbox.enabled: true` without strict keys.** A fresh deployment on a machine
   missing bubblewrap gets a warning and runs unsandboxed (the platform default) — documented in
   USING-THIS-TEMPLATE with the deps and the strict flip. Shipping strict in the template would brick
   first-run on most machines (SE-2).
5. **Live-vault instance specifics stay out of the template.** The live vault adds: the medical-domain
   network allowlist (pre-existing), `allowWrite` for `~/Documents/repo/value-memory-mining` (the
   framework repo working copy — without it, sandboxed `git commit` in the repo dies at the kernel,
   because the repo is outside the vault CWD) and for the harness scratchpad root. These live in the
   Site-authored merged file the operator applies; the template stays generic.
6. **The v0.1 local trial (`settings.local.json` write-acl hook) is retired at apply.** Superseded by
   the permission layer; removing it avoids parallel-hook interactions during burn-in observation
   (SE-9) and removes a guard whose ACL lives in an agent-writable Site (a self-editability the v0.1
   draft itself flagged).

## What this change deliberately defers

- **Stage-B strict flip** (`failIfUnavailable` + `allowUnsandboxedCommands: false`) — own change after
  clean burn-in.
- **`vault-close-cycle` driver** (control-flow inversion, Phase 2), **GitHub rulesets** (Phase 3),
  **soft hooks** (Phase 4), **Cupcake/OPA** (optional; deferred until a concrete need).
- **`70-Tailings/` / `71-Spoil/` enforcement** and the **`20-Claims/` matrix-footnote-² decision** —
  surfaced in the proposal's Gate-1 discrepancies; resolved by the operator, then a follow-up change.
