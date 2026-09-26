# Tasks — eliminate-repo-prime-command

> Origin: 2026-09-26 audit of `/vmm-repo-github` against `main` (`28c94ba`). Operator decision
> (2026-09-26): repo work stays in vault-rooted sessions; eliminate the command, moving anything
> not redundant into existing guidance. Supersedes a withdrawn relocate-to-framework-root draft
> (same branch, renamed before any push).

## 0. END STATE

`/vmm-repo-github` exists nowhere; every item it carried is held by a source of record or a control;
the three it alone held live in bootstrap step 5 and `AGENTS.md`; a test holds all of that; the live
vault's copy is removed and parity reads 0 drift.

## 1. Implementation

- [x] 1.1 Branch from `main` (`28c94ba`); renamed `change/eliminate-repo-prime-command` (unpushed).
- [x] 1.2 `git rm vault-template/.claude/commands/vmm-repo-github.md`; the interim framework-root copy
      removed; no copy remains.
- [x] 1.3 Redundancy map measured against `main` (proposal table): 12 held by sources of record,
      2 by controls, 3 moved.
- [x] 1.4 `session-bootstrap-loader` step 5: repo-work pointer, gated on `FRAMEWORK_ROOT`.
- [x] 1.5 `AGENTS.md` operating notes: Dependabot scope block; `npm ci` after a dependency bump.
- [x] 1.6 Non-archived references enumerated: `CHANGELOG.md` history only, left as is.

## 2. Tests (observed to fail first)

- [x] 2.1 `tests/test_repo_prime_command_eliminated.py`: 3 checks; on a clean worktree of `main`,
      **3 failed**; on this branch, 3 passed.

## 3. Spec

- [x] 3.1 None — `skip_specs: true`. No capability spec names the command; the lockstep prefix stays.

## 4. Regression

- [x] 4.1 Full suite green — 553 on `main` → 556 passed.
- [x] 4.2 `openspec validate --all --strict` — 7 passed, 0 failed.
- [~] 4.3 `tools/preflight.py .` → CLEAR (13/16 CI jobs reproduced incl. `standalone-vault-lint` and
      `runbook-lint`; CAN ARCHIVE); STEP 7 `SKIP` until the body exists — re-run at 6.3.

## 5. Gate 4 — operator authorization

No `protects:`-tagged file is touched. Surfaced for sign-off:

- **Vault sessions lose `/vmm-repo-github`**; the step-5 pointer, the driver and the guards replace it.
- **Deploy-down needs a manual removal** of `$VAULT_ROOT/.claude/commands/vmm-repo-github.md`.
- **`AGENTS.md` and bootstrap step 5 grow** by the three items only the card held.

- [x] 5.1 Surfaced; **Approved** — Keith Nielsen, 2026-09-26

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [x] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff (generated after the archive commit).
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.

## 7. Deploy-down

- [ ] 7.1 Operator: `tools/template-mirror.py` (carries the bootstrap edit).
- [ ] 7.2 Operator: remove `$VAULT_ROOT/.claude/commands/vmm-repo-github.md` (one vault commit).
- [ ] 7.3 `tools/template-parity.py $VAULT_ROOT` → **0 drift**.

## 8. Close the record (vault side, not this pull request)

- [ ] 8.1 The card `30-Sites/repo-work-bootstrap-enforcement/vmm-repo-github-card.md` is orphaned; the
      Site may be closed through the vault pipeline.
