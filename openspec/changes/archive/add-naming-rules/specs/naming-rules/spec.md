<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Cross-Platform Name Safety
All vault path components must pass the base safety rules (non-empty, NFC, no forbidden
chars, no reserved device names, ≤255 UTF-8 bytes, no leading dot or trailing space/dot).

#### Scenario: Validator rejects each forbidden class
- **WHEN** `vault_naming.py --check` receives a name with a forbidden character, reserved name, or format violation
- **THEN** it exits 1 and prints an INVALID message identifying the violation

### Requirement: Kebab-Slug Enforcement for Machine-Generated Names
Effort folder slugs and Treasury note stems must additionally match `^[a-z0-9]+(?:-[a-z0-9]+)*$`.

#### Scenario: Slug validator rejects uppercase and doubled hyphens
- **WHEN** `is_valid_slug` is called with `My-Insight` or `a--b`
- **THEN** it returns False

### Requirement: Dual-Boundary Enforcement at Executor and Hook
- **WHEN** a non-conforming name reaches either the refine executor or the pre-commit hook
- **THEN** it is rejected; no write or commit proceeds
