<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec delta: maintenance

## ADDED Requirements

### Requirement: The Seed Template Carries The GitHub Read-Hosts

The seed template `vault-template/.claude/settings.json` SHALL carry the GitHub read-hosts as
per-instance defaults: `api.github.com` and `github.com` in `sandbox.network.allowedDomains`, and
`WebFetch(domain:github.com)` in `permissions.allow`. A vault deployed from the template therefore
begins life with GitHub reads available, rather than one denied prompt away from losing them.

`sandbox.network.allowedDomains` is NOT mere prompt-suppression: a non-allowlisted host prompts, and a
denied prompt becomes a **session-scoped deny** — one denied `api.github.com` prompt disables the
already-working anonymous `gh`/REST reads for the rest of the session (the capability probe,
`pr-flow --plan`'s reads, `gh_read.py`'s anonymous fallback, and the ruleset re-measurement the docs
instruct an operator to run), with no error naming the cause.

This is NOT a relaxation of INV-14: the `localhost:3128` proxy is the sole egress regardless, the
allowlist governs **prompting** and never routing, both hosts answer anonymously (no credential is
involved), and the outbound guard keys on **commands**, not hosts. `settings.json` is SEED
(per-instance), never LOCKSTEP, so `template-parity` cannot compare it; the seed default SHALL instead
be asserted by test.

The template SHALL NOT seed `sandbox.filesystem.allowWrite` — a deployed vault grants its own write
scope, and seeding write access to sibling repositories into every deployment would be wrong. Seeded
values are defaults, not lockstep: an instance may legitimately diverge afterwards, which is exactly
why this is a seeded default plus a test rather than a lockstep comparison.

#### Scenario: A deployed vault has GitHub reads available on first run

- **WHEN** a vault is deployed from `vault-template/`
- **THEN** its `.claude/settings.json` carries `api.github.com` and `github.com` in
  `sandbox.network.allowedDomains` and `WebFetch(domain:github.com)` in `permissions.allow`
- **THEN** a denied prompt cannot silently disable GitHub reads, because the hosts are already
  allowlisted

#### Scenario: The seed default is asserted, not compared

- **WHEN** the seed read-hosts are removed from the template
- **THEN** a test fails — `settings.json` is SEED, so `template-parity` cannot catch it, and the
  omission is caught by assertion rather than comparison

#### Scenario: The template seeds no write access to sibling repositories

- **WHEN** the seed template's sandbox is read
- **THEN** it declares no `sandbox.filesystem.allowWrite` — each deployed instance grants its own
