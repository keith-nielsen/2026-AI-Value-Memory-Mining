<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta
- [x] 1.1 `maintenance` — ADDED "Platform and Dependency Floors" + scenarios

## 2. Implementation
- [x] 2.1 NEW `render-reconcile-runbook.md` (INV-3 loop)
- [x] 2.2 NEW `refine-pipeline-runbook.md` (detect → propose → human gate → atomic bank)
- [x] 2.3 `docs/USING-THIS-TEMPLATE.md` floors paragraph

## 3. Docs
- [x] 3.1 `CHANGELOG.md` `[Unreleased]`

## 4. Regression
- [x] 4.1 validate --strict (change + all)
- [x] 4.2 runbook-lint fields/sections on both new runbooks; validate-scripts.sh OK
- [x] 4.3 Floors spot-check: `--check` path stdlib-only (frontmatter/vault_lib absent)

## 5. Gate 4 + publish + live apply (human-gated)
- [ ] 5.1 [human] Gate-4 sign-off
- [ ] 5.2 [human] push branch; PR; CI; merge (INV-14)
- [ ] 5.3 [human] `cp` the 2 runbooks into live `96-Runbooks/`
- [ ] 5.4 [agent] record
- [ ] 5.5 [human] archive (ADDED-only, no ordering constraint); release cadence
