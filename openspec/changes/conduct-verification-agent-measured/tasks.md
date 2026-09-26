# Tasks — conduct-verification-agent-measured

> Origin: task 7.5 of `agent-conduct-standing-rules`, completed 2026-09-26 by the agent, not the
> operator; the runbook's §Verification still said "operator-observed". Named and excluded by #135.

## 0. END STATE

§Verification calls the cold-start check agent-measured and says how; the test docstring agrees; a test
holds it; the live vault receives it by mirror and parity reads 0 drift.

## 1. Implementation

- [x] 1.1 Branch `change/conduct-verification-agent-measured` from `main` (`d9db799`).
- [x] 1.2 Live occurrences enumerated — `grep -rn -i "operator-observed\|operator observed"` over the
      repo (excluding `node_modules`, `.git`): 3 hits; 1 live (the runbook), 2 archived (left as is).
      The test docstring's "operator observation" found on read.
- [x] 1.3 Runbook §Verification line rewritten; docstring STATED LIMIT rewritten.

## 2. Tests (observed to fail first)

- [x] 2.1 `test_the_cold_start_check_is_agent_measured` added. Against the unfixed runbook:
      **1 failed, 8 passed**; with the fix: 9 passed.

## 3. Spec

- [x] 3.1 None — `skip_specs: true`. Conforms to the existing *Runbook Format* requirement.

## 4. Regression

- [x] 4.1 Full suite green — 556 on `main` → 557 passed.
- [x] 4.2 `openspec validate --all --strict` — 7 passed, 0 failed (preflight's run). Run directly
      before the archive it fails 1: a `skip_specs` change has no deltas until archived.
- [~] 4.3 `tools/preflight.py .` → CLEAR (13/16 CI jobs reproduced; CAN ARCHIVE); STEP 7 `SKIP` until
      the body exists — re-run at 6.3.

## 5. Gate 4 — operator authorization

No `protects:`-tagged file is touched. Surfaced for sign-off:

- **The corrected sentence** in a runbook both roots read in full: the cold-start check is the
  agent's, and it must never be routed to the operator.
- **Deploy-down** is one operator-run mirror (it writes `96-Runbooks/`).

- [x] 5.1 Surfaced; **Approved** — Keith Nielsen, 2026-09-26

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff (generated after the archive commit).
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.

## 7. Deploy-down

- [ ] 7.1 Operator: `tools/template-mirror.py` (carries the runbook edit).
- [ ] 7.2 `tools/template-parity.py $VAULT_ROOT` → **0 drift**.
