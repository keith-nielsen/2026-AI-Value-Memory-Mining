<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: access-control

## ADDED Requirements

### Requirement: The Outbound Guard Judges Commands, Not Prose, And Never Fails Open (INV-14)

The harness `PreToolUse` outbound guard (`outbound-publish-guard-script`) is a conservative belt over
the load-bearing, env-free, fail-closed `pre-push` hook and the vault's remotelessness — it SHALL
narrow its false denials and close its fail-open **without weakening the true-positive set**: a
vault-outward or irreversible-outward command SHALL be denied in every case it was before.

**Prose is data, not a command.** The guard SHALL apply its outward-command matching to the
command's executable text: a `-m`/`--message`/`-F`/`--file` argument value (a commit message, a PR
body) that merely NAMES an outward command SHALL NOT raise the guard. Heredoc bodies SHALL NOT be
stripped — a heredoc can be executed, so the guard keeps conservatively over-firing there.

**The mandated bootstrap idiom resolves.** The guard SHALL resolve the effective target through an
optional leading `source <config>;` (or `. <config>;`) prefix before a `cd <path>`, as well as a bare
leading `cd` — so a command redirected to a non-vault sibling by the runbook-mandated idiom is not
mis-attributed to the reported working directory.

**It SHALL NOT fail open.** When neither `$VAULT_ROOT` nor `$CLAUDE_PROJECT_DIR` is set, the guard
SHALL determine whether the command's effective target is a vault by the presence of a vault marker
(`99-Operations/config.env`) at or above that target — a vault is defined by its marker — so a vault
whose environment was dropped is still protected and a non-vault tree stays inert. The environment-set
path is unchanged.

**A vault-outward deny SHALL explain its cause**, including the common case where no redirect was
recognised and the target fell back to the working directory, so the operator is not left to derive
why an apparently sibling-targeted command was refused.

#### Scenario: A commit message naming an outward command does not raise the guard

- **WHEN** a `git commit -m "…"` (or `-F <file>`) carries a message that mentions an outward command
  in its text, and the command itself is a local commit
- **THEN** the guard neither denies nor asks — the outward tokens live in a message body, which is
  data, not an executed command
- **THEN** a real outward command sharing the line (a genuine push, or a real publish carrying a
  non-message flag) is still matched — stripping the message does not hide the command

#### Scenario: The sanctioned bootstrap idiom resolves the effective target

- **WHEN** a command is `source <config>; cd <sibling-repo> && <outward>` — the mandated idiom
- **THEN** the guard resolves the effective target to the sibling repo, not the working directory, and
  does not hard-deny it as vault-outward
- **THEN** the same idiom pointed AT the vault is still hard-denied

#### Scenario: An unset environment does not fail open

- **WHEN** neither `$VAULT_ROOT` nor `$CLAUDE_PROJECT_DIR` is set and an outward command's effective
  target is a tree carrying a vault marker (`99-Operations/config.env`)
- **THEN** the guard HARD-DENIES it — it does not fall through for want of an environment variable
- **WHEN** the effective target has no vault marker (a plain repository)
- **THEN** the guard does not hard-deny it as vault-outward; the outward ASK / irreversible-DENY rails
  still apply

#### Scenario: A vault-outward deny names its cause

- **WHEN** the guard hard-denies a command whose effective target fell back to the working directory
  because no redirect was recognised
- **THEN** the deny message says so and names how to target a sibling (`git -C <path>` or a leading
  `cd`)
