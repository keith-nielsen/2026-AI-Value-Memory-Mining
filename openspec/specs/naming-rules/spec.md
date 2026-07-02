---
capability: naming-rules
protects: [INV-11]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: naming-rules

## Purpose

Define the vault naming ruleset (INV-11): what constitutes a valid path component,
what constitutes a valid kebab-case slug, and how conformance is enforced at the
boundary.
## Requirements
### Requirement: Cross-Platform Name Safety

Every vault path component (folder name, file stem — not extension) MUST satisfy
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

### Requirement: Kebab-Case Slug (Machine-Generated Names)

Machine-generated names MUST additionally be valid kebab-case slugs — this applies to
effort folder slugs in `30-Sites/` and `70-Tailings/`, and Treasury note file stems
in `40-Treasury/`:

Pattern: `^[a-z0-9]+(?:-[a-z0-9]+)*$`

- Lowercase ASCII letters and digits only
- Hyphens allowed as separators (not at start, end, or doubled)
- No uppercase, no underscores, no spaces

#### Scenario: Slug validator is stricter than base validator
- **WHEN** `is_valid_slug` is called
- **THEN** it returns `True` for `a-b-c` and `False` for `My-Insight` (uppercase) and `a--b` (doubled hyphen)

---

### Requirement: Enforcement at the Boundary (INV-11)

Name conformance MUST be enforced deterministically at the boundary, not by trusting
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

### Requirement: Language-Neutral Mirror

The `vault_naming.py` module, when run with no arguments, MUST write
`99-Operations/schemas/naming-rules.json` — a language-neutral mirror of the
`RULES` dict for non-Python consumers (future JS/Obsidian plugin, n8n node).

The JSON MUST contain: `slug_pattern`, `forbidden_chars`, `reserved_names`, `min_hyphen_tokens`,
`exempt_names`, `exempt_globs`, and `exempt_rationale_doc`.

#### Scenario: naming-rules.json is generated correctly
- **WHEN** `python3 ~/bin/vault_naming.py` is run with no arguments
- **THEN** it writes `naming-rules.json` containing `slug_pattern`, `forbidden_chars`, `reserved_names`, `min_hyphen_tokens`, `exempt_names`, `exempt_globs`, and `exempt_rationale_doc`

### Requirement: Token-Minimum Naming (≥3, silo-section-descriptor)

Every `.md` filename stem SHALL carry **at least three hyphen-separated tokens** — three is the
**floor, not the ceiling**. Authors SHALL use **more than three wherever the additional tokens supply
human-meaningful specificity**, because the namespace grows contention-prone as broad topics narrow
and digs reveal sub-sectors needing distinction; richer, more specific names pre-empt the overloading
that would otherwise collide later.

- **System-artifact families** (molds, operational scripts, Catalog indexes, schemas) SHALL use the
  **`silo-section-descriptor`** form, silo (subject) first — e.g. molds `<note-type>-mold-blank`.
- **Content stems** (Claims, Sites, Treasury notes) SHALL be ≥3-token topic slugs; longer is correct
  where it adds specificity (e.g. `swappable-stages-over-coresident-models`).
- **Dailies** (`YYYY-MM-DD`) are exempt (date-named).

This requirement is a **convention** at this stage: it governs new and renamed names through authoring
and review. Existing sub-three-token names are **grandfathered**; each family is brought into
conformance by its own change (molds: v0.1.7). **Mechanical enforcement** — extending `vault_naming.py`,
the commit-gate hook, and `naming-rules.json` to reject sub-three-token stems — is **deferred to a
later change**, sequenced after the families conform (turning on rejection earlier would block commits
on names not yet renamed).

#### Scenario: A new system-artifact name is silo-section-descriptor, ≥3 tokens
- **WHEN** a mold, script, Catalog index, or schema artifact is named or renamed
- **THEN** its stem is silo-first and carries at least three hyphen-separated tokens (e.g. `daily-mold-blank`)

#### Scenario: More tokens where specificity warrants
- **WHEN** a content topic narrows, or a dig reveals a sub-sector needing distinction
- **THEN** the stem carries more than three tokens to stay unambiguous (e.g. `swappable-stages-over-coresident-models`) rather than overloading a shorter name

#### Scenario: Dailies are exempt
- **WHEN** a daily note is named `YYYY-MM-DD`
- **THEN** the token-minimum does not apply

#### Scenario: Existing sub-three-token names are grandfathered at the convention stage
- **WHEN** this change is in effect and a pre-existing two-token name (e.g. `obsidian-usage`) is present
- **THEN** it is not rejected — the floor applies to new/renamed names by convention, and mechanical enforcement is deferred to a later change

### Requirement: Special-File Exemptions (INV-11)

A small set of filenames SHALL be **exempt** from the kebab-case and ≥3-token content rules because an
external tool or a universal convention depends on their **exact** name. The exemptions are data in the
`naming-rules` SSOT, mirrored to `naming-rules.json`:

- **`exempt_names`** — exact filenames: `README.md`, `LICENSE`, `LICENSE.md`, `CLAUDE.md`, `AGENTS.md`,
  `MEMORY.md`, `.gitignore`, `.gitkeep`, `.gitattributes`, `config.env`, `config.defaults.env`,
  `config.env.example`.
- **`exempt_globs`** — basename patterns: `*.example`, dailies `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md`.

`is_exempt(filename)` matches on the **filename (basename)**; a stem matching `exempt_names` or
`exempt_globs` SHALL be skipped by the kebab/≥3-token checks before they apply. Editor state under
`.obsidian/` is **out of scope via `.gitignore`** (editor-owned; the linter never traverses it), not a
per-name exemption — so no path-shaped glob is used. Each exemption is justified by its dependency class
(tool-mandated harness/git/config/pipeline vs. industry convention vs. ease-of-use) in
`docs/naming-exemptions-rationale.md` (pointed to by `exempt_rationale_doc`).

Consistent with ADR-0015, mechanical ≥3-token/kebab **rejection remains deferred**; this requirement
defines the exemption gate the linter honors **now**, so enabling that rejection later is switch-on-safe.

#### Scenario: A tool-mandated / convention filename is exempt
- **WHEN** the linter evaluates `README.md`, `CLAUDE.md`, `config.env.example`, or a daily `2026-07-02.md`
- **THEN** `is_exempt` returns true and the kebab/≥3-token content rules are not applied to it

#### Scenario: A normal content stem is not exempt
- **WHEN** the linter evaluates a content note stem such as `some-note` or a two-token `obsidian-usage`
- **THEN** `is_exempt` returns false (grandfathering, not exemption, governs pre-existing sub-3 names)

#### Scenario: Editor state is out of scope, not exempted
- **WHEN** `.obsidian/app.json` exists
- **THEN** it is excluded from naming governance by `.gitignore` (the linter does not traverse `.obsidian/`), and `is_exempt('app.json')` is false — the exemption set carries no path-shaped globs

