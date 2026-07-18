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

- [ ] In `openspec/constitution.md`, replace the third Gate-1 bullet:

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

- [ ] In `openspec/constitution.md`, extend Gate 3 by appending one bullet after
  "All named tests and CI pass green before Gate 4.":

  ```
  - Every named test/lint result is evidenced by its command and output — a tally
    with its denominator, a diff, or an exit status — never by a prose assertion
    or a shell-printed verdict string (an `echo "ok"` proves nothing: the shell
    knows only an exit code, not the answer to the question asked).
  ```

## 3. Constitution — Gate 4 re-run rule

- [ ] In `openspec/constitution.md`, replace the first Gate-4 bullet:

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

- [ ] (a) In `openspec/templates/constitution-override/proposal.md`, insert directly after the
  line `**Blast radius — every artifact referencing this principle:**`:

  ```
  **Enumeration transcript (mandatory — the checklist below is derived from it, and Gate 4
  re-runs it):**

  ```transcript
  $ <search command(s) sweeping openspec/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md>
  <full, untruncated output — never head/tail-truncated>
  ```
  ```

- [ ] (b) In the Gate-3 section, append after `**CI green on this PR:** ☐`:

  ```
  **Verification transcripts attached for every named test (tally/diff/exit status — no prose verdicts):** ☐
  ```

- [ ] (c) In the Gate-4 section, append after
  `**Second review confirms blast radius was fully addressed:** ☐`:

  ```
  **Gate-1 transcript re-run; output diffed clean against the proposal:** ☐
  ```

## 5. AGENTS.md operating notes

- [ ] Append two bullets to `## Operating notes (footguns this repo has hit)`:

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

- [ ] Confirm `openspec/adr/0031-require-transcript-verification.md` present (ships with this
  change, status Proposed → Accepted at Gate 4).
- [ ] `README.md`: update **both** ADR-count occurrences (lines 29 and 247) `30 ADRs` → `31 ADRs`
  and extend the range descriptor in line 247 (`framework choice → transcript verification`).

## 7. Verification (produce transcripts for each — this change's own rule)

- [ ] `openspec validate --strict` — paste exit status.
- [ ] Re-run the task-0 enumeration command — paste output; diff against task 0; every hit must be
  in the disposition list.
- [ ] `grep -rn '[0-9][0-9] ADRs' README.md docs/ AGENTS.md CONTRIBUTING.md` — paste output; every
  occurrence must read `31 ADRs`.
- [ ] `ls openspec/adr/ | wc -l` vs the README claim — paste both.
- [ ] CI green on the PR (constitution-lint, vocabulary-lint, scope-review, adr-count) — paste the
  check tally (`gh pr checks <N> | cut -f2 | sort | uniq -c` — a tally with a denominator).
