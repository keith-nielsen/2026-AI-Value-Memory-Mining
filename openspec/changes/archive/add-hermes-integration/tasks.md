<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Prompt Contract

- [x] 1.1 Write `99-Operations/schemas/refine-prompt.md` with the agent system prompt
- [x] 1.2 Prompt specifies: PROPOSE only, no Treasury/Operations writes, JSON output matching §12.10
- [x] 1.3 Prompt includes kebab-slug constraint for `target_note` with pattern reference

## 2. Phase 3 Harness Scaffolding

- [x] 2.1 Implement harness entrypoint with `--dry-run` flag (default on)
- [x] 2.2 `--dry-run` mode: write a fixture proposal JSON to `_refine-proposals/`, no network/model call
- [x] 2.3 Validate `target_note` stem with `is_valid_slug()` before deposit (local rejection)
- [x] 2.4 Confirm no code path writes to `40-Treasury/` or `99-Operations/`

## 3. Runtime Mapping Documentation

- [x] 3.1 Document Hermes workspace as `dir:<VAULT_ROOT>/30-Sites/<slug>` (absolute, preserved)
- [x] 3.2 Document dispatch as one-shot (not `--goal`)
- [x] 3.3 Document done state: `kanban_complete()` on proposal deposit
- [x] 3.4 Document blocked state: `kanban_block(reason=...)` (never partial Treasury write)
- [x] 3.5 Document profile and toolset constraints in `openspec/adr/0006-hermes-agent-runtime.md`

## 4. Acceptance Verification (A3.1–A3.3)

- [x] 4.1 Harness `--dry-run` writes schema-valid proposal to `_refine-proposals/`, no network call
- [x] 4.2 Code inspection: no write path to `40-Treasury/` or `99-Operations/`
- [x] 4.3 Fixture with `target_note` stem `Bad:Name`: harness rejects locally, writes nothing
- [x] 4.4 Same fixture injected directly to `_refine-approved/`: executor rejects it (dual-boundary proof)
