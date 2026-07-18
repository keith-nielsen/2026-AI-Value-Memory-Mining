---
capability: agent-integration
protects: [INV-4, INV-5, INV-8, INV-11]
---
<!-- SPDX-License-Identifier: Apache-2.0 -->
# Spec: agent-integration

## Purpose

Define the Phase 3 agent-assisted refine harness: the proposal contract, the dry-run
scaffolding, and the Hermes Agent runtime mapping. Build is spec-only in Phase 3;
live wiring is deferred (§14.1).
## Requirements
### Requirement: Phase 3 Harness — Spec-Only Scaffolding

The Phase 3 harness SHALL be built as disabled-by-default scaffolding:

- Default mode: `--dry-run` — writes a fixture proposal to `_refine-proposals/`,
  makes no network or model call
- Live mode: not wired; the model call is stubbed

The harness **must** have no code path that writes to `40-Treasury/` or
`99-Operations/` (INV-4, INV-5). It validates the proposed `target_note` stem
with `is_valid_slug()` before deposit — local rejection before the executor's
boundary check (INV-11, dual enforcement).

#### Scenario: Dry-run produces a schema-valid proposal
- **WHEN** the harness runs in `--dry-run` mode against a fixture Site
- **THEN** it writes a JSON file to `20-Claims/_refine-proposals/` that validates against the proposal schema (§12.10)
- **THEN** it makes no network call

#### Scenario: Harness has no Treasury write path
- **WHEN** the harness source is inspected
- **THEN** there is no code path that opens, creates, or writes any file under `40-Treasury/` or `99-Operations/`

#### Scenario: Harness rejects non-conforming target_note
- **WHEN** the harness is given a fixture proposal with `target_note` stem `Bad:Name`
- **THEN** it rejects it locally and writes nothing to `_refine-proposals/`

---

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

### Requirement: Hermes Agent Runtime Mapping (Deferred)

When Phase 3 is activated (live wiring deferred), the harness SHALL run as a
Hermes Kanban worker with the following fixed mapping:

| Parameter | Value | Rationale |
|---|---|---|
| Workspace | `dir:<VAULT_ROOT>/30-Sites/<slug>` | Absolute path; preserved on completion |
| Dispatch mode | One-shot (not `--goal`) | Per-turn judge loop risks flooding local LLM |
| Done state | `kanban_complete()` on deposit | Kanban done ≠ Treasury write |
| Blocked state | `kanban_block(reason=...)` | Never a partial Treasury write |
| Profile | Dedicated refine profile | Main agent (`Kent`) orchestrates; refine profile runs the worker |
| Toolset | Must not enable write to Treasury or Operations | INV-4, INV-5 |

Containment consequence: the Hermes worker runs with operator uid and full FS
access (Hermes's trusted-local-user, single-host threat model). INV-4 is enforced
by the executor + commit-gate hook, not by the runtime. The hook fires on every
commit, including the worker's.

Operational constraints for activation (not build items — Hermes config):
- Cap `kanban.max_in_progress` to avoid flooding local LLM
- Single-host boards — the two workstations run separate boards
- Run `hermes dashboard` on localhost only (never `--host 0.0.0.0`)

#### Scenario: Worker deposit does not write Treasury
- **WHEN** a Hermes refine worker completes a card
- **THEN** it calls `kanban_complete()` after depositing a proposal in `_refine-proposals/`
- **THEN** it writes nothing to `40-Treasury/` or `99-Operations/`; the commit-gate hook backstops the boundary on the worker's commit

### Requirement: Verification Deliverables Are Transcripts

An *enumerate* or *verify* step in a governed procedure SHALL be satisfied only by a pasted,
re-runnable command transcript: the exact command(s) plus their full, untruncated output.
This applies wherever such a step appears — the Informed-Upheaval gates, an ordinary change's
tasks, a runbook checklist. A list or verdict composed from reasoning SHALL NOT satisfy the
step.

Rationale (the failure record this encodes): enumeration performed by reasoning is bounded by
what the agent thought of, not by the corpus, and has shipped misses three times (F8, F9, F17 in
the live vault's determinism-failure-modes record); a check whose failure case is not observable
has produced false "all green" verdicts (F20, three instances in one session). A transcript
converts "did the agent think of everything?" (unfalsifiable) into "does the transcript match
the corpus?" (re-runnable, diffable).

Constraints on the transcript:

- The output SHALL NOT be truncated (`head`/`tail`/sampling): narrowing the output is the same
  defect as narrowing the scope.
- Every hit in an enumeration transcript SHALL be dispositioned (edited here / not edited,
  with reason) so the reviewer can diff hits against actions.
- Verification evidence SHALL be a form that shows its own denominator or failure case — a
  tally, a diff, an exit status. A literal verdict string printed by the shell (`echo "ok"`,
  `... || echo "clean"`) SHALL NOT count as evidence: the shell knows only an exit code, not
  the answer to the question asked.

#### Scenario: A blast-radius enumeration is satisfied by a transcript

- **WHEN** a `constitution-override` proposal reaches Gate 1
- **THEN** its blast-radius section contains the search command(s) and their full output
- **THEN** the Gate-4 reviewer re-runs the command(s) and diffs; a clean diff confirms the
  enumeration, a dirty diff rejects it

#### Scenario: A composed list without a transcript is rejected at review

- **WHEN** a proposal's enumeration or verification step is a prose list with no command
  transcript
- **THEN** the review rejects the gate as unsatisfied, regardless of the list's apparent quality

#### Scenario: A truncated enumeration is invalid

- **WHEN** an enumeration transcript pipes through `head -N` or otherwise samples its output
- **THEN** the step is unsatisfied — the transcript must carry the full output

#### Scenario: A shell-printed verdict is not verification evidence

- **WHEN** a verification step's evidence is a success string emitted by `&& echo` / `|| echo`
- **THEN** the step is unsatisfied; the deliverable is the underlying evidence (tally, diff,
  exit status) read by the reviewer

