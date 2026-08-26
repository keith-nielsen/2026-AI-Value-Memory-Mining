<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0015 — Token-minimum naming: ≥3 tokens (floor, not ceiling), silo-section-descriptor

**Status:** Accepted
**Date:** 2026-06-27
**Relates:** `naming-rules` spec (INV-11) · change `naming-3token-minimum` · extends ADR-0013 (naming-and-identity)
and ADR-0014 (mold-naming)

## Context

Filenames need enough disambiguating context as the vault grows. Generic, short stems collide and
go anonymous in flat/search/migrated views (the problem ADR-0013/0014 began addressing for indexes
and molds). A general rule is needed so every artifact carries enough signal — and so it survives the
namespace becoming contention-prone as broad topics narrow and digs reveal sub-sectors.

## Decision

ADD a *Token-Minimum Naming* requirement to `naming-rules`:

- **≥3 hyphen-tokens — the floor, not the ceiling**; use *more* wherever the extra tokens add
  human-meaningful specificity.
- **System-artifact families** (molds, scripts, Catalog indexes, schemas) → `silo-section-descriptor`,
  silo first (e.g. `daily-mold-blank`).
- **Content stems** (Claims/Sites/Treasury) → ≥3-token topic slugs; longer is correct.
- **Dailies** (`YYYY-MM-DD`) exempt. Existing sub-3 names **grandfathered**; each family conforms via
  its own change.

## Options considered

1. **Convention now vs mechanical enforcement now** — chose **convention now**. Turning on validator
   rejection of sub-3 stems while pre-existing sub-3 names exist (indexes, content) would block all
   commits until every family is renamed. So the rule lands as documented convention (SSOT in the
   spec + agent guidance), and mechanical enforcement (`vault_naming.py` + commit-gate hook +
   `naming-rules.json`) is a **separate later change**, gated on full conformance.
2. **≥3 floor vs exactly-3** — chose **floor, not ceiling**. A fixed "exactly 3" would force
   minimisation and lose specificity; the rule explicitly invites more tokens where they help.

## Consequences

- The spec is the single source of truth for the rule; agents get it via `AGENTS.md`.
- Families conform incrementally (molds done in v0.1.7; scripts/schemas/indexes/content queued); the
  eventual enforcement change is the backstop.
- **Sacrifice:** none structural — the rule is convention-level until enforcement is wired, and no
  name is renamed by this change. The cost deferred to the enforcement change is bringing the
  remaining families into conformance before rejection can be turned on.
