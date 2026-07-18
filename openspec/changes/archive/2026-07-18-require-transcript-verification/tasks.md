<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — require-transcript-verification

> Apply steps are written to be executed mechanically (by a lower-effort model or a human)
> with zero interpretation: every edit carries its exact anchor and replacement text.
> Verification steps produce transcripts — this change's own rule, applied to itself.

## 0. Enumeration transcript (Gate-1-style; the blast radius below derives from it)

Command run 2026-07-18 on `main` (re-run and diff at review):

```transcript
$ grep -rn 'blast radius\|Enumerate the full' openspec/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md | grep -v 'changes/archive'
openspec/project.md:41:### Safety — highest blast radius if violated
openspec/adr/0008-invariant-criticality-ordering.md:26:| Safety | INV-4–8 | Highest blast radius if violated; access control and containment |
openspec/adr/0008-invariant-criticality-ordering.md:28:| Consistency | INV-11–13 | Structural conventions; important but narrower blast radius |
openspec/adr/0017-runbook-naming.md:26:  into the blast radius for no naming gain.
openspec/constitution.md:47:diagram, index name, and glossary entry references this frame — the blast radius is
openspec/constitution.md:154:- Enumerate the full blast radius: every spec, script, template, diagram, and
openspec/constitution.md:158:- A written migration plan covering every artifact in the blast radius.
openspec/constitution.md:168:- A second review confirming the blast radius was fully addressed.
openspec/specs/maintenance/spec.md:394:blast radius. CI SHALL enforce the declaration
openspec/templates/constitution-override/proposal.md:66:<!-- Step-by-step description of how every artifact in the blast radius is updated
openspec/templates/constitution-override/proposal.md:97:**Second review confirms blast radius was fully addressed:** ☐
.github/pull_request_template.md:11:     Ceremony changes: copy the Gate-1 blast radius.
.github/pull_request_template.md:30:- [ ] Declared-scope block present and matches the diff (ceremony changes: mirrors the Gate-1 blast radius)

$ grep -rn '[0-9][0-9] ADRs' README.md docs/ AGENTS.md CONTRIBUTING.md
README.md:29:   constitutional protection, 30 ADRs, 6 capability specs, and a live change-management
README.md:247:| [`openspec/adr/`](openspec/adr/) | 30 ADRs: framework choice → naming token floor |
```

Disposition of every hit: `constitution.md:154` → task 1; `constitution.md:168` → task 3;
`templates/constitution-override/proposal.md:97` → task 4c (line kept, checkbox appended after
it); template Gate-1 section → task 4a; `README.md` 29/247 → task 6. Not edited, with reason:
`project.md:41`, ADR-0008/0017 (different, historical sense of "blast radius");
`maintenance/spec.md:394` and `.github/pull_request_template.md:11`/`:30` (consumers of Gate-1
output — their contract is unchanged); `constitution.md:47` (CONST-01 prose), `:158` (Gate-2,
unchanged), template `:66` (Gate-2 comment, unchanged). Additions at locations the enumeration
does not flag (stated so the diff is fully accounted for): Gate-3 bullet (task 2), template
Gate-3 checkbox (task 4b), `AGENTS.md` notes (task 5) — additive text, no existing hit to map.

## 1. Constitution — Gate 1 transcript rule

- [x] In `openspec/constitution.md`, replace the third Gate-1 bullet:

  OLD:
  ```
  - Enumerate the full blast radius: every spec, script, template, diagram, and
    vocabulary term that references the element.
  ```
  NEW:
  ```
  - Enumerate the full blast radius: every spec, script, template, diagram, and
    vocabulary term that references the element — delivered as a **pasted,
    re-runnable command transcript** (the exact search command(s) plus their full,
    untruncated output), never a list composed from reasoning. Enumeration is
    bounded by the corpus, not by what the proposer thought of; the command set
    must sweep the whole repo (`openspec/ vault-template/ docs/ .github/ README.md
    AGENTS.md CONTRIBUTING.md`).
  ```

