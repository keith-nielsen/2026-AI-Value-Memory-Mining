<!-- SPDX-License-Identifier: Apache-2.0 -->

## MODIFIED Requirements

### Requirement: Asynchronous Platform State Is Awaited, Never Assumed

Platform state that is computed asynchronously SHALL be treated as **not yet ready** rather than as a
verdict. Absence of check runs SHALL NOT be read as checks passing, and an uncomputed mergeability
result SHALL NOT be read as mergeable. The driver SHALL provide a readiness probe that answers a
single named condition in one request with a meaningful exit code, so that a wait is testable rather
than described. The driver SHALL NOT itself block or sleep; waiting SHALL be expressed as
re-invocation. Polling SHALL respect the channel's published rate budget, SHALL honour the retry and
reset headers the platform returns, and the driver SHALL report the remaining budget before it is
exhausted, because a channel that runs out mid-lifecycle blinds every guard that depends on it.

Where a mutation's own response asserts the state it produced, that response SHALL take precedence
over a subsequent read of an eventually-consistent view. A write response is the answer of the
endpoint that performed the work; a read view is a weaker, later signal, and SHALL NOT be permitted to
overrule it. Two reads of the same fact through different endpoints MAY disagree, so the driver SHALL
NOT treat whichever endpoint it happens to consult first as authoritative.

While the driver is verifying a mutation, a read that returns no data SHALL be treated as **no answer
yet**, never as evidence that the mutation did not occur. A failed read, an empty result and a result
carrying data are three distinct outcomes and SHALL be distinguishable at the point of decision.

While the driver is verifying a **merge**, it SHALL NOT emit the command for any step that precedes
the merge in the lifecycle. Once a pull request has merged, the pre-merge guards describe a state the
branch has left, so the only correct outcomes are to confirm the merge or to report that it is not yet
visible. This restriction SHALL be scoped to the verification of a merge and SHALL be released as soon
as the merge is observed to have landed, so that the cleanup steps which legitimately follow are never
suppressed.

#### Scenario: No check runs have registered yet
- **WHEN** the head commit has zero check runs
- **THEN** the driver reports NOT READY and exits `2`
- **THEN** it does not report the checks as green and does not emit a merge

#### Scenario: Mergeability has not been computed
- **WHEN** the mergeability of the pull request is reported as uncomputed
- **THEN** the driver reports NOT READY and exits `2`
- **THEN** it does not treat an uncomputed result as mergeable

#### Scenario: A wait is required
- **WHEN** the driver reports that it is waiting on a platform condition
- **THEN** it names a probe that tests that condition and returns an exit code
- **THEN** it does not describe a wait that has no way to be tested

#### Scenario: The read budget is nearly exhausted
- **WHEN** the remaining rate budget falls below the cost of a further invocation
- **THEN** the driver reports the remaining budget and the time until it resets

#### Scenario: The mutation's response asserts a state the read view does not yet show
- **WHEN** the driver is verifying a merge and the captured response of that merge asserts it landed
- **THEN** the driver routes to the post-merge path on the strength of that response
- **THEN** it confirms against the read view with bounded lag tolerance rather than requiring the read
  view to agree before it will proceed

#### Scenario: Two endpoints disagree about the same fact
- **WHEN** one read reports a pull request merged and another read of the same pull request does not
- **THEN** the driver does not treat the endpoint it consulted first as authoritative
- **THEN** it reports the disagreement rather than silently adopting either answer

#### Scenario: A read returns nothing while a mutation is being verified
- **WHEN** the driver is verifying a mutation and the read returns an empty result
- **THEN** the driver treats the result as no answer yet
- **THEN** it does not conclude that the mutation did not occur

#### Scenario: A merge is being verified and the read view has not caught up
- **WHEN** the driver is verifying a merge and no read confirms it within the retry ladder
- **THEN** the driver reports WAITING and exits `2`
- **THEN** it emits no command belonging to any step that precedes the merge, including local commands
  such as a rebase

#### Scenario: The merge is confirmed and cleanup remains
- **WHEN** the driver observes that the merge has landed while verifying it
- **THEN** the restriction on emitting earlier steps is released
- **THEN** the cleanup steps that follow the merge are emitted normally
