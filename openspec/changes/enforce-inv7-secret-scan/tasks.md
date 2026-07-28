<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — enforce-inv7-secret-scan

## 1. Mechanism (done, commit `2c0604b`)

- [x] `vault-template/99-Operations/scripts/secret-scan-script.md` — new Layer-0 meta-script → `~/bin/vault_secrets.py`
- [x] `vault-template/99-Operations/scripts/commit-gate-script.md` — call `--staged`; document the three asymmetries with the INV-11 half
- [x] `.github/workflows/ci.yml` — `secret-scan` job (`fetch-depth: 0`, selftest → full object-DB scan)
- [x] `tests/test_secret_scan.py` — 13 cases incl. negative controls (prose must not trip; advisory must not gate; secret must not appear in output; unreachable blob must be found)
- [x] Phase-0 baseline sweep of both repos, instrument validated against a planted-secret control first

## 2. Ceremony

- [x] `openspec/changes/enforce-inv7-secret-scan/proposal.md` — Gates 1–2 authored from transcripts
- [x] `specs/access-control/spec.md` — ADDED Requirement + 5 scenarios
- [x] `openspec validate --all` green (8 passed, 0 failed)
- [x] `openspec/adr/0036-enforce-inv7-secret-scan.md` — **Accepted** (Keith Nielsen, 2026-07-28)
- [x] `README.md` ADR count 35 → 36 + reference `0036` (CI-guarded by `adr-count-lint`) — verified rc=0

## 3. Blast-radius edits (from the Gate-1 transcript)

- [x] `README.md:113` — 13 → 14 literate meta-scripts
- [x] `docs/obsidian.md:8` — 13 → 14 scripts
- [x] `docs/obsidian.md:147` — 13 → 14 scripts
- [x] `SECURITY.md:37` — name the mechanism in the INV-7 row (INV-7 row only; an "Enforced by" column across all rows was rejected as scope creep)
- [x] `CHANGELOG.md` — v0.1.35 stamped in this PR (the v0.1.31 lesson: deferring it costs an extra PR)
- [x] `tools/template-sync-manifest.json` — verified **no change needed** (directory-prefix lockstep)

## 4. Operator decision — RESOLVED 2026-07-28

- [x] **Run separately.** Folding the `access-control` lines 68/73 retraction into this ceremony was
      proposed by the agent on a proximity argument ("same spec, same ceremony"), checked against
      `CONTRIBUTING.md:65` — *"One change, one purpose. Don't bundle unrelated capabilities"* — and
      **retracted**. Recorded as **F29** in the live vault's failure catalog, with the operator's
      rollback-entanglement rationale: a bundle creates undeclared dependencies, so a later rollback
      of one concern silently drags the others back. `fleet-hygiene-bundle` (2026-07-06) is
      explicitly **not** precedent. Queued as its own change: retract the stale claim that the commit
      gate enforces INV-4/INV-5 (superseded by ADR-0022's kernel enforcement).

## 5. Ship

- [ ] `tools/ship-release.py v0.1.35` — gated commands, re-verified per layer
- [ ] PR with ```scope block; `scope-review` job clean
- [x] Gate-4 human sign-off recorded in the proposal — **Approved, Keith Nielsen, 2026-07-28**
- [ ] Archive **on the feature branch before merge** (else a second archive PR is owed)
- [ ] Tag → Release; `pr-state.py` parity check

## 6. Deploy to the live vault (operator-only)

- [ ] `tools/template-mirror.py` — repo → live
- [ ] **Operator** runs `vault-render.py render` (agent gets EROFS by design)
- [ ] `vault-render.py reconcile` — zero drift across 14 targets
- [ ] Confirm the live gate fires: stage a synthetic HIGH-tier token, observe the block, discard
