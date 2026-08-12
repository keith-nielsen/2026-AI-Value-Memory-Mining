<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: An Architecture Decision Record Citation Resolves

Architecture Decision Records (ADRs) SHALL be numbered contiguously from `0001` with no gap and no
duplicate. Continuous integration (CI) SHALL derive the expected set from the records present rather
than from a literal range, because a hardcoded range is correct only on the day it is written and
passes silently thereafter while validating a shrinking fraction of the corpus.

Every ADR identifier cited anywhere in the repository SHALL resolve to a record that exists. A
citation is an assertion that a decision was recorded; where the record does not exist, the citation
documents a deliberation that no reader can inspect and cannot be distinguished from one that never
happened.

A citation to a record that does not yet exist SHALL be permitted **only** within a change directory
under `openspec/changes/`, excluding its archive. A change directory is a proposal and is forward-looking
by nature; specifications, workflow configuration, README, contributor documentation, and archived
changes are records, and a record SHALL resolve. An archived change is a record for this purpose:
a forward reference that was permitted while the change was live SHALL fail once it is archived,
because by then the record it promised is owed.

The check SHALL report the citing file and line for each unresolved identifier, because an identifier
alone does not locate the assertion that must be corrected.

#### Scenario: An identifier is cited in workflow configuration but no record exists
- **WHEN** CI configuration cites an ADR identifier that resolves to no file
- **THEN** the check fails and names the citing file and line
- **THEN** the failure is reported as an unresolved citation, distinctly from a numbering gap

#### Scenario: A live change declares a record it owes
- **WHEN** a change directory outside the archive cites an ADR identifier that does not yet exist
- **THEN** the check passes for that citation
- **THEN** no annotation is required on the citation, because its location establishes that it is a proposal

#### Scenario: A change carrying a forward reference is archived
- **WHEN** a change directory containing an unresolved ADR citation is moved into the archive
- **THEN** the check fails for that citation
- **THEN** the failure names the record that is now owed

#### Scenario: A record is added out of sequence
- **WHEN** a new ADR is added whose number leaves an earlier number unused
- **THEN** the contiguity check fails and names the missing number
- **THEN** the result does not depend on any literal range held in the check itself
