<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Pillar Vocabulary Tokens Are Kebab-Case Slugs

Every token in the `PILLARS` vocabulary MUST be a valid kebab-case slug as defined
by the `naming-rules` `slug_pattern` (`^[a-z0-9]+(?:-[a-z0-9]+)*$`) and MUST pass
the cross-platform-safety and reserved-name checks of `validate_name()` — i.e. the
token MUST satisfy `is_valid_slug()`.

The ≥3-hyphen-token floor (`has_min_hyphen_tokens`, INV-11) does **NOT** apply to
pillar tokens. That floor governs `.md` stems; a pillar token is a name *fragment*
that is interpolated into a stem (`<pillar>-domain-index`), and the resulting stem
satisfies the floor on its own.

A multi-word pillar is expressed as a single hyphenated token (`mental-health`),
never as two whitespace-separated words. The `PILLARS` delimiter remains whitespace.

Rationale: a pillar token is interpolated directly into the machine-generated
Catalog index filename `40-Treasury/Catalog/<pillar>-domain-index.md`. Constraining
the token to the slug grammar makes the vocabulary and the filename agree by
construction, with no pillar→slug transform and no display/slug identity split.

#### Scenario: Well-formed pillar vocabulary passes

- **WHEN** the linter runs with `PILLARS="mental health financial social technology calling"`
- **THEN** each token is validated with `is_valid_slug()`
- **THEN** all six tokens pass and no violation is recorded

#### Scenario: Multi-word pillar as a single kebab token passes

- **WHEN** `PILLARS` contains the token `mental-health`
- **THEN** `is_valid_slug("mental-health")` is true and no violation is recorded
- **THEN** the derived index filename is `mental-health-domain-index.md`, which
  satisfies the INV-11 ≥3-token floor

#### Scenario: Malformed pillar token fails the lint

- **WHEN** `PILLARS` contains a token that fails `is_valid_slug()` — e.g.
  `Mental_Health` (uppercase + underscore), `CON` (reserved name), or `-lead`
  (leading hyphen)
- **THEN** the linter records a violation naming the offending token and the
  `PILLARS` key
- **THEN** the linter exits `EXIT_VIOLATION`
- **THEN** no Catalog index is derived from the malformed token

#### Scenario: Pillar vocabulary is validated before frontmatter is checked

- **WHEN** the linter runs
- **THEN** `PILLARS` well-formedness is validated before Treasury `pillars`
  frontmatter is validated against it
- **THEN** a malformed vocabulary is reported as a vocabulary violation, not as a
  cascade of per-note frontmatter violations
