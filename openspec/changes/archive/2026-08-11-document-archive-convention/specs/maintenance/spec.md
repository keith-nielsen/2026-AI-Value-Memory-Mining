<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: A Change Is Archived On Its Own Branch

An OpenSpec change SHALL be archived on the feature branch that carries it, within the same pull
request that merges it. Archiving moves `openspec/changes/<slug>/` to
`openspec/changes/archive/<YYYY-MM-DD>-<slug>/`, applies the change's delta into the corresponding
`openspec/specs/` capability spec, and records the CHANGELOG entry. The archive step SHALL precede
opening the pull request.

Archiving is part of the change, not follow-up work. A change that merges unarchived leaves
`openspec/specs/` describing a state the repository has already left, and owes a second pull request to
close the gap.

Where another in-flight change carries a delta against the **same** capability spec, the archive SHALL
be deferred and applied in merge order. Applying two deltas to one spec file from independently
prepared branches allows the later archive to overwrite the earlier one's requirements without conflict
— the changes touch the same file but need not touch the same lines. This exception SHALL be recorded
with the name of the concurrent change it defers to, so that a second pull request is a stated
consequence rather than an unexplained one.

The convention SHALL be discoverable from the contributor documentation and SHALL NOT rest solely in
per-change task files, which are not read at the moment the decision is made.

Where this convention is restated or re-derived, the derivation SHALL be a pasted command transcript
over the merge history, not an inference from commit subjects: a dedicated archive commit does not
imply a separate pull request.

#### Scenario: A change is ready to merge
- **WHEN** a change's tasks are complete and its pull request has not yet been opened
- **THEN** the change directory is moved into the archive, its delta is applied to the capability spec,
  and the CHANGELOG entry is recorded on that same branch
- **THEN** the pull request that merges the change also carries its archive

#### Scenario: A concurrent change touches the same capability spec
- **WHEN** another in-flight change carries a delta against the same capability spec
- **THEN** the archive is deferred and applied in merge order
- **THEN** the deferral names the concurrent change, and the resulting second pull request is recorded
  as the accepted cost of the exception

#### Scenario: A change merged without being archived
- **WHEN** a change reaches `main` with no archive
- **THEN** a second pull request to archive it is owed and is tracked as owed
- **THEN** the capability spec is understood to be lagging the repository until that pull request lands
