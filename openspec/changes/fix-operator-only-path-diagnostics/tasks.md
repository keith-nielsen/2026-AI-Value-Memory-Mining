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

## 3. Tests
- [ ] 3.1 `tests/test_fleet.py` — EROFS on a `deploy_target` yields exit 4 and a message containing
      "OPERATOR-ONLY"; simulate by rendering into a read-only directory rather than by monkeypatching,
      so the test exercises the real syscall path
- [ ] 3.2 `tests/test_fleet.py` — a non-EROFS `OSError` still propagates (guards against the swallow)
- [ ] 3.3 Full fleet suite green

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
