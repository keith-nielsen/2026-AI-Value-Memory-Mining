<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0043 — The driver's emission downgrades a prompt; it never creates a refusal

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-08-17)
**Date:** 2026-08-17
**Change:** `emission-record-downgrades-ask`
**Relates:** **ADR-0018** (private-by-default publish guard — the tripwire posture this relies on);
**ADR-0027** (effective-target refinement, which this generalises); **ADR-0041** (pre-flight);
vault failure class 10.

## Context

The vault's failure log adopted **class 10 — unauthorized deviation from a codified route** on
2026-08-17. It is the oldest pattern in that catalogue: carried unnumbered since 2026-07-01, invoked
eight times, tallied never, with ten attested instances.

Its stage-1 shape never varies: **the driver prints the exact command, and the agent retypes it
wrong.** On 2026-08-16 the driver emitted `git -C <literal> push -u origin <branch>` with the
instruction *"run exactly this"*. What ran was `R=…; cd "$R"; timeout 180 git -C "$R" push …`. The
guard resolves effective targets from raw text, could not resolve `"$R"`, ignored the redirect, fell
back to the reported working directory — the vault — and denied. **Correctly.** A day of wrong
conclusions followed, including a failure-log entry that blamed the instruments and a queue item
scoped against a driver that was right.

Prose has been tried and has failed on the record: F19 wrote the rule, F32 restated it as *"the part
that must not regress"* and observed that *"the shortest, loudest feedback loop the system can produce
did not change the next command"*, and F37 banked the driver case ten days before it recurred.

`write_saved_plan()` already solves this — for the **operator**. Its docstring cites F14 and F26, the
operator-side instances of the same class. It was gated to `runs == OPERATOR` on the assumption that
an agent transfers commands losslessly.

## Decision

**Record every emitted command, and let the outbound guard use that record to DOWNGRADE its
confirmation prompt to an allowance — never to create a refusal.**

Zones, by effective target:

| Zone | Command | Result |
|---|---|---|
| deployed vault | outward | HARD DENY (unchanged) |
| governed repository | byte-identical to a live record | **allow, no prompt** |
| governed repository | anything else | confirm, **and show the difference** |
| elsewhere | outward / publish | confirm (unchanged) |

> **The invariant: the record may only ever downgrade a confirmation to an allowance. It may never
> create a refusal.**

Absent, expired, wrong-branch, unparseable, or a fault in the comparison — all fall through to the
prompt raised today. The change therefore **cannot make the guard stricter than it already is**, which
is what permits it to ship without a burn-in period, unlike ADR-0039's gate.

A repository is **governed** exactly when a driver has emitted for it: the record names its own
subject. That was chosen over reading `$FRAMEWORK_ROOT` because the guard is a hook with no guarantee
that the operator's shell environment reaches it — a control that silently disables itself when an
environment variable is unset is the kind of unstated dependency this repository has had to retract
before.

## Options considered

| Option | Why not |
|---|---|
| **Deny when no record exists** | The first draft. It converts a working confirmation into a refusal and manufactures over-denial (RC-E) — the pattern that trains readers to route around guards. Tier 2 already handles the ad-hoc case correctly |
| **Have the driver execute its own command** | Removes the retyping, but the mutation then happens inside a Python subprocess where the text matcher cannot see it. Every "remove the retyping" variant launders the verb off the channel the guard watches |
| **Write a plan file for agent steps too** (`bash next.sh`) | Same defect: the verb moves inside a script, and `bash …/next.sh` carries nothing for the matcher to see |
| **Read `$FRAMEWORK_ROOT`** | Silently inert if the variable does not reach the hook's environment |

## Consequence

- The prescribed route becomes the **frictionless** path and deviation becomes the one that stops with
  a diff. Today they cost the same — one prompt each — so nothing but memory favours the correct one.
- **Operator interrupts fall**: driver-emitted pushes stop prompting; only off-script commands do.
- Every remaining prompt on a governed repository is a **signal** — either the agent deviated, or the
  driver's lifecycle has a gap. Neither is countable today.
- A **second, independent** diagnostic was added after a test exposed it: a denial caused by a redirect
  the guard could not resolve now says so, printing what was written and what it resolved to. That is
  what the 2026-08-16 reader needed and did not get, and it works with no record at all.

## Sacrifice

**The record is forgeable by the agent it governs.** It lives in the agent's own write scope, so an
agent that wrote its own record could authorise its own command.

This is accepted deliberately, and is consistent with ADR-0018's stated posture: *safe-by-default and
a governed guarantee, not a physical impossibility* — a tripwire for a cooperating agent. **The threat
model is agent error, and class 10 is an error class.** A mangled retype does not also produce a
matching record; that is the entire basis on which this works.

It is written into the `maintenance` spec as a **requirement**, not a footnote, because an unstated
limitation on a control is indistinguishable from a control that does not have it — the exact defect
retracted from `constitution.md` §4 in PR #85. **An allowance means "matched a record". It never means
"authorised" or "verified", and no report may say otherwise.**

**And the honest bound: this addresses stage 1 of class 10 only.** Stages 2 and 3 — misreading a
failure as evidence about the system, and instituting a workaround unilaterally — are untouched. The
operator's standing concern that the recidivism is unsolvable is recorded with the class and is **not**
claimed to be answered here.
