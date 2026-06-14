<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: File-Integrity Monitoring (FIM) on Protected Areas
osquery scheduled queries monitor writes to `40-Treasury/` and `99-Operations/`
by processes other than those in the approved script set.

#### Scenario: Unexpected Treasury write is logged
- **WHEN** a process not in the approved set writes a file under `40-Treasury/`
- **THEN** the FIM query detects the event within 10 minutes
- **THEN** an alert is appended to `99-Operations/telemetry/fim.log`
- **THEN** no automatic enforcement occurs (detect only; operator reviews)

### Requirement: Egress Monitoring for Vault Processes
osquery monitors network connections opened by `vault_*.py` and `hermes` processes.
Connections to anything other than `localhost` are flagged (vault scripts are offline,
INV-6; any outbound connection is anomalous).

#### Scenario: Unexpected egress connection is logged
- **WHEN** a vault script opens a non-localhost network connection
- **THEN** the egress query logs it to `99-Operations/telemetry/egress.log`
- **THEN** the alert includes: process name, PID, remote address, timestamp