## 2. Constitution — Gate 3 evidence rule

- [x] In `openspec/constitution.md`, extend Gate 3 by appending one bullet after
  "All named tests and CI pass green before Gate 4.":

  ```
  - Every named test/lint result is evidenced by its command and output — a tally
    with its denominator, a diff, or an exit status — never by a prose assertion
    or a shell-printed verdict string (an `echo "ok"` proves nothing: the shell
    knows only an exit code, not the answer to the question asked).
  ```

## 3. Constitution — Gate 4 re-run rule

- [x] In `openspec/constitution.md`, replace the first Gate-4 bullet:

  OLD:
  ```
  - A second review confirming the blast radius was fully addressed.
  ```
  NEW:
  ```
  - A second review confirming the blast radius was fully addressed — by
    re-running the Gate-1 transcript and diffing its output against the proposal,
    not by re-reading the composed sections.
  ```

## 4. Override template

- [x] (a) In `openspec/templates/constitution-override/proposal.md`, insert directly after the
  line `**Blast radius — every artifact referencing this principle:**`:

  ```
  **Enumeration transcript (mandatory — the checklist below is derived from it, and Gate 4
  re-runs it):**

  ```transcript
  $ <search command(s) sweeping openspec/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md>
  <full, untruncated output — never head/tail-truncated>
  ```
  ```

- [x] (b) In the Gate-3 section, append after `**CI green on this PR:** ☐`:

  ```
  **Verification transcripts attached for every named test (tally/diff/exit status — no prose verdicts):** ☐
  ```

- [x] (c) In the Gate-4 section, append after
  `**Second review confirms blast radius was fully addressed:** ☐`:

  ```
  **Gate-1 transcript re-run; output diffed clean against the proposal:** ☐
  ```

## 5. AGENTS.md operating notes

- [x] Append two bullets to `## Operating notes (footguns this repo has hit)`:

  ```
  - **A checklist step that says *enumerate* or *verify* is satisfied only by a pasted,
    re-runnable command transcript** — the command plus its full output, never a list or a
    verdict composed from reasoning, and never `head`/`tail`-truncated (narrowing the output
    is the same defect as narrowing the scope). Corollary: **never let the shell print a
    literal verdict string** — `ok` / `clean` / `pass` inside an `echo` is unearned; print
    evidence (a count with its denominator, a diff, an exit status) and read it (ADR-0031).
  - **A command handed to the operator names its execution path** — who runs it (actor) and
    what channel it travels through (terminal paste, editor, file apply). Long or multi-line
    content is delivered as a file the operator applies, never a long interactive paste — the
    interactive prompt reflows and corrupts long pastes (ADR-0031; failure F14 in the live
    vault's determinism-failure-modes record).
  ```

## 6. ADR + counts

- [x] Confirm `openspec/adr/0031-require-transcript-verification.md` present (ships with this
  change, status Proposed → Accepted at Gate 4).
- [x] `README.md`: update **both** ADR-count occurrences (lines 29 and 247) `30 ADRs` → `31 ADRs`
  and extend the range descriptor in line 247 (`framework choice → transcript verification`).

## 7. Verification (produce transcripts for each — this change's own rule)

- [x] `openspec validate --strict` — paste exit status.
- [x] Re-run the task-0 enumeration command — paste output. Expected differences from task 0
  (anything else is a miss): (a) hits inside `openspec/changes/require-transcript-verification/`
  and `openspec/adr/0031-*` — this change's own files quoting the phrases; (b) the
  `constitution.md` Gate-1/Gate-4 lines and template lines reworded/shifted by tasks 1, 3, 4.
  Every remaining hit must map to the task-0 disposition list.
- [x] `grep -rn '[0-9][0-9] ADRs' README.md docs/ AGENTS.md CONTRIBUTING.md` — paste output; every
  occurrence must read `31 ADRs`.
