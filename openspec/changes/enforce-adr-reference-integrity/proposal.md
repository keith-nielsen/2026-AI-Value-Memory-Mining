<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: enforce-adr-reference-integrity

## Why

`.github/workflows/ci.yml:513` has cited **ADR-0039** since PR #58 (2026-08-06). No such ADR existed —
shipped CI configuration asserting a record that was never written. The originating change never
planned one; its proposal cites ADR-0034 and ADR-0038 only, so the number was coined in the comment
and never redeemed.

That is the same disease as the `constitution.md` §4 false rows already in the hardening queue —
**documentation and mechanism out of correspondence** — and it survived nine merged pull requests
because nothing in CI checks that an ADR citation resolves.

Measured 2026-08-11, corpus-wide:

```
grep -rhoE "ADR-[0-9]{4}" --include=*.md --include=*.yml --include=*.py . | sort -u
→ 40 distinct ADR ids cited;  38 files on disk (0001–0038, contiguous, no duplicates)
→ dangling: ADR-0039 (.github/workflows/ci.yml:513)
            ADR-0040 (openspec/changes/estate-scoped-capability-probe/tasks.md:106)
```

**The two dangling citations are different in kind, and that difference is the whole design problem.**
`ADR-0039` is shipped configuration claiming a record exists. `ADR-0040` is a change directory
declaring work it owes. A naive "every cited ADR must exist" rule fails the honest one — the RC-E
over-denial shape the corpus already warns about in `assert_preconditions`.

## Three defects, not one

Auditing the citation gap surfaced two more in the same `spec-lint` job:

| # | Defect | Evidence |
|---|---|---|
| 1 | **`Check all expected ADRs exist` is very nearly vacuous** — `EXPECTED = [f"openspec/adr/{i:04d}-" for i in range(1, 9)]`, hardcoded when the corpus had 8 ADRs. It validates **8 of 38** and passes regardless of anything added since. | `ci.yml`, `spec-lint` |
| 2 | **A gap in the numbering is undetectable.** The README check compares README's claimed count to `n` and requires the highest number to appear. Ship `0040` without `0039` and both move consistently — it passes with a hole in the record. | `ci.yml`, `spec-lint` |
| 3 | **Nothing checks that a cited ADR resolves.** This is what let `ADR-0039` dangle in shipped CI config for nine pull requests. `link-check` does not reach it: these are bare ids in prose and comments, not markdown links. | measured above |

Defect 1 is item 10's class exactly — *a tool that reports a non-result as a result*. It has been
green on every run while checking almost nothing.

## What Changes

- **ADDED requirement** (`maintenance`): *An Architecture Decision Record Citation Resolves* — the ADR
  set is contiguous from `0001`; every cited id resolves; forward references are confined to change
  directories. 4 scenarios.
- **ADDED** `openspec/adr/0039-flip-scope-review-blocking.md` — the missing record, consolidated from
  the `ci.yml` comment block and `flip-scope-review-blocking`'s proposal rather than reconstructed.
  **This change cannot pass its own check without it**, which is why the two ship together.
- **MODIFIED** `.github/workflows/ci.yml` (`spec-lint`) — replace the `range(1, 9)` hardcode with a
  contiguity assertion; add the reference-integrity check.
- **MODIFIED** `README.md` — ADR count 38 → 39 in three places and the range `ADR-0001–0038` →
  `ADR-0001–0039`. Enforced by the existing README count check, so this is hard lockstep, not tidying.

## The forward-reference policy — scoped, and read off the data

Operator decision 2026-08-11, from three candidates:

| | Policy | Verdict |
|---|---|---|
| 1 | **Strict** — any dangling citation fails; forward references need an ADR stub marked `Status: Proposed` | rejected: forces a stub before the decision is made, and stubs linger |
| 2 | **Marked-owed** — `ADR-0040 (owed)` is permitted anywhere | rejected: an escape hatch that can say "(owed)" forever — the §4 disease in a new place |
| 3 | **Scoped** — dangling permitted **only** inside `openspec/changes/<slug>/`; anywhere else it fails | **chosen** |

The rationale is structural rather than stylistic: **a change directory is a proposal, and proposals
are forward-looking by nature; everything else — `ci.yml`, specs, `README.md`, `AGENTS.md`,
`CONTRIBUTING.md`, and the archive — is a record, and a record must resolve.** Applied to the measured
data it produces exactly the right verdicts with no annotation convention to maintain: `ADR-0039` in
`ci.yml` **fails**; `ADR-0040` in a change directory **passes**.

Note the deliberate consequence: **archived changes are records, not proposals.** A forward reference
that was legitimate while a change was live becomes a dangling citation once archived — which is
correct, because by then the ADR it promised should exist.

## Nature of the change — ordinary, not a constitution-override

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the classification test
  applies.
- **ADD-only.** No existing requirement is modified, weakened, or narrowed; nothing is sacrificed, so
  there is no override and no Gate-4 sacrifice to accept. Precedent: PR #53 added a requirement to this
  same `protects:`-tagged spec and classified itself ordinary.
- `constitution.md` §2 places conventions at **Tier 2** — *"Ordinary OpenSpec change — no ceremony
  required."* §5's agent hard stop triggers on *modifying* a `protects:`-tagged element; this adds.
- Therefore: **ordinary OpenSpec change.**

⚠ `constitution-lint` performs no diff analysis, so CI passing is not evidence this classification is
right. It stands on the reasoning above.

## Blast radius (swept 2026-08-11, re-runnable)

```
grep -rhoE "ADR-[0-9]{4}" --include=*.md --include=*.yml --include=*.py . | sort -u
grep -nE "[0-9]+\s+(ADRs?|Architecture Decision Record)" README.md
grep -rn "ADR-0039\|ADR-0040" --include=*.md --include=*.yml . | grep -v node_modules
```

| Reference | Action |
|---|---|
| `.github/workflows/ci.yml` `spec-lint` (2 steps) | **UPDATE** — contiguity + reference integrity |
| `.github/workflows/ci.yml:513` (`ADR-0039` citation) | **no change** — the citation becomes true when the ADR lands |
| `README.md:29`, `:100`, `:250` | **UPDATE** — count 38 → 39; range → `ADR-0001–0039` |
| `openspec/changes/estate-scoped-capability-probe/tasks.md:106` (`ADR-0040`) | **no change** — legitimate forward reference under the chosen policy; the sibling change owes it |
| `openspec/adr/0001`–`0038` | **no change** — contiguous, verified |

## Regression evidence

Nothing is built yet — every task is `[ ]`. Per the standing Definition of Done, `[~]` is claimed only
when built and `[x]` only when a test was **observed to fail without the change**. The reference check
must be observed **failing on today's tree** (`ADR-0039` dangling) before the ADR is added, or the test
proves nothing: adding the ADR first makes the check pass vacuously and the evidence evaporates.

## Impact

No `vault-template/` change; no schema change; no existing requirement modified. `spec-lint` becomes
strictly stronger, which means **it may fail on the first run against pre-existing corpus state** —
that is the check working, and any finding it raises is a real defect to fix, not a reason to weaken
the rule.
