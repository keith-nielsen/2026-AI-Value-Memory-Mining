## ADDED Requirements

### Requirement: An Emitted Command Passes The Controls The Estate Already Runs

Where a driver emits a command for a human or an agent to execute, that command SHALL pass the
estate's own command-form controls. A driver SHALL NOT prescribe a form its own guard refuses.

An emitted command is an instruction. Where the instruction is a form the estate has ruled out, the
recipient is placed between two controls that disagree: following the driver trips the guard, and
obeying the guard abandons the route. Both readings are defensible, so the operator resolves it by
judgement — which is the state the driver exists to remove.

This is not hypothetical. The lifecycle driver emitted a `gh pr` subcommand at its pull-request step
while the invocation-form allowlist refused that exact form, and the same driver correctly used
`gh api` with an explicit REST path at three other steps, each with a written rationale for avoiding
the subcommand. The rule existed, was applied three times, and was missed once; nothing compared the
emissions against the guard, so the gap persisted rather than being caught on the next run.

The comparison SHALL be made by an automated check rather than by review. A reviewer reading an
emitted command cannot tell that it is refused without running the guard, and a rule enforced only by
attention has already failed in this estate.

#### Scenario: An emitted command is checked against the guard that would receive it
- **WHEN** a driver's emitted command forms are enumerated
- **THEN** each is submitted to the invocation-form guard, and any form the guard refuses fails the
  check, naming the emitting site and the guard's own replacement text

#### Scenario: A newly added emission is covered without being registered
- **WHEN** a new emitted form is added to a driver
- **THEN** it is checked by the same enumeration, so coverage does not depend on the author
  remembering to add it to a list

### Requirement: A Read Channel Known To Fail Silently Is Not The First Choice

Where more than one channel can answer a read, a tool SHALL prefer the channel whose failures are
observable, and SHALL NOT reach first for a channel known to fail silently. Where the less-preferred
channel is retained, it SHALL be retained as a **named fallback** and the channel that answered SHALL
be reported.

GitHub's GraphQL surface returns success for operations that did not take effect — the estate records
a body edit that reported success and did not apply. A REST call with an explicit path fails loudly
by comparison. Ordering the fallback chain GraphQL-first therefore makes the silent-failure channel
the default answer and the observable one the exception, which inverts the property that matters.

Retention is deliberate and bounded: a channel that answers a question no other channel can answer
SHALL be kept, and its absence SHALL be reported as unavailable rather than guessed. **Availability of
such a channel SHALL NOT be inferred from the outcome of an unrelated read**, because a preference
change elsewhere then removes a layer that had nothing to do with it.

#### Scenario: The observable channel is tried first
- **WHEN** a tool reads a pull request's state and both REST and GraphQL can answer
- **THEN** REST is attempted first, GraphQL is used only if REST fails, and the report names which
  channel answered

#### Scenario: A uniquely-answerable layer is retained, not removed
- **WHEN** a channel is the only one that can distinguish an outcome another channel flattens
- **THEN** that channel is retained for that question, and where it is unavailable the tool reports
  the layer as unavailable rather than substituting an answer that cannot express the distinction

#### Scenario: Layer availability is determined independently
- **WHEN** one read's channel preference changes
- **THEN** the availability of an unrelated layer is unaffected, because each layer's availability is
  determined from the tool it needs rather than from another read's outcome
