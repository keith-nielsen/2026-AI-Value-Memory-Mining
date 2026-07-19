<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Operator-Only Paths Fail Legibly

A fleet script whose write target lies in an area the Area Access Matrix withholds from the agent
SHALL, on a write refused by the OS sandbox (`OSError` with `errno == EROFS`), exit with a distinct
status of **4** and a message that names the path, states the denial is **by design**, and directs the
reader to run the step as the operator. It SHALL NOT emit a bare traceback for this case, and SHALL
re-raise any other `OSError` unchanged.

The denial itself is correct and is not relaxed: `vault-render.py render` writes only
`deploy_target`s (`~/bin/`, `99-Operations/hooks/`, `.claude/hooks/`) and `vault_naming.py` in emit
mode writes only `99-Operations/schemas/naming-rules.json` — all areas the matrix marks `A: —` or
places outside the vault. What changes is legibility. A bare traceback carries no signal that the
failure is intentional, so the reader's first hypothesis is a broken deploy, a missing dependency, or a
misconfigured sandbox, and time is spent debugging a fault that does not exist. This is strictly worse
after the Stage-B strict flip, which removes the burn-in fallback that currently makes such failures
survivable.

Exit **4** is reserved for "denied by design" so that a caller can distinguish it from a genuine fault
(exit 1). Read-only modes are unaffected and MUST remain available: `vault-render.py reconcile` still
reports drift, and `vault_naming.py --check` / `--check-strict` still gate commits.

#### Scenario: Render refused by the sandbox explains itself
- **WHEN** `vault-render.py render` attempts a `deploy_target` write and the OS sandbox refuses it with
  `EROFS`
- **THEN** it prints the blocked path, states that render is an operator-only path denied by design,
  notes that this is not a broken deploy, directs the reader to run it as the operator, and points at
  `reconcile` as the still-available read-only mode
- **THEN** it exits **4**, and no traceback is printed

#### Scenario: Schema regeneration refused by the sandbox explains itself
- **WHEN** `vault_naming.py` is run in emit mode and the write to
  `99-Operations/schemas/naming-rules.json` is refused with `EROFS`
- **THEN** it prints an equivalent operator-only message and exits **4**
- **THEN** `--check` and `--check-strict` are unaffected, so the commit gate continues to function

#### Scenario: A genuine I/O fault is not swallowed
- **WHEN** either script's write fails with an `OSError` whose `errno` is **not** `EROFS` — a full disk,
  a permission error, a missing parent
- **THEN** the exception propagates unchanged, so a real fault is never disguised as a governance denial
