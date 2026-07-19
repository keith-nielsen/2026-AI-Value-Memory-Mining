<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — fix-operator-only-path-diagnostics

## 1. Spec
- [x] 1.1 `specs/maintenance/spec.md` — ADD "Operator-Only Paths Fail Legibly" (3 scenarios,
      including the non-EROFS re-raise so this cannot become a blanket error swallow)
- [x] 1.2 `openspec validate --all --strict` green — **8 passed, 0 failed**, 2026-07-20

## 2. Fleet
- [x] 2.1 `render-reconcile-script.md` — `import errno`; wrap the `render` write; EROFS → 4-line
      operator-only message + `SystemExit(4)`; any other `OSError` re-raises
- [x] 2.2 `naming-rules-script.md` — `import errno`; same treatment for the emit-mode write
- [x] 2.3 Verify each note still carries **exactly one** code fence (B5) — confirmed, 1 each
- [x] 2.4 Verify both code blocks parse — confirmed, `ast.parse` clean
- [ ] 2.5 Confirm `reconcile` and `--check`/`--check-strict` paths are untouched by inspection of the
      final diff (they exit above the amended blocks)

## 3. Tests — **+4 cases** (planned as 2; the split below proved necessary)
- [x] 3.1 `test_render_operator_only_path_explains_itself` — exit 4, message, **no traceback**
- [x] 3.2 `test_naming_emit_operator_only_path_explains_itself` — same for emit mode
- [x] 3.3 `test_naming_check_modes_unaffected_by_the_erofs_branch` — `--check-strict` still passes a
      good name and rejects a 2-token one **while the schema path is unwritable**; the commit gate is
      the property most likely to be broken by a careless edit here
- [x] 3.4 `test_non_erofs_oserror_is_not_swallowed` — **real `chmod 0444` → `EACCES`**, asserts the
      exception propagates and is *not* relabelled as operator-only
- [x] 3.5 Full suite green — **56 passed**, 2026-07-20

**Method note (planned vs. actual).** Task 3.1 originally said "render into a read-only directory rather
than monkeypatching, so the test exercises the real syscall path." **That plan was wrong and was
corrected during execution:** `chmod` produces `EACCES` (13), not `EROFS` (30) — a different errno that
this feature must deliberately *not* catch. A chmod-based EROFS test would therefore have exercised the
re-raise branch while appearing to test the operator-only branch, and passed for the wrong reason. Real
`EROFS` requires a read-only *mount*, unprivileged-unavailable in CI. Resolution: the denied errno is
injected via a `sitecustomize` shim in the child process (3.1–3.3) — everything else stays real, the
actual deployed script in a real subprocess running its own except-branch — and the errno that *can* be
produced for real is used to test the branch that must *not* fire (3.4). Recorded rather than silently
re-specified.

## 4. Ceremony
- [ ] 4.1 `CHANGELOG.md` `[Unreleased]` entry
- [ ] 4.2 PR with a ```scope block
- [ ] 4.3 CI green = Gate 3
- [ ] 4.4 Gate-4 re-check + operator `Approved`
- [ ] 4.5 Archive

## 5. Deployment (ORDERING HAZARD — read before shipping)
- [ ] 5.1 Mirror both amended notes into the live vault
- [ ] 5.2 **The OPERATOR runs `vault-render.py render`.** The agent cannot — its every `deploy_target`
      is denied, which is the exact condition this change exists to explain. **The fix ships inside the
      script that deploys it, so it cannot self-deploy.** Until the operator renders, the live vault
      keeps the old traceback behaviour (annoying, not dangerous)
- [ ] 5.3 `tools/template-parity.py <VAULT_ROOT>` → 0 drift
- [ ] 5.4 Verify live: run `vault-render.py render` as the **agent** and confirm the new message +
      exit 4 (this is the only end-to-end proof the change works where it matters)
- [ ] 5.5 Update P17 in the live Site — layer 3 built; the three-layer table's "not yet built" row closes
