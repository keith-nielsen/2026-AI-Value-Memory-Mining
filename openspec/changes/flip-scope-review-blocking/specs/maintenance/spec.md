<!-- SPDX-License-Identifier: Apache-2.0 -->

## MODIFIED Requirements

### Requirement: Scope-Review CI Gate (Declared Scope)

Every pull request SHALL declare its authorized change surface as a fenced ```scope block in the
PR body — root-relative paths, one per line, directories with a trailing `/`, no glob syntax; the
non-file surfaces the checker inspects are declared with prefixed entries (`env: NAME`,
`dep: package`, `endpoint: /route`); for ceremony changes the declaration mirrors the Gate-1
blast radius. CI SHALL enforce the declaration
deterministically (INV-6 posture at the CI layer — offline, no LLM in the decision path):

- **Extraction is fail-closed:** a missing, empty, or malformed declaration fails the job with an
  instructive message. The PR body reaches the extractor via environment variable, never shell
  interpolation. Entries containing glob characters, or lacking both `/` and `.`, are rejected
  (the pinned checker matches directory prefixes and exact paths only).
- **Comparison is deterministic and self-contained:** the diff against the merge base is compared
  to the declared scope by a repo-owned, stdlib-only comparator — exact-path / directory-prefix
  matching, no fuzzy branches, no third-party runtime dependency, no registry fetch, no network.
  The gate SHALL NOT depend on external packages at run time (the declared-scope concept and
  schema were informed by an evaluated external tool, credited in the CHANGELOG).
- **The threshold is repo-owned:** the job fails on any finding — undeclared file (medium) or
  undeclared workflow env var / dependency (high). Malformed inputs fail closed.
- **The gate is BLOCKING (Phase B, complete).** The job SHALL NOT carry `continue-on-error`; a
  finding fails the job and the run. Phase A's report-only burn-in is discharged. Dependabot PRs
  remain exempt by actor, and the job does not run on the `push` trigger.
- **Where the block binds SHALL be stated, not assumed.** A failing job blocks a merge through the
  lifecycle driver, which refuses to emit a merge command while any check is failing. Adding this
  job to the branch ruleset's required contexts is a **separate** decision, because the job reports
  `skipped` on the `push` trigger and on dependabot PRs, and whether a `skipped` conclusion
  satisfies a required context cannot be dry-run on this plan.

#### Scenario: PR without a Declared-scope block fails extraction
- **WHEN** a pull request is opened whose body contains no fenced ```scope block
- **THEN** the `scope-review` job fails at the extraction step, naming the fix (add the block per
  the PR template), and no checker invocation occurs
- **THEN** the failure is not suppressed — the job has no `continue-on-error`

#### Scenario: Diff touching an undeclared path is a failing finding
- **WHEN** the PR diff modifies a file matched by no declared entry (e.g. an undeclared
  `docs/` file riding along with a scripts change)
- **THEN** the checker reports a `scope.file` finding and the threshold step exits non-zero,
  listing the offending path(s) — the author either shrinks the diff or amends the declaration
  deliberately
- **THEN** the lifecycle driver refuses to emit a merge command while that check is failing

#### Scenario: Declared-only diff passes
- **WHEN** every path in the PR diff is matched by a declared entry (exact path or directory
  prefix) and no undeclared dependencies/endpoints/env-vars are introduced
- **THEN** the threshold step exits 0 and reports PASS with any low-severity advisories

#### Scenario: The job is renamed only while its context is unrequired
- **WHEN** the job's `name` is changed, since the name is the check-context identity
- **THEN** the change is made while the context is absent from the ruleset's required contexts
- **THEN** any later addition to required contexts uses the new name, so no required context is
  ever renamed out from under a merge
