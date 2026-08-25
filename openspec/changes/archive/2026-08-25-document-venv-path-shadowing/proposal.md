<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: document-venv-path-shadowing

## Why

`config.env` prepends the vault's virtual environment to `PATH`. That is correct and deliberate —
vault work must run against the vault's interpreter — but it silently changes what the token `python3`
means for the rest of the shell, and the file said nothing about it.

**Measured 2026-08-20, in one shell:** `python3 -m pytest` → `No module named pytest`, while bare
`pytest` → `9.1.1`. The tool was on `PATH` the whole time; only the interpreter had changed. An agent
read the first result as *"pytest is not installed"* and reported a constitutional Gate-3 blocker that
did not exist.

That is the same failure class the corpus already catalogues under capability claims: **an error
message is accurate about the process that emitted it and silent about the question being asked.**
`No module named X` is a fact about one interpreter's import path, not about the machine. The message
names the tool rather than the interpreter, which is exactly why the two get confused.

## What Changes

Two halves, and the second is why this is a change rather than a comment.

**1. The environment file states its own effect.** `vault-template/99-Operations/config.env.example`
gains a block at the point of the `PATH` prepend, naming both invocation forms, what each resolves to,
and citing the measurement. A reader hitting `No module named pytest` is looking at an error, and the
next place they look is the file that changed their shell — not a runbook.

**2. The rule is written down where it binds.** Two `maintenance` Requirements: that a shipped
environment file states the resolution it changes, and that a shadowed import failure is not evidence
of a missing tool until the bare-name form has been tried.

## Why a Requirement and not just the comment

The comment alone would be the shape this repository has repeatedly measured as insufficient — prose
asking a reader to be careful. What makes the second Requirement worth having is that it is
**falsifiable in a transcript**: it names a specific pair of invocations and requires both to be
reported when they disagree. A reviewer can check whether that was done. "Be careful with `PATH`"
cannot be checked by anyone.

It is honestly a weak-to-moderate control — it constrains what a report may claim, not what a shell
may do. Recorded at that strength rather than dressed up as enforcement.

## Nature of this change — ordinary, not a constitution-override

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only. Two new Requirements; no existing requirement modified, weakened or narrowed. INV-2
  (one commit per change) and INV-3 (literate note is the source, render produces the target) are
  untouched — no fleet script changes. INV-6 is upheld: the change adds documentation and reporting
  rules and introduces no network or LLM call anywhere.
```

The edit to `vault-template/99-Operations/config.env.example` is a **SEED** file by
`tools/template-sync-manifest.json` — lockstep covers only `99-Operations/scripts/` and
`99-Operations/schemas/`. So the template change does not propagate by mirror; a deployed vault's
`config.env` is owned per instance, and the delta is merged into it by the operator, never copied over.

## Deliberately NOT in this change

- **Changing the `PATH` prepend itself.** It is correct. The defect was silence about its consequence,
  not the behaviour.
- **A lint asserting the comment is present.** Considered and rejected as theatre: it would check that
  a string exists in a file, which is not the property that matters, and it would refuse a deployment
  whose operator legitimately rewrote their own SEED file.
- **Mirroring into the live vault.** `config.env.example` is SEED; the live `config.env` is
  instance-owned. The operator merges the delta if they want it.

## Impact

- `vault-template/99-Operations/config.env.example` — one comment block at the prepend
- `openspec/specs/maintenance/spec.md` — 2 ADDED Requirements (4 scenarios)
- `CHANGELOG.md` — `[Unreleased]` entry
