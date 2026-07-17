<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks: add-template-parity-check

## 1. Probe (pre-implementation)
- [x] 1.1 Confirm the missing axis: `reconcile` covers note → `~/bin`; nothing covers template → live
- [x] 1.2 Full-tree survey of `vault-template/` vs the live vault (56 ok / 9 differ / 2 missing) →
      10 of 11 divergences are legitimate per-instance seed; exactly 1 is real drift → scope must be
      a lockstep allowlist, not a full diff
- [x] 1.3 Prototype run against the REAL trees surfaced the generated-`naming-rules.json` case →
      manifest needs an `exclude` for vault-generated artifacts

## 2. Implementation
- [x] 2.1 `tools/template-parity.py` (stdlib-only, offline, detection-only; byte-exact bidirectional
      per lockstep prefix; prints the denominator; exit 0/1/3)
- [x] 2.2 `tools/template-sync-manifest.json` (lockstep = `99-Operations/scripts/`,
      `99-Operations/schemas/`; exclude = `naming-rules.json`)
- [x] 2.3 `tests/test_template_parity.py` (6 subprocess-driven cases)
- [x] 2.4 Spec delta: `maintenance` +1 ADDED Requirement, 5 scenarios
- [x] 2.5 AGENTS.md Operating-notes bullet: run parity after a post-merge mirror
- [x] 2.6 README repo-structure tree: add `tools/`
- [x] 2.7 CHANGELOG `[Unreleased]` entry

## 3. Verification
- [x] 3.1 `tests/test_template_parity.py` — 6 passed locally
- [ ] 3.2 `openspec validate add-template-parity-check --strict` green
- [ ] 3.3 Full local regression: `openspec validate --all --strict` + `pytest` green
- [ ] 3.4 PR CI green (its own scope-review PASS on the declared block)

## 4. Ceremony
- [x] 4.1 Gate-4 human sign-off — **Approved, Keith Nielsen, 2026-07-18** (recorded in proposal.md)
- [ ] 4.2 Merge; archive in merge order relative to `add-telemetry-segment` (both MODIFY `maintenance`)
- [ ] 4.3 Tag + GitHub Release + parity verify (INV-14 outbound ASK) + mirror BOTH halves
      (there is no template half here — the tool is repo-only; nothing to mirror into the live vault)
