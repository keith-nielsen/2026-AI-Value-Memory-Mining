<!-- SPDX-License-Identifier: Apache-2.0 -->
## Why

The vault operates on sensitive personal knowledge. There is currently no mechanism
to detect unauthorized file access, unexpected writes to protected areas
(particularly `40-Treasury/` and `99-Operations/`), or network egress from vault
processes. The INV invariants describe what *should not* happen; this change adds
observability so violations can be *detected* at runtime, not just prevented by
design.

osquery provides file-integrity monitoring (FIM) via SQLite queries against the
filesystem, process table, and network sockets — without requiring kernel modules
or privileged daemons beyond the osquery installation itself.

## What Changes

### New Capabilities

- `telemetry`: osquery-based file-integrity monitoring over `VAULT_ROOT` and network
  egress monitoring for vault processes. Includes scheduled osquery queries for:
  - FIM on `40-Treasury/` and `99-Operations/` (detect unexpected writes)
  - Process network-connection monitoring for `vault_*.py` and `hermes` processes
  - Alert export to a local log file (no external telemetry endpoints)

### Modified Capabilities

- `maintenance`: Add the telemetry query scripts as literate meta-scripts in
  `99-Operations/scripts/`; add `osquery` to the technology constraints note.

## Impact

- `openspec/specs/maintenance/spec.md` will gain a Telemetry section (delta below)
- New `vault-template/99-Operations/scripts/telemetry-fim.md` (FIM query schedule)
- New `vault-template/99-Operations/scripts/telemetry-egress.md` (egress monitor)
- `osquery` added as an optional runtime dependency (INV-6 still holds — the queries
  are deterministic reads, not network or LLM calls)
- This change is **explicitly deferred** per PRD §14.1; this proposal documents the
  design intent for when activation is appropriate (after OS-level ACL hardening)

> **Status: DEFERRED — do not implement until security hardening (§14.1) is complete.**
