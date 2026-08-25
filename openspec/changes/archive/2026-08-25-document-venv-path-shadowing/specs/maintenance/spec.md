<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: An Environment File States The Resolution It Changes

Where a shipped environment file alters how a subsequent command resolves — by prepending to `PATH`,
by activating a virtual environment, or by exporting a variable a later tool reads — it SHALL state
that consequence at the point where it causes it.

The `PATH` prepend that puts the vault's virtual environment first changes what the token `python3`
means for the remainder of the shell. That is deliberate: vault work must run against the vault's own
interpreter. But it means `python3 -m <tool>` thereafter resolves inside an environment that ships
only the vault's dependencies, so a developer tool installed in the operator's environment is not
importable and reports itself missing — while the same tool invoked by its **bare name** resolves
through `PATH` and runs normally.

The statement SHALL name both forms and what each resolves to, and SHALL cite the measurement rather
than describe the hazard in the abstract. A warning that says "be careful with `PATH`" does not let a
reader distinguish the two cases at the moment they are looking at an error message.

The statement SHALL live in the environment file itself, not only in a runbook or a contributing
guide. The reader who needs it is looking at the file that caused the behaviour, and a cross-reference
is read after the wrong conclusion has already been drawn.

#### Scenario: The environment file documents its own effect
- **WHEN** a reader opens the shipped environment file at the point of the `PATH` prepend
- **THEN** the consequence for interpreter resolution is stated there, naming both invocation forms
  and citing the measurement that established it

#### Scenario: The statement sits at the cause, not in the header
- **WHEN** the environment file is read from the top by someone who has not yet run anything
- **THEN** the statement is found beside the prepend that causes the behaviour, so it is read at the
  moment it becomes relevant rather than before the behaviour it explains has occurred

### Requirement: A Shadowed Import Failure Is Not A Missing Tool

An import failure reported by an interpreter SHALL NOT be treated as evidence that the named tool is
absent from the machine, where an environment file on the current shell has altered interpreter
resolution.

`No module named <tool>` is a statement about **one interpreter's** import path. It is not a statement
about the operator's machine, and the two are routinely confused because the message names the tool
rather than the interpreter. Before reporting a tool as missing, the bare-name invocation SHALL be
tried, and the two results SHALL be reported together where they disagree.

This is the same class as a capability asserted from a single error message: the error is accurate
about the process that emitted it and silent about the question actually being asked.

#### Scenario: A module reports itself missing under the shadowed interpreter
- **WHEN** `python3 -m <tool>` reports `No module named <tool>` in a shell that has sourced the
  environment file
- **THEN** the tool is not reported absent until the bare-name invocation has been tried
- **THEN** where the bare name succeeds, both results are reported together and the difference is
  attributed to interpreter resolution, not to installation state

#### Scenario: The tool is genuinely absent
- **WHEN** both the module form and the bare-name form fail
- **THEN** the tool may be reported absent, and the report names both invocations as evidence
