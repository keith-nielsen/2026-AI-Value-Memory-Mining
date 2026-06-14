<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0007 — Apache-2.0 License

**Status:** Accepted (LOCKED)  
**Date:** 2026-06-10

## Context

The repository is intended for broad public adoption as a template. License options:

- **MIT** — maximally permissive; no explicit patent grant; widely understood
- **Apache-2.0** — permissive; includes an explicit patent grant; contributor
  patent retaliation clause; NOTICE file convention for attribution
- **GPL/AGPL** — copyleft; would require any derivative work to be open-source;
  incompatible with the broad-adoption goal
- **Creative Commons** — appropriate for content, not software/configuration

**Patent/disclosure note:** publishing this repository discloses the Value Mining
methodology, foreclosing most patent routes (absolute novelty abroad; 1-year US
grace period). Protectable assets going forward are the brand/name (trademark),
the specific implementation, and any services/premium tiers.

## Decision

License under **Apache-2.0**. Add `LICENSE`, `NOTICE`, per-file SPDX headers
(`SPDX-License-Identifier: Apache-2.0`), and a copyright line
(`Copyright 2026 Keith Nielsen`).

No CLA is required at launch — Apache alone permits anyone (including competitors)
to commercialize. A CLA is only needed if commercialization-around-the-process is
later pursued.

## Consequences

- Anyone can fork, modify, and distribute — including commercially — without
  opening their changes.
- The explicit patent grant reduces legal risk for enterprise adopters.
- The NOTICE file must be maintained as third-party components are added.
- Trademark of the framework name is a separate track from this license decision.
