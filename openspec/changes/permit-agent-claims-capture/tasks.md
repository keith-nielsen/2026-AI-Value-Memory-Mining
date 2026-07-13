<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `access-control` — MODIFY "Area Access Matrix": `20-Claims/` Agent `—` -> `RW`; footnote 2
      reworded (direct capture permitted; `_refine-approved/` gate untouched); +1 scenario

## 2. Docs + housekeeping

- [x] 2.1 `AGENTS.md` — add a `20-Claims/` capture row to the access table
- [x] 2.2 `README.md` — ADR count 18 -> 25 in all three spots; range `ADR-0001–0025`
- [x] 2.3 `.github/workflows/ci.yml` — ADR-count consistency guard (README count == actual file count)
- [x] 2.4 ADR-0025 (Proposed; flips to Accepted at Gate 4)
- [x] 2.5 CHANGELOG `[Unreleased]` entry

## 3. Regression (before Gate 3 closes)

- [x] 3.1 `openspec validate permit-agent-claims-capture --strict` + `openspec validate --all --strict`
- [x] 3.2 `pytest tests/`
- [x] 3.3 ci.yml ADR-count guard passes locally (25 == 25); no `settings.json` diff

## 4. Gate 4 + release (human-gated)

- [ ] 4.1 Gate-4 sign-off recorded in `proposal.md`; ADR-0025 -> Accepted
- [ ] 4.2 PR; CI green; human merge (INV-14: agent pushes via operator-authorized `git -C`)
- [ ] 4.3 Archive (sync `access-control` spec) + CHANGELOG release heading + tag `v0.1.20`
