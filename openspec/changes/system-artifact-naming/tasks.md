## 1. Specs

- [x] 1.1 `maintenance` delta — MODIFIED Script Inventory (note names; deploy targets unchanged)
- [x] 1.2 `vault-structure` delta — MODIFIED Frontmatter Schemas (schema doc references)
- [x] 1.3 `agent-integration` delta — MODIFIED Refine Proposal JSON Schema (`index_links` pattern + `refine-prompt` ref)

## 2. Scripts (vault-template)

- [x] 2.1 `git mv` 14 script notes → `<…>-script.md`; `deploy_target` frontmatter unchanged (`commit-gate-script` keeps `…/hooks/pre-commit`)
- [x] 2.2 Repoint doc references to script note names (`docs/`, `00-Docs/`, `AGENTS.md`, `README.md`, `.github/`)

## 3. Schemas (vault-template)

- [x] 3.1 `git mv` `frontmatter`→`note-frontmatter-schema`, `runbook`→`runbook-format-schema`, `refine-prompt`→`refine-prompt-contract`; updated self-referential `deploy_target`s
- [x] 3.2 Repoint schema-doc references (`docs/`, `AGENTS.md`, `00-Docs/`, internal cross-ref)

## 4. Indexes (vault-template)

- [x] 4.1 `git mv` 7 Catalog files → `<pillar>-domain-index` + `home-master-index`
- [x] 4.2 Repoint `home-master-index` links + `index_links` (examples, `.github` fixture) + all `[[…-index]]` references

## 5. Regression

- [x] 5.1 `openspec validate --all` green (8/8)
- [x] 5.2 `constitution-lint` (6 specs retain `protects:`) + `vocabulary-lint` (GRADES) green
- [x] 5.3 `validate-scripts.sh` green (sandboxed; renders all renamed scripts + smoke-tests)
- [x] 5.4 Grep: no residual old names outside `openspec/` and CHANGELOG history — clean. (Full CI on push.)

## 6. Gate 4 + release (human-gated)

- [ ] 6.1 Gate-4 sign-off recorded in `proposal.md` (Keith — human only)
- [ ] 6.2 `openspec/adr/00NN-system-artifact-naming.md`
- [ ] 6.3 `/opsx:archive` + CHANGELOG `[0.1.9]` + tag `v0.1.9`
- [ ] 6.4 Mirror to live vault (script + index renames + reference repoints + re-render + reconcile)
