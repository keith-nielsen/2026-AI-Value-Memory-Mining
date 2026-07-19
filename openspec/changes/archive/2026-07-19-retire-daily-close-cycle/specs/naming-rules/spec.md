<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: Token-Minimum Naming (≥3, silo-section-descriptor)

Every `.md` stem SHALL carry **at least three hyphen-separated tokens** — a floor, not a ceiling.
**Use more tokens where they add human-meaningful specificity**, because the namespace grows
contention-prone as broad topics narrow and digs reveal sub-sectors needing distinction; richer,
more specific names pre-empt the overloading that would otherwise collide later.

- **System-artifact families** (molds, operational scripts, Catalog indexes, schemas) SHALL use the
  **`silo-section-descriptor`** form, silo (subject) first — e.g. molds `<note-type>-mold-blank`.
- **Content stems** (Claims, Sites, Treasury notes) SHALL be ≥3-token topic slugs; longer is correct
  where it adds specificity (e.g. `swappable-stages-over-coresident-models`).
- **Date-stemmed notes** (`YYYY-MM-DD`) are exempt (date-named). The exemption is retained after
  ADR-0032 retired the framework's daily cycle: pre-existing dailies remain under the commit gate,
  and `10-Logbook/` stays a manual working area where a date-stemmed note may still be authored.

This requirement is a **convention** at this stage: it governs new and renamed names through authoring
and review. Existing sub-three-token names are **grandfathered**; each family is brought into
conformance by its own change (molds: v0.1.7). **Mechanical enforcement** — extending `vault_naming.py`,
the commit-gate hook, and `naming-rules.json` to reject sub-three-token stems — is **deferred to a
later change**, sequenced after the families conform (turning on rejection earlier would block commits
on names not yet renamed).

#### Scenario: A new system-artifact name is silo-section-descriptor, ≥3 tokens
- **WHEN** a mold, script, Catalog index, or schema artifact is named or renamed
- **THEN** its stem is silo-first and carries at least three hyphen-separated tokens (e.g. `effort-mold-blank`)

#### Scenario: More tokens where specificity warrants
- **WHEN** a content topic narrows, or a dig reveals a sub-sector needing distinction
- **THEN** the stem carries more than three tokens to stay unambiguous (e.g. `swappable-stages-over-coresident-models`) rather than overloading a shorter name

#### Scenario: Dailies are exempt
- **WHEN** a note is named `YYYY-MM-DD`
- **THEN** the token-minimum does not apply — regardless of whether the framework generated it
  (the exemption outlives the retired daily cycle; ADR-0032)

#### Scenario: Existing sub-three-token names are grandfathered at the convention stage
- **WHEN** this change is in effect and a pre-existing two-token name (e.g. `obsidian-usage`) is present
- **THEN** it is not renamed by this requirement; each family conforms through its own change
