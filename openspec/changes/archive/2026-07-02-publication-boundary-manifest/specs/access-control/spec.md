## ADDED Requirements

### Requirement: Publication Boundary — Path-Level Manifest for Public Remotes (INV-14)

Under INV-14, a deployed vault SHALL enforce publication **at the path level** for any remote the
operator designates public. The publishable surface is a **default-deny allowlist**:
`99-Operations/schemas/publish-manifest.json` lists the `public_allow` path globs (framework machinery
only — e.g. `CLAUDE.md`, `96-Runbooks/**`, `97-Molds/**`, `99-Operations/{scripts,schemas,hooks}/**`,
`config.defaults.env`, `00-Docs/**`, `**/.gitkeep`). Any path not matched is **private by default**
(fail-safe: a new or forgotten path stays private).

A remote listed in `PUBLIC_REMOTE_ALLOWLIST` (`config.env`) MAY receive **only** manifest-allowlisted
paths; a push to such a remote whose diff touches any non-allowlisted path SHALL be refused. This layer
is **additive** to — never a replacement for — the remote-level deny-by-default rule (a remote not in
`PUSH_ALLOWLIST` and not in `PUBLIC_REMOTE_ALLOWLIST` is still refused outright). `PUBLIC_REMOTE_ALLOWLIST`
empty (the default) ⇒ the path-gate is inert and posture is unchanged. Enforced structurally by the
deterministic `push-guard-script` (`pre-push`, INV-6); the same manifest MUST be honored by any future
public-export/mirror tool. Principle: *publish the machine, never the ore.*

#### Scenario: Private path to a public remote is refused
- **WHEN** a push targets a remote in `PUBLIC_REMOTE_ALLOWLIST` and the pushed diff touches a path not matched by `publish-manifest.json` `public_allow` (e.g. `30-Sites/…`, `98-Warehouse/…`, `99-Operations/config.env`)
- **THEN** the `pre-push` hook aborts with an INV-14 path-boundary violation naming the offending path; nothing is transmitted

#### Scenario: Framework-only push to a public remote is permitted
- **WHEN** a push targets a `PUBLIC_REMOTE_ALLOWLIST` remote and every path in the diff matches `public_allow`
- **THEN** the push is permitted

#### Scenario: Default-deny is fail-safe for new paths
- **WHEN** a new top-level path exists that is not listed in `publish-manifest.json`
- **THEN** it is treated as private and cannot be pushed to a public remote until deliberately added to `public_allow`

## MODIFIED Requirements

### Requirement: Secrets Prohibition (INV-7)

No credentials, API keys, tokens, or passwords SHALL appear in any vault file.
Scripts read secrets from the environment (`os.environ`), not from vault files.
Structural configuration is split into a **public defaults** file and a **private instance**:
`99-Operations/config.defaults.env` (tracked, framework defaults — vocabularies, guard defaults) is
sourced first; `99-Operations/config.env` (gitignored, personal/machine overrides — absolute
`VAULT_ROOT`, `PATH`, any customized `PILLARS`) is sourced last and never published. Neither contains
credentials.

#### Scenario: No secrets in config; private instance is gitignored
- **WHEN** `config.defaults.env` and `config.env` are inspected
- **THEN** they contain only structural configuration (`VAULT_ROOT`, `PILLARS`, `GRADES`, `REFINE_GATE_GRADES`, `KNOWLEDGE_STAGES`, `EFFORT_STATUSES`, `SPOIL_STATUSES`, `DISPOSITIONS`, `VAULT_PUBLISH_GUARD`, `PUSH_ALLOWLIST`, `PUBLIC_REMOTE_ALLOWLIST`) — no credentials
- **THEN** the live `config.env` is gitignored (private instance); only `config.defaults.env` + `config.env.example` are tracked/publishable
