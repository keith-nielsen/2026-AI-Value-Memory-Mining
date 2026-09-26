# Tasks — relocate-repo-prime-to-framework-root

> Origin: 2026-09-26 audit of `/vmm-session-rebooted` and `/vmm-repo-github` against `main` (#134).
> Operator decision (2026-09-26): option (a) — move the repo-work prime to the framework repo, with
> the future intent of a full framework/vault split.

## 0. END STATE

The repo-work prime lives in this repository's `.claude/commands/`, depends on no vault, and restates
no source of record; vaults no longer receive it; the card's two otherwise-unrecorded facts live in
`AGENTS.md`; a test holds the boundary; the live vault's copy is removed and parity reads 0 drift.

## 1. Implementation

- [x] 1.1 Branch `change/relocate-repo-prime-to-framework-root` from `main` (`28c94ba`).
- [x] 1.2 `git rm vault-template/.claude/commands/vmm-repo-github.md`.
- [x] 1.3 Add `.claude/commands/vmm-repo-github.md` — the one instruction, pointers to `AGENTS.md`,
      `CONTRIBUTING.md`, `docs/version-control-legal-moves.md`; no vault-side names.
- [x] 1.4 `AGENTS.md` operating notes: Dependabot scope block; `npm ci` after a dependency bump.
- [x] 1.5 Every non-archived reference to the prime enumerated: 2 files (`CHANGELOG.md` history, left
      as is; the removed file itself).

## 2. Tests (observed to fail first)

- [x] 2.1 `tests/test_repo_prime_framework_standalone.py`: 4 checks, **4 failed** before 1.2–1.3,
      4 pass after.
- [x] 2.2 Adversarial: the coupling check catches `VAULT_ROOT`, `FRAMEWORK_ROOT`, `30-Sites` in the
      removed prime's text (`git show HEAD:…`); the route check fails with the `--plan` line removed.

## 3. Spec

- [x] 3.1 None — `skip_specs: true`. No capability spec names the prime; the `.claude/commands/`
      lockstep prefix is unchanged.

## 4. Regression

- [x] 4.1 Full suite green — 553 on `main` → 557 passed.
- [x] 4.2 `openspec validate --all --strict` — 7 passed, 0 failed.
- [~] 4.3 `tools/preflight.py .` → CLEAR (13/16 CI jobs reproduced, trial merge clean, CAN ARCHIVE);
      STEP 7 `SKIP` until the body exists — re-run with `--body-file` at 6.3.

## 5. Gate 4 — operator authorization

No `protects:`-tagged file is touched. Surfaced for sign-off:

- **Vaults lose `/vmm-repo-github`.** Framework work starts from a session rooted in this repo.
- **Deploy-down needs a manual removal** of `$VAULT_ROOT/.claude/commands/vmm-repo-github.md`;
  parity reads `MISSING-IN-TEMPLATE` until it is done.
- **`AGENTS.md` grows by two operating notes** carried over from the retired card.

- [ ] 5.1 Surfaced; awaiting sign-off.

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff (generated after the archive commit).
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.

## 7. Deploy-down

- [ ] 7.1 Operator: `tools/template-mirror.py`.
- [ ] 7.2 Operator: remove `$VAULT_ROOT/.claude/commands/vmm-repo-github.md` (one vault commit).
- [ ] 7.3 `tools/template-parity.py $VAULT_ROOT` → **0 drift**.

## 8. Close the record (vault side, not this pull request)

- [ ] 8.1 The card `30-Sites/repo-work-bootstrap-enforcement/vmm-repo-github-card.md` is orphaned; the
      Site may be closed through the vault pipeline.
