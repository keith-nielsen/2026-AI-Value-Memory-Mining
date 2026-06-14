<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Phase 3 Harness Is Disabled by Default
The harness defaults to `--dry-run`; no live model is wired in this change.

#### Scenario: Dry-run produces a schema-valid proposal
- **WHEN** the harness runs in `--dry-run` mode
- **THEN** it writes a valid proposal JSON to `_refine-proposals/` and makes no network call

### Requirement: Harness Has No Treasury or Operations Write Path
- **WHEN** the harness source is inspected
- **THEN** no code path opens or writes files under `40-Treasury/` or `99-Operations/`

### Requirement: Hermes Runtime Mapping Is Fixed
The workspace is `dir:<VAULT_ROOT>/30-Sites/<slug>`, dispatch is one-shot, done
state is `kanban_complete()` on deposit, and the toolset must not enable Treasury
or Operations writes.

#### Scenario: Blocked worker never writes partially
- **WHEN** the harness cannot produce a clean proposal
- **THEN** it calls `kanban_block(reason=...)` and writes nothing
