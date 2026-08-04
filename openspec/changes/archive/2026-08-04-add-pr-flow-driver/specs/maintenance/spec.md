<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Pull Request Lifecycle Is Driven, Not Composed

The framework repo SHALL provide a guarded, **level-triggered** driver (`tools/pr-flow.py`) that
mechanizes the branch → push → pull request → checks → merge → branch-deletion lifecycle, and
contributors
SHALL walk it rather than hand-composing the sequence. The driver SHALL hold no state file,
re-deriving state from the world on every invocation, so that a missed step or a lost session is
corrected by the next pass rather than remembered. It SHALL NOT execute any outward mutation: it
SHALL emit the next single command verbatim and exit `2`, so that the invariant INV-14 outbound
guard — which
text-matches the command the caller runs — keeps firing on every outward step. The contract is
**challenge and response**: the driver challenges, the caller responds by running exactly the emitted
command, and the driver verifies on re-invocation that the action actually completed.

#### Scenario: The branch does not contain the base tip
- **WHEN** the driver runs on a branch that is not a descendant of the base's remote tip
- **THEN** it emits a rebase command and exits `2`
- **THEN** it does not emit any push, pull-request-create, or merge command
- **THEN** the emitted reason states that a pull request opened on a stale base reports checks that
  are not
  about its own change

#### Scenario: The base ref could not be refreshed
- **WHEN** the fetch of the base ref fails
- **THEN** the driver reports the base as UNVERIFIED and refuses to advance
- **THEN** it does not evaluate base-currency against the stale remote-tracking ref

#### Scenario: A local operation is still in progress
- **WHEN** `.git/rebase-merge`, `.git/rebase-apply`, `.git/MERGE_HEAD`, or `.git/CHERRY_PICK_HEAD`
  is present
- **THEN** the driver refuses with exit `1` and names the marker it found
- **THEN** the refusal states that a half-finished rebase silently blocks branch deletion later

#### Scenario: The remote branch has diverged from local
- **WHEN** the remote branch exists and its commit SHA (secure hash algorithm value, the identifier
  of a commit) differs from the local branch SHA
- **THEN** the emitted push command uses `--force-with-lease` and never a bare `--force`

#### Scenario: A local command is emitted while another branch is checked out
- **WHEN** the branch under test needs a local mutation and is not the checked-out branch
- **THEN** the driver emits the branch switch first and does not emit the mutation

#### Scenario: An emitted command is not executable as written
- **WHEN** a required input for the next command is absent
- **THEN** the driver refuses with exit `1` and names the missing input
- **THEN** it does not emit a command containing a placeholder

#### Scenario: A merge reports success but the branch survives
- **WHEN** the pull request is merged and the remote branch still resolves on origin
- **THEN** the driver emits the branch-deletion command rather than reporting the lifecycle complete
- **THEN** the emitted reason states that the deletion is not implied by the merge's success report

#### Scenario: The lifecycle has already completed
- **WHEN** the branch is absent both locally and on origin and its pull request is merged
- **THEN** the driver reports the lifecycle complete and exits `0`

### Requirement: The Remaining Route Is Shown Before The Next Step

The driver SHALL make the whole remaining route visible before any step is taken, so that planning
does not have to be reconstructed from recall. Every invocation SHALL print a route header naming
each step, its completion state, the current position, and the owner of the next step. The driver
SHALL additionally provide a `--plan` mode that reports every step with its executor, its authority,
its guard, and whether that guard was **measured** now or is **projected**. Command text SHALL be
emitted for the current step only; the driver SHALL NOT compose command text for a step whose
preconditions have not been reached, because an unreached step's command is a prediction and would be
indistinguishable in the output from a verified one.

#### Scenario: A route is requested before the lifecycle begins
- **WHEN** `--plan` is invoked
- **THEN** every remaining step is listed with its executor and its authority
- **THEN** each step is marked as measured or projected
- **THEN** no command text appears for any projected step

#### Scenario: A step is emitted
- **WHEN** the driver emits the next command
- **THEN** the output also carries the route header showing position and remaining steps

### Requirement: Authority Is Distinguished From Execution

The driver SHALL state, for every step, both **who executes it** and **whose authority permits it**,
and SHALL NOT conflate the two. Execution SHALL NOT be assigned to the operator wherever the agent is
measured capable of performing it; in that case the operator's role is **consent**, discharged
through the INV-14 outbound ask at the moment of execution. The consent mechanism SHALL be measured
by evaluating the outbound guard against the command in question, not declared from a stored table.
For any step whose authority rests with the operator, the driver SHALL print what is being authorized
in reviewable terms, and SHALL keep that statement short enough to be read rather than skipped.

