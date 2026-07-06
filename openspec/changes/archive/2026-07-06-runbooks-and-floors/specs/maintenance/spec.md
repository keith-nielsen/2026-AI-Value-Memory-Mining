<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Platform and Dependency Floors

The fleet SHALL declare and honor explicit floors, so implementers and future models never guess:

- **Python ≥ 3.12** (CI exercises 3.12 and 3.13); language features beyond the floor are not used.
- **Sole third-party dependency: `python-frontmatter`**, installed in the vault-local venv. The
  hook-critical paths — the git hooks, `vault_naming.py --check`, and `vault_lib`'s root/config
  helpers — MUST remain stdlib-only so they run on the system Python without the venv.
- **Platform floor: Linux/POSIX.** Bash hooks, executable bits, and POSIX path semantics are
  assumed; Windows is an explicit non-goal (documented, not silently broken).

#### Scenario: Hook-critical paths run without the venv
- **WHEN** the pre-commit naming gate or `vault_naming.py --check` runs on a system Python with
  no third-party packages installed
- **THEN** it completes normally — no `frontmatter` (or other third-party) import is reached on
  that path

#### Scenario: A new third-party dependency is a governed decision
- **WHEN** a change proposes any import beyond the standard library and `python-frontmatter`
- **THEN** it names the dependency in its proposal and updates this requirement — silent
  dependency growth is a violation
