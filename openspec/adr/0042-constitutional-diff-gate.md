<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0042 — The constitutional diff gate: refuse silence, not work

**Status:** **Proposed** (human sign-off pending)
**Date:** 2026-08-16
**Change:** `constitutional-diff-gate`
**Relates:** **PR #85** (retracted six false enforcement claims, and recorded this gate as owed);
**ADR-0039** (the `scope-review` Phase-A/Phase-B burn-in pattern this reuses); **ADR-0041**
(pre-flight the route locally); **ADR-0034** (required status checks and the context-naming trap).

## Context

`constitution.md` §5 used to argue that the Informed-Upheaval Protocol was the right mechanism because
it was, among other things, *"mechanically enforced (CI fails without the ceremony)."* PR #85 measured
that claim against `ci.yml` and the live ruleset and found it false — one of six such rows. It removed
the claim rather than softening it, and said why:

> That claim is removed rather than softened, because it was the load-bearing argument for why this
> mechanism was chosen […] **Restoring the fifth means building the diff gate, not rewording this
> paragraph.**

This ADR is that build.

**The inversion being closed.** By §2's own tier table, Tier-0 elements (INV-1–8, INV-11, INV-14) are
held by the sandbox, the hooks, the CI runners and the server-side rulesets — mechanisms that can
refuse. Tier 1 (`CONST-01`–`05` + INV-12), described in the same document as *"what the constitution
most exists to protect"*, was held by paperwork alone. **The layer named most precious had the least
resistance.**

**Why not more prose.** This repository's standing finding is `CONTRIBUTING.md:92` — *"a rule which
cannot refuse does not bind."* F38 supplied the local evidence: of three violations in one change, the
two caught at the moment of the mistake were caught by instruments that **refuse**; the one that
escaped to `main` was governed by a prose rule its own author had written hours earlier. Adding a
fifth paragraph to §3 would also be the class-9 defect — a criterion restated rather than derived —
committed inside the document that defines it.

## Decision

**Build a CI job that reads the diff and refuses a change that touches a `protects:`-tagged
specification without a committed declaration of its constitutional impact.**

Three properties define it, and the first is the one that makes it safe:

1. **The gate refuses silence, not work.** It does **not** evaluate whether a declaration is correct.
   Whether a change overrides a principle is the human judgement §5 reserves; a gate that guessed
   would refuse legitimate work while lending false authority to its own verdict. It establishes that
   the question was answered in writing and that the answer is in version control. That is the entire
   claim, and it is smaller than "mechanically enforced" — it must never again be described as more.
2. **The subject set is read from YAML frontmatter, never a substring match.** Measured on `main` @
   `a9df354`: **6** files carry a `protects:` frontmatter tag; **17** more quote the string in prose,
   including `CHANGELOG.md`, `.github/workflows/ci.yml`, and `openspec/constitution.md` itself. A
   `grep`-based gate would refuse the changelog, refuse the workflow that implements the gate, and
   deadlock the constitution.
3. **The declaration lives in the tree, not the pull-request body.** This deliberately diverges from
   `scope-review`, and the reason is disqualifying rather than stylistic: **a PR body can be edited
   after its checks report green, and editing it does not re-evaluate them.** A constitutional
   declaration that can be changed after verification is not evidence. It also makes the gate runnable
   locally, before any pull request exists (ADR-0041).

## Options considered

| Option | Why not |
|---|---|
| **Semantic gate** — infer from the diff whether a principle was overridden | Not decidable from a diff, and a wrong refusal on a legitimate change trains its reader to bypass every gate (RC-E). It would also usurp the judgement §5 reserves to a human |
| **Nothing; keep the prose** | The status quo PR #85 measured. Tier 1 stays the least-defended layer, and §5's own argument stays retracted |
| **Extend `constitution-lint`** | That job's context name is already in `required_status_checks`; renaming or reshaping a required context is the deadlock ADR-0034 warns about. A separate job keeps the existing context untouched |
| **Declaration in the PR body** (`scope-review`'s channel) | Editable after checks report green; unavailable to local pre-flight; lost when a body is regenerated |
| **Gate `constitution.md` too** | It carries no frontmatter tag, so it would need a special case — and gating it means every corrective edit needs a declaration. **PR #85, which removed six false claims, would itself have been refused.** Friction would land hardest on exactly the edits this operation has needed most |

## Consequence

- A change touching one of the six protected specs must add four lines to its proposal. Measured
  firing rate: **4 of the last 25 merges (16%)**, and all four already carried an
  `openspec/changes/` directory in the same diff — so the gate never demands something the author
  cannot supply.
- Archive PRs sync deltas into protected specs **by construction** and are handled explicitly: the
  declaration is resolved at either the live or the archived change path. Without this, the gate
  would refuse a routine ceremony step roughly every release cycle.
- `constitution.md` §4 gains a row describing what the job does, and its *"What is NOT mechanically
  enforced"* block gains a bullet that will become false at the Phase-B flip — deliberately, so the
  flip must rewrite it.
- The `constitution-override` template carried **three** of the claims PR #85 retracted, in the file
  an author reads *while performing the ceremony*. Corrected here to describe reality, not deleted.
  Item 14's standing rule — verify every row, not the ones the ticket names — applied across the
  boundary it stopped at last time.

## Sacrifice

**Stated plainly, because a gate that oversells itself is the defect this one exists to correct.**

- **A false declaration still passes.** `overrides: none` on a change that does override a principle
  is not detected, and cannot be by any mechanism short of the human review §5 already requires. What
  the gate removes is the *silent* case — where the question was never asked at all — and what it adds
  is a signed, versioned claim that Gate 4 can re-read.
- **`CONST-01`–`05` remain ungated** by this change; the constitution is out of the subject set.
  Closing that is a separate, smaller change: hashing the five principle sections in
  `constitution-lint` so an edit to a principle's *text* must be consciously re-baselined while prose
  corrections elsewhere pass. Recorded as owed rather than forgotten — the failure mode item 28 came
  from.
- **The gate is report-only for now.** Zero existing proposals carry the declaration block, so a
  blocking gate on day one would refuse 100% of legitimate spec changes. Until the flip, **a green
  gate is not evidence of anything**, and §4 says so.

## The one criterion this gate forks, and how the fork is detected

`TIER_2_IDS = {"INV-13"}` encodes the single exception from §2's tier table — Tier 2 needs no
ceremony. Everything else is treated as ceremony-requiring, so the encoding **fails toward the
ceremony** rather than away from it.

This is a fork of another artifact's rule, which is exactly the class-9 defect. It is accepted
knowingly, bounded to one identifier rather than a restatement of the whole table, and made
**detectable**: `test_tier2_exception_matches_the_constitution` reads §2 and fails the moment the
constitution stops listing INV-13 as Tier 2. A fork that cannot drift silently is a materially
different risk from one that can.
