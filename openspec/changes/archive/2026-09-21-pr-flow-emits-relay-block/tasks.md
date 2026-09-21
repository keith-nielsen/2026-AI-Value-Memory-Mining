# Tasks — pr-flow-emits-relay-block

> **Durable plan.** Finishable from here plus the artifacts it names, with no recollection of the
> conversation that produced it. Origin: determinism Site F43; hardening-queue item 39.

## 0. END STATE

`tools/pr-flow.py`, at an operator-owned step, emits a single copy-whole relay block (delimiters +
fenced `bash <saved-plan-path>   # <what> step:<name>`) designated for verbatim relay. Agent-owned
steps are unchanged. The block's command line is byte-identical to the saved-plan invariant form, so
item 40's Stop-hook can byte-check a relay against it. No flag, no state, no exit-semantics change,
no new refusal.

## 1. The emission

- [x] 1.1 In `emit()` (the operator-owned branch that calls `write_saved_plan`), emit the copy-whole
      block: an opening delimiter line naming it as the relay artifact, a fenced
      `bash <path>   # <plan_history_suffix>` line, a closing delimiter. Reuse `plan_history_suffix`
      so the tag is the same one the driver already computes — do not recompute it.
- [x] 1.2 The block is the SINGLE canonical relay form. Do not also print a second, differently
      shaped `To run it:` one-liner that the caller might copy instead — one form, no ambiguity
      (the ambiguity between two forms is itself an F43 finding).
- [x] 1.3 Agent-owned steps: unchanged, no block.
- [x] 1.4 ⚠ Markdown nesting: the block contains a fenced code span. It is emitted as plain text on
      the driver's stdout; the caller pastes it at the top level of its message. Do not assume the
      driver renders markdown — it does not; it prints bytes.

## 2. Tests

- [x] 2.1 Observe RED first: an operator-owned emission does NOT contain the block before 1.1.
- [x] 2.2 An operator-owned emission contains the block, and the command line within it is
      byte-identical to `bash <path>` + the step's tag (the item-40 contract).
- [x] 2.3 An agent-owned emission contains NO relay block.
- [x] 2.4 The existing `tests/test_emitted_command_shape.py` and `tests/test_gh_form_conformance.py`
      still pass (they parse driver output; confirm the new block does not derail them).

## 3. Consequences

- [x] 3.1 Any test or doc that parses the old `To run it:` one-liner is updated to the block, in the
      same change.
- [ ] 3.2 The vault memory `operator-command-formatting` gains a one-line note that the driver now
      emits the block (the relay rule becomes "copy the driver's block", strictly simpler). Memory
      store is gitignored, so this is a disk edit, not a repo artifact.

## 4. Regression

- [x] 4.1 Full suite green.
- [x] 4.2 `openspec validate --all --strict` — 0 failed.
- [x] 4.3 markdownlint (CI's four `--ignore` paths) — 0 findings.
- [~] 4.4 `tools/preflight.py . --body-file <path>` → CLEAR.

## 5. Gate 4 — maintenance spec touch (protected)

The delta adds a requirement to `openspec/specs/maintenance/spec.md`, `protects: [INV-2, INV-3,
INV-6]`. The touch is additive and engages none of the three (output presentation only), but the
hard stop requires explicit human confirmation for any touch of a protected element.

To be surfaced — **drafted by the agent; the sign-off is human-only and is NOT recorded until given:**

- **What is added:** a requirement that the operator handoff is emitted as a copy-whole block.
- **What it does NOT change:** commit structure (INV-2), the literate-note/render relationship
  (INV-3), determinism/network posture (INV-6) — none is engaged.
- **What breaks if this is wrong:** a mis-shaped block could make the caller's relay *harder*, not
  easier, re-introducing the F43 drift it exists to remove. The byte-identity test (2.2) is the
  guard against that.

- [x] 5.1 Tier-0 (protected-spec) touch surfaced; **Approved** — Keith Nielsen, 2026-09-21

## 6. Land it

⚠ **Archive BEFORE the first push** (the F43-adjacent lesson from prefer-rest #121: archiving after
the push changed the diff and broke the scope block, costing a body PATCH + re-trigger). Archive with
the spec delta applied (`openspec archive pr-flow-emits-relay-block`), so the pushed diff already
includes the archived paths and the scope block covers the final state from the first push.

- [ ] 6.1 Archive on this branch (spec delta applied to maintenance).
- [ ] 6.2 Write the PR body with a `scope` block covering the FINAL (post-archive) diff.
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; run each emitted step; merge via the driver; cleanup.
