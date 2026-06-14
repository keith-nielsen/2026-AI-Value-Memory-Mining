<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Core Module

- [x] 1.1 Write `99-Operations/scripts/naming.md` literate meta-script containing `vault_naming.py`
- [x] 1.2 Declare `RULES` dict with `slug_pattern`, `forbidden_chars`, `reserved_names`, `max_bytes`, `normalization`
- [x] 1.3 Implement `validate_name(name)` → list of violation strings
- [x] 1.4 Implement `is_valid_slug(slug)` → bool (stricter: applies slug pattern + base rules)
- [x] 1.5 Implement `slugify(text)` → best-effort kebab-case ASCII slug
- [x] 1.6 Implement `__main__` with `--check NAME` flag (exit 1 on violation) and no-args JSON emit

## 2. Pre-Commit Hook

- [x] 2.1 Write `99-Operations/scripts/pre-commit.md` literate meta-script
- [x] 2.2 Hook filters `git diff --cached --name-only --diff-filter=AR` (added/renamed only)
- [x] 2.3 Hook calls `vault_naming.py --check <stem>` for each `.md` file
- [x] 2.4 Hook blocks commit (exit 1) on any violation; prints INV-11 message

## 3. Integration

- [x] 3.1 Update `lint.md` to import `validate_name` and `is_valid_slug` from `vault_naming`
- [x] 3.2 Update `refine-execute.md` to call `is_valid_slug(note.stem)` before Treasury write
- [x] 3.3 Run render to deploy `vault_naming.py` to `~/bin/` and `chmod +x` the hook
- [x] 3.4 Run module once to emit `99-Operations/schemas/naming-rules.json`

## 4. Acceptance Verification (A1.8, A1.9)

- [x] 4.1 `vault_naming.py --check my-insight` → exit 0
- [x] 4.2 `vault_naming.py --check bad:name` → exit 1
- [x] 4.3 `vault_naming.py --check CON` → exit 1 (reserved device name)
- [x] 4.4 `is_valid_slug("a-b-c")` → True; `is_valid_slug("My-Insight")` → False
- [x] 4.5 Commit of `bad:name.md` blocked by hook; commit of `good-name.md` succeeds
- [x] 4.6 `naming-rules.json` contains `slug_pattern`, `forbidden_chars`, `reserved_names`
