<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: The Capability Probe Measures A Declared Estate

The capability probe SHALL take its subjects from **declared roots**, and SHALL NOT derive its subject
from the working directory. The estate has known members whose locations are configuration, not
discoveries: the vault (`VAULT_ROOT`) and the framework repository (`FRAMEWORK_ROOT`). A probe that
infers its subject from where the shell happens to be will silently measure the wrong thing and
report the result with the same confidence as a correct one.

Each member SHALL be evaluated against **that member's expected state**, not against a single
repository-shaped template. A finding SHALL be a deviation from what that member is supposed to be.

The vault is private by default and holds no remote (INV-14). Absence of a remote in the vault SHALL
be reported as the invariant **holding**, and SHALL NOT be reported as a failed channel. Where a
remote is **present** on the vault, the probe SHALL report a **violation** naming it, because that is
the condition INV-14 exists to prevent.

The trigger SHALL be presence, not demonstrated pushability. Establishing that a remote accepts a push
means attempting one from the vault — the act INV-14 forbids, and which the outbound guard refuses. A
probe may not commit the breach it is checking for. Presence is also the earlier signal: a remote that
lacks credentials today is one credential away from being pushable, and the invariant is already
broken at the moment the remote exists.

Where `FRAMEWORK_ROOT` is not declared, the estate SHALL be reported as one member: the vault layers
measured as normal, and every framework-repository layer reported `UNDECLARED`, distinctly from
`FAILED`. A deployed vault without the framework repository alongside it is a supported configuration,
not an error state.

The probe SHALL report which roots it measured, so that its output cannot be read as describing a
subject it did not examine.

The probe SHALL verify that the vault's protected subtrees are actually protected, by **attempting a
write** into each subtree governed by an autonomy ban (INV-4, INV-5) and reporting whether that write
was refused. A protection that is assumed rather than exercised is not evidence, and the guard is
enforced outside the vault's own filesystem, so it can lapse with no event the vault can observe. This
attempted write is operator-specified startup verification, and is therefore not an autonomous write.

A refused write SHALL be reported as the protection holding. A write that **succeeds** SHALL be
reported as a protection failure, because the subtree is writable and the invariant is resting on
nothing for the remainder of the session.

Where the probe's own write succeeds, the probe SHALL attempt to remove the artifact it created and
SHALL check the result of that removal. Where removal fails, the probe SHALL report the absolute path
of the residue distinctly from the protection failure itself, because an artifact left inside a
protected subtree is a second and separate defect.

Every failing outcome of this verification SHALL be reported together with the operator action it
calls for. A protection check that reports only a verdict obliges its reader to derive the remedy at
exactly the moment the governing assumption has been shown false.

Modes that operate on a single repository — pull-request routing, readiness, and precondition
assertion — SHALL continue to derive their subject from the working directory, which is correct for
them.

#### Scenario: The probe is run from the vault
- **WHEN** the capability probe runs with the working directory inside the vault
- **THEN** it measures the declared estate roots rather than the working directory
- **THEN** the framework-repository channels are measured against `FRAMEWORK_ROOT`, not against the vault

#### Scenario: A remoteless vault is reported
- **WHEN** the vault has no configured remote
- **THEN** the probe reports INV-14 as holding
- **THEN** it does not report a failed remote read, a failed push, or an unresolved repository slug

#### Scenario: A vault has acquired a remote
- **WHEN** the vault has any configured remote
- **THEN** the probe reports an INV-14 violation naming the remote
- **THEN** the violation is reported as a finding, not as a working capability
- **THEN** the probe does not attempt a push to establish whether the remote would accept one

#### Scenario: The framework repository is not declared
- **WHEN** `FRAMEWORK_ROOT` is unset
- **THEN** every framework-repository layer is reported `UNDECLARED`
- **THEN** no layer is reported `FAILED`, because an absent declaration is not a measured failure

#### Scenario: A protected subtree refuses the probe's write
- **WHEN** the probe attempts a write into a subtree under an autonomy ban and the write is refused
- **THEN** the protection is reported as holding for that subtree
- **THEN** no operator action is prescribed, because this is the expected result

#### Scenario: A protected subtree accepts the probe's write
- **WHEN** the write into a subtree under an autonomy ban succeeds
- **THEN** the probe reports a protection failure naming the subtree
- **THEN** the report states that the invariant is unenforced for the session and names the operator
  action, because the guard is enforced outside the vault and cannot be repaired from within it

#### Scenario: The probe cannot remove the artifact it created
- **WHEN** the probe's write succeeds and the removal of that artifact fails
- **THEN** the probe reports the residue and its absolute path separately from the protection failure
- **THEN** the report names the removal the operator must perform and the check confirming the residue
  was never committed

### Requirement: A Probe Reports Diagnoses, Not Internal Errors

A probe SHALL report, in its state column, a diagnosis of the channel it measured. Text produced by
the language runtime — exception messages, formatting errors, tracebacks — SHALL NOT be presented as a
channel's state, because a reader cannot distinguish a broken channel from a broken probe, and will
attribute the defect to the environment.

A failed precondition SHALL be reported as a precondition failure and SHALL NOT be routed through the
path that reports channel results. Where a guard substitutes a placeholder for an unavailable value,
that placeholder SHALL NOT reach code that assumes the value was obtained.

Where a probe quotes the output of a subprocess it invoked, it SHALL attribute the quotation to that
subprocess and SHALL select the line by relevance to the cause. Selecting a line by position yields
trailing remediation boilerplate in place of the diagnosis, and an unattributed fragment reads as
corrupted output.

#### Scenario: A required value could not be resolved
- **WHEN** an identifier a channel depends on cannot be resolved
- **THEN** the probe reports the unresolved precondition and names it
- **THEN** it does not attempt the dependent channel and does not report that channel as failed

#### Scenario: The probe's own code raises
- **WHEN** an exception is raised inside the probe rather than by the channel under test
- **THEN** the report distinguishes a probe defect from a channel result
- **THEN** no runtime exception text appears in a state column

#### Scenario: A subprocess error is quoted
- **WHEN** the probe quotes stderr from a command it ran
- **THEN** the quotation is attributed to that command
- **THEN** the line quoted is the one naming the cause, not the last line of the output
