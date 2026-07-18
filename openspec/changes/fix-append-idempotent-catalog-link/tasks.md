<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks: fix-append-idempotent-catalog-link

## 1. Probe (pre-implementation)
- [x] 1.1 Confirm the defect: executor bank-loop (lines 130–132) links unconditionally; `append` to
      an already-catalogued note duplicates its Catalog bullet; empty `index_links` defaults to the
      absent `pending-catalog` index and hard-rejects — no clean append path exists
- [x] 1.2 Confirm repo executor byte-identical to the live deployed note before editing (parity held)

## 2. Implementation
- [x] 2.1 `bank-execute-script.md`: guard the link write with `if f"[[{stem}]]" not in index_text`
- [x] 2.2 Rationale documents idempotent catalog linking
- [x] 2.3 Spec delta: `maintenance` +1 ADDED Requirement ("Catalog Linking Is Idempotent"), 2 scenarios
- [x] 2.4 `tests/test_fleet.py`: append-no-duplicate + new-index-still-linked
- [x] 2.5 CHANGELOG `[Unreleased]` entry

## 3. Verification
- [ ] 3.1 New fleet test case green; full `pytest` green
- [ ] 3.2 `openspec validate --all --strict` green
- [ ] 3.3 PR CI green (incl. scope-review PASS on the declared block)

## 4. Ceremony
- [x] 4.1 Gate-4 human sign-off — **Approved, Keith Nielsen, 2026-07-18** (recorded in proposal.md)
- [ ] 4.2 Merge; archive (merge order relative to `add-telemetry-segment`)
- [ ] 4.3 Tag + Release + parity verify (INV-14 outbound ASK)
- [ ] 4.4 **Mirror** the fixed `bank-execute-script.md` into the live vault; `render` to redeploy
      `~/bin/vault-refine-execute.py`; run `tools/template-parity.py <VAULT_ROOT>` → expect `0 drift`
- [ ] 4.5 THEN bank the gold-note errata append (carry-forward item #2) via the fixed executor
