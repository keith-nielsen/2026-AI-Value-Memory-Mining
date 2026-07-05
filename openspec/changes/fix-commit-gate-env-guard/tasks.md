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

- [x] 5.1 [human] Gate-4 sign-off recorded (post-merge; see provenance note in `proposal.md`)
- [x] 5.2 [human] PR #8; CI green; merged `23e0198` (2026-07-05)
- [x] 5.3 [human] Applied live + rendered (vault `7f9b33a`); `reconcile` zero drift
- [x] 5.4 [agent] Phase-1a CLOSED (2026-07-05): live hook verified env-free — no VAULT_ROOT error
      at any layer on the bare drive run; env-free recording commit through the live hook succeeded
      (vault `3be93a1`, the probe itself). Bare-run commit leg exposed a separate fleet defect —
      kanban same-day identical re-render → empty-index commit crash (INV-2 no-op clause +
      exit-code contract violation) — catalogued to wave-2 (systemic fix: nothing-staged guard in
      `vault_lib.commit_paths`). Verdicts in `phase-1a-acceptance-probes.md`
- [ ] 5.5 [human] Archive change + CHANGELOG heading + tag per release cadence (push main before
      tagging — F10 guard order)
