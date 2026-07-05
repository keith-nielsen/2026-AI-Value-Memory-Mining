<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta
- [x] 1.1 `maintenance` — `runtime:` enum + `git hook`; Daily Close Lifecycle + close-lint
      typo scenario

## 2. Implementation
- [x] 2.1 `commit-gate-script.md` — `runtime: git hook` (rendered hook byte-identical)
- [x] 2.2 `daily-close-script.md` — `--check` validates manifest-row dispositions against
      `DISPOSITIONS`; hardcoded-tuple guard removed
- [x] 2.3 `vault-template/96-Runbooks/session-bootstrap-loader.md` — clean-ops bullet env-free
      wording; `last-validated: 2026-07-06`

## 3. Docs
- [x] 3.1 `CHANGELOG.md` `[Unreleased]`

## 4. Regression
- [x] 4.1 validate --strict (change + all)
- [x] 4.2 validate-scripts.sh OK
- [x] 4.3 Battery: clean close-lint rc 0; typo'd manifest FAIL rc 1; pre-commit render
      byte-identical; runbook-lint fields/sections intact

## 5. Gate 4 + publish + live apply (human-gated)
- [ ] 5.1 [human] Gate-4 sign-off
- [ ] 5.2 [human] push branch; PR; CI; merge (INV-14)
- [ ] 5.3 [human] `cp` 2 notes + `render`/`reconcile`; hand-apply runbook edit to live
      `96-Runbooks/` (text in Site `bootstrap-runbook-refresh-proposal`)
- [ ] 5.4 [agent] record; live close-lint proof at next close
- [ ] 5.5 [human] archive (no ordering constraint) + release cadence
