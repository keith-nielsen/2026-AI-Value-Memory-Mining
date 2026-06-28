## 1. Runbook (SSOT)

- [x] 1.1 Create `vault-template/96-Runbooks/session-bootstrap-loader.md` (conforms to runbook schema; runbook-lint ok)

## 2. Adapters + SessionStart hook (in-repo)

- [x] 2.1 `AGENTS.md` + `vault-template/CLAUDE.md` point at the runbook (+ runbook list)
- [x] 2.2 SessionStart hooks: `.claude/settings.json` (repo) + `vault-template/.claude/settings.json` (ships to vaults)

## 3. Regression

- [x] 3.1 runbook-lint (all 3 runbooks ok) · settings.json valid JSON · `openspec validate --all` · `validate-scripts.sh` sandboxed VALIDATION OK

## 4. Release + mirror

- [ ] 4.1 `/opsx:archive` (no spec delta) + CHANGELOG `[0.1.10]` + tag `v0.1.10`
- [ ] 4.2 Mirror to live vault (runbook + `CLAUDE.md` pointer + `.claude/settings.json` hook)
- [ ] 4.3 Push repo to GitHub (commits + tags)
