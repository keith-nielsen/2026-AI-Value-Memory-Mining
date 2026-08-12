<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0040 — Archiving is part of the change, not a follow-up: archive on the feature branch

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-08-11)
**Date:** 2026-08-11
**Change:** `document-archive-convention`
**Relates:** **ADR-0031** (transcript verification — evidence must be a pasted command transcript, the
discipline that finally settled this); **ADR-0034** / **ADR-0039** (the gate chain this ceremony runs
through).

---

## Context

The rule for *when* an OpenSpec change is archived — the step that syncs its spec delta into
`openspec/specs/` — has never existed in any spec, ADR, or runbook. A grep of all six capability specs
for "archive" returns **zero requirements**. It has lived only in per-change `tasks.md` files: the one
place nobody reads at decision time.

On 2026-08-11 that gap cost a full working session. An agent asked to follow precedent **inverted the
convention twice in one day**, each time from a different flawed measurement, and each time reported
the result with full confidence:

1. **Commit subjects were read as PR boundaries.** 40+ archived changes carry a dedicated
   `archive(<slug>): apply delta; stamp CHANGELOG` commit. That is a separate *commit* — which
   routinely sits on the feature branch inside a single *pull request*. It was reported as evidence of
   a separate archive PR.
2. **"Earliest merge containing commit X"** (`git log --merges --ancestry-path X..main | tail -1`)
   returned impossible attributions — an archive credited to a `dependabot/` pull request numbered
   *lower* than the pull request that created the change.
3. **`--diff-filter=A` cannot see a move.** A directory moved into `archive/` records as a **rename**,
   so a merge-walk silently omitted every deferred archive — including the one known case — until
   `--no-renames` was supplied. The tell was a denominator that dropped without explanation.

The operator's own instinct was correct throughout and was twice talked out of it by these numbers.
That is the real cost being recorded here: **an undocumented convention does not merely get forgotten,
it gets confidently re-derived wrong, and the confidence travels further than the error.**

## The measurement (method of record)

Walk `main`'s first-parent merges; for each merge `M`, diff `M^1..M` **with `--no-renames`** and ask
what that merge *introduced*. Cross-check the result against a case already known.

```
git log --first-parent --merges --format=%H%x1f%s main
git diff --name-only --no-renames --diff-filter=A <merge>^1 <merge>
```

Pull-request era, denominator **14**:

| Shape | Count | Cases |
|---|---:|---|
| **ONE pull request — archived on the feature branch** | **12** | #6, #25, #33, #34, #36, #38, #39, #44, #45, #51, #53, … |
| Two pull requests — a separate archive pull request | 2 | #40→#41 (`release/v0.1.34`), #58→#59 (`chore/archive-…`) |

(47 archived changes exist; 32 predate the pull-request workflow and were committed directly to
`main`, so they are unattributable either way and are excluded from the denominator rather than
silently absorbed into it.)

**Both deviations share one cause.** `add-template-mirror-driver` and `flip-scope-review-blocking` each
carry a **`maintenance`** delta, and each had a concurrent sibling also touching `maintenance`
(`add-telemetry-segment`; `bootstrap-capability-probe`, merged three hours earlier). They are the
exception firing — not a rival convention.

Every written instruction already agreed with the 12: `CONTRIBUTING.md` orders `apply` → `archive` →
*then* open the pull request; `pr-flow.py` step 11 is *"spec delta archived on this branch"* and its
NOTE cites what v0.1.34 paid; `enforce-inv7-secret-scan`'s tasks.md says *"archive on the feature
branch before merge (else a second archive PR is owed)"* — **and that change followed it**, in PR #44.

## Options

1. **Leave it undocumented.** Rejected — it has now demonstrably produced a wrong answer twice, and the
   next re-derivation starts from the same three traps.
2. **Adopt the separate-archive-PR shape as the rule** (what the flawed measurement implied). Rejected:
   it contradicts every written instruction and 12 of 14 cases, and it costs an extra pull request per
   change for no benefit the record shows.
3. **Document the measured rule, with its exception, and enforce it mechanically in the same change.**
   Rejected *for now* on the enforcement half — see *Follow-on*. Shipping a guard whose exception is
   not yet expressible would either over-deny the legitimate concurrency case or carry an escape hatch,
   and the corpus already has enough documented-but-unenforced claims.
4. **Document the measured rule with its exception; name enforcement as a follow-on with its open
   design question.** Chosen.

## Decision

**A change is archived on its own feature branch, in the same pull request that merges it.** The
archive step moves `openspec/changes/<slug>/` to `openspec/changes/archive/<YYYY-MM-DD>-<slug>/`, syncs
the delta into `openspec/specs/`, and stamps the CHANGELOG — before the pull request is opened.

**Exception — concurrent changes touching the same capability spec.** Where another in-flight change
carries a delta against the *same* spec file, the archive is deferred and applied in merge order, to
avoid a batch archive silently overwriting the other's delta (last-writer-wins). The cost is a second
pull request, and that cost is accepted deliberately in that case only.

**This ADR does not claim any mechanism enforces the above.** The rule is documented; enforcement is
owed.

## Consequences

- The default path costs no extra pull request, and `openspec/specs/` never lags a merged change.
- `pr-flow.py` step 11 and its NOTE are **correct as written** and need no edit — an earlier reading of
  them as arguing against the convention was itself the inverted measurement talking.
- A deferred archive is now a *named* state with a stated reason, not an unexplained second pull
  request.
- The rule is discoverable at decision time: `CONTRIBUTING.md` for the flow, the `maintenance` spec for
  the requirement, this ADR for the reasoning and the measurement method.

## Sacrifice (what is knowingly given up)

**Enforcement is not shipped with the rule.** Until the follow-on lands, this convention is prose plus
a driver advisory, and a change can still merge unarchived without CI objecting — exactly the class of
gap that let this drift in the first place. That is accepted, consciously, in preference to shipping a
guard that would either block the legitimate concurrency case or contain a hole wide enough to make it
decorative.

**The 32 pre-workflow changes are excluded from the denominator**, so the rule rests on 14 cases, not
47. A larger sample is not available and is not manufactured here.

## Follow-on

**Owed:** mechanical enforcement of the archive step.

**Open design question that must be answered first:** how to express the concurrency exception without
an escape hatch. A naive guard — *a merged pull request must not leave a live `openspec/changes/<slug>/`
on `main`* — correctly catches the default violation but would have failed PR #58, which deferred
legitimately. A body marker declaring the deferral reintroduces an unverifiable claim. The promising
direction is deriving the exception from the corpus itself (two in-flight changes carrying deltas
against the same capability spec is a mechanically checkable condition), but the one measured instance
does not exhibit that signature at merge time, so the rule is not yet safely expressible.

**Trigger:** a design that decides the exception from repository state rather than from a declaration.
Until then, this remains documented and unenforced, and says so.
