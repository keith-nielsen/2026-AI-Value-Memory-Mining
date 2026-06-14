<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0005 — n8n as the Orchestration/Firewall Layer

**Status:** Accepted (build deferred — see PRD §14.1)  
**Date:** 2026-06-10

## Context

The agent pipeline (Phase 3+) needs an orchestration layer that:
1. Controls which external services the agent runtime can reach (egress firewall)
2. Provides event-driven triggers (new ore detected → dispatch refine card)
3. Stays local-first and self-hostable (no SaaS dependency)

Options:
- **Direct Hermes → cloud/local-LLM** — no intermediary; maximum simplicity,
  minimum control; no egress filtering
- **Zapier / Make** — cloud SaaS; violates the privacy/sovereignty posture of a
  personal vault; introduces a data-path outside the operator's control
- **n8n (self-hosted)** — open-source workflow automation; self-hostable; can act
  as an outbound firewall by being the only process with network egress; local
  webhook triggers work without external dependencies

## Decision

Use **n8n (self-hosted)** as the orchestration and egress-control layer when
agent operations are activated (deferred, §14.1). n8n sits between Hermes Agent
and any external services; the vault's deterministic scripts (INV-6) never call
it — only the agent-orchestration layer does.

## Consequences

- n8n provides a visual audit trail of all automation flows.
- Egress control is architectural: the vault host only needs outbound access to n8n,
  not to arbitrary external endpoints.
- n8n is orchestrated, not vendored — it runs as a separate process.
- Sacrifice: adds operational complexity (one more self-hosted service to maintain).
  This is acceptable given the privacy/sovereignty requirement for a personal vault.
- **Build deferred**: this ADR records the decision for when Phase 3 is activated;
  nothing in Phases 0–2 depends on n8n.
