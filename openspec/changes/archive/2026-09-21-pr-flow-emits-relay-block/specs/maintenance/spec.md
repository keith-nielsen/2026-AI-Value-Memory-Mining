<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## ADDED Requirements

### Requirement: The Operator Handoff Is Emitted As A Copy-Whole Block

For a step the driver assigns to the **operator** (one that writes a saved plan), `tools/pr-flow.py`
SHALL emit the handoff as a single **copy-whole block**: a delimited, paste-ready unit containing the
exact invariant `bash <saved-plan-path>` command together with its history-disambiguating
`# <what> step:<name>` tag, designated as the artifact the caller relays verbatim.

The purpose is to make the correct relay the **lazy** one. The caller's measured failure mode is
*reconstructing* the handoff line from the formatting rules — dropping the tag, swapping the path
form, reformatting — rather than copying it (determinism Site F43, ≥4 instances in one session on a
standing, retrievable rule). Emitting the finished block collapses the caller's task to reproducing
bytes and makes copying cheaper than reconstructing, so the caller's efficiency incentive produces
correctness instead of drift. A rule applied by the caller's election has the reliability of memory
(ADR-0034); this removes the reconstruction surface rather than adding another instruction against it.

The block carries only the command the driver already emits — no new command, no flag, no state, no
refusal. An **agent-owned** step (which the agent runs directly and for which no saved plan is
written) emits no relay block.

#### Scenario: An operator-owned step emits a copy-whole relay block

- **WHEN** the driver reaches a step it assigns to the operator and writes its saved plan
- **THEN** it emits a single delimited block containing the exact `bash <saved-plan-path>` command
  and its `# <what> step:<name>` tag
- **THEN** the block is labeled as the artifact to relay verbatim, so the caller copies it rather
  than composing a handoff of its own

#### Scenario: The block's command is byte-identical to the invariant handoff form

- **WHEN** the copy-whole block is emitted
- **THEN** the command line within it is byte-identical to `bash <saved-plan-path>` followed by the
  step's tag — the same invariant form written to the saved plan
- **THEN** a downstream check can compare a relayed line against the block without reconstructing
  either

#### Scenario: An agent-owned step emits no relay block

- **WHEN** the current step is one the driver assigns to the agent
- **THEN** no copy-whole relay block is emitted, because the agent runs the command directly and no
  saved plan is written for it
