<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0022 — OS/harness-enforced agent write scope (INV-4/5 made pre-action)

**Status:** Accepted (Gate-4, 2026-07-13; operator-approved in session)
**Date:** 2026-07-04
**Relates:** `access-control` spec · change `os-enforced-agent-write-scope` · ADR-0018 (the enforcement
posture precedent: structural, never trust-based) · live-vault Sites `determinism-failure-modes-claude`
(the evidence) and `protocol-harness-framework` (the research + superseded v0.1 draft)

## Context

Fourteen catalogued failures (F1–F14, 2026-06-30 → 07-04) yield one empirical conclusion: **only
externally-enforced guards held**. The agent acknowledged gates and re-read runbooks, then hand-authored
a script-owned daily note anyway (F13); bundled operator-staged files into its commits three times
(F3/F4/F5); and tagged an unmerged release it had itself documented as a hazard (F10). The two guards
that never failed were the INV-14 PreToolUse hook and the strict-order refusal inside
`vault-close-day.py` — both external. Meanwhile the `access-control` spec asserts "enforcement is
structural, never trust-based" while its Agent column was enforced post-hoc (commit-gate) or by trust,
with OS-level enforcement explicitly deferred (§14.1).

A v0.1 harness draft (custom PreToolUse scanner + JSON ACL) was authored and trialled, and honestly
documented its own limits: a command-text scanner cannot see interpreter writes ("the Bash hole"), it
false-positives on literal `>`; and it is bespoke machinery the operation must maintain. 2026-07-04
research found the platform now provides both needed layers natively.

## Options considered

1. **v0.1 custom guard (scanner + ACL).** Rejected: unclosable Bash hole, scanner false-positives,
   bespoke maintenance, and a root-of-trust (hash manifest) that native mechanisms make unnecessary.
2. **Policy engine (Cupcake / OPA-Rego).** Deferred, not rejected: right tool for argument-level rules
   and require-review flows, but adds a young dependency; the write-scope problem is fully covered by
   the two native layers. Revisit when a concrete need appears.
3. **Native OS sandbox + permission deny rules (chosen).** Kernel-enforced for shell (covers all child
   processes and interpreters); declarative harness rules for structured tools; maintained by the
   platform; self-protecting (the sandbox denies writes to its own settings at every scope).

## Decision

- Enforce the Area Access Matrix's Agent column **pre-action** at two layers: `sandbox.filesystem.
  denyWrite` on `40-Treasury/ 99-Operations/ .claude/ 96-Runbooks/ 97-Molds/ 10-Logbook/` (shell,
  kernel-enforced) and `permissions.deny` `Edit(...)` rules on the same scope plus the script-owned
  Logbook artifacts (structured tools). The disposition sidecar stays writable by pattern
  disjointness, Write-tool-only.
- Preserve actor typing via `sandbox.excludedCommands`: the agent drives owning scripts by **bare
  exact invocation** only; any other form runs sandboxed and fails closed on protected writes.
- **Two-stage adoption:** burn-in (escape-hatch fallback retained; fallbacks are observations) →
  strict (`failIfUnavailable` + no unsandboxed fallback) as a separate, later, deliberate change,
  ordered strictly after dependency verification (lockout hazard).
- No new invariant: this is INV-4/5 enforcement, not a new principle (frozen-ID rule untouched).

## Consequences

- F13's class (hand-authoring script-owned artifacts) and the v0.1 Bash hole are closed at the kernel;
  F3/F4/F5's staging sweeps lose their write vector into protected areas; the enforcement claim in
  `access-control` becomes true pre-action, not post-hoc.
- New operational contract: legitimate new agent write-needs are added deliberately by the operator
  (allowWrite / excludedCommands / rules) — friction by design. Kernel denials surface as blunt
  permission errors inside otherwise-familiar commands (expected; surface, don't route around).
- Burn-in reality: sandbox network allowlisting will prompt per new domain; some legitimate commands
  will fall back with prompts until the write inventory is learned.

## Sacrifice (what is knowingly given up)

The agent's *trusted* write reach — everywhere the matrix says it never belonged. Also: convenience
(operator now curates exceptions), a modest per-command sandbox overhead, and — during burn-in only —
absoluteness (the escape hatch keeps fallbacks possible behind the regular prompt). Two documented
open items are accepted rather than hidden: enumerated-deny (not default-deny) coverage for structured
tools, and the `20-Claims/` matrix-footnote-² discrepancy pending an operator decision.
