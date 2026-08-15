<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: preflight-route-before-mutation

## Why

The v0.1.39 ceremony (2026-08-11/13) took **four pull requests and repeated re-runs** to land three
changes. Sorting the re-runs by cause shows most were avoidable, and avoidable *locally*:

| Cause | Instance | Avoidable before pushing? |
|---|---|---|
| Declared scope missed the removed side of a rename | PR #64 `scope-review` FAIL → body fix + an empty commit to refresh the payload | **Yes** |
| A change could not archive because it cited an ADR it did not ship | archive branch built, failed with **9 unresolved citations**, abandoned, order reversed | **Yes** |
| Two changes appending to one capability spec | avoided by ordering — by luck, not by measurement | **Yes** |
| GitHub eventual consistency | head-propagation lag; `REFUSED` after `"merged": true`; an orphaned check run | **No** — a settling problem, not a prediction problem |

Every "yes" row is a question the repository can already answer about itself. Nothing was missing
except the habit of asking before mutating — and an agent asking by hand is exactly the improvisation
these drivers exist to remove (the *"four worse probes were hand-rolled instead"* failure recorded in
`2026-08-06-bootstrap-capability-probe`).

The archive dependency is the sharpest case. `enforce-adr-reference-integrity` cited **ADR-0040**, a
record it did not itself ship. The scoped forward-reference policy permits that in a **live** change
directory — but an archived change is a **record**, so the citation must resolve the moment it
archives. That change was therefore structurally unable to archive from the moment it was written, and
nothing said so until it was discovered by hand, after the merge, with the debt already incurred.

## What Changes

- **ADDED requirement** (`maintenance`): *The Route Is Pre-Flighted Before A Mutation* — the driver
  SHALL answer, locally and before any outward mutation, the route steps that are decidable from
  repository state; SHALL judge them with the shipped oracle rather than a restatement; and SHALL
  report a check that could not run distinctly from a check that failed. 5 scenarios.
- **ADDED** `openspec/adr/0041-*` — the decision, and the discharge of **ADR-0040's follow-on**.
- **ADDED** `tools/preflight.py` — prototyped and measured (see *Evidence*).
- **MODIFIED** `tools/pr-flow.py` — `--preflight`, and the archive step consults it.
- **MODIFIED** `CONTRIBUTING.md`, `README.md` (ADR count lockstep).

## What it models, and what it deliberately does not

| Step | Modelled | Oracle |
|---|---|---|
| 7 `body` | declared scope vs the real merge-base diff | `extract-declared-scope.py` + `check-scope-findings.py` |
| 8 `checks` | every stdlib CI check | extracted from `ci.yml` |
| 9 `mergeable` | conflict prediction | `git merge-tree` trial merge |
| 11 `archive` | can this change archive on its own branch? | simulate the archive, run the archive-sensitive checks |
| — | concurrency: two live changes on one capability spec | the change directories themselves |

**Not modelled, and not guessed at:** `pr`, `children`, `merge` — genuinely remote objects — and
anything decided by a ruleset the session cannot read. A pre-flight that pretends to know these would
be worse than none.

**Design constraint:** the pre-flight **extracts the shipped check and runs it**; it never
reimplements one. A second copy of a rule drifts from the first, which is the defect this repository
has now found in itself four times (`range(1, 9)`, `constitution-lint` §4, `md-lint`'s `|| true`, the
saved plan's floating verification). The pre-flight's answer must move when the check moves.

## The exception that was "not expressible" is expressible

**ADR-0040 deferred mechanical enforcement of the archive rule** because the concurrency exception
could not be decided from repository state: the naive guard — *a merged pull request must not leave a
live change directory on `main`* — would have failed PR #58's legitimate deferral.

Simulation resolves it without a declaration to trust: **a change that cannot archive is precisely a
change that must defer**, and that is now decidable. This change discharges that follow-on and records
the discharge in its ADR, rather than leaving ADR-0040 carrying an open item it no longer needs.

## Evidence (prototype, measured before proposing)

Run against `507fe2f` — the exact commit where the tangle formed:

```
PRE-FLIGHT @ 507fe2f  —  1 live change(s)
DEPENDENCY (simulated archive, judged by the repo's own checks)
  MUST DEFER  enforce-adr-reference-integrity
              Check every cited ADR resolves: …/proposal.md:22: cites ADR-0040 but no such record exists
```

With a second live change added against the same capability spec:

```
CONCURRENCY
  ORDERED  'maintenance' spec is touched by 2 live changes: enforce-adr-reference-integrity, some-other-change
           archive in merge order; the later one rebases before archiving
  MUST DEFER  enforce-adr-reference-integrity   …cites ADR-0040…
  CAN ARCHIVE some-other-change
```

Full route pre-flight on a real branch: 11 stdlib checks run, trial merge clean, scope PASS (2 files),
archive clear.

**A defect found in the prototype itself, and fixed before proposing:** the first cut reported `FAIL`
for a CI step that writes to `/tmp` — read-only in a write-scoped sandbox. That is a check which
*could not run*, not one that *failed*. Conflating them is the same non-result-as-a-result disease, and
a pre-flight that cries wolf gets switched off. `SKIP` and `FAIL` are now distinct, and the requirement
below mandates that distinction rather than leaving it to implementation taste.

## Nature of the change — ordinary, not a constitution-override

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the test applies.
- **ADD-only.** No existing requirement modified, weakened, or narrowed. ADR-0040's *follow-on* is
  discharged — a follow-on is a recorded intention, not a requirement, so nothing is overridden.
- `constitution.md` §2 places conventions at Tier 2 — *"Ordinary OpenSpec change — no ceremony
  required."*

⚠ `constitution-lint` performs no diff analysis, so CI passing is not evidence of this classification.

## Archiving

Archived on this branch per ADR-0040, once the tasks are complete. The exception does not currently
apply — no other live change carries a `maintenance` delta. **This change cites ADR-0041, which it
ships itself**, so it can discharge its own forward reference; the pre-flight is expected to report
`MUST DEFER` until that ADR is written, which is the mechanism working on its own author.

## Blast radius (swept 2026-08-13, re-runnable)

```
grep -rn "preflight\|pre-flight" openspec/ tools/ CONTRIBUTING.md README.md AGENTS.md
grep -n "Follow-on" openspec/adr/0040-archive-on-the-feature-branch.md
grep -nE "[0-9]+\s+(ADRs?|Architecture Decision Record)" README.md
```

| Reference | Action |
|---|---|
| `openspec/adr/0040-…` follow-on | **DISCHARGED** by ADR-0041; 0040 itself is immutable and not edited |
| `tools/pr-flow.py` | **UPDATE** — `--preflight`; archive step consults it |
| `CONTRIBUTING.md` | **UPDATE** — pre-flight before the push |
| `README.md` | **UPDATE** — ADR count lockstep |
| `.github/workflows/ci.yml` | **no change** — the pre-flight reads it; CI is unchanged |

## Impact

No `vault-template/` change. No existing requirement modified. CI behaviour unchanged — this moves
the *timing* of an answer the repository already gives, from after a push to before one.
