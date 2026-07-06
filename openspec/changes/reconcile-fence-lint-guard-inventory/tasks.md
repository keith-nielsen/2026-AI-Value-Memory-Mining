<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta
- [x] 1.1 `maintenance` — LMF: enum `+ harness hook`, single-fence scenario; Script Inventory:
      `outbound-publish-guard-script.md` row

## 2. Implementation
- [x] 2.1 `render-reconcile-script.md` — ≠1 fence → VIOLATION, exit 1, nothing rendered
- [x] 2.2 NEW `outbound-publish-guard-script.md` — code byte-identical to shipped guard;
      `deploy_target: .claude/hooks/…`; `runtime: harness hook`

## 3. Docs
- [x] 3.1 `CHANGELOG.md` `[Unreleased]`

## 4. Regression
- [x] 4.1 validate --strict (change + all)
- [x] 4.2 validate-scripts.sh OK (17-note render + reconcile zero drift)
- [x] 4.3 Battery: two-fence note VIOLATION rc 1, no render; guard renders byte-identical;
      clean render rc 0

## 5. Gate 4 + publish + live apply (human-gated)
- [ ] 5.1 [human] Gate-4 sign-off
- [ ] 5.2 [human] push branch; PR; CI; merge (INV-14)
- [ ] 5.3 [human] `cp` 2 notes + `render`/`reconcile` (guard render is operator-run; zero drift
      expected — byte-identical)
- [ ] 5.4 [agent] record; fence lint self-exercises on every future render
- [ ] 5.5 [human] archive after `fleet-hygiene-bundle` and `commit-ownership-de-sweep`
      (accretion order); release cadence
