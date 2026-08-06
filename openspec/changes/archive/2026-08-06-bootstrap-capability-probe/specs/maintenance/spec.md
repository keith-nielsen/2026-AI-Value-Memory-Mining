<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: The Session Prime Measures Capability Before Asserting It

The cold-start prime SHALL run a capability probe and report its layers before the session makes any
claim about what it can read, write, or reach. A capability limit SHALL NOT be asserted from
recollection, from a stored path list, or from a single command's failure — a denial is evidence about
the command that failed, never about the class of channels it belongs to.

Write scope, `gh` credential, `git` credential, and network reachability are **independent layers**:
they SHALL be reported separately and none SHALL be inferred from another. The prime SHALL reference
the existing capability reporter rather than restate its checks, so that one system owns the criterion
and every consumer imports it.

Capability SHALL be distinguished from authority: a channel the agent can execute may still require
operator authorization (INV-14), and measuring the former never confers the latter.

#### Scenario: A credential error is not reported as a network verdict
- **WHEN** a `git` operation fails with a credential-storage-lock error naming a read-only filesystem
- **THEN** the prime reports a write-channel failure
- **THEN** it does not report the network, the remote, or any other credential channel as unavailable

#### Scenario: Capability is measured before it is asserted
- **WHEN** the session is asked what it can write or reach and the probe has not yet run
- **THEN** the probe is run and the answer is derived from its output
- **THEN** no capability claim is issued from a stored path list or from a previous session's memory

#### Scenario: A changed write scope contradicts recollection
- **WHEN** the configured write scope has changed since the claim was last true
- **THEN** the probe reports the current scope
- **THEN** the probed scope governs and the conflicting recollection is discarded, because a stored
  answer preserves a wrong one

#### Scenario: One channel fails while another succeeds
- **WHEN** `gh` mutations are unavailable because the operator credential is unreadable by the session
- **THEN** the report still attributes `git` mutations and anonymous reads to the channels that serve them
- **THEN** the session continues on the working channels instead of reporting itself blocked
