<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: conduct-verification-agent-measured

## Why

`agent-conduct-standing-rules` §Verification (PR #134) says a real cold start's SessionStart preview
check is **operator-observed**. That is backwards, and measured so:

- **The operator cannot observe it.** The SessionStart hook's output is delivered to the agent's
  context — as a 2 KB preview, with the full output saved to a file, when it is long. The preview is
  not shown to the operator (the operator, 2026-09-26, rejecting a request to confirm it).
- **The agent can, and did.** On 2026-09-26 the check (task 7.5 of the archived
  `agent-conduct-standing-rules` change) was completed by the agent reading line 1 of the saved hook
  output: the pointer to this runbook, inside the preview. An operator asked to confirm it would have
  been asked to report on something they were never shown.

The wrong word is not cosmetic: a runbook's §Verification is where the next agent reads who performs a
check, so "operator-observed" instructs it to route an unobservable check to the operator. The same
claim sits in the docstring of `tests/test_conduct_doc_registration.py`.

`eliminate-repo-prime-command` (#135) named this defect and deliberately excluded it (F29); this is
that change.

## What Changes

- **`vault-template/96-Runbooks/agent-conduct-standing-rules.md` §Verification:** the cold-start line
  reads **agent-measured**, says why (the preview is delivered to the agent, never shown to the
  operator), and names the measurement (the first line of the hook's output, from the saved file when
  truncated). No rule, cost line or other section changes.
- **`tests/test_conduct_doc_registration.py`:** the docstring's STATED LIMIT is corrected the same way,
  and one test is added — §Verification names the cold-start check, calls it agent-measured, and does
  not say "operator-observed". It guards against vacuity by first asserting the line exists.
- **No spec change** (`skip_specs: true`). Conforms to the existing *Runbook Format* requirement.

### Deliberately NOT in this change

- The archived records that carry the old wording (`2026-09-26-agent-conduct-standing-rules/tasks.md`
  7.5; `2026-09-26-eliminate-repo-prime-command/proposal.md`) — archives are immutable.
- §Rollback's "not pruned until this document is verified loading in both roots": both working-memory
  stores were pruned on 2026-09-26 while only the vault root is verified. Whether to amend that
  sentence or verify the framework root is a separate decision (queue item 44.3).
- The framework root's stale `.claude/commands/vmm-session-rebooted.md` (undecided).

## Impact

- One sentence in a lockstep runbook read in full by every session in both roots; ~180 bytes added.
- **Deploy-down:** `tools/template-mirror.py` carries the runbook to the live vault (operator-run —
  it writes `96-Runbooks/`); parity then reads 0 drift.
- Not constitutional: no file touched carries a `protects:` key.

## Verification

- The new test, run against the unfixed runbook, **fails 1** (8 pass); with the fix, 9 pass.
- Full suite, `openspec validate --all --strict`, and preflight — recorded in `tasks.md` §4.
- After merge: mirror; `tools/template-parity.py $VAULT_ROOT` → 0 drift.