#### Scenario: A command the agent can run requires the operator's authority
- **WHEN** the next command is a `git` push that the capability probe reports as runnable
- **THEN** the driver names the agent as executor and the operator as authority
- **THEN** it names the outbound ask as the mechanism by which that authority is discharged
- **THEN** it does not instruct the operator to run the command themselves

#### Scenario: A command the agent cannot run
- **WHEN** the next command requires a credential this process does not hold
- **THEN** the driver names the operator as executor
- **THEN** the reason states both the technical cause and the policy that keeps it so

#### Scenario: A push is emitted from a session whose working directory is a deployed vault
- **WHEN** any push command is emitted
- **THEN** it carries an explicit effective-target redirect
- **THEN** the emitted command is not a bare push that the outbound guard would resolve to the vault

### Requirement: Preconditions Are Re-Asserted At The Moment Of Mutation

Because an operator-executed command may be run long after the driver measured the state that
justified it, preconditions SHALL be re-asserted at the moment of mutation rather than only at the
moment of emission — the **time-of-check-to-time-of-use (TOCTOU)** gap SHALL NOT be left open. Where the
platform offers a server-side precondition, it SHALL be used in preference to a client-side check:
the merge SHALL be requested with the head SHA that the pull request must still match, so that a
raced merge is refused by the server rather than detected afterwards. A saved plan SHALL carry an
expiry and SHALL refuse to execute once stale, and consent recorded against one state SHALL NOT carry
over to a different one.

#### Scenario: The head moved between emission and execution
- **WHEN** a merge is requested with a head SHA that no longer matches the pull request
- **THEN** the merge is refused by the platform and does not occur
- **THEN** the driver reports the refusal as a raced state rather than a failure of the change

#### Scenario: A saved plan is run after the state changed
- **WHEN** a generated command file is executed and the asserted preconditions no longer hold
- **THEN** the assertion fails and the mutation does not run
- **THEN** the output states which precondition moved

#### Scenario: A saved plan is run after it expires
- **WHEN** a generated command file is executed past its stated expiry
- **THEN** it refuses and directs the caller to re-derive the plan

### Requirement: Asynchronous Platform State Is Awaited, Never Assumed

Platform state that is computed asynchronously SHALL be treated as **not yet ready** rather than as a
verdict. Absence of check runs SHALL NOT be read as checks passing, and an uncomputed mergeability
result SHALL NOT be read as mergeable. The driver SHALL provide a readiness probe that answers a
single named condition in one request with a meaningful exit code, so that a wait is testable rather
than described. The driver SHALL NOT itself block or sleep; waiting SHALL be expressed as
re-invocation. Polling SHALL respect the channel's published rate budget, SHALL honour the retry and
reset headers the platform returns, and the driver SHALL report the remaining budget before it is
exhausted, because a channel that runs out mid-lifecycle blinds every guard that depends on it.

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

### Requirement: A Body-Derived Check Is Re-Triggered By A Push, Not A Re-Run

Where a required check reads the pull request body from the event payload, the driver SHALL state
that the payload is a snapshot taken at push time, and that a re-run replays the original payload.
Correcting the body SHALL therefore be followed by a push rather than a re-run. The pull request
title and body SHALL be brought current **before** the merge is emitted, and the correction SHALL be
made through the REST (Representational State Transfer) endpoint, because the convenience command
for editing a pull request can fail
silently behind a deprecated layer.

#### Scenario: A body-derived check is failing after the body was corrected
- **WHEN** the failing check derives its input from the pull request body
- **THEN** the driver prescribes a push and states that a re-run would replay the stale payload

#### Scenario: The body is corrected
- **WHEN** the pull request body or title requires correction
- **THEN** the emitted command uses the REST endpoint
- **THEN** the driver re-reads the field afterwards to confirm the change landed

### Requirement: Platform Capability Is Probed, Not Recalled

The driver SHALL provide a `--capabilities` mode that MEASURES, at invocation time, which channels
this process can actually use — state reads, `git` mutations, `gh` mutations, and the remaining read
budget — and reports the resulting division of labour. Ownership of a command SHALL NOT be asserted
from a stored table or from recollection, because the environment that determines it varies between
sessions and a stored answer preserves a wrong one.

