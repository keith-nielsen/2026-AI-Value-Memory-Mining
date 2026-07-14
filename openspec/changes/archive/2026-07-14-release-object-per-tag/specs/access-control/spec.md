<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: Private by Default — No Unbid Publication (INV-14)

A deployed vault SHALL be private by default. No automated actor (Agent or Script) may push,
mirror, or otherwise replicate vault content to any remote or external/third-party destination,
**except** a destination the operator has explicitly listed in `PUSH_ALLOWLIST` (`config.env`).
With `PUSH_ALLOWLIST` empty (the default), every outbound push is refused.

Creating a public repository, or publishing to an external distribution hub, from within the vault
SHALL require explicit, deliberate **human** confirmation — and SHALL never be initiated as an
agent's unprompted suggestion.

Enforcement is **structural**, never trust-based:
- a deterministic `pre-push` hook (`push-guard-script`, INV-6) that denies by default and permits only
  an allowlisted remote; and
- the agent harness guard (`.claude` `PreToolUse`) that hard-denies any outward command whose
  **effective target** is the deployed vault, and raises a loud ASK **hard stop** before **any** other
  outward-replication or public-facing publication.

The harness guard SHALL judge "targets the vault" from the command's **effective target** — honoring a
leading `cd <path>`, `git -C <path>`, or `gh -R <owner/repo>` redirect, and treating a command that
names the vault path as an outward operand as vault-outward — **not** from the shell's reported working
directory alone (which, in a live agent session, is always the vault even when the command operates on
a sibling repository). Every outward-replication or distribution-publish command that is **not**
vault-denied — including a plain `git push` — SHALL raise the ASK hard stop; no outward command may
silently defer. The ASK is a structural stop: it cannot proceed without an explicit human confirmation
in any permission mode. Before triggering it, the agent SHALL present an overview summary and the
absolute path to the governing `proposal.md`.

This invariant is **additive** to the Safety band and weakens nothing: INV-4/5 bound *writes within*
the vault; INV-14 bounds *replication outward*. INV-14 is appended per the frozen-ID rule (ADR-0008);
INV-1–13 are unchanged.

#### Scenario: Automated push to a non-allowlisted remote is denied
- **WHEN** an Agent or Script triggers `git push` from the vault to a remote not in `PUSH_ALLOWLIST`
- **THEN** the `pre-push` hook aborts with an INV-14 violation; nothing is transmitted

#### Scenario: Agent must not propose outbound publication
- **WHEN** a task could be "helped" by pushing/mirroring vault content outward or creating a public repo
- **THEN** the agent does not suggest or perform it; the harness `PreToolUse` guard denies the vault-outward command and requires deliberate human action for any public publication

#### Scenario: Operator opt-in is explicit and deliberate
- **WHEN** the operator wants an off-machine backup
- **THEN** it is permitted only after the operator deliberately adds that (private) remote to `PUSH_ALLOWLIST`; a tired or quick assent solicited by an agent does not satisfy this

#### Scenario: A publish to a sibling repo from a vault-rooted session is asked, not denied
- **WHEN** the agent runs `gh release create` or `git push` whose effective target is a non-vault
  sibling repository (e.g. `cd <framework-repo> && gh release create …`, or `-R <owner/repo>`) from a
  session where `VAULT_ROOT` is set to the deployed vault
- **THEN** the harness guard does NOT hard-deny it as vault-outward; it raises the ASK hard stop, and the
  command proceeds only on explicit human approval

#### Scenario: A plain git push never defers silently
- **WHEN** the agent runs a `git push` (including `git -C <path> push`) whose effective target is not the
  deployed vault
- **THEN** the harness guard raises the ASK hard stop rather than deferring; the push cannot execute
  without explicit human confirmation, in any permission mode

#### Scenario: Vault-outward push is still hard-denied
- **WHEN** the agent runs any outward command whose effective target is inside the deployed vault (by
  cwd, by `git -C`/`cd` into the vault, or by naming the vault path as an operand)
- **THEN** the harness guard HARD-DENIES it — unchanged; the ASK relaxation applies only to non-vault targets
