# Tasks — detect-git-hook-registration

> **Durable plan.** Origin: GitHub platform hardening queue item 35, defect D2. The INV-11/INV-7 hooks
> render into `99-Operations/hooks/` but git ignores them until `core.hooksPath` is set — LOCAL config
> no tracked file or render can set. Operator decisions (2026-09-22): **detect + document** (not
> auto-register), and the framework repo **relies on CI** (no local gate). D1 is already handled by
> render (the hooks are rendered artifacts); D3 is a deliberate no.

## 0. END STATE

`reconcile` reports a deployed-but-unregistered git-hook set as drift (exit 1), naming the fix, and
never sets `core.hooksPath` itself. A test proves it (unregistered → finding; registered → ok; only
`.gitkeep` → skipped). The maintenance spec records the detection and that registration is an operator
deploy step.

## 1. The detection (detect, never fix)

- [x] 1.1 `render-reconcile-script.md`: after the render/reconcile loop, when `99-Operations/hooks/`
      holds real hooks (beyond `.gitkeep`), read `core.hooksPath` via a local `git config` subprocess;
      if it does not resolve to the hooks dir, print `HOOKS-UNREGISTERED` with the operator fix and
      count it as drift. Runs in both modes; only `reconcile` fails on it. Never sets the config.
- [x] 1.2 Update the note's Rationale + `updated:` date; keep exactly one code fence; code parses.

## 2. Tests (red-first)

- [x] 2.1 Deployed hooks + unset `core.hooksPath` → `HOOKS-UNREGISTERED` + fix command + exit 1.
- [x] 2.2 Registered `core.hooksPath` → reports registered, exit 0.
- [x] 2.3 Hooks dir with only `.gitkeep` → not a finding.
- [x] 2.4 The existing render-root-resolution tests stay green (no hooks dir → check skipped).

## 3. Spec

- [x] 3.1 `maintenance` ADDED "Git Hook Registration Is Detected, Not Assumed" — the detection, the
      detect-don't-fix posture (INV-3), and that registration is an operator deploy step; the framework
      repo relies on CI.

## 4. Regression

- [x] 4.1 Full suite green.
- [ ] 4.2 `openspec validate --all --strict` — 0 failed.
- [ ] 4.3 markdownlint (CI's four `--ignore` paths) — 0 findings.
- [ ] 4.4 `tools/preflight.py . --body-file <path>` → CLEAR.

## 5. Gate 4 — maintenance touch + a control-script behaviour change

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md` (`protects: [INV-2, INV-3,
INV-6]`) and gives `reconcile` a new exit-1 drift condition.

- **What this touches** — a new DETECTION in `reconcile` (no auto-fix), plus its maintenance
  requirement. INV-3 is strengthened, INV-6 intact (local git read).
- **What breaks if wrong:** a false `HOOKS-UNREGISTERED` would fail a clean vault's `reconcile` (the
  registered-case and gitkeep-case tests guard against it); a missed detection leaves the silent
  gap (the unregistered-case test guards that).

- [x] 5.1 Tier-0 (maintenance touch + control-script change) surfaced; **Approved** — Keith Nielsen, 2026-09-22

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff.
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.
- [ ] 6.5 ⚠ **Deploy-down owed:** re-render the reconcile note into the live vault (operator-run,
      EROFS for the agent). The live vault already has `core.hooksPath` set, so `reconcile` will report
      the hooks as registered — verify that after the render.
