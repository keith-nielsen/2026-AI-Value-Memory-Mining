<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `maintenance` — ADD requirement: "Governance Tooling Is Pinned and Ceremony Templates Live
      Outside the Change Tree" (version-agnostic; +3 scenarios)

## 2. Relocation + references

- [x] 2.1 `git mv` template → `openspec/templates/constitution-override/proposal.md`; remove empty
      `changes/templates/`
- [x] 2.2 Repoint 7 references + CI `test -f` guard (`changes/templates/` → `templates/`):
      `constitution.md`, `ci.yml`, `AGENTS.md`, `README.md`, `CONTRIBUTING.md`,
      `docs/USING-THIS-TEMPLATE.md`, `ISSUE_TEMPLATE/change-proposal.yml`

## 3. Version bump + docs

- [x] 3.1 `package.json` pin `1.4.1 → 1.6.0`; regenerate `package-lock.json`
- [x] 3.2 `README.md` ADR count `25 → 26` (3 sites) + range `ADR-0001–0026`
- [x] 3.3 ADR-0026 (Proposed; flips to Accepted at Gate 4)
- [x] 3.4 CHANGELOG `[Unreleased]` entry

## 4. Regression (before Gate 3 closes)

- [x] 4.1 `openspec validate relocate-override-template-openspec-16 --strict` + `openspec validate --all
      --strict` **under 1.6.0** green (8 passed/0 failed)
- [x] 4.2 `pytest tests/` green (25 passed)
- [x] 4.3 adr-count guard (26 == 26, latest 0026) + constitution-lint green (markdown/link/spec/runbook lints run in CI)

## 5. Gate 4 + release (human-gated)

- [x] 5.1 Gate-4 sign-off recorded in `proposal.md`; ADR-0026 → Accepted (operator "Approved", 2026-07-13)
- [ ] 5.2 PR (supersedes Dependabot #18); CI green; human merge (agent pushes via operator-authorized `git -C`)
- [ ] 5.3 Archive (sync `maintenance` spec) + CHANGELOG release heading + tag; close #18 as superseded
