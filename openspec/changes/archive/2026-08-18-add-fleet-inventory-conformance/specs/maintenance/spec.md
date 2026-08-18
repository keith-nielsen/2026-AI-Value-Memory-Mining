<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: The Script Inventory Matches The Deployed Fleet

Any document that enumerates the Layer-0 fleet — the `maintenance` Script Inventory table and the
repository README's operational-script table — SHALL name **exactly** the set of script notes present
in `99-Operations/scripts/`, with no member missing and none named that does not exist. Any stated
count SHALL equal the number of rows presented.

This SHALL be mechanically verified, and the verification SHALL report **both directions**: a note
with no row, and a row with no note. A check that detects only omissions passes on a table naming a
script deleted a month earlier.

Three checks govern the fleet, and between them they leave one seam: `render` and `reconcile` govern
note → deployed, and `template-parity` governs template → live vault, but **nothing governs spec →
note**. A script can therefore ship, deploy, and enforce an invariant while absent from the
specification that governs it, indefinitely and with every build green. That is how INV-7 secret-scan
enforcement shipped on 2026-07-28 and remained absent from this specification, while a README
simultaneously stated a count disagreeing with its own table.

An absence has no string to match, so no search-based sweep can find it. Only an enumeration compared
against ground truth can. An enumeration maintained by hand is a duplicate of a machine-checkable
fact, and drifts the moment anything ships.

#### Scenario: A shipped script missing from the inventory is caught
- **WHEN** a script note exists in `99-Operations/scripts/` with no row in an enumeration
- **THEN** the conformance check fails, naming the missing note

#### Scenario: An inventory naming a nonexistent script is caught
- **WHEN** an enumeration names a script note that does not exist
- **THEN** the conformance check fails, naming the phantom entry

#### Scenario: A stated count disagreeing with its own table is caught
- **WHEN** an enumeration's stated count differs from the number of rows it presents
- **THEN** the conformance check fails, naming both numbers

### Requirement: Declared Cadence Matches Declared Runtime

No document SHALL state a schedule for a script whose note does not declare a `cron` runtime, and no
document SHALL instruct a reader to edit a `schedule:` field.

`render` deploys code and marks it executable; it installs no schedules, and nothing reads a
`schedule:` field. A cadence a script cannot honour is a decorative declaration, and instructing a
reader to edit an unread field teaches that the documentation is approximate — the same lesson a
documented absolute contradicted by practice teaches.

#### Scenario: A cron expression against a manual script is caught
- **WHEN** a live document states a schedule for a note whose `runtime:` is not `cron`
- **THEN** the cadence conformance check fails, naming the document and the note

### Requirement: Every Fleet Member Has Behavioural Coverage

Every member of the Layer-0 fleet SHALL be exercised by at least one behavioural test that invokes it
as a real subprocess and asserts an observable outcome.

Detection-only members SHALL additionally be asserted to write nothing and create no commit, because
for a tool whose correct behaviour is to report, a silent no-op and a correct report are
indistinguishable from an exit code alone.

An uncovered fleet member is code whose relocation, refactor or retirement nothing would catch.

#### Scenario: A detection-only member is proven not to mutate
- **WHEN** a detection-only fleet member runs against a fixture vault
- **THEN** it reports its findings, and the vault's git status and commit count are unchanged
