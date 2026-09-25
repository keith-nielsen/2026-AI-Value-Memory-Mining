<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## ADDED Requirements

### Requirement: Supply-Chain Inputs Are Pinned Immutably And Adopted After A Cooldown

Every GitHub Action a workflow references SHALL be pinned to a full 40-hexadecimal commit SHA, followed
by a trailing comment naming its version (`# vX.Y.Z`). A tag SHALL NOT be used as a reference, because a
tag can be re-pointed after review and every consumer then runs the new target with no change in this
repository; a commit SHA cannot. First-party actions are pinned like any other. Only a local action
(`./…`), which is this repository's own code at the checked-out commit, is exempt.

Every Dependabot ecosystem SHALL declare its update cooldown explicitly: **14 days for npm, 7 days for
every other ecosystem**. A cooldown SHALL NOT be left to the platform default, because a default is a
policy this repository does not own and can change without any event here. The cooldown governs
version updates only; security updates are not delayed by it.

Both properties SHALL be enforced by an offline, deterministic test that fails on a tag reference, on a
SHA pin without its version comment, and on a missing or off-policy cooldown.

#### Scenario: A workflow references an action by tag

- **WHEN** any `uses:` line in `.github/workflows/` names a tag or branch instead of a 40-hex commit SHA
- **THEN** the supply-chain test fails, naming the file, line and reference

#### Scenario: A SHA pin carries no version comment

- **WHEN** a `uses:` line is pinned to a commit SHA but has no trailing `# vX.Y.Z` comment
- **THEN** the supply-chain test fails, because the pin can then be neither maintained by Dependabot nor
  read by a reviewer

#### Scenario: An ecosystem inherits the platform's cooldown

- **WHEN** a `package-ecosystem` block in `.github/dependabot.yml` declares no cooldown, or a value other
  than the policy's
- **THEN** the supply-chain test fails, naming the ecosystem and the value found
