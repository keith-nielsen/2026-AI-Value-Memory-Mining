<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0037 — Give INV-6 a runner: static AST analysis plus a network-namespace behavioural check

**Status:** **Proposed** (Gate-4 pending — human-only sign-off, constitution §5)
**Date:** 2026-07-28
**Relates:** `maintenance` (INV-6) · change `enforce-inv6-offline-check` · **sibling of ADR-0036**
(the other half of the same audit; INV-6 was the last Tier-0 invariant left unenforced) ·
ADR-0030 (the add-the-enforcement-Requirement-beside-the-rule pattern) · live-vault Site
`github-canary-barium-lunch-investigation` (RC-D control validity, RC-E over-denial)

## Context

The 2026-07-28 Tier-0 enforcement audit asked one question of each invariant: *what fires without
agent cooperation?* After ADR-0036 shipped, four of nine had an answer — INV-4 and INV-5 at the
kernel, INV-11 and INV-7 at the commit gate. **INV-6 was the last with none.** Measured, not
assumed: a grep across `tests/` and all fifteen CI jobs for
`socket|network|offline|urllib|requests|unshare` returned one hit, and it was **prose in a module
docstring**.

**INV-6's defect has the opposite shape to INV-7's, and the contrast is the useful part.** INV-7's
Requirement carried a *wrong* scenario — it inspected two config files, Factor A standing in for
Factor B. INV-6's scenario was **already correct and behavioural**: *"WHEN any `[script]` operation
runs · THEN it issues no network request and invokes no model."* Nothing ran it.

So the operation now has both failure modes on record: a well-formed rule verified by the wrong
observation, and a well-formed rule verified by **no observation at all**. The second is the harder
one to notice, because reading the spec is reassuring — the scenario looks like a test, and the only
way to discover it never executes is to go looking for its runner.

**The design constraint that determined the mechanism.** A text-matching checker flags exactly the
two scripts it must not. `outbound-publish-guard` and `push-guard` implement the INV-14 rail and
their entire purpose is to *name* outward verbs inside regex literals. Measured on the shipped
files: naive grep hits **6** and **2**; AST/command-position violations **0** and **0**. A control
that fails the two most security-relevant scripts in the fleet on every run does not get obeyed, it
gets disabled — RC-E, *over-denial is camouflage*. This is the same self-reference trap that bit the
INV-7 scanner on the day it shipped, when its own private-key fixture matched its own pattern table;
that instance cost an hour and a branch rebuild, and this one was designed around from the start.

## Options

- **(a) Leave it as prose.** Rejected. The operation's own record is unambiguous: prose rules do not
  fire. F16, F20 (twice after its corrective was written), F27 (a verbatim recurrence of F25 whose
  corrective was already binned ENFORCE), and RC-D, whose paragraph stating the control-validity rule
  was violated by the next measurement in the same document.
- **(b) Static text/grep scan only.** Rejected on the measurement above: it flags the INV-14 guards
  8 times between them for doing their job. It also cannot distinguish `git diff` from `git push`
  without subcommand awareness.
- **(c) Static AST analysis only.** Insufficient alone. Complete over text, blind to semantics:
  `__import__` with a computed name, `eval`, or a C extension is undecidable. Shipping it alone would
  invite exactly the overclaim this ADR exists to prevent.
- **(d) Dynamic namespace run only.** Insufficient alone. Complete over semantics, bounded by test
  coverage — and coverage is thinnest precisely where the network verbs live, because the two INV-14
  guards have no tests at all.
- **(e) Both halves, each with its incompleteness stated in the spec (chosen).** The two are
  complementary in exactly the dimension the other is blind to.
- **(f) Sandbox/seccomp syscall filtering of the fleet at runtime.** Deferred. Stronger than (d), but
  it is machinery to build and maintain for a fleet that (e) already shows to be clean, and the
  operation's standing posture is to keep the trusted surface small.

## Decision

Adopt (e).

- **`tools/inv6-offline-check.py`** — repo-only, stdlib-only, offline. Python by AST; bash by a
  conservative command-position scan, explicitly the weaker half. Indirection (computed dynamic
  import, non-literal argv) is reported **UNRESOLVED** and fails the check rather than passing
  silently.
- **`.github/scripts/inv6-offline-dynamic.sh`** — runs the fleet suite inside an unprivileged network
  namespace, having first proven the network is reachable **outside** and unreachable **inside** in
  the same run. If isolation cannot be established it **fails closed**.
- Both checkers **selftest before they run**, and the static one refuses to report clean if its own
  selftest fails. Third use of the exit-3 control-gate pattern in this operation.
- The spec gains an **ADDED** Requirement; the existing INV-6 Requirement is left intact (ADR-0030
  pattern).
- **Repo-side only.** No fleet member is added, so there is no `render`, no mirror, and no operator
  deploy step. The fleet is authored upstream and deployed down; a deployed vault cannot author a
  script, and `reconcile` plus `template-parity` already prove the deployed copies are byte-identical
  to the checked ones.
- **No new invariant.** INV-6's text and tier are untouched; ADR-0008's frozen IDs are unaffected.

## Consequences

- INV-6 moves from *stated* to *checked*. **All nine live Tier-0 invariants now have a mechanism** —
  the condition RC-B identified as absent for INV-14 for a year no longer holds anywhere in the set.
- CI gains two jobs and roughly a minute.
- A future fleet script that genuinely needs the network must become an `[agent]` operation. That is
  not a new constraint; it is what INV-6 has always said, now with something that notices.
- The **two INV-14 guards remain untested**, so the dynamic half does not cover them. Named here so
  it is queued rather than forgotten — the precise mistake that let INV-6 sit unenforced.

## Sacrifice (what is knowingly given up)

**Completeness, in both directions, permanently.** Static analysis cannot see through `__import__`,
`eval`, or a C extension; the dynamic half sees only what the tests exercise. **A green result means
"no statically visible network call, and none on the paths the suite exercises" — it does not mean
"the fleet is offline."** That bound is written into the spec text, the tool's `--help`, and its
closing output, so it travels with the result instead of being dropped at the first summary. Anyone
citing a pass as proof of offline behaviour has made the Factor-A substitution this ADR was written
to end.

**The bash half is knowingly weak.** Four fleet scripts are bash, and a command-position regex faces
the same unbounded-language problem that leaves the INV-14 guard with three known holes. It is
better than nothing and worse than the AST path, and the spec says so rather than implying parity
between the two.

**Runner-environment dependence.** The dynamic half needs an unprivileged network namespace. Where
that is unavailable the job fails rather than degrading quietly — chosen deliberately, because a
check that downgrades to "skipped" under adverse conditions is how a green badge stops meaning
anything.
