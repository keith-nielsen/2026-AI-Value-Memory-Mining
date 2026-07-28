<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — enforce-inv6-offline-check

## 1. Mechanism

- [x] `tools/inv6-offline-check.py` — static half; Python by AST, bash by command-position scan; selftest-gated
- [x] `.github/scripts/inv6-offline-dynamic.sh` — dynamic half; netns run with both controls proven, fail-closed
- [x] `.github/workflows/ci.yml` — jobs `inv6-offline-static` and `inv6-offline-dynamic`
- [x] `tests/test_inv6_offline.py` — 28 cases, weighted to the false-positive direction
- [x] Discrimination demonstrated on the **real** guard files (naive grep 6/2 vs AST 0/0), not only on fixtures

## 2. Ceremony

- [x] `proposal.md` — Gates 1–3 authored from transcripts
- [x] `specs/maintenance/spec.md` — ADDED Requirement + 5 scenarios
- [x] `openspec/adr/0037-enforce-inv6-offline-check.md` — **Accepted** (Keith Nielsen, 2026-07-28)
- [x] `README.md` ADR count 36 → 37 + reference `0037` — `adr-count-lint` verified rc=0
- [x] `CHANGELOG.md` — v0.1.36
- [x] Gate-4 human sign-off recorded — **Approved, Keith Nielsen, 2026-07-28**

## 3. Verified before sign-off

- [x] `openspec validate --all` — 8/8
- [x] `pytest tests/` — 104 passed (76 prior + 28 new, no regressions)
- [x] static check — 14 fleet notes, 0 violations, 0 unresolved
- [x] dynamic check — 38 passed offline, both controls proven in the same run
- [x] fail-closed path — verified by making it fire (exit 1, "INVALID instrument")

## 4. Ship (after merge)

- [ ] `tools/ship-release.py v0.1.36` — runs **after** merge; first guard is merge-ancestor proof
- [ ] PR with ```scope block; `scope-review` clean
- [ ] Archive **on the feature branch before merge**
- [ ] Tag → Release; parity **37/37**

## 5. Deploy

- [x] **None owed.** `vault-template/` is untouched (verified: `git diff --stat main..HEAD -- vault-template/` empty), so there is no mirror and no operator `render`. Repo-side only.

## 6. Queued separately (F29 — one change, one purpose)

- [ ] **Tests for the two INV-14 guards** — they have none, so the dynamic half cannot cover them. The
      single largest gap this change leaves, and it is stated in the tool's own output rather than hidden.
- [ ] Retract stale `access-control` lines 68/73 (commit gate no longer enforces INV-4/5)
- [ ] Two probably-stale `SECURITY.md` deferred-work entries (superseded by ADR-0022)
- [ ] `validate-scripts.sh` hardcoded `/tmp` diagnostic paths
- [ ] `add-telemetry-segment` re-scope — predates the INV-14 findings; proposes an osquery dependency
- [ ] F28 rule 3 unmechanized — nothing verifies `"commit X said Y"` against `git log`
