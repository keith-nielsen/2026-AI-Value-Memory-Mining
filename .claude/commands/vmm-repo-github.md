---
description: Repo-work prime — load this repository's contribution route BEFORE planning any pull request, OpenSpec change, CI, workflow, Dependabot, branch, merge, release, or ship work. Invoke when the work is proposed, not when it is executed.
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

## The one instruction

**Ask the driver for the route. Never describe it from memory, never hand-compose the sequence.**

```
python3 tools/pr-flow.py --plan --branch <BR> --base main
```

It prints the whole route, each step with its executor, its authority, and whether its guard was
MEASURED or only PROJECTED. With no branch in flight, say so and run nothing.

## Then read the sources of record — this prime restates none of them

- `AGENTS.md` — the constitutional hard stop, the invariants, and the operating notes (footguns).
- `CONTRIBUTING.md` — §*Landing a change*, §*Before the first mutation*, §*Before the first push*,
  §*Shipping a version*.
- `docs/version-control-legal-moves.md` — the barred forms first, then the legal move set.

## Scope

This prime serves sessions rooted in **this repository**. It depends on no deployed vault, by design:
the framework repo's GitHub work is to stand alone from any vault (operator, 2026-09-26). A vault
session that finds itself doing repo work should hand the work to a session rooted here.
