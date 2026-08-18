<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: Relocation Does Not Widen Agent Write Scope

Relocating Layer-0 machinery within Layer 0 SHALL leave the agent's write scope byte-for-byte
unchanged. A protected silo SHALL remain denied to the agent after relocation exactly as before it,
and this SHALL be verified by an attempted write rather than assumed.

Containment and permission are independent axes. Moving the fleet inside the tree buys forkability,
version isolation and repository-side runnability; it SHALL NOT be treated as, or accompanied by, a
loosening of the protections that keep an agent from rewriting its own guards. Placing the deploy
directory inside a protected silo is deliberate: the agent must remain unable to modify the code that
constrains it.

A widening of agent write scope is a governed decision with its own human sign-off, and SHALL NOT
ride in as a side effect of a relocation.

#### Scenario: The protected silo still refuses the agent after relocation
- **WHEN** the capability probe attempts a real write into the silo holding the deploy directory
- **THEN** the write is refused and the probe reports the silo protected

### Requirement: A Relocated Artifact Carries Its Harness Exclusion In The Same Commit

Where a harness settings file names an artifact by an exact path, relocating that artifact SHALL
update the settings file **in the same commit**. There SHALL be no intermediate state in which the
artifact has moved and the exclusion has not.

The failure mode of that intermediate state is **silent**. An exclusion is matched as an exact
string: when the named artifact moves, the entry does not error, it ceases to match, and the
resulting refusal is indistinguishable from a genuine denial. No automated test observes it, because
the fleet's tests invoke scripts as subprocesses and never traverse the harness.

Because no gate can close this, confirmation that a relocated exclusion still **matches** SHALL be an
explicit operator step performed through the real harness after the relocation lands, and its result
SHALL be recorded. A path-resolution check establishes only that the named artifact exists.

#### Scenario: The relocated exclusion is confirmed through the real harness
- **WHEN** the relocation has landed and the operator invokes the relocated artifact through the harness
- **THEN** the invocation proceeds under its exclusion, and the result is recorded as evidence
