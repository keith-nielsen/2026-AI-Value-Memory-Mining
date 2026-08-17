<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: An Outward Command Is Checked Against The Driver's Emission

Where a lifecycle driver emits a command for execution, it SHALL record that command, together with
the step and branch it was derived for and an expiry, in a location the outbound guard can read
without network access.

The outbound guard SHALL classify an outward command by its **effective target**, resolved from the
command text as it already resolves a leading directory change, an explicit repository argument, and
an explicit remote-repository selector. Three zones SHALL be distinguished: the deployed vault, a
repository whose lifecycle a driver governs, and everywhere else.

Where the effective target is the deployed vault, the existing refusal SHALL apply unchanged. Where
the effective target is elsewhere, the existing confirmation SHALL apply unchanged, so that a one-off
outward command against an ungoverned repository remains possible without a driver.

Where the effective target is a governed repository and the command is **byte-identical** to a live
recorded emission for the current branch, the guard SHALL allow it without a confirmation prompt.
Where it is not, the guard SHALL raise the existing confirmation and SHALL additionally report the
difference between the command presented and the command recorded.

**The record SHALL only ever downgrade a confirmation to an allowance. It SHALL NOT create a
refusal.** Every failure of the mechanism — an absent record, an expired record, a record written for
another branch, an unparseable record, or a fault in the comparison — SHALL fall through to the
confirmation that is raised today. A control that can only relax an existing prompt cannot make the
system stricter than it was, and this property is what permits it to ship without a burn-in period.

A recorded emission SHALL expire, and SHALL be discarded when the lifecycle it belongs to completes.
A record that outlives its step is an authorisation left lying where a later, different command can
match it.

Reporting a difference SHALL name what differs rather than merely stating that something does.
Mangled commands differ in ways the author cannot see by re-reading — an unexpanded variable, a
prefix that displaces a leading directory change — and a guard that reports only a mismatch obliges
its reader to find the cause at the moment they have already demonstrated they cannot.

#### Scenario: The emitted command is run verbatim
- **WHEN** an outward command targets a governed repository
- **AND** it is byte-identical to a live recorded emission for the current branch
- **THEN** the guard allows it without raising a confirmation
- **THEN** it reports which recorded step authorised it

#### Scenario: The emitted command is run with modifications
- **WHEN** an outward command targets a governed repository
- **AND** a live emission exists but the command text differs from it
- **THEN** the guard raises the confirmation that is raised today
- **THEN** it reports the difference between the presented and recorded commands

#### Scenario: No emission has been recorded
- **WHEN** an outward command targets a governed repository
- **AND** no live recorded emission exists
- **THEN** the guard raises the confirmation that is raised today
- **THEN** it does not refuse the command

#### Scenario: An outward command targets an ungoverned repository
- **WHEN** an outward command's effective target is neither the vault nor a governed repository
- **THEN** the guard behaves exactly as it does today
- **THEN** no recorded emission is required for it to proceed

#### Scenario: An outward command targets the vault
- **WHEN** an outward command's effective target is the deployed vault
- **THEN** the guard refuses it
- **THEN** the presence or absence of a recorded emission does not change that outcome

#### Scenario: The record is expired or written for another branch
- **WHEN** a recorded emission exists but has expired, or names a branch other than the current one
- **THEN** the guard treats it as absent
- **THEN** the confirmation raised today is raised

### Requirement: A Downgrade Record Is Forgeable And Says So

The recorded emission SHALL be writable by the same agent whose commands it governs, and this
limitation SHALL be documented wherever the mechanism is described.

The mechanism therefore protects against **error**, not against **intent**. A mistaken or mangled
command does not also produce a matching record, which is the property the mechanism relies on; an
agent that chose to write its own record could authorise its own command. This is consistent with the
outbound rail's stated posture — a safe default and a governed guarantee, not a physical
impossibility, and a tripwire for a cooperating agent.

It is stated as a requirement rather than left as a remark because an unstated limitation on a control
is indistinguishable from a control that does not have it. This repository has previously had to
retract enforcement claims that described protection it did not possess, and the correction is to
record the gap where the mechanism is described, not to describe the mechanism more favourably.

An allowance granted by this mechanism SHALL therefore be reported as a match against a record, and
SHALL NOT be reported as an authorisation, an approval, or a verification.

#### Scenario: The mechanism is described in documentation
- **WHEN** the emission record is described in a specification, decision record, or script note
- **THEN** the description states that the record is writable by the agent it governs
- **THEN** it states that the mechanism addresses error rather than intent

#### Scenario: An allowance is reported to the reader
- **WHEN** the guard allows a command because it matched a recorded emission
- **THEN** the report states that the command matched a record
- **THEN** the report does not claim the command was authorised or verified
