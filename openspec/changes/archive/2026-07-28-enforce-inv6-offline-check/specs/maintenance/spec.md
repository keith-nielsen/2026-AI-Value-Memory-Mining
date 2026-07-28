<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: INV-6 Is Enforced by Static and Dynamic Checks

INV-6 SHALL be enforced by two complementary mechanisms rather than asserted in prose. Neither is
sufficient alone, and the incompleteness of each SHALL be stated wherever the result is reported.

**Static half.** `tools/inv6-offline-check.py` SHALL analyse every Layer-0 fleet note's code fence
and report any statically visible network call. Python SHALL be analysed by **AST**, not by text
search: an import of a network module or a `subprocess`/`os` invocation of a network binary or a
remote-contacting `git` subcommand is a violation, while a string literal *naming* such a verb is
not. Bash SHALL be analysed by a conservative command-position scan, which is the weaker half and
SHALL NOT be claimed as complete.

**The naming-versus-calling distinction is load-bearing, not a nicety.** The `outbound-publish-guard`
and `push-guard` notes implement the INV-14 rail, and their function is to *name* outward verbs
inside regex literals. A text-matching checker flags them — measured at 6 and 2 hits respectively —
and a control that fails the two most security-relevant scripts in the fleet on every run will be
disabled rather than obeyed.

**Indirection SHALL be reported, never ignored.** A dynamic import with a computed name, or a
`subprocess` call with a non-literal argv, SHALL be reported as **UNRESOLVED** and SHALL fail the
check. Silence there would be a claim the tool cannot support.

**Dynamic half.** CI SHALL run the fleet behaviour suite inside an unprivileged **network
namespace**, and SHALL prove the isolation before believing the result: the network MUST be shown
reachable outside the namespace and unreachable inside it, in the same run. If isolation cannot be
established the job SHALL **fail closed** — an unisolated run is not a weaker result, it is no
result.

**Scope.** The Layer-0 fleet only (`99-Operations/scripts/`). Repo-side maintainer tools are not
`[script]` operations; `ship-release.py` legitimately performs authenticated reads and INV-6 is not
engaged for it. Applying this check to `tools/` would manufacture violations out of correct
behaviour.

**Bound on what a pass means.** A green result means *no statically visible network call, and none
on the paths the suite exercises*. It does **not** mean the fleet is offline. Coverage is the limit
of the dynamic half, and it is thinnest where the network verbs live — the two INV-14 guards
currently have no tests. This bound SHALL NOT be dropped when the result is summarised.

#### Scenario: A fleet script that calls the network fails the static check

- **WHEN** a fleet note's Python imports a network module, or invokes a network binary or a
  remote-contacting `git` subcommand via `subprocess`/`os`
- **THEN** `inv6-offline-check.py` reports a VIOLATION naming the note, line, and reason, and exits non-zero

#### Scenario: A guard that names an outward verb is not flagged

- **WHEN** a fleet note contains an outward verb such as `git push` or `gh repo create` only as a
  string or regex literal — as the INV-14 guards necessarily do
- **THEN** the check reports no violation for it

#### Scenario: Indirection is reported rather than passed

- **WHEN** a fleet note performs a dynamic import with a computed name, or a `subprocess` call whose
  argv is not a literal
- **THEN** the finding is reported as UNRESOLVED and the check exits non-zero

#### Scenario: The dynamic check refuses when it cannot isolate

- **WHEN** the network is unreachable outside the namespace, or the namespace fails to block traffic,
  or no unprivileged network namespace is available
- **THEN** the job exits non-zero with an explicit "INVALID instrument" message and reports no verdict
  about INV-6

#### Scenario: The fleet suite completes with no network available

- **WHEN** the fleet behaviour suite runs inside a proven-isolated network namespace
- **THEN** it completes successfully, evidencing that the exercised paths make no network call
- **AND** the reported result carries its coverage bound
