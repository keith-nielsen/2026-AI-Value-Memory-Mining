## ADDED Requirements

### Requirement: A Tool Resolves Every Operand From One Root

Where a tool operates on two or more artifacts belonging to the same tree, it SHALL resolve all of
them from a **single** root, and SHALL NOT mix a configured root with an implicit one such as the
process working directory.

A relative path in a data file is resolved against whatever the reader supplies. Where one operand
comes from a resolved root and another from the working directory, the tool is silently operating on
**two trees at once**. Its report then describes a comparison nobody asked for: a clean result means
"these two unrelated things happen to agree", and a failure names a file the caller never nominated.

This is not hypothetical and it was not found by reading the code. `vault-render.py` read its notes
from `VAULT_ROOT` while resolving each note's relative `deploy_target` against the process working
directory. A validation harness reported **`reconcile 15/15 ok, exit 0`** while comparing a live
vault's notes against a clone's deployed files — a clean pass measuring the wrong tree, produced by
the very instrument built to verify a change to a restricted area. In `render` mode the same
resolution **writes**, so one tree's code blocks would be deployed into another tree's paths.

Where a relative path in a data file names an artifact of the resolved tree, the tool SHALL join it
to that root. An absolute path SHALL be honoured as written, because an absolute path is an explicit
instruction rather than an unresolved fragment.

#### Scenario: A relative artifact path is joined to the resolved root
- **WHEN** a tool resolves a relative path taken from an artifact belonging to a configured root
- **THEN** the path is joined to that root, and the result does not depend on the working directory
  the tool happened to be started from

#### Scenario: Standing in a different tree does not change the verdict
- **WHEN** the tool is invoked with a configured root naming one tree, from a working directory
  inside a different tree
- **THEN** every operand is read from the configured tree, and no artifact of the other tree is read,
  written, or named in the report

### Requirement: A Documented Behaviour Claim Is Verified By A Test

Where a runbook, gate, or contributor document states how a shipped tool behaves, that statement
SHALL be verified by a test, and the test SHALL be demonstrated capable of failing.

A behaviour claim is load-bearing in a way a description is not: a reader plans against it, and a
reader who plans against a false claim builds something that cannot work. The session gates are read
and acknowledged at the start of every session, which makes a false gate the most-trusted wrong
statement in the estate.

Measured: the cold-start gates stated that the script fleet is *"env-free (root self-resolution)"*.
The shared contract `vault_lib.find_vault_root()` is **env-FIRST** — a configured root wins outright,
and the working-directory walk is only a fallback. That claim was acknowledged at the opening of
every session, and it is the reason the harness above was built wrong: it assumed resolution from the
script's own location and pinned nothing.

The estate already holds that *a rule which cannot refuse does not bind*. The same applies to its own
documentation: **a claim no instrument can contradict is not a specification, it is a belief.**

Where the claim is about a behaviour a test cannot reach, the document SHALL state the claim as
unverified rather than as fact.

#### Scenario: A gate's behavioural claim has a test behind it
- **WHEN** a runbook or gate asserts how a shipped tool resolves, refuses, or reports
- **THEN** a test asserts the same property against the shipped implementation, and that test has
  been observed to fail without it

#### Scenario: An unverifiable claim is marked, not asserted
- **WHEN** a behaviour cannot be reached by any available instrument
- **THEN** the document says so at the point of the claim, so a reader can tell a measured statement
  from an expectation