- [x] `ls openspec/adr/ | wc -l` vs the README claim — paste both.
- [ ] CI green on the PR (constitution-lint, vocabulary-lint, scope-review, adr-count) — paste the
  check tally (`gh pr checks <N> | cut -f2 | sort | uniq -c` — a tally with a denominator).

## Apply transcripts (task 7, 2026-07-18)

### `openspec validate require-transcript-verification --strict`

```transcript
$ openspec validate require-transcript-verification --strict
Change 'require-transcript-verification' is valid
EXIT_STATUS=0
```

### Re-run of the task-0 enumeration command

```transcript
$ grep -rn 'blast radius\|Enumerate the full' openspec/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md | grep -v 'changes/archive'
openspec/constitution.md:47:diagram, index name, and glossary entry references this frame — the blast radius is
openspec/constitution.md:154:- Enumerate the full blast radius: every spec, script, template, diagram, and
openspec/constitution.md:163:- A written migration plan covering every artifact in the blast radius.
openspec/constitution.md:177:- A second review confirming the blast radius was fully addressed — by
openspec/project.md:41:### Safety — highest blast radius if violated
openspec/adr/0031-require-transcript-verification.md:14:The Informed-Upheaval Protocol's Gate 1 says "Enumerate the full blast radius"; Gate 3 says
openspec/adr/0031-require-transcript-verification.md:15:tests "pass green"; Gate 4 says "a second review confirming the blast radius was fully
openspec/adr/0017-runbook-naming.md:26:  into the blast radius for no naming gain.
openspec/adr/0008-invariant-criticality-ordering.md:26:| Safety | INV-4–8 | Highest blast radius if violated; access control and containment |
openspec/adr/0008-invariant-criticality-ordering.md:28:| Consistency | INV-11–13 | Structural conventions; important but narrower blast radius |
openspec/templates/constitution-override/proposal.md:74:<!-- Step-by-step description of how every artifact in the blast radius is updated
openspec/templates/constitution-override/proposal.md:107:**Second review confirms blast radius was fully addressed:** ☐  
openspec/changes/require-transcript-verification/tasks.md:8:## 0. Enumeration transcript (Gate-1-style; the blast radius below derives from it)
openspec/changes/require-transcript-verification/tasks.md:14:openspec/project.md:41:### Safety — highest blast radius if violated
openspec/changes/require-transcript-verification/tasks.md:15:openspec/adr/0008-invariant-criticality-ordering.md:26:| Safety | INV-4–8 | Highest blast radius if violated; access control and containment |
openspec/changes/require-transcript-verification/tasks.md:16:openspec/adr/0008-invariant-criticality-ordering.md:28:| Consistency | INV-11–13 | Structural conventions; important but narrower blast radius |
openspec/changes/require-transcript-verification/tasks.md:17:openspec/adr/0017-runbook-naming.md:26:  into the blast radius for no naming gain.
openspec/changes/require-transcript-verification/tasks.md:18:openspec/constitution.md:47:diagram, index name, and glossary entry references this frame — the blast radius is
openspec/changes/require-transcript-verification/tasks.md:19:openspec/constitution.md:154:- Enumerate the full blast radius: every spec, script, template, diagram, and
openspec/changes/require-transcript-verification/tasks.md:20:openspec/constitution.md:158:- A written migration plan covering every artifact in the blast radius.
openspec/changes/require-transcript-verification/tasks.md:21:openspec/constitution.md:168:- A second review confirming the blast radius was fully addressed.
openspec/changes/require-transcript-verification/tasks.md:22:openspec/specs/maintenance/spec.md:394:blast radius. CI SHALL enforce the declaration
openspec/changes/require-transcript-verification/tasks.md:23:openspec/templates/constitution-override/proposal.md:66:<!-- Step-by-step description of how every artifact in the blast radius is updated
openspec/changes/require-transcript-verification/tasks.md:24:openspec/templates/constitution-override/proposal.md:97:**Second review confirms blast radius was fully addressed:** ☐
openspec/changes/require-transcript-verification/tasks.md:25:.github/pull_request_template.md:11:     Ceremony changes: copy the Gate-1 blast radius.
openspec/changes/require-transcript-verification/tasks.md:26:.github/pull_request_template.md:30:- [ ] Declared-scope block present and matches the diff (ceremony changes: mirrors the Gate-1 blast radius)
openspec/changes/require-transcript-verification/tasks.md:36:`project.md:41`, ADR-0008/0017 (different, historical sense of "blast radius");
openspec/changes/require-transcript-verification/tasks.md:49:  - Enumerate the full blast radius: every spec, script, template, diagram, and
openspec/changes/require-transcript-verification/tasks.md:54:  - Enumerate the full blast radius: every spec, script, template, diagram, and
openspec/changes/require-transcript-verification/tasks.md:81:  - A second review confirming the blast radius was fully addressed.
openspec/changes/require-transcript-verification/tasks.md:85:  - A second review confirming the blast radius was fully addressed — by
openspec/changes/require-transcript-verification/tasks.md:112:  `**Second review confirms blast radius was fully addressed:** ☐`:
openspec/specs/maintenance/spec.md:394:blast radius. CI SHALL enforce the declaration
openspec/changes/require-transcript-verification/proposal.md:6:was **read and then not executed**: the blast radius was composed by reasoning about where scripts
openspec/changes/require-transcript-verification/proposal.md:38:   blast radius **by re-running the Gate-1 transcript and diffing**, not by re-reading the list.
.github/pull_request_template.md:11:     Ceremony changes: copy the Gate-1 blast radius.
.github/pull_request_template.md:30:- [ ] Declared-scope block present and matches the diff (ceremony changes: mirrors the Gate-1 blast radius)
```

