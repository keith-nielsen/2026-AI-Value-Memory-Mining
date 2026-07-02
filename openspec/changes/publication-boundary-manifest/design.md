## Context

ADR-0018/INV-14 established private-by-default at the **remote** level (deny every push unless the
remote is allowlisted). A residual gap: if an operator ever allowlists a remote meant to receive only
*framework* content — a public template mirror — the remote-level rule alone would let a push of
**private** paths through. Publication is irreversible (cached/mirrored/indexed). The guarantee should
be **path-aware**, and the private config instance should not be publishable at all.

This change was implemented in the live vault ahead of the ceremony (ratify-in-place); this record
documents and ratifies it, and carries the mirror into `vault-template/` so forks inherit it.

## Goals / Non-Goals

**Goals:** a fail-safe (default-deny) path-level publication allowlist enforced by the deterministic
push-guard for public-designated remotes; clean framework/instance config separation so the private
`config.env` is gitignored behind public defaults.

**Non-Goals:** replacing the remote-level INV-14 gate (this layers on it); building the public-export
tool itself (only specifying that it MUST honor the manifest); OS-level egress control (deferred).

## Decisions

- **Additive, under existing INV-14 — not a new invariant.** The path-gate only ever *refuses more*; it
  never permits a push the remote-level rule would deny. No frozen-ID impact (ADR-0008).
- **Default-DENY allowlist, not a denylist.** Fail-safe: a new/forgotten path is private automatically.
  A denylist is fail-open (one missing entry leaks). Mirrors INV-14's deny-by-default philosophy.
- **Two independent allowlists.** `PUSH_ALLOWLIST` = full-vault private-backup remotes (unchanged).
  `PUBLIC_REMOTE_ALLOWLIST` = remotes that may receive only manifest-allowed paths. Both empty by default.
- **Layered config (defaults + gitignored override), not append/clobber.** `config.defaults.env`
  (public, sourced first) + `config.env` (private overrides, sourced last, gitignored). Every existing
  `source config.env` keeps working; framework default updates flow without overwriting personal values.
- **Language-neutral manifest.** `publish-manifest.json` mirrors the allowlist for non-Python consumers
  (a future export tool, JS/Obsidian plugin), the same pattern as `naming-rules.json`.

## Risks / Trade-offs

- **Inherited honest limit (ADR-0018):** `--no-verify`, hook-strip, `VAULT_PUBLISH_GUARD=off` all bypass;
  not an unbreakable cage. Safe-by-default + governed + loud-to-remove.
- **A future public-export tool must also honor the manifest** — the hook covers `git push`, not an
  arbitrary copy tool. Recorded as a standing requirement on that (deferred) tool.
- **Maintenance:** the `public_allow` list must be extended deliberately as new framework paths appear —
  which is the point (fail-safe).
