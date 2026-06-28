## MODIFIED Requirements

### Requirement: Refine Proposal JSON Schema

All proposals — from the live harness, dry-run, or any future model — MUST conform to
this agent output contract schema:

```json
{
  "target_note": "40-Treasury/<kebab-title>.md",
  "mode": "create | append",
  "insight_md": "string — distilled durable value, Markdown",
  "provenance_md": "string — what was tried/decided/rejected and why",
  "index_links": ["40-Treasury/Catalog/<pillar>-domain-index.md", "..."],
  "frontmatter": {
    "pillars": ["<value from PILLARS>"],
    "grade": "<value from GRADES>",
    "crucible": false
  }
}
```

Agent rules (from the prompt contract in `99-Operations/schemas/refine-prompt-contract.md`):
- Distill, don't transcribe; uncertain findings go in `provenance_md`, not `insight_md`
- Use only pillar values from `PILLARS` and grade values from `GRADES`
- Flag suspected duplicates in `provenance_md`
- `target_note` stem must be a valid kebab-case slug

#### Scenario: Executor enforces the slug rule at the boundary
- **WHEN** a fixture proposal with `target_note` stem `Bad:Name` is placed in `_refine-approved/`
- **THEN** the refine executor rejects it with `REJECT: target_note stem 'Bad:Name' is not a valid kebab slug`
- **THEN** it writes nothing to `40-Treasury/`
