<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `maintenance` — MODIFIED Requirement "Shared Fleet Plumbing and Exit-Code Contract
      (vault_lib)": additive governance-hook clause + commit-gate scenario

## 2. Implementation

- [x] 2.1 `commit-gate-script.md` — delete the vestigial `: "${VAULT_ROOT:?}"` guard (audit:
      unused anywhere in the hook body); Rationale documents the environment-free property +
      burn-in provenance; `updated:` bumped
- [x] 2.2 `push-guard-script.md` audited — already self-locates (`${VAULT_ROOT:-.}` +
      conditional config sourcing); no change needed

## 3. Docs

- [x] 3.1 `CHANGELOG.md` — `[Unreleased]` entry

## 4. Regression (repo-side, before Gate 3 closes)

- [x] 4.1 `openspec validate fix-commit-gate-env-guard --strict` + `openspec validate --all
      --strict` (8/8, 2026-07-05)
- [x] 4.2 `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [x] 4.3 Env-free end-to-end: bare kanban → write + commit through the hook, rc 0; negative
      control `bad:name.md` → `BLOCKED` rc 1 (INV-11 intact, env-free)

## 5. Gate 4 + publish + live apply (human-gated)

- [ ] 5.1 [human] Gate-4 sign-off in `proposal.md`
- [ ] 5.2 [human] PR from `ops/fix-commit-gate-env-guard`; CI green; merge (INV-14: agent cannot)
- [ ] 5.3 [human] `cp` the note into live `99-Operations/scripts/`; `~/bin/vault-render.py render`
      + `reconcile` (zero drift)
- [ ] 5.4 [agent] Final Phase-1a closure: bare `~/bin/vault-kanban-render.py` end-to-end, no env,
      commit through hook; append verdict to `phase-1a-acceptance-probes.md`
- [ ] 5.5 [human] Archive change + CHANGELOG heading + tag per release cadence (push main before
      tagging — F10 guard order)
