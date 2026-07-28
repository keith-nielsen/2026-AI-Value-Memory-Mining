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
- [ ] `openspec/adr/0036-enforce-inv7-secret-scan.md`
- [ ] `README.md` ADR count 35 → 36 + reference `0036` (CI-guarded by `adr-count-lint`)

## 3. Blast-radius edits (from the Gate-1 transcript)

- [ ] `README.md:113` — 13 → 14 literate meta-scripts
- [ ] `docs/obsidian.md:8` — 13 → 14 scripts
- [ ] `docs/obsidian.md:147` — 13 → 14 scripts
- [ ] `SECURITY.md:37` — name the mechanism in the INV-7 row (advisory)
- [ ] `CHANGELOG.md` — v0.1.35
- [x] `tools/template-sync-manifest.json` — verified **no change needed** (directory-prefix lockstep)

## 4. Operator decision — pending

- [ ] Fold in the retraction of `access-control` lines 68/73 (stale claim that the commit gate
      enforces INV-4/INV-5 — superseded by ADR-0022's kernel enforcement), or run it separately?

## 5. Ship

- [ ] `tools/ship-release.py v0.1.35` — gated commands, re-verified per layer
- [ ] PR with ```scope block; `scope-review` job clean
- [ ] Gate-4 human sign-off recorded in the proposal
- [ ] Archive **on the feature branch before merge** (else a second archive PR is owed)
- [ ] Tag → Release; `pr-state.py` parity check

## 6. Deploy to the live vault (operator-only)

- [ ] `tools/template-mirror.py` — repo → live
- [ ] **Operator** runs `vault-render.py render` (agent gets EROFS by design)
- [ ] `vault-render.py reconcile` — zero drift across 14 targets
- [ ] Confirm the live gate fires: stage a synthetic HIGH-tier token, observe the block, discard
