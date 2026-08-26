<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0018 — Private by default: INV-14 + the outbound publish guard

**Status:** Accepted
**Date:** 2026-06-29
**Relates:** `access-control` · `maintenance` specs · `constitution.md` (Tier-0) · `project.md` · change
`private-by-default-publish-guard` · extends ADR-0008 (frozen INV IDs)

## Context

A deployed vault holds private, irreversible-if-leaked material. Nothing structural prevented an
automated actor — or a tired human led by one — from publishing it to a public/external remote; the
triggering incident was an agent *suggesting* a push of the private vault to a public repo (captured as
the live-vault `safety-rail-requirements` Claim). Public data is cached, mirrored, indexed; the mistake
is effectively irreversible. Instructions degrade exactly when judgment does — the rail must be
structural and self-defending.

## Decision

- **Add `INV-14` (Tier-0, Safety band):** *private by default; no unbid publication.* No automated actor
  may replicate vault content outward except to an operator-allowlisted remote; public-facing
  publication requires deliberate human confirmation, never an agent's unprompted suggestion. Enforced
  structurally, never by trust. **Appended** per ADR-0008 (INV-1–13 unchanged) — additive, no principle
  weakened; the Safety band is strengthened (INV-4/5 bound writes *within* the vault, INV-14 bounds
  replication *outward*).
- **Home:** `access-control` spec (`protects:` += INV-14, new Requirement); defined in `project.md`.
- **Enforcement (forkable):** `push-guard-script` → `99-Operations/hooks/pre-push`, **deny-by-default**,
  permitting only a remote in `PUSH_ALLOWLIST` (`config.env`); a portable Claude Code `PreToolUse` guard
  (`.claude/hooks/outbound-publish-guard.py`, keyed on `$VAULT_ROOT`/`$CLAUDE_PROJECT_DIR`) that
  hard-denies vault-outward commands and raises a loud confirmation before any public publish.

## Options considered

1. **Memory/instruction only** — rejected: advisory; fails under fatigue (the exact failure mode).
2. **Convention (Tier-2) script** — rejected by the operator: too easy to strip silently.
3. **Tier-0 invariant + structural rails (chosen)** — self-defending: weakening/removing INV-14 itself
   requires the full Informed-Upheaval ceremony. Safe-by-default for every fork.

## Consequences

- A deployed vault cannot push anywhere until the operator deliberately allowlists a (private) remote.
  Forks inherit this deny-by-default posture.
- The protection is **self-defending** — removal is a conscious constitutional act, not a quiet edit.
- The public template repo is unaffected (no `VAULT_ROOT` → vault-deny inert; only the public-publish
  ASK applies, which is appropriate for releases/repo-creation).
- **Sacrifice / honest limit:** the friction of opt-in publishing; and Tier-0 cannot *physically* force a
  fork to stay safe — git hooks don't clone, `--no-verify` bypasses, and an owner can delete the hook or
  set `VAULT_PUBLISH_GUARD=off`. INV-14 guarantees **safe-by-default + governed + loud-to-remove**, not
  an unbreakable cage. OS-level egress control remains a deeper, deferred hardening.
