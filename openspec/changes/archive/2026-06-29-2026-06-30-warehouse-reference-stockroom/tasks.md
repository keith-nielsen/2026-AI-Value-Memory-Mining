## 1. Specs (deltas)

- [x] 1.1 `vault-structure` delta — MODIFIED *Three-Layer Model* (Warehouse charter) + *Folder Structure* (shelves, charter para, shelf-naming scenario, ADR-0016 `<pillar>-domain-index.md` straggler fix)
- [x] 1.2 `access-control` delta — MODIFIED *Area Access Matrix* (Warehouse row note; privileges unchanged)

## 2. Template (vault-template)

- [x] 2.1 Scaffold `98-Warehouse/{Books,Music,Art,Pictures,Audio}/.gitkeep`
- [x] 2.2 `00-Docs/README.md` — charter line `98-Warehouse/ ← reference stockroom …`
- [x] 2.3 `99-Operations/schemas/refine-prompt-contract.md` — `<pillar>-index.md` → `<pillar>-domain-index.md` (completes ADR-0016; matches `agent-integration` spec)

## 3. Regression

- [x] 3.1 `openspec validate --all --strict` green
- [x] 3.2 `constitution-lint` — both `vault-structure` + `access-control` retain `protects:`
- [ ] 3.3 CI green on push

## 4. Gate 4 + release (human-gated)

- [x] 4.1 Gate-4 sign-off recorded in `proposal.md` (human only)
- [x] 4.2 `openspec/adr/0019-warehouse-reference-stockroom.md` → Status: Accepted
- [x] 4.3 `openspec archive` + CHANGELOG `[0.1.14]` + tag `v0.1.14`
- [x] 4.4 Mirror to live vault (parity check — shelves + README already applied 2026-06-30)
