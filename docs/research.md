---
title: "Agentic AI Workflows — Background Research (2026)"
source: "source/agentic-ai-workflows-report.md"
date: "2026-06"
---

# Agentic AI Workflows — Background Research (2026)

This document summarises the research that informed the architectural choices in
this system. The full report is in `source/agentic-ai-workflows-report.md`.

---

## The Landscape Split

The agentic AI space in 2026 divides sharply into two worlds:

**Enterprise** (Salesforce Agentforce, Microsoft Copilot Studio, UiPath, ServiceNow,
IBM watsonx Orchestrate): multi-agent orchestration across business systems with
built-in governance and compliance. Gartner projects 40%+ of enterprise applications
will embed role-specific AI agents by end of 2026.

**Individual / power-user**: a three-layer stack has emerged with strong consensus:
1. Knowledge base ("second brain") — where notes and context live
2. AI agent layer — the LLM that reasons over your data
3. Automation/orchestration layer — connecting tools and triggering workflows

This system is designed for the individual layer.

---

## Knowledge Base: Why Obsidian

The 2026 consensus strongly favors Obsidian for AI-native personal workflows:

- **Plain text is AI-native.** Markdown files can be read and written by any AI agent
  without an API layer, conversion, or vendor lock-in.
- **Any-model flexibility.** Connect to Claude, GPT, Gemini, local Ollama models, or
  any future model. No provider lock.
- **MCP integration with Claude Code.** Direct vault read/write without plugins.
- **2,700+ plugins** as of February 2026; 1.5 million users (22% YoY growth). Smart
  Connections (RAG), Dataview (frontmatter queries), and Bases feature compete
  increasingly with Notion's structured data.
- **Full offline access and data ownership.** Files never leave the machine without
  explicit sync.

Notion remains strong for team collaboration but has structural liabilities for
personal AI workflows: cloud dependency, proprietary format, single AI vendor,
increasingly painful search at scale.

---

## The Convergent Stack

Four tools appear together in nearly every successful individual workflow:

| Layer | Tool | Why |
|-------|------|-----|
| Knowledge base | Obsidian | Local-first, plain-text, AI-native |
| Orchestration | n8n (self-hosted) | Visual workflows, API connections, local control |
| Agent layer | Claude / local LLM | Reasoning over vault content |
| Local inference | Ollama / LM Studio | Privacy-preserving, offline, cost-controlled |

The hybrid model — cloud model for reasoning, local model for sensitive tasks — is the
most common pattern. Full local (Strix Halo + llama.cpp + Ollama) is emerging as
viable for power users who want complete data isolation.

---

## What Works: Practitioner Consensus

From aggregated practitioner reports:

**High-value patterns:**
- **Structured capture → structured vault.** Systems with enforced frontmatter schemas
  dramatically outperform unstructured archives for AI retrieval quality. The AI
  extracts better signal when the metadata is machine-readable.
- **Git as the ground truth.** Using git for version control over Markdown vaults
  enables rollback, audit trail, and conflict detection — especially important when
  agents write to the vault.
- **Separation of concerns: script vs. agent.** Deterministic operations (daily notes,
  lint, disposal) should never call LLMs. Mixing deterministic and agentic paths
  in the same script is a common failure mode.
- **Proposal-only agents.** Practitioners who allowed agents to write directly to
  their knowledge archives consistently reported trust erosion. Those who gated
  agent writes through human approval kept high archive quality.
- **Local-first, cloud-bootstrap.** Start with cloud models for reasoning; migrate
  high-sensitivity tasks to local inference as models improve. Design for model
  swappability from the beginning.

**Common failure modes:**
- Inbox growth without triage — the vault becomes another pile to avoid.
- Trusting agent output without verification — quality degrades over time.
- Naming chaos — inconsistent file/folder names break linking and search.
- Auto-sync collisions — multiple devices writing to the same vault without conflict
  detection.

---

## Security Considerations

Personal knowledge vaults are high-sensitivity targets: they contain daily logs,
financial notes, health information, social observations, and operational metadata.

Key risks practitioners report:
- **Exfiltration via agent toolsets.** An agent with read access to a vault and
  network egress can exfiltrate its entire contents. Network-isolated agent execution
  is the only reliable mitigation.
- **Prompt injection via vault content.** Maliciously crafted notes can redirect an
  agent's behavior. Sandboxing agent reads to specific folders is partial mitigation.
- **Sync-as-exfiltration.** Cloud sync services (iCloud, Dropbox, OneDrive) by
  definition copy vault content to vendor servers. This system defaults to git-only
  sync; cloud sync is a user choice.

This system's architectural response:
- No secrets in vault files (INV-7)
- Agent write scope bounded to assigned Site + `_refine-proposals/` (INV-4)
- `99-Operations/` is human-write-only (INV-5)
- Deterministic scripts make no network or LLM calls (INV-6)
- Exfiltration telemetry (osquery FIM, egress monitoring) is explicitly deferred but
  scoped in the build PRD §14

---

## Why This System Is Designed the Way It Is

The architecture choices in Value Mining are direct responses to the practitioner
failure modes above:

| Failure mode | This system's response |
|---|---|
| Inbox pile | Claim → Prospect gate; Sort triage forces a decision |
| Agent trust erosion | Deposit-not-merge; human gate; no direct Treasury writes |
| Naming chaos | INV-11 + naming validator + pre-commit hook |
| Grade inflation | Grade = value only; estimated at ore, confirmed at refine |
| Archive bloat | Tailings retained but separated; Spoil terminal; Polish replaces versioning |
| Sync collisions | Git-only sync; one-commit-per-operation (INV-2) |
| Script/agent confusion | Three explicit execution classes: `[script]` / `[agent]` / `[gate]` |
