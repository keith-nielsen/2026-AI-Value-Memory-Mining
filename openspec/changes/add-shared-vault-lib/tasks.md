<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `maintenance` — ADDED Requirement "Shared Fleet Plumbing and Exit-Code Contract
      (vault_lib)" + scenarios (bare no-env drive invocation, machine-distinguishable gate
      refusal, YAML-typed closed, read-only self-check)
- [x] 1.2 `maintenance` — MODIFIED Requirement "Script Inventory" (+ `vault-lib-script.md` row;
      shared-module import note)

## 2. Implementation (vault-template)

- [x] 2.1 NEW `99-Operations/scripts/vault-lib-script.md` → `~/bin/vault_lib.py` (root resolution,
      `load_config`/`vocab` precedence chain, `fm`/`is_closed`, `commit_paths`, exit-code
      constants, `say`, read-only self-check CLI)
- [x] 2.2 `render-reconcile-script.md` — inline bootstrap copy of the resolution contract (must
      not import the module it deploys)
- [x] 2.3 `daily-note-script.md` — root + YAML-typed `is_closed`
- [x] 2.4 `dig-rollover-script.md` — root, `is_closed`, `commit_paths`; refusals exit 3
- [x] 2.5 `kanban-render-script.md` — root, `fm`, `commit_paths`; `GRADES`/`EFFORT_STATUSES` from
      config SSOT
- [x] 2.6 `daily-close-script.md` — root + `DISPOSITIONS` via `vocab()`; gate refusals exit 3;
      classification + commit scope untouched
- [x] 2.7 `bank-execute-script.md` — root only

## 3. Docs

- [x] 3.1 ADR-0023 (Proposed; flips to Accepted at Gate 4)
- [x] 3.2 `CHANGELOG.md` — `[Unreleased]` entry (drafted with the change, not after — F10 lesson)

## 4. Regression (repo-side, before Gate 3 closes)

- [x] 4.1 `openspec validate add-shared-vault-lib --strict` + `openspec validate --all --strict`
      (8/8, 2026-07-05)
- [x] 4.2 `bash .github/scripts/validate-scripts.sh` green locally — `VALIDATION OK` (render
      bootstrap, py_compile incl. `vault_lib.py`, smoke, close lifecycle, INV-11 boundary)
- [x] 4.3 Sandbox-vault checks: self-check rc 0 (six vocab keys); bare no-env render/daily-note/
      kanban all rc 0 (kanban: one scoped commit, no sweep); rollover + close-day refusals
      `BLOCKED:` + rc 3; `closed: false` → open
- [x] 4.4 vocabulary/constitution lint preconditions (ceremony artifacts present; no off-metaphor
      terms)

## 5. Live vault (operator + agent, out of band of this repo)

- [ ] 5.1 [human] Gate-4 review + sign-off; then copy the 7 notes into live
      `99-Operations/scripts/` and run `vault-render.py render`; `reconcile` → zero drift
- [ ] 5.2 [agent] Re-run probe P5 bare (`~/bin/vault-kanban-render.py`, no env) → one scoped
      commit; **SE-5 closed** (exclusion demonstrably lifts the sandbox); `vault_lib.py`
      self-check; rollover gate → exit 3; append verdicts to `phase-1a-acceptance-probes.md`
- [ ] 5.3 [both] Schedule follow-ups: wave-2 adoption; B3 de-sweep + commit ownership; B4
      bank-execute hardening; `runtime:` enum alignment

## 6. Gate 4 + release (human-gated)

- [ ] 6.1 Gate-4 sign-off recorded in `proposal.md`; ADR-0023 → Accepted
- [ ] 6.2 PR from `ops/add-shared-vault-lib`; CI green; human merge (INV-14: agent cannot)
- [ ] 6.3 Archive (sync `maintenance` spec) + CHANGELOG release heading + tag (human, post-merge)
