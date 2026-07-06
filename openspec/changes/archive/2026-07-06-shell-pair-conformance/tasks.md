<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta
- [x] 1.1 `maintenance` — vault_lib requirement: shell-pair conformance paragraph + scenario

## 2. Implementation
- [x] 2.1 `site-slag-script.md` — usage gate; inline root resolution; `--check` slug (INV-11);
      src/dest gates; pathspec-scoped commit (sweep removed)
- [x] 2.2 `spoil-dump-script.md` — same

## 3. Docs
- [x] 3.1 `CHANGELOG.md` `[Unreleased]`

## 4. Regression
- [x] 4.1 validate --strict (change + all)
- [x] 4.2 validate-scripts.sh OK (bash -n + shellcheck both)
- [x] 4.3 Battery: happy slag scoped + staged-file untouched; invalid slug rc 1; missing src
      rc 3; dest collision rc 3; happy dump rc 0; usage rc 1

## 5. Gate 4 + publish + live apply (human-gated)
- [x] 5.1 [human] Gate-4 sign-off recorded (post-merge)
- [x] 5.2 [human] PR #13; CI green; merged `b6ccbd8`
- [x] 5.3 [human] Applied live + rendered (vault `3ff560b`)
- [x] 5.4 [agent] Recorded 2026-07-06; rendered movers carry all gates; live proof at next real slag/dump
- [ ] 5.5 [human] archive after fix-commit-gate → wave-2 (accretion order); release cadence
