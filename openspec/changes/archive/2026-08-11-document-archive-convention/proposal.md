<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: document-archive-convention

## Why

The rule for when an OpenSpec change is archived exists in **no spec, ADR, or runbook**. A grep of all
six capability specs for "archive" returns **zero requirements**. It has lived only in per-change
`tasks.md` files — the one place nobody reads at decision time.

On 2026-08-11 that gap cost a full working session. Asked to follow precedent, the agent **inverted the
convention twice in one day**, each time from a different flawed measurement, each time reported with
full confidence, and twice talked the operator out of a correct instinct:

| # | Flawed method | What it produced |
|---|---|---|
| 1 | Read `archive(<slug>)` **commit subjects** as pull-request boundaries | "40+ of 48 archive in a separate PR" — but a separate *commit* routinely sits on the feature branch inside one *PR* |
| 2 | `git log --merges --ancestry-path X..main \| tail -1` | Impossible attributions — an archive credited to a `dependabot/` PR numbered *lower* than the PR that created the change |
| 3 | Merge-walk with `--diff-filter=A` | Silently omitted **every deferred archive**, because a directory moved into `archive/` records as a **rename**. The tell was a denominator dropping without explanation |

The lesson is not "be careful with git". It is that **an undocumented convention does not merely get
forgotten — it gets confidently re-derived wrong, and the confidence travels further than the error.**

## The measurement of record

Walk `main`'s first-parent merges; for each merge `M`, diff `M^1..M` **with `--no-renames`** and ask
what that merge introduced. Cross-check against a case already known.

```
git log --first-parent --merges --format=%H%x1f%s main
git diff --name-only --no-renames --diff-filter=A <merge>^1 <merge>
```

Pull-request era, denominator **14**:

| Shape | Count |
|---|---:|
| **ONE pull request — archived on the feature branch** | **12** |
| Two pull requests — separate archive PR | 2 |

47 archived changes exist; **32 predate the pull-request workflow** and were committed straight to
`main`, so they are excluded from the denominator rather than absorbed into it.

**Both deviations share one cause** — `add-template-mirror-driver` (#40→#41) and
`flip-scope-review-blocking` (#58→#59) each carry a `maintenance` delta and each had a concurrent
sibling touching `maintenance`. They are the exception firing, not a rival convention.

Every written instruction already agreed: `CONTRIBUTING.md` orders `apply` → `archive` → *then* open
the PR; `pr-flow.py` step 11 is "spec delta archived on this branch"; `enforce-inv7-secret-scan`'s
tasks.md says "archive on the feature branch before merge (else a second archive PR is owed)" — **and
that change followed it**, in PR #44.

## What Changes

- **ADDED requirement** (`maintenance`): *A Change Is Archived On Its Own Branch* — archive on the
  feature branch in the merging PR; defer only for a concurrent change touching the same capability
  spec, naming it; the convention must be discoverable outside per-change task files; re-derivations
  must use a pasted transcript over merge history, not commit subjects. 3 scenarios.
- **ADDED** `openspec/adr/0040-archive-on-the-feature-branch.md` — context, the three flawed methods,
  the method of record, options, decision, consequences, sacrifice, follow-on.
- **MODIFIED** `CONTRIBUTING.md` — state the rule and its exception at the flow, where the decision is
  actually made.
- **MODIFIED** `README.md` — ADR count 39 → 40 (hard lockstep, enforced by the existing count check).

### What is deliberately NOT in this change

**No CI guard.** An earlier plan shipped the requirement and its enforcement together, on the argument
that a rule without a mechanism is the `constitution.md` §4 defect. That argument is half right: §4's
defect is **claiming** enforcement that does not exist. This change documents a rule and states plainly
that nothing enforces it yet, which is honest rather than defective.

The guard is deferred because its **exception is not yet expressible**. The naive rule — *a merged PR
must not leave a live `openspec/changes/<slug>/` on `main`* — correctly catches the default violation
but **would have failed PR #58, which deferred legitimately**. A pull-request-body marker declaring the
deferral reintroduces an unverifiable claim. Deriving the exception from repository state is the
promising direction, but the one measured instance does not exhibit that signature at merge time.
Recorded as ADR-0040's follow-on with that trigger, rather than shipped half-understood.

**No `pr-flow.py` edit.** An earlier draft queued the step-11 NOTE as text to fix, on the belief it
argued against the convention. **It states the convention correctly and cites a real cost (v0.1.34).**
That queued item is withdrawn.

## Nature of the change — ordinary, not a constitution-override

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the test applies.
- **ADD-only.** No existing requirement modified, weakened, or narrowed; nothing sacrificed, so no
  override and no Gate-4 sacrifice to accept. Precedent: PR #53, PR #62.
- `constitution.md` §2 places conventions at **Tier 2** — *"Ordinary OpenSpec change — no ceremony
  required."* §5's hard stop concerns *modifying* a `protects:`-tagged element; this adds.

⚠ `constitution-lint` performs no diff analysis, so CI passing is not evidence of this classification.
It rests on the reasoning above.

## This change is archived on its own branch

Per the rule it documents. The exception does not apply: `estate-scoped-capability-probe` carries a
`maintenance` delta but is **unimplemented and parked on its own branch**, so there is no concurrent
archive to order against. `enforce-adr-reference-integrity` merged in PR #62 and owes a second archive
PR — that debt is tracked below, not silently absorbed here.

## Blast radius (swept 2026-08-11, re-runnable)

```
grep -rn "archive" openspec/specs/*/spec.md
grep -rn "opsx:archive\|archive" CONTRIBUTING.md AGENTS.md README.md
grep -nE "[0-9]+\s+(ADRs?|Architecture Decision Record)" README.md
```

| Reference | Action |
|---|---|
| `openspec/specs/*/spec.md` | **zero** hits before this change — the gap being closed |
| `CONTRIBUTING.md` flow block | **UPDATE** — state the rule + exception |
| `README.md` (3 ADR-count sites) | **UPDATE** — 39 → 40, range → `ADR-0001–0040` |
| `tools/pr-flow.py` step 11 + NOTE | **no change** — correct as written |
| `openspec/changes/archive/*` | **no change** — historical records, correctly immutable |

## Debt this change does not clear

`enforce-adr-reference-integrity` (PR #62) merged unarchived and owes an archive PR. It is blocked
until **ADR-0040 exists**, because its proposal and tasks cite `ADR-0040` nine times and the
reference-integrity check merged in that same PR fails an archived change carrying unresolved
citations. Landing this change unblocks it. That ordering is a consequence of the rule working, and is
stated here rather than discovered in CI.

## Impact

No `vault-template/` change. No script change. No existing requirement modified.
