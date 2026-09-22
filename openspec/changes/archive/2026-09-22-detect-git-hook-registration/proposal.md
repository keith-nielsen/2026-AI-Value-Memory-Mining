<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: detect-git-hook-registration

## Why

The INV-11/INV-7 git hooks render into `99-Operations/hooks/`, but git enforces them only when
`core.hooksPath` points at that directory — and `core.hooksPath` is LOCAL git config that no tracked
file, no `render` run, and no `template-parity` comparison can set or observe. So a freshly
deployed+rendered vault has byte-perfect hooks that git silently ignores (`.git/hooks` samples win),
enforcing nothing while reporting clean. The live vault only works because someone set `core.hooksPath`
by hand on 2026-08-26; a fresh deployment does not. This is the silent-success class (kin to item 32)
and hardening-queue item 35's core defect (D2).

The queue's D1 ("the template ships no hooks") is already handled: the hooks are RENDERED artifacts,
so `render` deploys them on deploy — the empty template `hooks/` dir (just `.gitkeep`) is correct, and
shipping static hook copies would fork the rendered artifact (the class-9 defect). The queue's D3 (the
framework repo running the gate locally) is a deliberate NO — CI is the repo's backstop. So this change
addresses D2 only, and does it by DETECTION, not auto-fix.

## What Changes

- **`reconcile` detects deployed-but-unregistered hooks** (`render-reconcile-script.md`): when
  `99-Operations/hooks/` holds real hooks but `core.hooksPath` does not resolve to it, it prints a
  finding — the deployed dir, the current `core.hooksPath`, and the operator fix — and counts it as
  drift (exit 1). It **never sets** `core.hooksPath` (INV-3: detect, never auto-fix). It runs in both
  modes so a fresh `render` warns immediately; only `reconcile` counts it as drift.
- **The fix is self-documenting at the point of need** — reconcile prints
  `git config core.hooksPath 99-Operations/hooks`, so an operator who runs `render`/`reconcile` on
  deploy is told exactly what to do. The spec records that registration is an operator deploy step.

## Impact

- A deployed vault can no longer silently run an unenforced commit gate: the gap is loud on the next
  `render`/`reconcile`, not discovered after a bad commit slips through.
- `reconcile` reads `core.hooksPath` via a local `git config` subprocess (no network — INV-6 intact;
  sibling fleet scripts already shell out to git).
- **Deploy-down owed:** the reconcile note must be re-rendered into the live vault (operator-run). The
  live vault already has `core.hooksPath` set, so it will report the hooks as registered.

## Constitutional impact

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md` (`protects: [INV-2, INV-3,
INV-6]`). It strengthens INV-3's detect-don't-fix posture (a new detection, no auto-fix) and keeps
INV-6 (the git read is local). Additive; `overrides: none`.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only (a new drift detection; INV-3 detect-don't-fix preserved, INV-6 local read)
```

## Verification

- Red-first: `test_reconcile_flags_unregistered_git_hooks` fails against the pre-change reconcile,
  which never looked at `core.hooksPath`.
- Deployed hooks + unset `core.hooksPath` → `HOOKS-UNREGISTERED` finding + the fix command + exit 1.
- Registered `core.hooksPath` → reports the hooks as registered, exit 0.
- A hooks dir with only `.gitkeep` (the template shape) is not a finding.
- The existing render-root-resolution tests stay green (their temp vault has no hooks dir, so the
  check is skipped).
- Full suite, `openspec validate --all --strict`, and markdownlint all clean.
