<!-- SPDX-License-Identifier: Apache-2.0 -->
## Why

The ceremony's enumeration and verification steps are, today, prose asking a model to be
thorough — and the failure record proves that never holds. Gate 1 of `retire-effort-projections`
was **read and then not executed**: the blast radius was composed by reasoning about where scripts
are typically described, and a second Tier-0 `protects:`-tagged spec was missed (F17, caught at
Gate 3 by a residual sweep, not by the gate whose job it was). The same session produced a CI
check whose filter structurally could not select a failure, captioned "empty = all green" above 26
printed rows (F20) — plus two recurrences *after* that lesson was committed. Earlier: two
blast-radius misses (F8/F9) and a `head -3` that truncated an enumeration into a sample.

The root cause is single and named (operator, F17): **a gated change is not a discovery
activity.** Problem-solving is generative — bounded by what the agent thinks of. Enumeration must
be exhaustive — bounded by the corpus. `grep` is exhaustive; reasoning is not. And a verification
whose failure case is not observable is decoration: the instructive contrast in the same session
was the README ADR count, where the same class of error **never shipped because a mechanical
check** (`adr-count` guard) **covered it**. The difference was not care; it was coverage.

This change converts the ceremony's two unfalsifiable deliverables — "did the proposer think of
everything?" and "did the checks pass?" — into falsifiable ones: **"does the pasted transcript
match the corpus?"** and **"does the pasted output show the evidence?"** It is program item 2 of
the root-cause synthesis in the live vault's `determinism-failure-modes-claude` Site
(`failure-modes-root-cause-synthesis.md`, RC-2 + RC-4), and it deliberately ships **before** the
driver builds, because it is the control that makes lower-cost execution of the remaining program
items reviewable.

## What Changes

1. **Constitution §3 — Gate 1** (`openspec/constitution.md:154`): the blast-radius enumeration is
   delivered as a **pasted, re-runnable command transcript** — the exact search command(s) plus
   their full, untruncated output — never a list composed from reasoning. The command set must
   sweep the whole repo corpus.
2. **Constitution §3 — Gate 3** (`openspec/constitution.md:163`): every named test/lint result is
   evidenced by its command and output (a tally with a denominator, a diff, an exit status) —
   never a prose assertion or a shell-printed verdict string.
3. **Constitution §3 — Gate 4** (`openspec/constitution.md:168`): the second review confirms the
   blast radius **by re-running the Gate-1 transcript and diffing**, not by re-reading the list.
4. **Override template** (`openspec/templates/constitution-override/proposal.md`): Gate-1 gains a
   mandatory enumeration-transcript block (the checklist is *derived from* it); Gate-3 gains a
   verification-transcripts checkbox; Gate-4 gains a transcript-re-run checkbox.
5. **`AGENTS.md` operating notes**: two additions — (a) the transcript rule generalized to all
   governed work (enumerate/verify ⇒ transcript; no truncation; no shell-printed verdict
   strings); (b) commands handed to the operator name their **execution path** (actor + delivery
   channel), and long/multi-line content travels as a file, never a long interactive paste (F14).
6. **`agent-integration` spec**: ADDED Requirement *Verification Deliverables Are Transcripts*
   (delta in `specs/agent-integration/spec.md`) — the durable spec anchor for 1–5.
7. **ADR-0031** (`require-transcript-verification`, Proposed) + README ADR counts 30 → 31 (both
   occurrences; the `adr-count` CI guard enforces totality).

## Classification (surfaced deliberately for the operator)

This is a **conforming amendment, ordinary change + ADR — not a constitution-override**: it
overrides no CONST/INV principle and weakens nothing; it strengthens the ceremony's own
deliverable format (additive). Precedent: `enforce-naming-token-floor` (ADR-0030) modified two
`protects:`-tagged specs as an ordinary change because it strengthened enforcement. It does,
however, edit `openspec/constitution.md` §3 text — surfaced here per §5 so the human sign-off on
this proposal is explicit and informed. If the operator judges the ceremony's own text to deserve
the override ceremony, say so and this change will be re-cast.

## Impact

- Affected specs: `agent-integration` (ADDED requirement; `protects:` tags untouched).
- Affected governed docs: `openspec/constitution.md` (§3 gate text, additive),
  `openspec/templates/constitution-override/proposal.md`, `AGENTS.md`, `README.md` (ADR counts).
- Not affected (verified by the enumeration transcript in `tasks.md`): the maintenance spec's
  scope-declaration requirement and `.github/pull_request_template.md` — both *consume* Gate-1
  output and keep working unchanged; the `scope-review` CI job; all fleet scripts.
- Cost accepted: ceremony verbosity — proposals carry long transcripts. That is the point: the
  length is the evidence. A transcript can still be faked or go stale; the rule's claim is
  falsifiability (a reviewer can re-run and diff), not impossibility.

## Sign-off

Proposal approved by the operator (explicit "Approved", in-session, 2026-07-18) — authorizes
the apply per tasks.md. Final Gate-4 re-check occurs at PR review; ADR-0031 flips
Proposed → Accepted there.
