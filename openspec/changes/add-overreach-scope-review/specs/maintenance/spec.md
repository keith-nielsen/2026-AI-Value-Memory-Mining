<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

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
- **Comparison is deterministic and pinned:** the diff against the merge base is compared to the
  declared scope by the exact-pinned checker (`overreach@0.7.0`, MIT) in scope-injection mode —
  no API keys, no network model calls, no repository writes. Checker upgrades are ordinary
  governed changes.
- **The threshold is repo-owned:** the job fails on any finding of severity medium or higher
  (an out-of-scope file is medium; the checker's own exit code fires only on high and SHALL NOT
  be the gate). Low-severity findings are advisory. Malformed checker output fails closed.
- **Two-stage adoption:** Phase A runs report-only (`continue-on-error`) as burn-in; the flip to
  blocking is its own governed change after clean burn-in. Dependabot PRs are exempt by actor.

#### Scenario: PR without a Declared-scope block fails extraction
- **WHEN** a pull request is opened whose body contains no fenced ```scope block
- **THEN** the `scope-review` job fails at the extraction step, naming the fix (add the block per
  the PR template), and no checker invocation occurs

#### Scenario: Diff touching an undeclared path is a failing finding
- **WHEN** the PR diff modifies a file matched by no declared entry (e.g. an undeclared
  `docs/` file riding along with a scripts change)
- **THEN** the checker reports a `scope.file` finding and the threshold step exits non-zero,
  listing the offending path(s) — the author either shrinks the diff or amends the declaration
  deliberately

#### Scenario: Declared-only diff passes
- **WHEN** every path in the PR diff is matched by a declared entry (exact path or directory
  prefix) and no undeclared dependencies/endpoints/env-vars are introduced
- **THEN** the threshold step exits 0 and reports PASS with any low-severity advisories

#### Scenario: Checker crash fails closed
- **WHEN** the checker invocation produces missing or malformed JSON output
- **THEN** the threshold step exits non-zero (fail-closed); the gate never passes by silence