#### Scenario: Capabilities are reported without network access
- **WHEN** a probe cannot reach its endpoint
- **THEN** the probe reports that capability as failed and exits `0`
- **THEN** it does not raise, because a probe that crashes teaches its caller to skip probing

#### Scenario: gh is unavailable but git is not
- **WHEN** `gh` cannot authenticate while `git` push and anonymous reads succeed
- **THEN** the report attributes `gh` mutations to the operator and `git` mutations to the agent
- **THEN** the report states the mechanism, not merely the verdict

### Requirement: GitHub Reads Degrade To An Unauthenticated Channel

Read-only GitHub tooling in this repo SHALL attempt the unauthenticated REST API (application
programming interface) before requiring
`gh`, and SHALL report the channel that answered alongside the data. A read that cannot be served by
any channel SHALL be reported as UNAVAILABLE and SHALL NOT be synthesised from another layer.

#### Scenario: A sandboxed agent reads pull request state
- **WHEN** `gh` cannot reach the operating system (OS) keyring and reports an authentication failure
- **THEN** `tools/pr-state.py` continues over the anonymous channel instead of exiting blocked
- **THEN** the output marks the report DEGRADED and names the channel that answered

#### Scenario: A GraphQL-only layer cannot be read
- **WHEN** the reporter is running on the degraded channel
- **THEN** the GraphQL-only layers are reported as UNAVAILABLE
- **THEN** no line attributes REST-sourced data to GraphQL

### Requirement: Branches Not Owned By This Repo Are Never Rewritten

The driver SHALL distinguish a branch that exists locally from one that exists only on the remote,
and SHALL NOT emit a rebase, a push, or a branch deletion for a remote-only branch. Bot branches are
maintained by the automation that created them, and rewriting or deleting one detaches it from that
automation or causes the pull request to be recreated. Locality SHALL be determined by an explicit
`refs/heads/` lookup, because a bare revision parse resolves a remote-tracking ref and reports a
foreign branch as local.

#### Scenario: A Dependabot pull request is driven
- **WHEN** the branch exists on origin but not under `refs/heads/`
- **THEN** the driver reports the branch as not local and skips the rebase and push guards
- **THEN** after the merge it leaves the remote branch in place

### Requirement: Stacked Pull Requests Are Retargeted Before The Parent Merges

The driver SHALL detect open pull requests whose base is the branch being merged, and SHALL refuse to
emit a merge while any exists, naming each child and prescribing the retarget. The driver SHALL NOT
couple branch deletion to the merge command: the convenience flag that does so both defeats the
platform's own retargeting of dependent pull requests and reports success when the deletion did not
occur. Branch deletion SHALL be a separate step whose effect is verified. Where the branch under test
is itself stacked, the driver SHALL say so.

#### Scenario: A pull request has children stacked on it
- **WHEN** an open pull request targets the branch being merged as its base
- **THEN** the driver refuses with exit `1` and names each child pull request
- **THEN** the refusal prescribes retargeting each child before this merge

#### Scenario: A merge is emitted
- **WHEN** the driver emits a merge command
- **THEN** that command does not also delete the branch
- **THEN** branch deletion is emitted separately and confirmed by a subsequent read

#### Scenario: The pull request under test is itself a stacked child
- **WHEN** the base is not the default branch
- **THEN** the driver reports that the pull request is stacked

### Requirement: Ambiguous Or Unmergeable Pull Request State Is Refused, Not Guessed

The driver SHALL query pull requests in every state rather than open ones alone, SHALL refuse when
more than one open pull request shares the head branch, SHALL refuse to advance a draft, and SHALL
refuse when the platform reports the pull request as not mergeable. A closed-unmerged pull request
SHALL be reported when a new one is proposed for the same branch, so that creating a replacement is a
stated consequence rather than an accident.

#### Scenario: Two open pull requests share a head branch
- **WHEN** more than one open pull request has the same head
- **THEN** the driver refuses with exit `1` and names each
- **THEN** it does not select one

#### Scenario: The pull request cannot be merged
- **WHEN** the platform reports the pull request as not mergeable
- **THEN** the driver refuses with exit `1`

#### Scenario: The pull request is a draft
- **WHEN** the pull request is marked draft
- **THEN** the driver refuses with exit `1`

#### Scenario: A closed-unmerged pull request exists for the branch
- **WHEN** no open pull request exists but a closed-unmerged one does
- **THEN** the driver reports it before emitting a create command
