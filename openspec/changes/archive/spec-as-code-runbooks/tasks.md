# Tasks — spec-as-code-runbooks

## Specs (deltas → live)
- [x] `vault-structure` delta: `96-Runbooks` band + reserved note `90–95`; `runbook` schema + daily `closed:`
- [x] `maintenance` delta: Runbook Format + Daily Close Lifecycle requirements; Script Inventory `vault-close-day`
- [x] Apply both deltas to the live specs

## Band + schema + vocab
- [x] `vault-template/96-Runbooks/` band
- [x] `99-Operations/schemas/runbook.md` (meta-schema)
- [x] `99-Operations/schemas/frontmatter.md` daily `closed:`
- [x] `99-Operations/config.env` `DISPOSITIONS`

## Charter runbooks
- [x] `96-Runbooks/seal-provenance.md`
- [x] `96-Runbooks/close-daily.md`

## Deterministic scripts
- [x] `99-Operations/scripts/close-daily.md` → `vault-close-day.py`
- [x] `rollover.md` + `daily-note.md` gate updates (capture-stub always; rollover gated; BLOCKED banner)

## Mold
- [x] `97-Molds/daily.md` `closed:` + `## Close` / `## Carry-over`

## ADRs
- [x] `0011-spec-as-code-runbooks.md`
- [x] `0012-daily-close-lifecycle.md`

## CI teeth + adapters
- [x] `.github/scripts/runbook-lint`, `close-lint`; `ci.yml` jobs
- [x] `validate-scripts.sh` adds `vault-close-day`
- [x] `AGENTS.md` Runbooks pointer + footguns; `CLAUDE.md` pointer

## Gate + release
- [x] Regression green (openspec --strict, lints, validate-scripts, link-check, CI)
- [x] **Gate 4 — Keith AUTHORIZE**
- [x] `CHANGELOG [0.1.5]`; archive change; tag `v0.1.5` + release
- [x] Mirror to live vault (~/Documents/Vault)
