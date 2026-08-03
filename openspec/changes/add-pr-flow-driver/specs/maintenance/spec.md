<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: PR Lifecycle Is Driven, Not Composed

The framework repo SHALL provide a guarded, re-entrant driver (`tools/pr-flow.py`) that mechanizes
the branch → push → PR → checks → merge → branch-deletion lifecycle, and contributors SHALL walk it
rather than hand-composing the sequence. The driver SHALL hold no state file, re-deriving state from
the world on every invocation. It SHALL NOT execute any outward mutation: it SHALL emit the next
single command verbatim and exit `2`, so that the INV-14 outbound guard — which text-matches the
command the caller runs — keeps firing on every outward step.

#### Scenario: The branch does not contain the base tip
- **WHEN** the driver runs on a branch that is not a descendant of the base's remote tip
- **THEN** it emits a rebase command and exits `2`
- **THEN** it does not emit any push, PR-create, or merge command
- **THEN** the emitted reason states that a PR opened on a stale base reports checks that are not
  about its own change

#### Scenario: A local operation is still in progress
- **WHEN** `.git/rebase-merge`, `.git/rebase-apply`, `.git/MERGE_HEAD`, or `.git/CHERRY_PICK_HEAD`
  is present
- **THEN** the driver refuses with exit `1` and names the marker it found
- **THEN** the refusal states that a half-finished rebase silently blocks branch deletion later

#### Scenario: The remote branch has diverged from local
- **WHEN** the remote branch exists and its SHA differs from the local branch SHA
- **THEN** the emitted push command uses `--force-with-lease` and never a bare `--force`
- **THEN** the emitted reason states that the lease refuses rather than overwrites if anything else
  pushed meanwhile

#### Scenario: Checks are failing
- **WHEN** any completed check run on the PR head concluded other than success, neutral, or skipped
- **THEN** the driver refuses with exit `1` and names each failing check
- **THEN** the refusal states that this repository's `main` ruleset carries no
  `required_status_checks`, so the merge would otherwise succeed over a red check

#### Scenario: A merge reports success but the branch survives
- **WHEN** the PR is merged and the remote branch still resolves on origin
- **THEN** the driver emits the branch-deletion command rather than reporting the lifecycle complete
- **THEN** the emitted reason states that `--delete-branch` is not atomic and prints a success tick
  even when the deletion did not occur

#### Scenario: Every emitted command names who runs it
- **WHEN** the driver emits any command
- **THEN** the output carries an explicit owner for that command

### Requirement: Platform Capability Is Probed, Not Recalled

The driver SHALL provide a `--capabilities` mode that MEASURES, at invocation time, which channels
this process can actually use — state reads, `git` mutations, and `gh` mutations — and reports the
resulting division of labour. Ownership of a command SHALL NOT be asserted from a stored table or
from recollection, because the environment that determines it (sandbox posture, keyring reachability,
credential prompts) varies between sessions and a stored answer preserves a wrong one.

#### Scenario: Capabilities are reported without network access
- **WHEN** `--capabilities` runs in an environment where a probe cannot reach its endpoint
- **THEN** the probe reports that capability as failed and exits `0`
- **THEN** it does not raise, because a probe that crashes teaches its caller to skip probing

#### Scenario: gh is unavailable but git is not
- **WHEN** `gh` cannot authenticate while `git` push and anonymous reads succeed
- **THEN** the report attributes `gh` mutations to the operator and `git` mutations to either party
- **THEN** the report states the mechanism (the keyring), not merely the verdict

### Requirement: GitHub Reads Degrade To An Unauthenticated Channel

Read-only GitHub tooling in this repo SHALL attempt the unauthenticated REST API before requiring
`gh`, and SHALL report the channel that answered alongside the data. A read that cannot be served by
any channel SHALL be reported as UNAVAILABLE and SHALL NOT be synthesised from another layer.

#### Scenario: A sandboxed agent reads PR state
- **WHEN** `gh` cannot reach the OS keyring and reports an authentication failure
- **THEN** `tools/pr-state.py` continues over the anonymous channel instead of exiting blocked
- **THEN** the output marks the report DEGRADED and names the channel that answered

#### Scenario: A GraphQL-only layer cannot be read
- **WHEN** the reporter is running on the degraded channel
- **THEN** `mergeStateStatus` and run-level aggregation are reported as UNAVAILABLE
- **THEN** the layer-disagreement comparison is skipped rather than computed from one layer
- **THEN** no line attributes REST-sourced data to GraphQL
