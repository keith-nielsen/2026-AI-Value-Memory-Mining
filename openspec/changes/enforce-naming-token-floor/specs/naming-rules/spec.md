<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Token-Floor Enforcement Is Mechanical, Not Conventional

The ≥3-hyphen-token floor and the kebab-case rule SHALL be enforced mechanically for
**newly added or renamed** content names, not merely documented as convention.

`vault_naming.py` SHALL expose `--check-strict FILENAME`, which takes a **basename** (with
extension, because the exemption gate matches full filenames) and applies, in order:
`is_exempt` → `validate_name` → `slug_pattern` → `has_min_hyphen_tokens`.

The existing `--check STEM` (cross-platform safety only) SHALL retain its current contract,
so no existing caller changes behaviour implicitly.

The commit gate SHALL call `--check-strict` and SHALL remain scoped to
`git diff --cached --diff-filter=AR`. Existing names therefore stay grandfathered: the gate
structurally cannot block a commit over a name that was already committed.

This supersedes ADR-0015's staged-enforcement posture. ADR-0015 deferred mechanical
enforcement until **full conformance**; that condition is met (0 non-conforming names across
118 live `.md` files, 103 non-exempt), so the rule moves from convention to mechanism with no
rename pass.

#### Scenario: A newly added sub-3-token content name is blocked

- **WHEN** `20-Claims/xrp.md` is staged as an addition and committed
- **THEN** the commit gate exits non-zero
- **THEN** the message names the file and reports `fewer than 3 hyphen-tokens (INV-11)`
- **THEN** no commit is created

#### Scenario: A newly added conforming name passes

- **WHEN** `20-Claims/xrp-tokenomics-claim.md` is staged as an addition and committed
- **THEN** the gate exits zero and the commit is created

#### Scenario: Convention-mandated names are exempt at the gate

- **WHEN** `README.md` or a daily (`2026-07-17.md`) or an `*.example` file is added
- **THEN** `is_exempt` matches the full filename and the kebab/floor rules are not applied
- **THEN** the gate exits zero

#### Scenario: An existing non-conforming name is grandfathered

- **WHEN** a file whose name predates enforcement is **modified** (status `M`, not `A`/`R`)
- **THEN** `--diff-filter=AR` excludes it from the gate
- **THEN** the commit is created and the name is not re-litigated

#### Scenario: The refine executor rejects a sub-3 target before writing

- **WHEN** an approved proposal names `target_note` `40-Treasury/short-note.md`
- **THEN** the executor's whole-proposal pre-flight records a floor violation
- **THEN** it exits `EXIT_VIOLATION` and **no** file is written under `40-Treasury/`
- **THEN** the executor is never left half-applied by a gate rejection at commit time
