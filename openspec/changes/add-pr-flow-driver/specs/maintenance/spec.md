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

#### Scenario: A local command is emitted while another branch is checked out
- **WHEN** the branch under test needs a local mutation and is not the checked-out branch
- **THEN** the driver emits the branch switch first and does not emit the mutation
- **THEN** the emitted reason states that the bare command would act on the wrong branch

#### Scenario: The lifecycle has already completed
- **WHEN** the branch is absent both locally and on origin and its PR is merged
- **THEN** the driver reports the lifecycle complete and exits `0`
- **THEN** it does not refuse, because absence on both sides is the normal end state

### Requirement: Branches Not Owned By This Repo Are Never Rewritten

The driver SHALL distinguish a branch that exists locally from one that exists only on the remote,
and SHALL NOT emit a rebase, a push, or a branch deletion for a remote-only branch. Bot branches —
Dependabot's above all — are maintained by the automation that created them, and rewriting or
deleting one detaches it from that automation or causes the pull request to be recreated. Locality
SHALL be determined by an explicit `refs/heads/` lookup, because a bare revision parse resolves a
remote-tracking ref by DWIM and reports a foreign branch as local.

#### Scenario: A Dependabot pull request is driven
- **WHEN** the branch exists on origin but not under `refs/heads/`
- **THEN** the driver reports the branch as not local and skips the rebase and push guards
- **THEN** the merge command it emits omits `--delete-branch`
- **THEN** after the merge it leaves the remote branch in place

### Requirement: Stacked Pull Requests Are Retargeted Before The Parent Merges

The driver SHALL detect open pull requests whose base is the branch being merged, and SHALL refuse
to emit a merge while any exists. Merging a parent with `--delete-branch` auto-closes its stacked
children irrecoverably: GitHub refuses both to reopen a pull request whose base branch is gone and
to retarget a closed one. Where the branch under test is itself stacked — its base is not the
default branch — the driver SHALL say so.

#### Scenario: A pull request has children stacked on it
- **WHEN** an open pull request targets the branch being merged as its base
- **THEN** the driver refuses with exit `1` and names each child pull request
- **THEN** the refusal states that the children must be retargeted before this merge

#### Scenario: The pull request under test is itself a stacked child
- **WHEN** the base is not the default branch
- **THEN** the driver reports that the pull request is stacked and is lost if its parent merges first

### Requirement: Ambiguous Or Unmergeable Pull Request State Is Refused, Not Guessed

The driver SHALL query pull requests in every state rather than open ones alone, SHALL refuse when
more than one open pull request shares the head branch, and SHALL refuse to advance a draft. A
closed-unmerged pull request SHALL be reported when a new one is proposed for the same branch, so
that creating a replacement is a stated consequence rather than an accident.

#### Scenario: Two open pull requests share a head branch
- **WHEN** more than one open pull request has the same head
- **THEN** the driver refuses with exit `1` and names each
- **THEN** it does not select one, because selecting silently is how the wrong one gets merged

#### Scenario: The pull request is a draft
- **WHEN** the pull request is marked draft
- **THEN** the driver refuses with exit `1`

#### Scenario: A closed-unmerged pull request exists for the branch
- **WHEN** no open pull request exists but a closed-unmerged one does
- **THEN** the driver reports it before emitting a create command

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
