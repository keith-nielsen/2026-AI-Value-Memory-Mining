## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Language-Neutral Mirror

The `vault_naming.py` module, when run with no arguments, MUST write
`99-Operations/schemas/naming-rules.json` — a language-neutral mirror of the
`RULES` dict for non-Python consumers (future JS/Obsidian plugin, n8n node).

The JSON MUST contain: `slug_pattern`, `forbidden_chars`, `reserved_names`, `min_hyphen_tokens`,
`exempt_names`, `exempt_globs`, and `exempt_rationale_doc`.

#### Scenario: naming-rules.json is generated correctly
- **WHEN** `python3 ~/bin/vault_naming.py` is run with no arguments
- **THEN** it writes `naming-rules.json` containing `slug_pattern`, `forbidden_chars`, `reserved_names`, `min_hyphen_tokens`, `exempt_names`, `exempt_globs`, and `exempt_rationale_doc`
