<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0030 — Switch on ADR-0015's token floor: enforcement at the gate, the executor, and the linter

**Status:** Proposed
**Date:** 2026-07-17
**Relates:** `naming-rules` (INV-11) · `maintenance` · change `enforce-naming-token-floor` · **completes ADR-0015** (which deferred this) · sibling of ADR-0029 (pillar tokens)

## Context

ADR-0015 (2026-06-27) set the ≥3-hyphen-token floor and chose **convention now, mechanical
enforcement later**, because turning on rejection while non-conforming names existed "would
block all commits until every family is renamed." It named the enforcement as *"a **separate
later change**"*, gated on **full conformance**.

That change was never written. Until today the entire pending item was one sentence in an ADR
and three commented-out lines in `knowledge-lint-script`. It had no proposal and nothing
tracking it. The families conformed incrementally exactly as ADR-0015 predicted — molds in
v0.1.7, then scripts, runbooks, indexes, content — and nobody returned to flip the switch,
because the thing that would have noticed was a comment.

**The gate is satisfied.** Measured across the whole live vault: 118 `.md` files, 15 exempt,
103 subject to a strict rule, **0 failing** `is_valid_slug`, **0 failing** the floor.

**Three findings made this cheaper than it looked:**

1. **`has_min_hyphen_tokens` was called by nothing** — its only references were its own
   definition, the linter's import, and the commented-out `elif`. ADR-0015's rule was enforced
   **nowhere**; the floor was dead code.
2. **The commit gate's grandfathering fear never applied to it.** The hook reads
   `--diff-filter=AR` — added/renamed only, explicitly commented *"existing names are
   grandfathered"*. It structurally cannot touch an existing name. The fear was about the
   **linter**, which sweeps everything — and there, conformance is now total.
3. **The exemption list already covered the awkward names** (`README.md`, `CLAUDE.md`,
   `AGENTS.md`, `MEMORY.md`, dailies, `*.example`, config files), so a strict gate does not
   block them.

This is the same defect as ADR-0029's, one level up: **a rule that lives as a comment,
enforced by nothing.** ADR-0015's grandfathering was the *reason* for the comment; the reason
expired and left no signal behind.

## Decision

Enforce the existing rule at three points. **`min_hyphen_tokens: 3` and `slug_pattern` are
unchanged — this ADR adds no rule, it switches on ADR-0015's.**

- **`vault_naming.py --check-strict FILENAME`** (new): takes a *basename*, applies
  `is_exempt` → `validate_name` → `slug_pattern` → `has_min_hyphen_tokens`. `--check STEM`
  keeps its contract, so no existing caller moves implicitly.
- **Commit gate**: calls `--check-strict` on the basename; stays `--diff-filter=AR`.
- **Refine executor**: pre-flight rejects a sub-3 `target_note` **before any write**.
- **Linter**: the staged `elif` is enabled, and the floor additionally covers Treasury stems
  and effort folder slugs, which had kebab but no floor.

## Options considered

1. **Enforce at gate + executor + linter (CHOSEN).** The gate stops names entering; the linter
   catches the corpus; the executor stops the producer. All three, because two of them alone
   leave a hole — see option 3.
2. **Linter only (uncomment the `elif`) — rejected.** The minimal reading of "switch it on",
   but it catches a bad name only *after* it is committed. The gate is where ADR-0015 said
   enforcement belongs (*"vault_naming.py + commit-gate hook + naming-rules.json"*).
3. **Gate + linter, skip the executor — rejected, and the tests proved why.** Enabling the
   gate broke two *pre-existing* bank tests: the executor writes `40-Treasury/<stem>.md` and
   then calls `commit_paths`, so a sub-3 stem that passed pre-flight would be **written and
   then blocked at commit**, stranding the executor half-applied with an uncommitted Treasury
   file. The executor's pre-flight is not optional once the gate enforces the floor; it is the
   thing that keeps "reject at the boundary, no Treasury write" true.
4. **Do nothing; leave it staged — rejected.** The null option was live and considered. It
   loses because the deferral's stated precondition is *met*, and a rule enforced by nothing
   is not a rule — it is documentation that the next producer may miss, exactly as `PILLARS`
   was missed this morning.

## Consequences

- INV-11 moves from convention to mechanism, which is what ADR-0015 called for. **No name is
  renamed**; conformance was already 100%, which is *why* the switch can flip.
- **Live workflow constraint (the real cost):** a newly added content note must carry ≥3 kebab
  tokens. `xrp.md` and `kanban.md` would now be **BLOCKED at commit**. That is ADR-0015's
  intent, but it is a change to how the operator names things, and it is the thing accepted at
  Gate 4.
- Test fixtures `good-insight` and `existing-note` (2 tokens each) were renamed to
  `good-durable-insight` / `existing-durable-note`. The fixtures were themselves violating the
  convention the repo documents — a small, honest confirmation that unenforced rules decay.
- **Sacrifice:** short names are gone for new content. `xrp.md` must become
  `xrp-tokenomics-claim.md`. The floor was always a *floor, not a ceiling* (ADR-0015), so this
  costs terseness at creation time and buys names that survive a flat/search/migrated view.
  The escape hatch is the exemption list, which is deliberately narrow and rationale-documented
  (`docs/naming-exemptions-rationale.md`) — not a general opt-out.
