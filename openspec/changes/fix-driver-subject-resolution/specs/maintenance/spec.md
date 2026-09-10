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

Where the subject is resolved by source 3, the driver SHALL state in its output that the subject was
**discovered rather than declared**, so a reader can tell the two apart. Where a declared subject and
the working-directory toplevel are both repositories and differ, the driver SHALL name the one it
took and the reason, in the route output rather than in source comments.

Where the resolved subject is not a git repository, the driver SHALL refuse inside its declared exit
vocabulary, naming the resolved path — never a traceback.

This requirement exists because the same defect was already corrected for the capability probe and
not for the lifecycle, in the same file. A driver that measures the wrong repository does not fail
loudly: it emits a well-formed route with a plausible blocked step, indistinguishable from a genuine
one, and can conceal a real finding at an earlier step.

⚠ **Stated blind spot.** This requirement governs the subject the driver *measures*. It does NOT
assert that an emitted command's effective target matches that subject; that is a separate axis,
covered for pushes by *Authority Is Distinguished From Execution* and not generalised here.

#### Scenario: The working directory is a deployed vault
- **WHEN** the driver is invoked with a declared framework root while the process runs inside a
  deployed vault
- **THEN** it measures the declared framework root
- **THEN** its route reflects that repository's branches, base and commits
- **THEN** it does not report the vault's absence of remotes as a lifecycle failure

#### Scenario: No subject is declared
- **WHEN** neither `--repo` nor a declared framework root is available
- **THEN** the driver resolves the working-directory toplevel
- **THEN** it states that the subject was discovered rather than declared

#### Scenario: An explicit subject conflicts with the declared estate
- **WHEN** `--repo` names a repository other than the declared framework root
- **THEN** the driver acts on the path given by `--repo`
- **THEN** it does not silently substitute the declared estate

#### Scenario: The resolved subject is not a repository
- **WHEN** the resolved subject path is not a git repository
- **THEN** the driver refuses with a blocked exit code and names the resolved path
- **THEN** it does not raise, because an escaping exception is outside the declared exit contract
