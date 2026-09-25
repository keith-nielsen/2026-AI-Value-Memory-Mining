<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: agent-conduct-standing-rules

## Why

The standing behavioural rules for an agent lived only in the per-root working-memory stores (~80 KB),
loaded as an index of one-line summaries. That fails two ways: a summary line is recollection, not an
artifact (the rules are applied from memory, not from a source of record), and the vault store carried
development-side rules no vault operator needs. Memory-partition Phase 3 (2026-09-16) set the fix: one
lockstep runbook holding the universal rules, reached at session start in both roots.

A draft was built and parked on 2026-09-16 (`9214e11`, rebased as `88beaa7`). Re-validated against the
current estate on 2026-09-26, it would have shipped broken:

- **It fails CI `runbook-lint`** — 6 problems: none of the six required sections, and `class: conduct`
  where the schema's `class` is the literal `procedure`.
- **Its delivery could not deliver.** It `cat`ed the 17 KB doc after the bootstrap in the SessionStart
  hook. That hook's output was measured (2026-09-25) reaching the agent as a **2 KB preview** of a
  12.6 KB whole — so ~30 KB behind 2 KB: the rules would never reach context.
- **Content drift:** controls built since 2026-09-16 made parts of it redundant or wrong, and one
  standing rule postdates it.

## What Changes

- **`vault-template/96-Runbooks/agent-conduct-standing-rules.md`** — rewritten to the runbook format
  (Purpose · Preconditions · Steps · Standing rules · Pitfalls · Verification · Rollback,
  `class: procedure`), 17,045 → 14,317 bytes, 29 → 27 rules, each carrying `cost:`, a date,
  `terminal` or `gate:`, and its source memory.
- **Delivery (operator decision 2026-09-26, Option B — harness-agnostic first):**
  - SessionStart in both roots **names** the doc as its **first** output line (210 bytes, inside the
    preview), then prints the bootstrap as before. The doc is not `cat`ed.
  - `session-bootstrap-loader` step 2 points to it, so the fully-read bootstrap path reaches it on any
    harness.
- **Adapters** (the session-bootstrap-loader precedent): `AGENTS.md` runbook list and
  `vault-template/CLAUDE.md` point at it.
- **`tests/test_conduct_doc_registration.py`** — lockstep coverage; the pointer precedes the bootstrap
  and is not `cat`ed, in both roots; bootstrap step 2 points here; rules numbered contiguously; every
  rule has a cost line and `terminal`/`gate:`. Runbook format is left to CI `runbook-lint`.
- **No spec change** (`skip_specs: true`): the runbook conforms to the existing *Runbook Format*
  requirement, as `session-bootstrap-loader` did (2026-06-28). Precedent for the flag:
  `2026-09-14-md-lint-phase-a-fix-sweep`.

## Content review — against the controls that exist today

Controls inventoried: the outbound-publish guard (since #131 it ignores `-m`/`-F` values), the `gh`
invocation guard (`gh api <REST>` and `gh auth status` only), the relay-conformance `Stop` hook
(byte-checks a relayed `next.sh` line), `permissions.deny` (five `gh` forms; the vault also denies
`Edit` on its five protected prefixes), the driver's labelled copy-whole emissions and verify tails,
`test_gh_form_conformance`, and the capability probe.

| Draft rule | Verdict | Reason |
| --- | --- | --- |
| 14 outbound-guard tokens | collapsed to `gate:` + residual | "prose quoting counts" and "the `cd` idiom defeats detection" are fixed (#131). Measured 2026-09-25: an inline `-m` and `-F <file>` defer; a **heredoc body** and a **variable path** still deny — the residual kept |
| 19 paste formatting | rewritten (now 16) | "applies to driver-composed commands too" became wrong: driver blocks are copied verbatim, enforced by the relay hook (items 39/40). Added F44 (no heredoc edits to structure-sensitive files) |
| 15 deny rule vs output | trimmed (now 13) | the "driver emits a denied form" clause is obsolete — `test_gh_form_conformance` |
| 20 provenance labels | trimmed (now 17) | drivers label their emissions; rule kept for agent-composed commands |
| 10 "OS-enforced" | removed | a substrate fact, not conduct; stays in `os-write-scope-sandbox-burn-in` |
| 9 timeout ≠ denial | merged into 3 | one habit: one observation is not a finding |
| 16 DENY binds the next command | merged into 11 | one sentence of consequence for the refusal rule |
| — | **added** (18) | *the operator's "done" is a cue to verify* — standing since 2026-09-22 (PR #130 closed unmerged) |

The other 19 rules stand: each governs judgement or output, which no `PreToolUse` hook reaches. Every
`→` source memory was confirmed to exist; each changed cost line was re-taken from its source.

## Impact

- Every session in either root is pointed at the rules at start, inside the visible preview.
- **Deploy-down owed** (the #115 shape): the operator runs `template-mirror` (carries the new runbook
  and the bootstrap's step-2 edit — lockstep), then parity must read 0 drift. The live vault's SEED
  files take the delta by **merge, never copy**: `$VAULT_ROOT/.claude/settings.json` (SessionStart
  command) and `$VAULT_ROOT/CLAUDE.md` (one pointer line) — delivered as described before/after edits,
  never a heredoc (F44).
- **After a cold start confirms it loads**, memory-partition Phase 3 completes: the conduct-bound
  entries in the working-memory stores collapse to pointers here. Not before — pruning first would
  leave the rules in neither place.
- Out of scope, owned elsewhere: the bootstrap's own truncation (the same 2 KB preview hides most of
  it) is filed separately rather than folded into this change (F29).

## Verification

- `tests/test_conduct_doc_registration.py`: 8 pass; against the parked design it **fails 3** — pointer
  order, bootstrap step 2, rule numbering.
- CI `runbook-lint` passes (the parked doc: 6 problems).
- The rewritten SessionStart command, executed: the pointer is line 1 (210 bytes).
- Template bootstrap equalled the live copy before this change (no prior drift), so a post-mirror
  0-drift parity result proves the mirror carried it.
