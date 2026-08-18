<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: Fleet Executables Carry The Vault Prefix

Every rendered fleet executable SHALL be named with a `vault-` or `vault_` prefix.

The fleet's deploy directory is placed on `PATH` by `config.env`, so its names share a namespace with
every other executable a shell can reach. The operation currently has zero collisions across every
directory on `PATH`, and the prefix is the sole reason — an accident that has never been written down.
`vault` is a widely installed binary name, so the collision the prefix prevents is realistic rather
than theoretical.

`PATH` contribution SHALL be **appended, not prepended**, and SHALL be idempotent under repeated
sourcing. Prepending would give fleet executables precedence over system binaries throughout any shell
that sourced the configuration, which the prefix makes unnecessary; and a non-idempotent contribution
accumulates a duplicate entry on every re-source.

`config.env` SHALL be the only place the deploy directory is added to `PATH`. No shell profile is
modified, so the contribution is scoped to shells that opt in and vanishes when they exit.

#### Scenario: An unprefixed fleet executable is refused
- **WHEN** a script note declares a `deploy_target` whose basename lacks a `vault-` or `vault_` prefix
- **THEN** the naming check fails, naming the note and the target

#### Scenario: Repeated sourcing does not duplicate the path entry
- **WHEN** `config.env` is sourced three times in one shell
- **THEN** the deploy directory appears exactly once in `PATH`