Disposition check against task-0's expected-differences note: (a) all `openspec/adr/0031-*` hits (lines
14–15) and all `openspec/changes/require-transcript-verification/{tasks.md,proposal.md}` hits are this
change's own files quoting the phrases — expected, excluded. (b) `constitution.md:154` (task 1, reworded,
same anchor line), `constitution.md:163` (was `:158`, shifted +5 by task 1's insertion, text unchanged —
task-0 disposition "not edited"), `constitution.md:177` (was `:168`, task 3, reworded, shifted +9 by tasks
1+2's insertions), `templates/constitution-override/proposal.md:74` (was `:66`, shifted +8 by task 4a,
text unchanged — task-0 disposition "not edited"), `templates/constitution-override/proposal.md:107` (was
`:97`, task 4c target checkbox, shifted +10 by tasks 4a+4b, text unchanged). All remaining hits
(`constitution.md:47`, `project.md:41`, `adr-0008:26/28`, `adr-0017:26`, `specs/maintenance/spec.md:394`,
`.github/pull_request_template.md:11/30`) are byte-identical to task 0 — not edited, as disposed. No
unmapped hits found.

### ADR-count grep

```transcript
$ grep -rn '[0-9][0-9] ADRs' README.md docs/ AGENTS.md CONTRIBUTING.md
README.md:29:   constitutional protection, 31 ADRs, 6 capability specs, and a live change-management
README.md:247:| [`openspec/adr/`](openspec/adr/) | 31 ADRs: framework choice → transcript verification |
```

Both occurrences read `31 ADRs`, as required.

### ADR file count vs README claim

```transcript
$ ls openspec/adr/ | wc -l
31

$ grep -n 'ADRs' README.md
29:   constitutional protection, 31 ADRs, 6 capability specs, and a live change-management
240:using the `spec-driven` schema. ADRs are implemented as a project convention alongside
247:| [`openspec/adr/`](openspec/adr/) | 31 ADRs: framework choice → transcript verification |
```

