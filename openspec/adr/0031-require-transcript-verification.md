<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0031 — Ceremony enumeration and verification deliverables are command transcripts

**Status:** Proposed (2026-07-18)
**Change:** `require-transcript-verification`
**Relates to:** ADR-0030 (mechanical over conventional enforcement), the
`determinism-failure-modes-claude` record (F8, F9, F14, F17, F20) and its root-cause synthesis
(RC-2: self-composed verification shares a common-mode failure with the thing verified; RC-4:
framing misses are effort-insensitive — enumeration must be corpus-bounded, not
cognition-bounded).

## Context

The Informed-Upheaval Protocol's Gate 1 says "Enumerate the full blast radius"; Gate 3 says
tests "pass green"; Gate 4 says "a second review confirming the blast radius was fully
addressed." All three name deliverables whose absence of quality is **unobservable**: a
plausible composed list and an exhaustive one look identical; a passing check and an inert one
print similar output. The failure record supplies the evidence: F17 (Gate 1 read, then satisfied
by reasoning; a Tier-0 `protects:`-tagged spec missed), F8/F9 (blast-radius misses, same class),
F20 (a filter that structurally could not select a failure, read as "all green" — recurring
twice more after the corrective was written), and a `head -3` that silently truncated an
enumeration. The instructive contrast, same session as F17: the README ADR count had a
mechanical guard and the identical error class **never shipped**. The difference was not care;
it was coverage. Raising model effort does not close this class — F14 occurred at xhigh — because
a blind spot is out-of-frame at every effort level. `grep` is exhaustive; reasoning is not.

## Options

- **(a) Keep the prose principles** ("be thorough", "verify before acting") — rejected: the
  operation's own gold-graded finding is that knowledge held the line zero times out of six;
  a principle without a mechanical check is a wish.
- **(b) LLM-as-judge review of proposals** — rejected: reintroduces a generative, non-reproducible
  reviewer into the deterministic layer (INV-6 posture), and shares the common-mode failure it
  is meant to catch.
- **(c) Transcript deliverables (chosen)** — enumeration and verification are satisfied only by
  pasted, re-runnable command transcripts with full output and per-hit disposition; verdict
  strings printed by the shell are banned as evidence. Converts unfalsifiable diligence into a
  diffable artifact; the Gate-4 reviewer re-runs, not re-reads.
- **(d) CI-parsed machine-checkable transcripts** — deferred, not rejected: a lint that re-runs
  the embedded command and diffs mechanically is a natural hardening once the transcript format
  has settled. Review remains human at this step.

## Decision

Adopt (c) across the ceremony surface: constitution §3 gate text (Gate 1 transcript, Gate 3
evidence-not-verdicts, Gate 4 re-run-and-diff), the `constitution-override` template (mandatory
transcript block + checkboxes), an ADDED `agent-integration` requirement as the durable spec
anchor, and two `AGENTS.md` operating rules generalizing the discipline to all governed work —
including the delivery-channel rule (commands handed to the operator name actor + channel; long
content travels as a file, never an interactive paste — F14).

## Consequences

- Gate-1/Gate-3 quality becomes reviewable by re-execution: a miss is a dirty diff, not a
  judgment call. The F8/F9/F17 class becomes structurally detectable at the gate that owns it.
- Proposals get longer and their authoring slightly slower — the length is the evidence.
- Lower-effort executors become safer to delegate to: their work product carries its own
  falsifiable audit trail (this is the enabling control for the fix-program's execution split).

## Sacrifice

Ceremony brevity, and the comfort of narrative diligence. Honestly bounded: a transcript is
still text — it can be faked or go stale between authoring and review. The rule's guarantee is
**falsifiability** (any reviewer can re-run and diff at any moment), not impossibility of
deceit; mechanical re-execution in CI (option d) is the available escalation if staleness or
fakery is ever observed in practice.
