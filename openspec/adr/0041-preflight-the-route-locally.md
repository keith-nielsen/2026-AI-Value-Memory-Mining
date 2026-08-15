<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0041 — Pre-flight the route locally: move the checks we already have from continuous integration to the keyboard

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-08-16)
**Date:** 2026-08-16
**Change:** `preflight-route-before-mutation`
**Relates:** **ADR-0040** (archive on the feature branch — this **discharges its deferred follow-on**,
that the concurrency exception is decidable from repository state); **ADR-0034** (server-side rulesets);
**ADR-0023** (env-free fleet).

## Context

The operation's response to every defect has been to add a control that catches it. Those controls
work — three refused correctly on 2026-08-15 alone (the Gate-4 approval gate on a misplaced sign-off,
`Spec lint` on a citation that only became dangling *because* the change was archived, and the
readiness probe, which was right while a wrapper around it lied). But they are all **detective**: they
fire after the work is done, and each one adds surface to the thing it protects.

The operator named the problem directly: *"my strong preference and ultimate goal would be to reduce
the occurrence count of up-front errors … rather than create a large/complex set of rails to capture
blunders that should be avoided in the first instance."*

**The diagnosis that motivates this ADR is that almost none of the recent errors were missing rules.
They were failures to apply rules that already existed.** The Gate-4 section convention was written
down; the citation rule was written down and mechanically enforced — in continuous integration, after
a push, a pull request and a red check. The same checker ran locally in about two seconds once
extracted from `ci.yml` by hand.

So the lever is not another rule. It is **latency**: the distance between making a mistake and being
told about it. A rule enforced only after a push costs a push, a pull request, a red check-run, a
context switch and a fix commit. The same rule enforced at the keyboard costs nothing.

## The measurement

`.github/workflows/ci.yml` declares **15 jobs** across **40 named steps**. Before this change:

| | |
|---|---|
| Reproducible locally by one command | **0** |
| Commands an author had to remember and run separately | 4 (`openspec validate`, `pytest`, `validate-scripts.sh`, `inv6-offline-check.py`) |
| Jobs whose failure was discoverable only after a push | the rest |

Remembering four commands is a weak control, and it failed in the ordinary way: they were run
faithfully all session and the one check that was *not* in the habit — citation integrity — is the one
that turned a pull request red.

**Dogfood result, measured before this ADR existed:** running the pre-flight against its own branch
reported `MUST DEFER preflight-route-before-mutation` because *"Check every cited ADR resolves"* fails
against the **simulated** archive — this change cites ADR-0041, which did not yet exist. That is
exactly the failure that hit PR #79, caught before any push.

## Options

1. **More detective controls.** Rejected: it is what the operator asked us to stop doing, and it
   treats a latency problem as a coverage problem.
2. **A checklist in `CONTRIBUTING.md`.** Rejected: this repository's own record is that only artifacts
   which can *refuse* bind. Prose that must be remembered is the control that already failed.
3. **A `Makefile` wrapping the four commands.** Closer, but it wraps only what is already remembered,
   and it cannot model the route steps (scope against the real diff, trial merge, simulated archive)
   that have no local equivalent at all.
4. **A pre-flight tool that runs the *shipped* checks and models the route.** Adopted.

## Decision

**A single local command reproduces everything continuous integration can tell us, plus the route
steps it cannot, and it is run before a push.**

Three properties are load-bearing:

- **It runs the shipped check, never a restatement of it.** Steps are extracted from `ci.yml` and
  executed; the local answer therefore cannot drift from the remote one. A pre-flight that
  reimplemented the logic would rot silently, and a stale pre-flight is worse than none because it is
  believed.
- **A check that could not run is `SKIP`, never `PASS`.** An environment limitation is named as one and
  excluded from the findings. This is the defect class the repository keeps finding in itself —
  `md-lint`'s `|| true`, the two hardcoded `/tmp` paths, and a poll loop that reported `READY` over 22
  pending checks because `cmd || true` had swallowed the exit code.
- **Coverage is reported and must partition.** Every job declared in `ci.yml` is accounted for as
  reproduced, unrunnable-with-reason, or deliberately-not-reproduced-with-reason. A job matching none
  of those is printed as an **unaccounted silent gap** and fails the run. Without this, adding a job to
  `ci.yml` tomorrow would quietly shrink the fraction the tool covers while it kept printing `CLEAR` —
  the exact way a green check comes to mean nothing.

**Discharging ADR-0040's follow-on.** That ADR left open whether the concurrency exception could be
decided mechanically. It can: a change that cannot archive cleanly *is* a change that must defer, and
the simulation answers it by copying the live change to an archive path and running the
archive-sensitive checks against it.

**This is not a gate.** The pre-flight reports; it does not block the push step. Making it blocking
before its false-positive rate is measured would repeat the over-denial failure (RC-E, queue item 22),
and a control that blocks correct work trains its reader to bypass it.

## Consequences

- The four remembered commands become one, and it prints what it did **not** check.
- **12 of 15 jobs reproduced locally.** The three that are not are named with reasons: `md-lint`
  (tool not installed, and the job is advisory anyway), `secret-scan` (hardcoded `/tmp`), and
  `scope-review` (reproduced by the route section against the real merge-base diff).
- Two of the three unreproduced jobs are unreproduced **because of known defects in those jobs**, so
  the coverage report doubles as a standing reminder of queue item 10.
- A clean pre-flight is explicitly **not** a promise the remote will be green, and the tool says so.

## Sacrifice

**Runtime.** The pre-flight runs the full test suite and every extractable check, so it costs tens of
seconds rather than being instant. That is the trade: seconds at the keyboard against a push, a pull
request, a red check-run and a fix commit.

**Coupling to `ci.yml`'s shape.** Step extraction depends on the stdlib-heredoc form. A job written
another way is invisible to extraction — which is precisely why the coverage report exists and why an
unaccounted job fails the run rather than being silently omitted.

## Follow-on

- Measure the false-positive rate before considering making it blocking (task 4.3).
- `secret-scan` and `validate-scripts.sh` both hardcode bare `/tmp` (queue item 10). Fixing those moves
  coverage from 12/15 to 13/15 and removes a SKIP that is a defect rather than a limitation.
- If a merge queue is adopted, `mergeable` becomes a server-side question and that section should be
  retired rather than maintained.
