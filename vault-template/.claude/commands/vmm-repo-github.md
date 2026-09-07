---
description: Repo-work prime — load the framework-repo contribution context BEFORE planning any repo, pull request, OpenSpec, CI, workflow, Dependabot, branch, merge, release, or ship work. Invoke at the moment repo work is proposed, not when it is executed.
---

## The one instruction that survives everything below

**Ask the driver for the route. Never describe it from memory, never hand-compose the sequence.**

```
python3 "$FRAMEWORK_ROOT/tools/pr-flow.py" --plan --branch <BR> --base main
```

It prints all 14 steps with each step's executor, its authority, and whether the guard was MEASURED
or only PROJECTED. `CONTRIBUTING.md` §*Landing a change* states the rule this enforces:
***"Walk it; do not hand-compose the sequence."***

Departing from a codified route without approval is **failure class 10** — recorded in the failure
ledger as invoked eight times and tallied never, with no instrument that detects it. On 2026-09-06 it
cost three rounds against a repository whose contributor guide opens with the sentence above.

The operator's *entire* side of the lifecycle is one invariant command —
`bash "$FRAMEWORK_ROOT/.git/pr-flow/next.sh"` — written by the driver only when the pending step is
theirs. **Never hand-compose a `gh` mutation.** Once an operator step is emitted, stop touching the
driver until they report it done: `next.sh` is a single mutable slot, and re-running the driver
overwrites a step they have not yet run.

## Then load the full card

Read, in full, before planning:

```
$VAULT_ROOT/30-Sites/repo-work-bootstrap-enforcement/vmm-repo-github-card.md
```

⚠ **If that file is absent, unreadable, or does not carry a `CARD-VERSION:` marker, say so plainly
and STOP.** Do not proceed on recollection and do not substitute your own account of the ceremony —
a missing card that degrades into improvisation is exactly the silent-success failure this prime
exists to prevent. Report the absence and ask.

## Provisional pointer — read before "improving" this file

**The indirection is deliberate and temporary.** The card lives under `30-Sites/` because that area
is agent-writable, so its content can be iterated without a governed change while it is still
settling. **This stub is the stable half** and should change rarely; the card is the volatile half.

**Hardening condition:** when the card stops changing, one governed change promotes its content into
a protected, LOCKSTEP-declared location and replaces this pointer with the content itself. At that
point a drift test against `AGENTS.md` / `CONTRIBUTING.md` becomes mandatory — restating another
system's rule instead of importing it is **failure class 9**.

⚠ **While provisional, the Site `repo-work-bootstrap-enforcement` must not be closed, slagged or
spoiled** — doing so deletes the card this stub depends on. That is a live coupling between the vault
pipeline and a deployed control.

⚠ **In a vault other than the one this was authored in, the card path will not exist.** That is known
and accepted: the stub fails **loudly** per the rule above rather than degrading silently, and the
card is promoted into a protected location once refined.
