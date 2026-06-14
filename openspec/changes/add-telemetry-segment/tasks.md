<!-- SPDX-License-Identifier: Apache-2.0 -->
> **DEFERRED — do not implement until security hardening (PRD §14.1) is complete.**
> This task list documents the planned work for when the change is activated.

## 1. Prerequisites (confirm before activating)

- [ ] 1.1 OS-level write-protection of `99-Operations/` is implemented (§14.1)
- [ ] 1.2 osquery is installed and `osqueryi`/`osqueryd` are available on the host
- [ ] 1.3 Confirm osquery license compatibility with Apache-2.0 (Apache-2.0 ✓)

## 2. FIM Query Script

- [ ] 2.1 Write `99-Operations/scripts/telemetry-fim.md` literate meta-script
- [ ] 2.2 Query monitors writes to `40-Treasury/` and `99-Operations/` by unexpected processes
- [ ] 2.3 Output appends to `99-Operations/telemetry/fim.log` (local only, no remote)
- [ ] 2.4 Schedule: every 5 minutes via osquery scheduled query pack

## 3. Egress Monitor Script

- [ ] 3.1 Write `99-Operations/scripts/telemetry-egress.md` literate meta-script
- [ ] 3.2 Query monitors network connections by processes matching `vault_*.py` and `hermes`
- [ ] 3.3 Alert on any connection not to `localhost` (vault processes should be offline, INV-6)
- [ ] 3.4 Output appends to `99-Operations/telemetry/egress.log`

## 4. Spec and Documentation Updates

- [ ] 4.1 Add Telemetry section to `openspec/specs/maintenance/spec.md` (delta below)
- [ ] 4.2 Update `AGENTS.md` to note that telemetry alerts are human-reviewed, not auto-enforced
- [ ] 4.3 Update `SECURITY.md` to remove telemetry from the "deferred" list

## 5. Acceptance Verification

- [ ] 5.1 A test write to `40-Treasury/` by an unexpected process is logged within 10 minutes
- [ ] 5.2 A network connection from `vault_render.py` is logged as an egress alert
- [ ] 5.3 Scheduled queries survive a host restart (`osqueryd` daemon is persistent)
