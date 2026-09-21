<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: access-control

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
- the agent harness guard (`.claude` `PreToolUse`) that HARD-DENIES (a) any outward command whose
  **effective target** is the deployed vault, and (b) any **irreversible** outward command regardless
  of target (see "Irreversible Outbound Is Operator-Only"); and raises a loud ASK **hard stop** on the
  one remaining outward form — a reversible branch push to a non-vault target.

The harness guard SHALL judge "targets the vault" from the command's **effective target** — honoring a
leading `cd <path>`, `git -C <path>`, or `gh -R <owner/repo>` redirect, and treating a command that
names the vault path as an outward operand as vault-outward — **not** from the shell's reported working
directory alone (which, in a live agent session, is always the vault even when the command operates on
a sibling repository).

The ASK raised on a reversible branch push prompts for explicit human confirmation **in an interactive
session**. ⚠ It does **not** hold in every permission mode: measured 2026-09-20, under **auto mode** a
`PreToolUse` ASK **silently proceeds** — it neither prompts nor blocks. The ASK is therefore relied
upon only where its failure is tolerable: a branch push, whose ref is reversible (force-push / delete)
and whose disclosure to a non-vault remote is an accepted residual. For every **irreversible** outward
command the guard emits a **DENY**, not an ASK, precisely because DENY holds in every mode while the
ASK does not (F31 — a control is described at the strength it has). The `pre-push` hook and the
server-side ruleset are the mode-independent backstops beneath both.

This invariant is **additive** to the Safety band and weakens nothing: INV-4/5 bound *writes within*
the vault; INV-14 bounds *replication outward*. INV-14 is appended per the frozen-ID rule (ADR-0008);
INV-1–13 are unchanged.

#### Scenario: Automated push to a non-allowlisted remote is denied

- **WHEN** an Agent or Script triggers `git push` from the vault to a remote not in `PUSH_ALLOWLIST`
- **THEN** the `pre-push` hook aborts with an INV-14 violation; nothing is transmitted

#### Scenario: Agent must not propose outbound publication

- **WHEN** a task could be "helped" by pushing/mirroring vault content outward or creating a public repo
- **THEN** the agent does not suggest or perform it; the harness `PreToolUse` guard denies the vault-outward command
  and requires deliberate human action for any public publication

#### Scenario: Operator opt-in is explicit and deliberate

- **WHEN** the operator wants an off-machine backup
- **THEN** it is permitted only after the operator deliberately adds that (private) remote to `PUSH_ALLOWLIST`; a
  tired or quick assent solicited by an agent does not satisfy this

#### Scenario: A reversible branch push to a sibling repo is asked, not denied

- **WHEN** the agent runs a `git push` of a branch (not a tag) whose effective target is a non-vault
  sibling repository, from a session where `VAULT_ROOT` is set to the deployed vault
- **THEN** the harness guard does NOT hard-deny it as vault-outward, and does NOT deny it as
  irreversible; it raises the ASK hard stop (which prompts in an interactive session)

#### Scenario: A reversible branch push never defers silently in an interactive session

- **WHEN** the agent runs a `git push` (including `git -C <path> push`) of a branch whose effective
  target is not the deployed vault, in an interactive session
- **THEN** the harness guard raises the ASK hard stop rather than deferring; the push cannot execute
  without explicit human confirmation
- **THEN** in auto mode the ASK does not surface and the push may proceed — an accepted residual,
  because the branch ref is reversible; the guard does not overstate this as an all-modes stop

#### Scenario: Vault-outward push is still hard-denied

- **WHEN** the agent runs any outward command whose effective target is inside the deployed vault (by
  cwd, by `git -C`/`cd` into the vault, or by naming the vault path as an operand)
- **THEN** the harness guard HARD-DENIES it — unchanged; the ASK relaxation applies only to non-vault,
  reversible targets

## ADDED Requirements

### Requirement: Irreversible Outbound Is Operator-Only (INV-14)

The harness `PreToolUse` outbound guard SHALL **hard-DENY** every outward command that is not a plain
branch push — because such commands are **irreversible** (git and the server-side ruleset cannot roll
them back) and the ASK the guard would otherwise raise does not hold in auto mode. Denied forms
include: a `v*` tag push (`refs/tags/…`), `git remote add|set-url`, `gh repo create` / `gh repo edit
--visibility public`, a release publish / edit / upload (the subcommand forms and the REST endpoints
that write a release), a release asset upload, and a package publish (`npm`/`yarn`/`pnpm`/`twine`/
`docker`/`cargo`/`gem`). The one outward form that is **not** denied is a branch push, whose ref is
reversible.

The refusal SHALL be evaluated **before** the driver-emission downgrade, so that an irreversible
command is denied even when it byte-matches a driver's emitted command: irreversible outbound is the
operator's, run in their own terminal (via the ceremony), where this `PreToolUse` hook does not fire.
The refusal SHALL name the operator as the actor who runs it, so a denial produces a handoff rather
than a dead end.

This is a **DENY**, not an ASK, deliberately: DENY holds in every permission mode, whereas the ASK
was measured to silently proceed in auto mode. The vault HARD DENY (effective target inside the vault)
is evaluated first and is unchanged.

#### Scenario: A release publish is denied on the agent's channel

- **WHEN** the agent runs a release publish — `gh release create`, or a REST write to a release
  endpoint (`POST /repos/{slug}/releases`, `PATCH`/`DELETE` on a release) — with any non-vault target
- **THEN** the harness guard HARD-DENIES it and names the operator as the actor who runs it
- **THEN** it is denied even if the command byte-matches a live driver emission (the check precedes the
  downgrade)

#### Scenario: A version tag push is denied

- **WHEN** the agent runs `git push … refs/tags/vX.Y.Z`
- **THEN** the harness guard HARD-DENIES it — a published `v*` tag is frozen by the ruleset and cannot
  be moved or deleted, so it is irreversible and operator-only

#### Scenario: Adding a remote or creating a repository is denied

- **WHEN** the agent runs `git remote add|set-url`, `gh repo create`, or `gh repo edit --visibility
  public`
- **THEN** the harness guard HARD-DENIES it as irreversible outbound

#### Scenario: A branch push is not caught by this requirement

- **WHEN** the agent runs a `git push` of a branch (no `refs/tags/`) to a non-vault target
- **THEN** the irreversible-outbound DENY does NOT fire; the command falls through to the
  driver-emission downgrade or the ASK, per "Private by Default"
