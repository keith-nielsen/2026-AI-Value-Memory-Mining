<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: The Route Is Pre-Flighted Before A Mutation

The driver SHALL answer, before any outward mutation, every route step that is decidable from
repository state, and SHALL report those answers together. A question the repository can already
answer about itself SHALL NOT be deferred to the platform, because the platform answers it only after
a push has been spent and, for a body-derived gate, only after a further push.

A pre-flight SHALL judge each step with the **shipped** check rather than a restatement of it: the
check's own text SHALL be executed. A second copy of a rule drifts from the first, and the pre-flight
must move when the rule moves rather than preserving an answer the rule no longer gives.

A step whose outcome is held by the platform — the existence of a pull request, pull requests stacked
on the branch, the merge itself, and any decision made by a repository ruleset the session cannot
read — SHALL be reported as not locally decidable, and SHALL NOT be predicted.

A check that **could not run** in the current environment SHALL be reported distinctly from a check
that **failed**, and SHALL NOT be counted as a finding. Reporting an environment limitation as a
defect is the same non-result-as-a-result error the pre-flight exists to catch, and a pre-flight that
raises false findings will be disregarded, taking its true findings with it.

The pre-flight SHALL determine whether each live change can be archived on its own branch by
**simulating** the archive and running the archive-sensitive checks against the simulated state,
rather than by reasoning about the change's contents. Where a change cannot archive, the pre-flight
SHALL name the artifact that blocks it.

Where more than one live change carries a delta against the same capability spec, the pre-flight SHALL
report that the archives are ordered, and SHALL name the changes involved, because two deltas applied
to one spec file can overwrite each other without ever conflicting.

#### Scenario: A declared scope does not cover the diff
- **WHEN** a pre-flight runs against a branch whose diff exceeds the scope declared in its body
- **THEN** the undeclared paths are named before the branch is pushed
- **THEN** the report distinguishes the removed and added sides of a rename, both of which the diff carries

#### Scenario: A change cites a record it does not ship
- **WHEN** a live change's archived form would fail an archive-sensitive check
- **THEN** the pre-flight reports that the change must defer its archive
- **THEN** it names the artifact that must exist first, rather than reporting only that the check failed

#### Scenario: Two live changes touch one capability spec
- **WHEN** more than one live change carries a delta against the same capability spec
- **THEN** the pre-flight reports the archives as ordered and names the changes
- **THEN** the later change is directed to rebase before archiving

#### Scenario: A check cannot run in this environment
- **WHEN** a check fails because the environment cannot execute it rather than because the repository is wrong
- **THEN** the pre-flight reports it as not runnable here and names the limitation
- **THEN** the result is excluded from the findings and does not fail the pre-flight

#### Scenario: A step is decided by the platform
- **WHEN** a route step's outcome is held by the platform rather than by repository state
- **THEN** the pre-flight reports it as not locally decidable
- **THEN** it does not report a predicted outcome for that step