`ls openspec/adr/ | wc -l` = 31, matching the README's `31 ADRs` claim.

### Not run (requires a PR that does not exist yet)

- `gh pr checks <N> | cut -f2 | sort | uniq -c` — deferred; final task-7 checkbox left unticked.

### Ship-prep transcripts

Run after the coordinator accepted the apply and directed archiving (2026-07-18).

#### `openspec archive require-transcript-verification --yes`

```transcript
$ openspec archive require-transcript-verification --yes
Proposal warnings in proposal.md (non-blocking):
  ⚠ Why section should not exceed 1000 characters
Task status: 13/14 tasks
Warning: 1 incomplete task(s) found. Continuing due to --yes flag.

Specs to update:
  agent-integration: update
Applying changes to openspec/specs/agent-integration/spec.md:
  + 1 added
Totals: + 1, ~ 0, - 0, → 0
Specs updated successfully.
Change 'require-transcript-verification' archived as '2026-07-18-require-transcript-verification'.
```

The 13/14 warning is the final task-7 checkbox (CI-on-a-PR), left unticked deliberately since no PR
exists yet — `--yes` was used to proceed past it per the coordinator's instruction, not a missed task.

#### Post-archive `git status --short`

```transcript
$ git status --short
 D openspec/changes/require-transcript-verification/proposal.md
 D openspec/changes/require-transcript-verification/specs/agent-integration/spec.md
 D openspec/changes/require-transcript-verification/tasks.md
 M openspec/specs/agent-integration/spec.md
?? openspec/changes/archive/2026-07-18-require-transcript-verification/
```

#### Spec grep for the new requirement

```transcript
$ grep -n "Verification Deliverables Are Transcripts" openspec/specs/agent-integration/spec.md
102:### Requirement: Verification Deliverables Are Transcripts
```

#### `openspec validate --all --strict` (repo-wide validate has no bare invocation; `--all` covers every spec + live change)

```transcript
$ openspec validate --all --strict
- Validating...
✓ spec/access-control
✓ change/add-telemetry-segment
✓ spec/agent-integration
✓ spec/maintenance
✓ spec/naming-rules
✓ spec/value-pipeline
✓ spec/vault-structure
Totals: 7 passed, 0 failed (7 items)
EXIT_STATUS=0
```

(Bare `openspec validate --strict` was tried first and errored with "Nothing to validate," suggesting
`--all`/`--changes`/`--specs`/`<item-name>` — `--all --strict` was run instead, as the closest repo-wide
equivalent.)

#### README archived-changes grep

```transcript
$ grep -n 'archived changes' README.md
249:| [`openspec/changes/`](openspec/changes/) | 14 archived changes, 1 live (deferred), override template |
```

#### `agent-integration` spec Requirement count, before/after

```transcript
$ git show HEAD:openspec/specs/agent-integration/spec.md | grep -c 'Requirement:'
3
$ grep -c 'Requirement:' openspec/specs/agent-integration/spec.md
4
```

4 = 3 + 1, confirming exactly the one new Requirement ("Verification Deliverables Are Transcripts") landed.

#### `git status --short` after staging the ship-prep paths

```transcript
$ git add openspec/changes/require-transcript-verification openspec/changes/archive/2026-07-18-require-transcript-verification openspec/specs/agent-integration/spec.md README.md CHANGELOG.md
$ git status --short
M  CHANGELOG.md
M  README.md
R  openspec/changes/require-transcript-verification/proposal.md -> openspec/changes/archive/2026-07-18-require-transcript-verification/proposal.md
R  openspec/changes/require-transcript-verification/specs/agent-integration/spec.md -> openspec/changes/archive/2026-07-18-require-transcript-verification/specs/agent-integration/spec.md
R  openspec/changes/require-transcript-verification/tasks.md -> openspec/changes/archive/2026-07-18-require-transcript-verification/tasks.md
M  openspec/specs/agent-integration/spec.md
```
