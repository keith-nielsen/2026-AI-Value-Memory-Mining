<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0035 — Adopt the strict write-scope sandbox on the reference deployment (Stage-B flip)

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-07-27)
**Date:** 2026-07-27
**Change:** `adopt-strict-write-scope-sandbox` (recording ADR, **no spec delta, no `vault-template/`
change**). Records an **instance-only** operational adoption: the reference deployment's live
`.claude/settings.json` moves from *burn-in* to *strict* — the second, deliberate stage the
`access-control` spec's **OS/Harness-Enforced Agent Write Scope** requirement already specifies. It
executes an anticipated stage; it does not change the enforcement model, so it touches no
`openspec/specs/` and no `vault-template/`. Not an OpenSpec change (OpenSpec requires a spec delta this
adoption has none of) — a docs PR plus an operator-applied instance-config edit.
**Relates / completes:** **ADR-0022** (OS-enforced agent write scope — established the two-stage
rollout and the burn-in this completes); **ADR-0033** (last write-scope change — flagged that "program
item 8, the ADR-0022 Stage-B strict flip, re-runs the Phase-1a probe sheet"); ADR-0025/ADR-0027 (the
guard stack this hardens the floor of).
**Answers, at the strongest local layer:** the standing residual named by probe **P15** — *the
write-scope guarantee currently holds only while the sandbox is on* — which `failIfUnavailable` plus a
removed unsandboxed fallback closes.

## Context

The OS write-scope sandbox (ADR-0022) shipped **burn-in** in v0.1.19 (2026-07-13): `sandbox.enabled`
with the escape-hatch fallback retained — a command that fails under the sandbox falls back to the
regular permission prompt, and every fallback is an observation. The spec always framed strict as a
**separate, deliberate operator action after clean burn-in**, gated on verified sandbox dependencies
(lockout hazard). Two weeks of clean burn-in later, that action is due.

**The residual strict closes (P15, 2026-07-20).** Substrate inspection established that the `EROFS` on
a denied write is a real kernel denial via a `ro` bind mount — but one that is **harness-established
and session-scoped**: it binds the agent, and it evaporates if the sandbox does not come up. The one
gap the burn-in config leaves is precisely *"the guarantee holds only while the sandbox is on."*
`failIfUnavailable: true` (refuse to start rather than run unsandboxed) plus `allowUnsandboxedCommands:
false` (no per-command escape hatch) is the remedy for that sole structural residual — not incremental
hardening.

**The evidence base is complete and was re-confirmed the day of this ADR.**
- **P6 / SE-4** (rev-2, 2026-07-19; **re-run 2026-07-27**): a Python write to `40-Treasury/` dies at the
  kernel with `OSError errno 30 (EROFS)`, file never created — the kernel, not the model-based
  classifier, refuses. Re-run today: **PASS**, with a **P12 control** write to `10-Logbook/` succeeding
  in the same session, proving the refusal is **path-specific**, not a blanket block.
- **P16 / SE-5** (2026-07-20): an `excludedCommands` match genuinely lifts the sandbox (purpose-built
  probe, superseding the inert P5 rev-2) — so the one drive path agents need still works under strict.
- **P2** (2026-07-19): the classifier layer is model-based and **non-deterministic**; the flip
  therefore rests on **kernel enforcement alone**, treating every classifier denial as a bonus.
- **SE-2 lockout guard (2026-07-27):** `bwrap` (`/usr/bin/bwrap`) and `socat` (`/usr/bin/socat`) are
  present on the host — the summary that first flagged them "not installed" is stale. The hard ordering
  (deps green **before** any `failIfUnavailable` merge) is satisfied.

## Decision

**Add `"failIfUnavailable": true` and `"allowUnsandboxedCommands": false` to the `sandbox` block of the
reference deployment's live `.claude/settings.json` — instance-only. The `vault-template/` default stays
in burn-in.**

- **Instance-only, not a template default.** `.claude/settings.json` is **SEED** in
  `template-sync-manifest.json` (instance-owned, never parity-compared), so an instance flip does not,
  and should not, propagate to forks. **SE-3 makes this mandatory, not merely tidy:** strict-by-default
  would convert every not-yet-observed legitimate write on a fresh machine into a hard failure, and
  would lock out any deployer lacking `bwrap`/`socat`. A fork adopts strict only after **its own** clean
  burn-in, exactly as `docs/USING-THIS-TEMPLATE.md` Step 4c already instructs. That guidance is
  therefore left unchanged.
- **The spec already covers this.** The **OS/Harness-Enforced Agent Write Scope** requirement's
  "Two-stage adoption" clause names the strict stage and its dependency guard verbatim. Executing the
  anticipated stage is an operational milestone, not a model change — hence **no spec delta**.
- **Scope is exactly two keys on one instance.** No area moves in or out of the denied set; the
  `denyWrite` list, `excludedCommands`, `allow`, and network allowlist are untouched.

## Options considered

- **(a) Instance-only flip; template stays burn-in (chosen).** Matches SE-3, the SEED nature of
  `settings.json`, and the spec's existing "separate deliberate operator action" wording. Operator
  decision, 2026-07-27.
- **(b) Ship the strict keys in `vault-template/` as a fork default.** Rejected: contradicts SE-3 and
  the lockout guard — a fork inherits strict before observing its write inventory or verifying deps,
  turning a safety feature into a day-one outage.
- **(c) Apply the keys live with no ADR.** Rejected: an enforcement-**posture** change recorded only as
  a config diff is one no future reader can distinguish from an accident — the precise anti-pattern
  ADR-0022 and ADR-0033 exist to prevent.

## Consequence / sacrifice

- **The escape hatch is gone.** Any legitimate write outside `allowWrite`/`excludedCommands` that
  burn-in did not surface now **hard-fails** instead of prompting. Accepted because burn-in ran clean
  and the write inventory was observed; the residual risk is a rare path that will announce itself as a
  loud failure, not silent corruption. Watch specifically the harness scratchpad under `/tmp` and
  `~/bin` render targets (operator-run per INV-3 — agent-side denial there is correct).
- **Fail-closed is a real lockout surface.** If the sandbox cannot initialise, the session refuses to
  start — *including the session that would fix it*. Mitigated by the verified-present deps (SE-2) and
  the deps-before-flip ordering; **reversal is removing the two keys** from the one instance file, no
  migration.
- **The Phase-1a probe sheet is re-run by this flip, and today's pre-flight is the first pass.** P6/P12
  were re-run 2026-07-27 and passed. The sheet's rows left stale by ADR-0033 (P2/T1/T5/P6 references to
  retired paths) remain a separate documentation cleanup, not a blocker — named here so the trap is
  defused by record.
- **Forks are unaffected.** They keep the burn-in default and the two-stage guidance; nothing about
  their onboarding changes.

## Application (operator, Phase-1b — the agent cannot perform this)

`.claude/` is itself in the denied set, so the agent is structurally unable to edit the live settings
file (this is what P6/T2 prove). The flip is a human action:

1. Confirm deps: `command -v bwrap socat` → both resolve. *(Verified 2026-07-27; re-confirm at apply.)*
2. Edit `/home/administrator/Documents/Vault/.claude/settings.json`, adding to the `sandbox` object:
   `"failIfUnavailable": true,` and `"allowUnsandboxedCommands": false,`.
3. Validate JSON parses, then **start a fresh session** and run the pre-flight probe once more (P6
   EROFS on `40-Treasury/`, P12 control write to `10-Logbook/`) to confirm the guarantee now also
   holds against sandbox-unavailability.
4. **Rollback:** remove the two keys; the instance returns to burn-in with no other change.
