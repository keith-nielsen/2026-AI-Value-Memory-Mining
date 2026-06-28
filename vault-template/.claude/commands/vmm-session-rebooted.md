---
description: Cold-start prime — execute the session-bootstrap-loader runbook (env + gates + JIT pointers)
---

Read and execute **`96-Runbooks/session-bootstrap-loader`** now — it is the single source of truth for
the cold-start prime. Perform its steps in order:

1. `source 99-Operations/config.env` (sets `VAULT_ROOT` / `PILLARS` / venv).
2. Engage the four gates: **governance-first · re-read-before-acting · autonomy-bans · clean-ops**.
3. Note (do not load) the just-in-time pointers from the runbook.
4. Verify `VAULT_ROOT` is set, then briefly confirm readiness.

Do not duplicate the runbook here — open it if anything is unclear; it is the SSOT.
