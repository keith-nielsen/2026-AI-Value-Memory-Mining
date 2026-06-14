<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0001 — OpenSpec as the SDD Framework

**Status:** Accepted  
**Date:** 2026-06-10

## Context

The repository needs a spec-driven development framework to govern how changes to
the vault methodology are proposed, implemented, and archived. Options considered:

- **Plain Markdown conventions** (proposal docs + manual spec updates) — no tooling
  enforcement, no consistent artifact format, prone to drift
- **OpenSpec** — lightweight CLI, tool-agnostic, iterative not waterfall, brownfield-
  friendly, propose→apply→archive lifecycle with AI-native skill integration
- **Custom framework** — maximum flexibility, maximum maintenance burden

The target audience includes AI coding assistants (Claude Code primary consumer)
and the methodology requires a way to teach the change lifecycle by example.

## Decision

Adopt **OpenSpec** (`@fission-ai/openspec`, `spec-driven` schema) as the SDD
framework for this repository.

ADRs and `openspec/constitution.md` are added as project conventions on top of
the base scaffold — they are not part of the OpenSpec CLI schema but are fully
compatible with it.

## Consequences

- Every change to vault behavior originates as an OpenSpec change (proposal +
  specs + design + tasks), giving contributors a consistent, discoverable path.
- The `.claude/` skills installed by `openspec init` make the lifecycle immediately
  available via `/opsx:propose`, `/opsx:apply`, `/opsx:archive`.
- Archived changes double as teaching artifacts showing the full lifecycle.
- The `spec-driven-with-adr` schema referenced in early design does not exist in
  v1.4.1; ADRs are implemented as a project-level convention instead.
