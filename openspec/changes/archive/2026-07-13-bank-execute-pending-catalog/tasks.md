<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta
- [x] 1.1 `maintenance` — MODIFY "Refine Executor Pre-Flight and Batch Isolation": add the
      Catalog-reachability bullet (empty `index_links` → holding index) + the default scenario

## 2. Code (vault-template)
- [x] 2.1 `bank-execute-script.md` — add `PENDING_CATALOG` constant
- [x] 2.2 `bank-execute-script.md` — normalize an explicit empty `index_links` to `[PENDING_CATALOG]`
      before `check()` (missing / non-list stays a schema reject)
- [x] 2.3 `40-Treasury/Catalog/pending-catalog-index.md` — NEW holding index shipped in template

## 3. Docs / ADR
- [x] 3.1 ADR-0024 (Proposed; flips to Accepted at Gate 4)
- [x] 3.2 `CHANGELOG.md` — `[Unreleased]` entry (drafted with the change)

## 4. Regression (before Gate 3 closes)
- [x] 4.1 `openspec validate bank-execute-pending-catalog --strict` + `--all --strict` = 8/8 pass
- [x] 4.2 `pytest tests/` = 25 passed (new default-to-holding case green; existing bank cases unchanged)
- [x] 4.3 A *named* non-existent index link still hard-rejects (existing test green — no regression)

## 5. Live vault (operator, out of band)
- [ ] 5.1 [human] Create `40-Treasury/Catalog/pending-catalog-index.md` in the deployed vault
      (Treasury is autonomy-banned, INV-5); until then an empty-`index_links` proposal safely rejects
- [ ] 5.2 [human] `vault-render.py render` to deploy the updated executor to `~/bin/`

## 6. Gate 4 + release (human-gated)
- [ ] 6.1 [human] Gate-4 sign-off recorded in `proposal.md` (agents may not sign)
- [ ] 6.2 [human] `openspec archive bank-execute-pending-catalog` → tag → PR to `main`
