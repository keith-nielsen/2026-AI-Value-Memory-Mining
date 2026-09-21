<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: pr-flow-emits-relay-block

## Why

The lifecycle driver emits an operator-owned step's command on a `To run it:` line, and the
agent relays that line into its message to the operator. The relay is where it breaks: **the agent
reconstructs the line from the formatting rules instead of copying it**, and every reconstruction is
a fresh chance to drop the history-disambiguating `# … step:…` tag, swap the absolute path for the
`$FRAMEWORK_ROOT` form, or reformat it. Determinism Site **F43** records this **≥4 times in a single
session**, on a rule (`operator-command-formatting`) that was standing, retrievable, and had a prior
recorded recurrence the whole time.

The doctrine the estate already holds (ADR-0034) explains why more prose will not fix it: *a rule
applied by an actor's election has the reliability of memory, which is the thing this program exists
to distrust.* And the recidivism is **efficiency-driven** — the agent trims because the trimmed form
feels cheaper.

So the fix works **with** that mechanism rather than against it: make copying the correct thing the
**lazy** thing. If the driver emits the finished, copy-whole relay block, relaying it verbatim is
*less* work than reconstructing it, and the caller's shortcutting pull produces correctness. It also
collapses the caller's task from "construct the handoff" to "emit these bytes," removing the
reconstruction surface this defect lives in. It is the prerequisite for the byte-check enforcement
(hardening item 40): a check can only compare a relay to a canonical block once the driver emits one.

## What Changes

- For an **operator-owned** step that writes a saved plan, `tools/pr-flow.py`'s `emit()` prints a
  single **copy-whole relay block** — a delimited, paste-ready unit containing the exact invariant
  `bash <saved-plan-path>` command **with its `# <what> step:<name>` tag** — designated as the
  artifact the caller relays verbatim.
- **Agent-owned** steps are unchanged: they emit no relay block (the agent runs them directly).
- No new command-line flag, no persistent state, no change to exit semantics, and no new refusal —
  the driver emits exactly what it emitted before, wrapped so it is copied rather than retyped.

## Impact

- **Caller-visible output surface** changes (this is why the change carries a proposal rather than
  shipping as a bare tooling fix, per `CONTRIBUTING.md` §*When a change ships without a proposal*).
  Tests that parse the driver's operator-facing output are updated in this change.
- Specs: adds one requirement to `openspec/specs/maintenance/spec.md` under the PR-lifecycle driver.
- Enables hardening item 40 (a Stop-hook that byte-checks a relayed line against this block).

## Constitutional impact

The delta touches `openspec/specs/maintenance/spec.md`, whose frontmatter carries
`protects: [INV-2, INV-3, INV-6]`. Checked against each:

- **INV-2** — untouched. Commit structure is unchanged; still one commit per automated change.
- **INV-3** — untouched. No script's literate-note/render relationship changes; `pr-flow.py` is a
  repo tool, not a rendered fleet script.
- **INV-6** — untouched. No network or LLM call is added; the driver's determinism is unaffected —
  this only formats output it already produces.

The touch is **additive and benign**: a new requirement about output presentation, engaging none of
the protected invariants and overriding nothing. It is surfaced for sign-off because the estate's
hard stop requires explicit human confirmation for **any** touch of a `protects:`-tagged element,
not only an overriding one.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only
```

## Verification

- A test asserts an operator-owned emission contains the copy-whole block, and that the command line
  within it is byte-identical to the invariant `bash <path>` form with its tag.
- A test asserts an agent-owned emission carries no relay block.
- The existing emitted-command-shape and conformance suites still pass.
- Full suite, `openspec validate --all --strict`, and markdownlint all clean.
