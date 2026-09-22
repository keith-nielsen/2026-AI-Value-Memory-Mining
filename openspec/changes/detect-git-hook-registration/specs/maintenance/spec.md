<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## ADDED Requirements

### Requirement: Git Hook Registration Is Detected, Not Assumed

The INV-11/INV-7 git hooks (`pre-commit`, `pre-push`) render into `99-Operations/hooks/`, but git
enforces them only when `core.hooksPath` points at that directory. `core.hooksPath` is LOCAL git
config: no tracked file, no `render` run, and no `template-parity` comparison can set or observe it —
it is neither rendered content nor a mirrored file. A deployed vault whose hooks are byte-perfect but
whose `core.hooksPath` is unset therefore enforces NOTHING while reporting clean — the silent-success
class this maintenance corpus exists to catch (kin to F29 and the hook-registration blind spot).

`reconcile` SHALL DETECT this: when `99-Operations/hooks/` holds deployed hooks (anything beyond a
`.gitkeep`) but `core.hooksPath` does not resolve to that directory, `reconcile` SHALL report the gap
— naming the deployed directory, the current `core.hooksPath` value, and the operator fix command —
and SHALL count it as drift (exit 1). `reconcile` SHALL NOT set `core.hooksPath` itself; registration
is a documented operator deploy step (INV-3: reconcile detects drift, it never auto-fixes). The
detection runs in both `render` and `reconcile` modes so a fresh `render` warns the moment the hooks
land unregistered, but only `reconcile` counts it as drift, matching render's own exit contract.

The framework repo deliberately does NOT run this commit gate locally — its `core.hooksPath` is unset
by design and CI is its backstop; this requirement governs deployed vaults, where the gate is
load-bearing.

#### Scenario: Deployed-but-unregistered hooks are reported as drift

- **WHEN** `reconcile` runs in a vault where `99-Operations/hooks/` holds deployed hooks but
  `core.hooksPath` does not point at that directory
- **THEN** it prints a finding naming the gap and the operator fix
  (`git config core.hooksPath 99-Operations/hooks`) and exits 1 — the silent-success (byte-perfect
  hooks enforcing nothing) is made loud
- **THEN** it does not set `core.hooksPath` itself

#### Scenario: Registered hooks reconcile clean

- **WHEN** `core.hooksPath` resolves to the deployed hook directory
- **THEN** `reconcile` reports the hooks as registered and does not flag them

#### Scenario: An empty template hooks directory is not a finding

- **WHEN** the hooks directory holds only `.gitkeep` (nothing deployed yet, the template shape)
- **THEN** `reconcile` does not report an unregistered-hooks finding — the check fires only when real
  hooks are present
