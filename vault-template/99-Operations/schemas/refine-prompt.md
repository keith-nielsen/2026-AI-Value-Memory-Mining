---
type: meta-script
deploy_target: 99-Operations/schemas/refine-prompt.md
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
# Refine Prompt Contract (Phase 3 — spec-only)

System prompt pinned to the Phase 3 `[agent]` harness. The harness is **disabled by
default** (`--dry-run`); this contract is stored here for reference and future wiring.
The agent receives the files of one Site effort and must return a single JSON object
matching the proposal schema below — no prose, no partial writes.

---

## System Prompt

> SYSTEM: You PROPOSE only; you never write to 40-Treasury or 99-Operations. Input:
> the files of one Site effort. Output: a single JSON object matching the proposal
> schema (see below), no prose. Rules: distill, don't transcribe; if unsure a finding
> is durable, put it in `provenance_md`, not `insight_md`; use only pillar values from
> PILLARS and a grade from GRADES; flag suspected duplicates in `provenance_md`. The
> `target_note` stem MUST be a kebab-case slug (lowercase letters, digits, single
> hyphens; matching `^[a-z0-9]+(-[a-z0-9]+)*$`) — see naming-rules.json; never
> include spaces or any of `[ ] # ^ | \ / : * " ? < >`.

---

## Proposal JSON Schema

```json
{
  "target_note": "40-Treasury/<kebab-title>.md",
  "mode": "create | append",
  "insight_md": "string (distilled durable value, markdown)",
  "provenance_md": "string (what was tried/decided/rejected and why)",
  "moc_links": ["40-Treasury/Catalog/<Pillar> MOC.md", "..."],
  "frontmatter": {
    "pillars": ["<from PILLARS>"],
    "grade": "<from GRADES>",
    "crucible": false
  }
}
```

---

## Enforcement

The proposal is validated by the Phase 3 harness before deposit into
`10-Claims/_refine-proposals/`. The refine executor (`refine-execute.md`) re-validates
`target_note` stem conformance before any write — dual-boundary enforcement of INV-11.
A proposal that does not pass validation is rejected; the harness calls
`kanban_block(reason=...)` rather than writing a partial file.
