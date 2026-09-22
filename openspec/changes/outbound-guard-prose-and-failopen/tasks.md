# Tasks — outbound-guard-prose-and-failopen

> **Durable plan.** Origin: GitHub platform hardening queue item 33 (full-estate review, four defects).
> The guard is a BELT over the env-free, fail-closed pre-push hook + remotelessness. These fixes narrow
> false denials and close the fail-open, with the true-positive set intact. Operator decision
> (2026-09-22): bundle all four (D1+D2+D3+light-D4) under one Gate 4, D4 fenced off and separately
> surfaced. D1 strips only `-m`/`-F` values, never heredocs.

## 0. END STATE

`outbound-publish-guard-script.md`: matches on message-stripped `scan` (D1); resolves the mandated
`source; cd` idiom (D2); explains a no-redirect deny (D3); and identifies the vault by its marker when
the env is unset (D4, only the fail-open line). The repo hook re-rendered byte-identical (F29). The
access-control spec records it.

## 1. Implementation (the note)

- [x] 1.1 D1: `_PROSE_ARG` + `_strip_arg_prose` (blank `-m`/`--message`/`-F`/`--file` VALUES); compute
      `scan` in `main()` and match/resolve on it; keep `cmd` for the emission exact-match and displays.
      Heredocs NOT stripped.
- [x] 1.2 D2: `_LEAD_CD` tolerates an optional leading `source <file>;` / `. <file>;` prefix.
- [x] 1.3 D3: `_unresolved_redirect_hint(cmd, cwd)` names the no-redirect cwd-fallback case.
- [x] 1.4 D4: `_has_vault_marker`; `_targets_vault` env-unset branch returns it instead of `False`
      (env-set path unchanged). Update the module docstring + Rationale; bump `updated:`.

## 2. Tests (red-first, each with a true-positive)

- [x] 2.1 D1: message naming a publish → defer; real publish/push with a message → still deny.
- [x] 2.2 D2: `source; cd <sibling>` → not denied; `source; cd <vault>` → denied.
- [x] 2.3 D3: no-redirect vault-outward deny names the fallback.
- [x] 2.4 D4: env-unset + marker → deny; env-unset + no marker → ask; env-set → unchanged.
- [x] 2.5 Update the existing mutation test's anchor to the renamed call arg (`is_reversible_outbound(scan)`).

## 3. Spec

- [x] 3.1 `access-control` ADDED "The Outbound Guard Judges Commands, Not Prose, And Never Fails Open".

## 4. Render + regression

- [x] 4.1 Re-render the repo hook byte-identical to the note (F29 parity test green).
- [x] 4.2 Full suite green.
- [ ] 4.3 `openspec validate --all --strict` — 0 failed.
- [ ] 4.4 markdownlint — 0 findings.
- [ ] 4.5 `tools/preflight.py . --body-file <path>` → CLEAR (incl. the INV-6 offline checks over the
      guard note — no new network/subprocess; the note stays stdlib-only, no process invocation).

## 5. Gate 4 — Tier-0 INV-14 control change

The delta ADDs a requirement to `openspec/specs/access-control/spec.md` (INV-14). It changes WHEN the
guard denies/asks (narrows false-denies, closes a fail-open) but not the true-positive set.

**Surfaced as two directions under one sign-off (fenced, not conflated):**

- **The RELAX (D1/D2/D3)** — the guard fires *less*: it no longer denies on prose in a message, resolves
  the mandated `source; cd` idiom to its real target, and explains a no-redirect deny. Risk: an
  under-fire. Bounded — D1 strips only non-executed `-m`/`-F` values (never heredocs); D2 adds only the
  known-good `source` prefix and still trusts the first `cd`; every relax test is paired with a
  true-positive that still denies; the mutation test is retained.
- **The TIGHTEN (D4)** — the guard fires *more*: env-unset no longer fails open (marker-based). The
  env-set path is byte-unchanged, so it only adds protection.
- **Backstop context:** the belt sits over the env-free, fail-closed `pre-push` hook and vault
  remotelessness; item 35 now detects an unregistered pre-push hook. So even D4's residual is covered.

- [x] 5.1 Tier-0 (INV-14 control change) surfaced; **Approved** — Keith Nielsen, 2026-09-22

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff.
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.
- [ ] 6.5 ⚠ **Deploy-down owed:** re-render the guard note into the live vault (operator-run), bundled
      with item 35's reconcile re-render — one `template-mirror` + `render`. Verify: the live guard is
      byte-identical, and `reconcile` reports the hooks registered.
