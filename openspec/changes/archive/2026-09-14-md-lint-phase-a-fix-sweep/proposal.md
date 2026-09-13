# Bring the markdown corpus to zero lint findings, so Phase A can reach its exit condition

<!-- markdownlint-disable MD038 -->
<!-- MD038 is disabled for this file: it quotes `trail ` -- a code span whose TRAILING
     SPACE is the defect under discussion -- and stripping it would destroy the example
     exactly as the autofix did to the spec this change repairs. -->

## Why

`ci.yml`'s `md-lint` job runs in **Phase A (audit)**: it reports findings and ends in an explicit
`exit 0`. Its exit condition is declared in the workflow itself —

> findings reach 0 and stay 0 across 5 consecutive merged PRs -> Phase B removes the `exit 0` below,
> in its OWN governed change, never folded into a change that also edits markdown.

`main` today carries **1138 findings**, essentially unchanged since audit mode landed (PR #110). The
gate cannot progress to `enforce` while the corpus is dirty, so markdown is effectively unverified:
the job runs, reports, and blocks nothing.

This change delivers the "reach 0" half. It deliberately does **not** touch `ci.yml` — the workflow's
own instruction is that the Phase B flip is a separate governed change and must never be folded into
one that edits markdown. This change edits 44 markdown files, so it is exactly the change that must
not flip the gate.

⚠ **Provenance, stated plainly.** Four of the seven commits were authored 2026-08-27 on an abandoned
branch that was never pushed and never had a proposal. They were recovered, verified against the
claims in their own commit messages, corrected where those claims did not hold (see Verification),
and brought up to date with `main`. This proposal is written after the work, not before it.

## What Changes

1. **44 markdown files** — mechanical and hand formatting to satisfy MD004/MD013/MD018/MD022/MD027/
   MD031/MD032/MD040/MD049/MD058/MD060: blank lines around headings, lists, tables and fences; 52
   over-length lines reflowed; 17 fences given language labels; tables aligned.
2. **`.markdownlint.yml`** — `MD025.front_matter_title: ""`, scoped to MD025 alone. This corpus
   deliberately carries both a frontmatter `title:` and a rendered `# H1`; MD025's default treats the
   frontmatter title *as* the H1, so the pair reads as two top-level headings. The repo's own
   `runbook-lint` job REQUIRES `title:` in every runbook, and GitHub renders frontmatter as a table
   rather than a heading, so the H1 is what titles the page.
3. **`openspec/specs/naming-rules/spec.md`** — restore a trailing space the mechanical `--fix` pass
   destroyed, and exempt that one line from MD038. See Verification; this is a defect the sweep
   introduced and this change repairs.
4. **`openspec/specs/maintenance/spec.md`** — two blank lines after two `#### Scenario:` headings
   added by PR #115 *after* this branch was cut. They are the last 4 findings in the corpus.

### What this change does NOT do

- It does not remove the `exit 0` from `md-lint`. Phase B is its own change, by the workflow's
  instruction.
- It adds no rule suppressions beyond the two named above (one scoped config option, one
  single-line disable), and disables no rule wholesale.

## Impact

- **Formatting only.** No requirement, scenario, or normative sentence is reworded anywhere. This is
  asserted as a measurement, not a promise — see Verification.
- ⚠ **All six protected specs are touched**, because the sweep is corpus-wide:

  | file | protects |
  | --- | --- |
  | `openspec/specs/access-control/spec.md` | CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14 |
  | `openspec/specs/agent-integration/spec.md` | INV-4, INV-5, INV-8, INV-11 |
  | `openspec/specs/maintenance/spec.md` | INV-2, INV-3, INV-6 |
  | `openspec/specs/naming-rules/spec.md` | INV-11 |
  | `openspec/specs/value-pipeline/spec.md` | CONST-01, CONST-03, INV-9, INV-10 |
  | `openspec/specs/vault-structure/spec.md` | CONST-02, CONST-04, CONST-05, INV-1, INV-12 |

  That is every protected spec in the repository, and between them every CONST and INV identifier.
  The breadth is a property of a corpus-wide formatter, not of the intent: four of the six have
  **byte-identical prose**, and the two that differ are the repair in item 3 and the blank lines in
  item 4.
- **No spec delta.** No requirement is added, modified or removed, so this change carries no
  `specs/` directory and declares `skip_specs: true` in its own `.openspec.yaml`, which is the
  mechanism the pinned OpenSpec 1.12.0 requires for a pure docs/tooling change. (Two 2026-06-28
  changes ship delta-free without that file; they predate the requirement and are not a precedent
  to copy.)
- **The MD025 scoping is a real narrowing of a check** and is the one place where the corpus is
  exempted rather than repaired. It was measured before being applied: with frontmatter and fenced
  code stripped, no file in the linted scope has more than one true H1, so the rule was catching
  zero real defects. The justification is recorded in `.markdownlint.yml` itself.

## Constitutional impact

Six `protects:`-tagged specs are touched. Checked against what actually changed in them rather than
asserted from the file list:

- **Four are prose-identical** (`access-control`, `agent-integration`, `value-pipeline`,
  `vault-structure`) — whitespace, table alignment and fence labels only, proven by token-multiset
  comparison.
- **`maintenance`** gains two blank lines. Verified with `git diff -w -b --ignore-blank-lines`
  returning empty output: no prose changed.
- **`naming-rules`** has one character restored — a trailing space inside a code span — plus a
  lint-disable comment. This **strengthens** INV-11's spec: the scenario had been left asserting that
  `trail` (a valid name) must be rejected, and now correctly shows `trail ` again.

No principle is relaxed, no requirement is reworded, and no authority is granted. The one rule
exemption (MD025) governs a markdown linter's view of this repository's files; it is not a
constitutional element and constrains nothing the constitution protects.

```constitutional-impact
touches: openspec/specs/access-control/spec.md, openspec/specs/agent-integration/spec.md, openspec/specs/maintenance/spec.md, openspec/specs/naming-rules/spec.md, openspec/specs/value-pipeline/spec.md, openspec/specs/vault-structure/spec.md
protects: [CONST-01, CONST-02, CONST-03, CONST-04, CONST-05, INV-1, INV-2, INV-3, INV-4, INV-5, INV-6, INV-7, INV-8, INV-9, INV-10, INV-11, INV-12, INV-14]
overrides: none
basis: formatting only; four of six protected specs are prose-identical by token-multiset comparison, one gains two blank lines with an empty -w -b diff, and one has a destroyed trailing space RESTORED — no requirement added, modified or removed, and no spec delta
```

## Verification

**The red proof is that the check failed first.** The sweep's own commit messages claim *"content
provably unchanged"*. That claim was tested rather than accepted, by comparing the token stream of
every changed file with all whitespace collapsed — so reflow, blank lines and table alignment vanish
and only real content differences survive.

**It found a defect.** `markdownlint --fix` had stripped the trailing space from `` `trail ` `` in
`openspec/specs/naming-rules/spec.md`, a code span whose trailing space *is* the test input, leaving
it annotated "(trailing space)" while reading `` `trail` `` — a valid name. MD038 had exactly one
finding on `main`, and this was it. An autofix cannot distinguish a significant space from a sloppy
one. Repaired in this change.

**It also refuted a suspected defect.** Four `###` headings are removed from `CHANGELOG.md`, which
looked like re-classified release history. Measuring each affected entry's `(release, section)` before
and after showed **4/4 unchanged**: release `[0.1.17]` carried duplicate `### Changed`/`### Fixed`
blocks, and the sweep consolidated them within the same release. Lossless.

Final state of all 44 files:

| outcome | count |
| --- | --- |
| prose byte-identical | 40 |
| emphasis style `_x_` → `*x*`, renders identically (`AGENTS.md`) | 1 |
| blockquote marker + fence label (`docs/obsidian.md`) | 1 |
| duplicate-section consolidation, verified lossless (`CHANGELOG.md`) | 1 |
| trailing space restored + disable comment (`naming-rules`) | 1 |

Gates, measured on this branch with `main` merged in:

| check | result |
| --- | --- |
| `markdownlint`, CI's exact scope | **0 findings, exit 0** (from 1138 on `main`) |
| `openspec validate --all --strict` | 6 passed, 0 failed |
| `python3 -m pytest tests/ -q` | 386 passed |
| merge into `main` | clean |

⚠ **Honest limit.** The content check that found the defect lives in a scratch directory and is not
part of this change. Nothing in the repository verifies that a formatting sweep preserves content, so
the next one has the same blind spot this one did.
