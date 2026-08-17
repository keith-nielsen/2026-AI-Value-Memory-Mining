<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: A Capability State Is A Single Word Naming What Was Found

Every state a capability report emits SHALL be a single word containing no whitespace, so that a
consumer can compare it without parsing prose.

Every such state SHALL be declared as a named constant in one place. States inlined at their print
sites have no discoverable legal set, and a new state can then be introduced by a typo without any
check observing it. An automated check SHALL assert that every state the report emits belongs to the
declared set.

A state SHALL name **what was found in this process**, and SHALL NOT name what is possible in the
world. The test is whether the token could be falsified by something outside the process that emitted
it: a state that could be is the wrong word. A capability report is read at the moment its reader has
no other information, so a token that overstates its own scope is not merely imprecise — it is the
specific error such a report exists to prevent.

Where a row reports a credential, the states SHALL distinguish three conditions: a usable credential,
the absence of a usable credential, and the absence of the tool itself. The first two describe the
credential; the third describes the tool, and SHALL be understood to leave the credential state
**unknown** rather than negative. A report that collapses the third condition into the second obliges
its reader to distinguish two different remedies from one token.

A row SHALL be named for what it measures rather than what may be inferred from it. Where a check
inspects a credential, the row names the credential; whether an operation is thereby possible is a
conclusion, and belongs in the column that already records who may run the operation.

Retiring a state token SHALL be preferred to narrowing one. A token reused with a tighter meaning
makes every previously-emitted transcript ambiguous, because nothing in the older output records which
meaning was in force.

#### Scenario: A state is emitted as a single word
- **WHEN** the capability report emits any state
- **THEN** that state contains no whitespace
- **THEN** it is one of the declared state constants

#### Scenario: An undeclared state is introduced
- **WHEN** a state is emitted that is not in the declared set
- **THEN** the automated check fails
- **THEN** the failure names the offending state

#### Scenario: A credential row reports three distinguishable conditions
- **WHEN** the tool is present and its credential is usable
- **THEN** the state reports the credential as usable
- **WHEN** the tool is present and no usable credential exists
- **THEN** the state reports the credential as absent
- **WHEN** the tool itself is not present
- **THEN** the state reports the tool as absent, distinctly from the credential case

#### Scenario: A row is named for its measurement
- **WHEN** a row is produced by inspecting a credential
- **THEN** the row is named for the credential
- **THEN** it is not named for an operation whose possibility is inferred from it

#### Scenario: A state token would be falsified from outside the process
- **WHEN** a candidate state asserts what is possible rather than what was found
- **THEN** it is rejected as a state name
- **THEN** the finding is expressed as what this process observed

### Requirement: A Capability Report Distinguishes Inspection From Attempt

For every channel it reports, the capability report SHALL record whether the channel was **attempted**
or whether a **precondition was inspected**, and SHALL make that distinction visible to its reader.

Where a channel was attempted, the report SHALL name the channel actually exercised. Two mechanisms
may carry the same label while traversing different paths — an operation invoked as a subprocess does
not necessarily cross a guard that inspects a shell command line — and a report that names only the
outcome cannot expose that divergence. Naming the exercised channel makes a future divergence visible
in the output rather than discoverable only by reading the source.

The report SHALL NOT encode evidence, channel, or reason inside a state token. A state answers what was
found; how it was found is a separate fact, and combining them produces a value that is neither
readable as a word nor parseable as a field.

The report SHALL offer a machine-readable form. A fixed-width table is a presentation, and a consumer
that parses it binds to column widths, so every cosmetic change becomes a breaking one. With a
machine-readable form available, the human table remains free to change.

#### Scenario: A channel that was exercised is reported as attempted
- **WHEN** the report includes a channel it actually exercised
- **THEN** the evidence records that the channel was attempted
- **THEN** the evidence names the channel that was exercised

#### Scenario: A channel whose precondition was inspected is not reported as attempted
- **WHEN** the report includes a channel for which only a precondition was read
- **THEN** the evidence records an inspection rather than an attempt
- **THEN** the reader can distinguish it from a channel that was exercised

#### Scenario: A consumer reads the report without parsing the table
- **WHEN** the report is requested in its machine-readable form
- **THEN** each channel is emitted with its state, its runner, its authority, and its evidence as
  separate fields
- **THEN** no field requires splitting a human-formatted line to recover
