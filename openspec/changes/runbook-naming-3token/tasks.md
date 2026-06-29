## 1. Specs

- [x] 1.1 `maintenance` delta — MODIFIED Daily Close Lifecycle (`close-daily` → `daily-close` ritual)
- [x] 1.2 `vault-structure` delta — MODIFIED Folder Structure (runbook examples) + Frontmatter Schemas (ritual ref)

## 2. Runbooks (vault-template)

- [x] 2.1 `git mv` `close-daily.md` → `daily-close-runbook.md`; update `id:`, `title:`, `# Runbook —` heading
- [x] 2.2 `git mv` `seal-provenance.md` → `provenance-seal-runbook.md`; update `id:`, `title:`, `# Runbook —` heading

## 3. Reference repoints

- [x] 3.1 `AGENTS.md` — runbook list + `seal-provenance` operating note
- [x] 3.2 `CLAUDE.md` (repo root adapter) — runbook examples
- [x] 3.3 `session-bootstrap-loader.md` — "Other runbooks" cross-ref
- [x] 3.4 `daily-close-script.md` — "the `close-daily` runbook" → `daily-close-runbook`
- [x] 3.5 `dig-rollover-script.md` — "run close-daily first" → "run daily-close first"
- [x] 3.6 `note-frontmatter-schema.md` — "set by close-daily" → "set by daily-close"

## 4. Regression

- [x] 4.1 `openspec validate runbook-naming-3token --strict` green
- [x] 4.2 `constitution-lint` (override + ADR present) + `vocabulary-lint` green
- [x] 4.3 Grep: no `close-daily` / `seal-provenance` outside `openspec/changes/archive/`, ADR history, CHANGELOG

## 5. Gate 4 + release (human-gated)

- [x] 5.1 Gate-4 sign-off recorded in `proposal.md` (Keith — Option A, 2026-06-29)
- [x] 5.2 `openspec/adr/0017-runbook-naming.md` (Accepted)
- [ ] 5.3 Archive (`openspec archive`/sync) + CHANGELOG `[0.1.12]` + tag `v0.1.12`
- [ ] 5.4 Mirror to live vault (runbook renames + reference repoints; no re-render)
