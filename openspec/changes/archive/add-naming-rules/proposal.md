<!-- SPDX-License-Identifier: Apache-2.0 -->
## Why

The vault uses machine-generated path components (effort folder slugs, Treasury note
stems) that must be safe across operating systems, Obsidian's wikilink parser, YAML
parsers, and shell scripts. Without a shared ruleset enforced at a hard boundary,
a single non-conforming character (a `:` or `|` in a filename) silently breaks
wikilinks, corrupts YAML front-matter parsing, and causes cross-OS sync failures.

The ruleset also needs a language-neutral mirror (JSON) so that future non-Python
consumers (a JS Obsidian plugin, an n8n automation node) can validate names without
duplicating the rules.

## What Changes

### New Capabilities

- `naming-rules`: A single-source-of-truth Python module (`vault_naming.py`)
  declaring the forbidden-character set, reserved device names, NFC-normalisation
  requirement, and kebab-slug pattern. Enforced at two hard boundaries: the refine
  executor (rejects non-conforming `target_note` stems before any Treasury write)
  and the pre-commit hook (blocks non-conforming file names before any commit,
  regardless of actor).

## Impact

- `openspec/specs/naming-rules/spec.md` is introduced (this change's delta spec)
- `vault-template/99-Operations/scripts/naming.md` is introduced (literate meta-script)
- `vault-template/99-Operations/scripts/pre-commit.md` is introduced (commit-gate hook)
- `vault-template/99-Operations/scripts/lint.md` imports the validator
- `vault-template/99-Operations/scripts/refine-execute.md` calls `is_valid_slug()` at the executor boundary
- `vault-template/99-Operations/schemas/naming-rules.json` is generated on first render
- INV-11 (Name conformance) is the governing invariant for this capability
