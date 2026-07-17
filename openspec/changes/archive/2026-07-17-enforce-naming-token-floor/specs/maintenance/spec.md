<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: The Linter Applies The Token Floor To Content Stems

The knowledge linter SHALL apply the ≥3-hyphen-token floor (`has_min_hyphen_tokens`) in
addition to the kebab rule, to every non-exempt content name it already checks:

- Treasury note stems (`40-Treasury/*.md`)
- Effort folder slugs (`30-Sites/*/`, `70-Tailings/*/`)
- Other content stems (`20-Claims`, `10-Logbook`, `40-Treasury/Catalog`)

The previously staged branch for this rule SHALL be enabled, not left commented. Special-file
exemptions (`is_exempt`) continue to be applied first.

The floor SHALL NOT be applied to pillar tokens, which are name *fragments* interpolated into
a stem rather than stems themselves (ADR-0029).

#### Scenario: A sub-3-token Treasury stem fails the lint

- **WHEN** the linter encounters a non-exempt `40-Treasury/short-note.md`
- **THEN** it records `Treasury stem not >=3-token kebab (INV-11)`
- **THEN** it exits `EXIT_VIOLATION`

#### Scenario: A sub-3-token effort folder fails the lint

- **WHEN** the linter encounters `30-Sites/sample/`
- **THEN** it records `effort folder not >=3-token kebab (INV-11)`

#### Scenario: The live corpus passes with the rule enabled

- **WHEN** the linter runs over a conforming vault
- **THEN** no floor violation is recorded, because enforcement was switched on only after
  full conformance was measured (0 of 103 non-exempt names failing)
