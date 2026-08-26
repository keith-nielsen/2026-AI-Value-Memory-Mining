<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: A Command-Form Rule Is Enforced By A Control That Can Refuse

Where the estate has established that a command form is wrong, that finding SHALL be carried by a
control capable of returning a refusal, and SHALL NOT be carried only by prose — a memory entry, a
runbook imperative, or a caveat in a document.

Prose informs; it cannot decline. A rule which cannot refuse does not bind, and the estate has
measured this in both directions: a memory line instructing the agent to read GitHub through `gh api`
rather than a `gh pr` subcommand was loaded in context and misled the agent twice, while a PreToolUse
hook returning a deny decision was observed to refuse and be obeyed in the same session. The
difference is the capacity to refuse, not the agent's willingness to comply.

A finding restated more emphatically is not a stronger control. Where a rule has already failed as
prose, restating it SHALL NOT be recorded as a remediation.

#### Scenario: A command form known to be wrong is refused rather than described
- **WHEN** the agent invokes a command form the estate has ruled out
- **THEN** the invocation is refused by a control, and the refusal is attributable to that control
  rather than indistinguishable from the command's own failure

### Requirement: A Refusal Names The Working Replacement

A control that refuses a command form SHALL name, in its refusal message, the form that works and
state the reason once.

A refusal carrying only a verdict requires its reader to re-derive the correct form at precisely the
moment they have demonstrated they cannot — the failure the outbound guard already records in its
own redirect hint. A bare denial therefore generates a retry rather than a correction, and a retried
denial teaches the agent that the control is an obstacle rather than an instruction.

#### Scenario: The refusal carries the replacement
- **WHEN** a `gh` invocation is refused for routing through an endpoint this estate has measured
  non-deterministic
- **THEN** the message names the REST equivalent and states the ground for the refusal in terms that
  hold independently of the session's credential state

### Requirement: Command-Form Policy Is Expressed As An Allowlist

A policy over command forms SHALL be expressed as an inversion — the permitted forms enumerated, all
others refused — and SHALL NOT be expressed only as an enumeration of forbidden forms.

An enumeration of forbidden forms lists the failures already suffered. Every form not yet suffered,
including every subcommand the upstream tool ships next, is permitted by omission and will be
discovered by failing rather than by being refused. This is enumeration drift, the defect class the
constitutional diff gate exists to catch; remedying it with a further enumeration reproduces it.

The permitted set SHALL be derived from a measured platform constraint rather than from incident
history, and SHALL include any form on which the estate's own capability instruments depend.

#### Scenario: An unlisted form is refused by default
- **WHEN** a `gh` subcommand that has never previously been ruled out is invoked
- **THEN** it is refused, because it is absent from the permitted set rather than present in a
  forbidden one

#### Scenario: The instrument that measures the channel is not refused by the policy
- **WHEN** the capability probe invokes `gh auth status` to report the credential layer
- **THEN** the invocation is permitted, because a policy that refuses the instrument measuring it
  destroys the evidence the estate relies on

### Requirement: A Fail-Open Control Retains A Fail-Closed Backstop

Where a control is implemented as a hook process whose failure mode is to defer, the estate SHALL
retain a harness-enforced refusal covering the known offenders, and that redundancy SHALL be recorded
as deliberate.

A PreToolUse hook exits zero to defer to normal flow, so a crashed interpreter, a malformed payload,
or an unrendered hook in a fresh clone all resolve to **permit**. The harness `permissions.deny` list
requires no process to start and therefore fails closed. The two mechanisms have opposite failure
directions: general-but-fails-open, and enumerated-but-fails-closed. Retaining both is not
duplication, and SHALL NOT be removed as such by a later simplification.

#### Scenario: The hook is absent and the known offenders are still refused
- **WHEN** the hook is unrendered, crashed, or unregistered, and a known offending form is invoked
- **THEN** the harness deny list refuses it without the hook participating

### Requirement: A PreToolUse Control Binds The Agent's Channel, Not Its Subprocesses

A PreToolUse command guard SHALL be documented as binding the command the agent invokes, and SHALL
NOT be represented as binding commands spawned by processes that command starts.

The hook receives the text of the tool call. A fleet script launched by that call may invoke the
guarded tool internally, and those invocations are never presented to the hook. A control described
without this boundary will be credited with coverage it does not have — the same overclaim the
estate's preflight scorecard was written to bound.

#### Scenario: An internal invocation is outside the control's reach
- **WHEN** a fleet script invoked through the Bash channel itself shells out to the guarded tool
- **THEN** the hook does not observe that invocation, and the control's documentation states this
  boundary rather than leaving it to be discovered

### Requirement: A Text-Matching Control Is Declared A Tripwire, Not A Barrier

A control implemented by matching command text SHALL declare its threat model as a cooperating agent,
and SHALL NOT be represented as preventing deliberate evasion.

Composition, indirection through a shell variable, and encoding all defeat text matching. The estate
already records this for the INV-14 matcher and reaches the same conclusion here: the failure being
defended against is the agent **forgetting**, not the agent **evading**. Declaring the boundary keeps
a later reader from resting weight the control cannot carry.

Verification of an evasion path SHALL be operator-instructed. An agent SHALL NOT execute an evasion
of a live control in order to characterise it, because routing around a refusal is the behaviour the
estate's guard-denial rule forbids regardless of the motive.

#### Scenario: The evasion boundary is documented rather than demonstrated
- **WHEN** the control's coverage is recorded
- **THEN** the forms it provably does not catch are named as uncaught, and are not exercised by the
  agent to prove it
