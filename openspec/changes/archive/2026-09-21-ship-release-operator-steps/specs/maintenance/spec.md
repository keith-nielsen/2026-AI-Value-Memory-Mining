<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## MODIFIED Requirements

### Requirement: The Operator Handoff Is Emitted As A Copy-Whole Block

For a step a **lifecycle driver** assigns to the **operator** — one that writes a saved plan — the
driver SHALL emit the handoff as a single **copy-whole block**: a delimited, paste-ready unit
containing the exact invariant `bash <saved-plan-path>` command together with its
history-disambiguating `# <what> step:<name>` tag, designated as the artifact the caller relays
verbatim.

Both lifecycle drivers SHALL emit this block through **one shared module** (`tools/driver_handoff.py`),
imported the way `gh_read.py` is the one shared read layer — never a second copy. The saved-plan
skeleton, the emission record, the history suffix, the copy-whole block and its `relay-line.txt`
sidecar have a single source, so the bytes the INV-14 outbound guard and the relay-conformance Stop
hook compare against cannot fork between the drivers (a second copy would be the class-9 defect). Each
driver supplies only its own pieces: `pr-flow.py` its `--assert-preconditions` line and its
`--after-mutation` verification tail; `ship-release.py` a re-invocation of itself as the verification
tail (it re-derives release state, trusting no silent success).

`ship-release.py` SHALL emit its **irreversible outbound steps** — the version-tag push and the
release create, which the INV-14 guard hard-denies on the agent's channel (they are operator-only) —
as operator handoffs in this form, rather than as a bare command the agent would hit a mid-flow DENY
on. The raw command MAY still be shown for review, but the copy-whole block is the designated relay
artifact.

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

- **WHEN** a lifecycle driver reaches a step it assigns to the operator and writes its saved plan
- **THEN** it emits a single delimited block containing the exact `bash <saved-plan-path>` command
  and its `# <what> step:<name>` tag
- **THEN** the block is labeled as the artifact to relay verbatim, so the caller copies it rather
  than composing a handoff of its own

#### Scenario: The block's command is byte-identical to the invariant handoff form

- **WHEN** the copy-whole block is emitted
- **THEN** the command line within it is byte-identical to `bash <saved-plan-path>` followed by the
  step's tag — the same invariant form written to the saved plan and to the `relay-line.txt` sidecar
- **THEN** a downstream check can compare a relayed line against the block without reconstructing
  either

#### Scenario: The ship-release driver hands over its irreversible steps as operator handoffs

- **WHEN** `ship-release.py` reaches its tag-push or release-create step (irreversible outbound,
  operator-only under the INV-14 guard)
- **THEN** it writes a saved `next.sh` and emits the copy-whole relay block through the shared module,
  with a verification tail that re-invokes `ship-release.py` (which re-derives release state) rather
  than another driver
- **THEN** the relayed block's command line is written byte-identical to the `relay-line.txt` sidecar,
  so the relay-conformance hook checks it exactly as it checks a pr-flow handoff

#### Scenario: An agent-owned step emits no relay block

- **WHEN** the current step is one the driver assigns to the agent
- **THEN** no copy-whole relay block is emitted, because the agent runs the command directly and no
  saved plan is written for it
