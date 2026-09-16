## ADDED Requirements

### Requirement: The Lifecycle Subject Is Declared, Not Discovered

The pull-request lifecycle driver SHALL resolve the repository it acts upon from the **declared
estate**, not from the process working directory. The estate has exactly two members and both
locations are known in advance, so discovery is never appropriate: a session's working directory is
incidental to the question *which repository is this lifecycle about*.

Resolution SHALL follow one stated total order, with no silent fourth source:

1. An explicit `--repo PATH` argument, which overrides everything below.
2. The declared framework root, taken from the environment.
3. The working-directory toplevel — **only** when neither above is available.

The driver SHALL state the resolved subject and which of the three sources produced it, on every
invocation. Where the subject came from source 3 it SHALL be named as **discovered** rather than
declared, so a reader can tell the two apart.

Where the resolved subject is not a git repository, the driver SHALL refuse inside its declared exit
vocabulary, naming the resolved path — never a traceback.

This requirement exists because the same defect was already corrected for the capability probe and
not for the lifecycle, in the same file. A driver that measures the wrong repository does not fail
loudly: it emits a well-formed route with a plausible blocked step, indistinguishable from a genuine
one, and can conceal a real finding at an earlier step.

⚠ **Stated blind spot.** This governs the subject the driver *measures*. It does NOT assert that an
emitted command's effective target matches that subject; that is a separate axis, covered for pushes
by *Authority Is Distinguished From Execution*.

#### Scenario: The working directory is a deployed vault

- **WHEN** the driver is invoked with a declared framework root while the process runs inside a
  deployed vault
- **THEN** it measures the declared framework root and names it as the subject
- **THEN** it does not report the vault's absence of remotes as a lifecycle failure

#### Scenario: No subject is declared

- **WHEN** neither an explicit subject nor a declared framework root is available
- **THEN** the driver resolves the working-directory toplevel
- **THEN** it states that the subject was discovered rather than declared

#### Scenario: An explicit subject conflicts with the declared estate

- **WHEN** an explicit subject names a repository other than the declared framework root
- **THEN** the driver acts on the explicit subject and does not silently substitute the estate

#### Scenario: The resolved subject is not a repository

- **WHEN** the resolved subject path is not a git repository
- **THEN** the driver refuses with a blocked exit code and names the resolved path
- **THEN** it does not raise, because an escaping exception is outside the declared exit contract

### Requirement: A Pre-Verification Is No Weaker Than The Gate It Models

Where a local control pre-verifies a CI gate, it SHALL apply the gate's full criterion, not a weaker
proxy for it. A control that green-lights what the real gate will fail is worse than no control,
because it is relied upon; the weaker predicate converts a reviewable refusal into a surprise at CI
time.

Specifically, the driver's declared-scope step SHALL verify that the scope block in the pull request
body **covers** every path in the merge-base diff, not merely that a well-formed block is
**present**. The criterion SHALL be obtained by invoking the shipped gate rather than by restating
its logic, so the two cannot drift apart.

Where the shipped gate cannot be reached, the pre-verification SHALL pass rather than invent a
refusal it cannot substantiate — the real gate remains downstream.

#### Scenario: A present but stale scope block is refused before the push

- **WHEN** a pull request body carries a well-formed scope block that does not cover every path in
  the merge-base diff
- **THEN** the driver refuses the step and names the undeclared paths
- **THEN** it emits the body correction, and states that the body-derived gate needs a push rather
  than a re-run, because that gate reads the body from the event payload as of push time

#### Scenario: A covering scope block advances the route

- **WHEN** the declared scope covers every path in the diff
- **THEN** the step passes, recording that the block is present AND covers the diff

### Requirement: Local Coverage Accounting Is Measured, Not Asserted

A tool that reports which CI jobs it reproduced SHALL determine each job's availability by
**attempting it**, and SHALL NOT carry a hardcoded reason for not running a job that could be run.
A static exclusion cannot notice when its own premise stops being true, and a partition entry with a
false reason is a coverage gap wearing the costume of a decision: the reader sees a job listed as
considered and dismissed.

A job excluded for a structural reason — one no local run can change — MAY be declared statically,
provided the reason names that structural cause.

#### Scenario: A tool becomes available between runs

- **WHEN** a linter is absent on one run and installed before the next
- **THEN** the first run reports it as not runnable, naming the real cause
- **THEN** the second run reproduces it, with no change to the reporting tool

#### Scenario: A reproduced job reports findings

- **WHEN** a job that is now reproduced locally fails
- **THEN** the tool reports that failure rather than the job's former exclusion reason
