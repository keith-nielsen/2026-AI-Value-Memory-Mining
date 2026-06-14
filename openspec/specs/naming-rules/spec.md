---
capability: naming-rules
protects: [INV-11]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: naming-rules

The vault naming ruleset (INV-11): what constitutes a valid path component, what
constitutes a valid kebab-case slug, and how conformance is enforced at the boundary.

---

## Requirement: Cross-Platform Name Safety

Every vault path component (folder name, file stem — not extension) must satisfy
the base safety rules. A violation is rejected at the commit-gate hook; existing
names are grandfathered.

Rules (authoritative set, mirrored to `naming-rules.json`):

| Rule | Constraint |
|---|---|
| Non-empty | Name must not be empty |
| NFC normalisation | Name must be Unicode NFC-normalised |
| No leading dot | Name must not start with `.` |
| No leading/trailing space | Name must not have leading or trailing whitespace |
| No trailing dot | Name must not end with `.` |
| No control characters | No characters with code point < 32 |
| No forbidden characters | Must not contain: `[ ] # ^ \| \\ / : * " ? < >` |
| No reserved device names | Must not be `CON`, `PRN`, `AUX`, `NUL`, `COM1`–`COM9`, `LPT1`–`LPT9` (Windows device names) |
| Max 255 UTF-8 bytes | Path component must not exceed 255 bytes when encoded as UTF-8 |

#### Scenario: Validator rejects each forbidden class
- **WHEN** `vault_naming.py --check` is called with each of: `bad:name`, `pipe|x`, `has#hash`, `CON`, `.hidden`, `trail ` (trailing space)
- **THEN** it exits 1 for each and prints an INVALID message

#### Scenario: Validator accepts valid names
- **WHEN** `vault_naming.py --check` is called with `my-insight` and `2026-06-11`
- **THEN** it exits 0 for each

---

## Requirement: Kebab-Case Slug (Machine-Generated Names)

Machine-generated names — effort folder slugs in `30-Sites/` and `70-Tailings/`,
and Treasury note file stems in `40-Treasury/` — must additionally be valid
kebab-case slugs:

Pattern: `^[a-z0-9]+(?:-[a-z0-9]+)*$`

- Lowercase ASCII letters and digits only
- Hyphens allowed as separators (not at start, end, or doubled)
- No uppercase, no underscores, no spaces

#### Scenario: Slug validator is stricter than base validator
- **WHEN** `is_valid_slug` is called
- **THEN** it returns `True` for `a-b-c` and `False` for `My-Insight` (uppercase) and `a--b` (doubled hyphen)

---

## Requirement: Enforcement at the Boundary (INV-11)

Name conformance is enforced **deterministically at the boundary**, not by trusting
producers to comply:

1. **Refine executor** (`vault-refine-execute.py`): validates `target_note` stem with
   `is_valid_slug()` before any Treasury write. A non-conforming name is rejected and
   the proposal is skipped — no write occurs.
2. **Commit-gate hook** (`99-Operations/hooks/pre-commit`): validates the stem of every
   newly added or renamed `.md` file before commit. Blocks the commit on violation.
   Fires on every commit: human, script, agent, or sync tool.

Dual enforcement means a non-conforming name is rejected even if injected directly
into `_refine-approved/`, bypassing the harness.

#### Scenario: Commit gate blocks a non-conforming name
- **WHEN** a file named `bad:name.md` is staged and committed
- **THEN** the pre-commit hook exits 1 with an INV-11 message and the commit is blocked

#### Scenario: Commit gate allows a conforming name
- **WHEN** a file named `good-name.md` is staged and committed
- **THEN** the pre-commit hook exits 0 and the commit proceeds

#### Scenario: Executor and harness both enforce at the boundary
- **WHEN** a fixture proposal with `target_note` stem `Bad:Name` is placed in `_refine-approved/`
- **THEN** the executor rejects it and writes nothing
- **WHEN** the same non-conforming stem is passed through the Phase 3 harness
- **THEN** the harness also rejects it locally before deposit (dual-boundary enforcement)

---

## Requirement: Language-Neutral Mirror

The `vault_naming.py` module, when run with no arguments, writes
`99-Operations/schemas/naming-rules.json` — a language-neutral mirror of the
`RULES` dict for non-Python consumers (future JS/Obsidian plugin, n8n node).

The JSON must contain: `slug_pattern`, `forbidden_chars`, `reserved_names`.

#### Scenario: naming-rules.json is generated correctly
- **WHEN** `python3 ~/bin/vault_naming.py` is run with no arguments
- **THEN** it writes `naming-rules.json` containing `slug_pattern`, `forbidden_chars`, and `reserved_names`
