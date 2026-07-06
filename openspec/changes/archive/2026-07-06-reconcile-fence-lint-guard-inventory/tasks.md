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
- [x] 5.1 [human] Gate-4 sign-off recorded (post-merge)
- [x] 5.2 [human] PR #14; merged `52d16c1`
- [x] 5.3 [human] Applied live + rendered (vault `1494595`); 17 notes, reconcile clean
- [x] 5.4 [agent] Recorded 2026-07-06; rendered vault-render.py carries the VIOLATION lint
- [ ] 5.5 [human] archive after `fleet-hygiene-bundle` and `commit-ownership-de-sweep`
      (accretion order); release cadence
