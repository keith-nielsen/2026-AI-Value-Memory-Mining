<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0025: Permit agent direct capture into 20-Claims

- **Status:** Accepted (Gate-4, 2026-07-13; operator-approved in session)
- **Date:** 2026-07-13
- **Change:** `permit-agent-claims-capture` (`constitution-override`; touches `access-control` spec,
  `protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`)
- **Relates:** implements the Gate-4 decision recorded in ADR-0022 (`os-enforced-agent-write-scope`)

## Context

The Area Access Matrix granted the agent no general `20-Claims/` write — only deposits into
`_refine-proposals/` (footnote 2). Live practice, however, routinely has the agent capturing Claims
directly at operator direction as an essential efficiency (e.g. the F3 recovery Claim). The
`os-enforced-agent-write-scope` change (ADR-0022) surfaced this discrepancy at Gate 4; the operator
decided the agent is explicitly permitted direct capture. The shipped OS/harness enforcement already
matches — `20-Claims/` is in neither the sandbox `denyWrite` nor the `permissions.deny` set — so the
matrix footnote was the sole remaining inconsistency.

## Decision

Amend the Area Access Matrix: the Agent cell for `20-Claims/` becomes `RW` (was `—`), and footnote 2 is
reworded to state the agent may capture directly into `20-Claims/`. The `_refine-approved/` row is
untouched (Agent `—`): promotion of value INTO `40-Treasury/` still requires the human gate.

## Options considered

- **(a) Permit direct capture (chosen).** Matrix matches practice + shipped enforcement; capture is
  frictionless. Cost: the soft "all capture via proposals" convention is relaxed.
- **(b) Deny `20-Claims/` and route all capture through `_refine-proposals/`.** Tighter, but adds
  friction to every capture, contradicts live practice and the shipped enforcement; rejected by the
  operator.

## Consequence / sacrifice

The agent gains routine direct-capture write to `20-Claims/` — a Layer-2 Workings area (CONST-02), the
least-protected layer. No Tier-0 invariant is weakened: INV-4/INV-5 protect Layers 1/0 (Treasury /
Operations), and the human `_refine-approved/` Treasury gate is unchanged. The **sacrifice**: the system
no longer treats a direct `20-Claims/` write as a violation, so capture is no longer forced through the
proposal path. Judged a net gain (efficiency + comfort-of-ride) with the load-bearing gate (Treasury
promotion) intact.
