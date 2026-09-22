<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: seed-github-read-hosts

## Why

The live vault's `.claude/settings.json` was amended (2026-09-19) to carry `WebFetch(domain:github.com)`
plus `api.github.com`/`github.com` in `sandbox.network.allowedDomains`. The seed template was **not**,
so every vault deployed from `vault-template/` ships without them — and `allowedDomains` is not mere
prompt-suppression: a denied prompt becomes a **session-scoped deny**, so one mis-clicked
`api.github.com` prompt silently disables `gh`/REST anonymous reads (the capability probe, `pr-flow
--plan`, `gh_read.py`'s fallback) for the rest of the session, with no error naming the cause. Because
`settings.json` is SEED not LOCKSTEP, `template-parity` cannot see the omission (item 32's blind spot).
This is hardening-queue item 38.

## What Changes

- **`vault-template/.claude/settings.json`** gains the GitHub read-hosts as seed defaults:
  `api.github.com` and `github.com` in `sandbox.network.allowedDomains`, and
  `WebFetch(domain:github.com)` in `permissions.allow`. The vault-specific research domains are **not**
  seeded (they are this vault's content allowlist, not a framework default).
- **The deliberate `allowWrite` decision:** the template seeds **no** `sandbox.filesystem.allowWrite`.
  A deployed vault has no business writing to the framework repo or the development store; each
  instance grants its own write scope. (The dev machine's own vault carries those paths because it IS
  the dev machine — legitimate instance divergence for a SEED value.)
- **A test asserts the seed default** (`tests/test_settings_paths.py`) — since parity cannot compare a
  SEED file, the omission is caught by assertion, not comparison (item 32's shape).

## Impact

- A freshly deployed vault has GitHub reads on first run rather than one prompt from losing them.
- **Not a relaxation of INV-14:** the `localhost:3128` proxy is the sole egress either way, the
  allowlist governs prompting and never routing, no credential is involved, and the outbound guard
  keys on commands not hosts. INV-14 is untouched.
- No behaviour change to any tool; the live vault already has these hosts, so no deploy-down is owed
  for THIS vault — the fix is for future deployments.

## Constitutional impact

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md` (`protects: [INV-2, INV-3,
INV-6]`) documenting the seed read-hosts. Additive; engages none of the three, and INV-14 is
explicitly untouched (host allowlisting governs prompting, the guard governs commands).

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only (a seed default + its test; no invariant engaged, INV-14 untouched)
```

## Verification

- Red-first: the seed-read-hosts test fails against the pre-change template (no `allowedDomains`).
- The template settings.json is valid JSON and carries the two hosts + the WebFetch entry.
- The template seeds no `allowWrite` (the deliberate decision, pinned by a test).
- Full suite, `openspec validate --all --strict`, and markdownlint all clean.
