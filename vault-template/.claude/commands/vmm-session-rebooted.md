---
description: Cold-start prime — execute the session-bootstrap-loader runbook (env + gates + JIT pointers)
---

Read and execute **`96-Runbooks/session-bootstrap-loader`** now — it is the single source of truth for
the cold-start prime. Perform its steps in order:

1. `source 99-Operations/config.env` (sets `VAULT_ROOT` / `FRAMEWORK_ROOT` / `PILLARS` / venv).
2. Engage the five gates: **governance-first · re-read-before-acting · autonomy-bans · clean-ops ·
   measure-don't-infer**.
3. Run the capability probe — `python3 "$FRAMEWORK_ROOT/tools/pr-flow.py" --capabilities` — and report
   its layers BEFORE any claim about what you can read, write, or reach.
   It measures the **declared estate** (`VAULT_ROOT` and `FRAMEWORK_ROOT`), never the directory you
   happen to be in. Two readings that are easy to get backwards:
   - a **remoteless vault is INV-14 holding**, not a broken channel — and a vault that *can* push is a
     violation, not a pass;
   - an empty `FRAMEWORK_ROOT` makes those layers **UNDECLARED**, an honest absence, never a failure.
   If step 1 left `FRAMEWORK_ROOT` empty, say so and continue — do **not** substitute the current
   directory, and do **not** hand-roll a replacement probe.
4. Note (do not load) the just-in-time pointers from the runbook.
5. Verify `VAULT_ROOT` is set, then briefly confirm readiness.

Do not duplicate the runbook here — open it if anything is unclear; it is the SSOT.
