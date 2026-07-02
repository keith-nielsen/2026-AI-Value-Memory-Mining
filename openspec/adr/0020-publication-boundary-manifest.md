<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0020 — Publication boundary: path-level default-deny manifest (extends INV-14)

**Status:** Accepted (Gate-4 sign-off: Keith Nielsen, 2026-07-02; drafted by Claude Code)
**Date:** 2026-07-02
**Relates:** `access-control` · `maintenance` specs · `constitution.md` (Tier-0) · change `publication-boundary-manifest` · **extends ADR-0018** (private-by-default publish guard) · ADR-0008 (frozen INV IDs — no new invariant)

## Context

ADR-0018 made a deployed vault private-by-default at the **remote** level: the `pre-push` guard denies
every push unless the target is in `PUSH_ALLOWLIST`. That closes the "push anywhere" hole but not the
"push the wrong *paths* to an intentionally-public remote" hole. As soon as an operator wants a public
*framework* mirror (the template repo), the remote-level rule alone would permit a push whose diff
includes private content — Claims, Sites, Treasury, Warehouse, the live `config.env`. Publication is
irreversible. The boundary needs to be path-aware, and the private config instance should not be
publishable at all. Guiding principle: **publish the machine, never the ore.**

## Decision

- **Path-level, default-deny publication allowlist.** `99-Operations/schemas/publish-manifest.json`
  lists `public_allow` globs (framework only: `CLAUDE.md`, `96-Runbooks/**`, `97-Molds/**`,
  `99-Operations/{scripts,schemas,hooks}/**`, `config.defaults.env`, `00-Docs/**`, `**/.gitkeep`).
  Anything unmatched is private by default (fail-safe).
- **Public-remote path gate.** A new `PUBLIC_REMOTE_ALLOWLIST` (`config.env`) designates remotes that may
  receive **only** manifest-allowed paths; `push-guard-script` refuses a push to such a remote whose diff
  touches any other path. Additive to — never replacing — the remote-level deny-by-default gate; both
  allowlists empty by default (posture unchanged).
- **Framework/instance config separation.** Public `config.defaults.env` (tracked, sourced first) +
  private `config.env` (gitignored overrides, sourced last). The private instance is never published;
  framework defaults flow to forks; every existing `source config.env` is unchanged in effect.
- **Home:** `access-control` spec (ADDED Requirement under INV-14; MODIFIED Secrets scenario);
  `maintenance` spec (Script Inventory: push-guard path-gate + `publish-manifest.json`).
- **No new invariant.** This is enforcement depth under the existing INV-14 (ADR-0008 untouched).

## Options considered

1. **Remote-level guard only (status quo, ADR-0018)** — rejected: leaks private paths to a public mirror.
2. **Denylist of private paths** — rejected: fail-open; one forgotten entry publishes private content.
3. **Default-deny path allowlist + public-remote gate (chosen)** — fail-safe; new paths private by default;
   layers cleanly on ADR-0018.

## Consequences

- A push to a public-designated remote can carry **only** framework paths; private content is refused,
  named path-by-path. Forks inherit this via the `vault-template/` mirror.
- The private `config.env` is gitignored and unpublishable; forks get working defaults from
  `config.defaults.env`.
- **Sacrifice / honest limit:** additive — strengthens INV-14, weakens nothing. Cost: more guard logic +
  a `publish-manifest.json` to maintain (deliberately, fail-safe). The `pre-push` hook covers `git push`
  only — a future public-export/mirror tool MUST also honor the manifest. Inherits ADR-0018's bypasses
  (`--no-verify`, hook-strip, `VAULT_PUBLISH_GUARD=off`): safe-by-default + governed + loud-to-remove,
  not an unbreakable cage.
