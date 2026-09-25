# Tasks — agent-conduct-standing-rules

> **Durable plan.** Origin: memory-partition Phase 3 (2026-09-16), parked awaiting a proposal; resumed
> as Tier 2 of the 2026-09-25 remediation order. Operator decisions (2026-09-26): delivery Option B
> (SessionStart pointer + bootstrap reference — harness-agnostic first); review the content against the
> controls that now exist; rewrite for accuracy, consistency and minimum size.

## 0. END STATE

A lint-clean lockstep runbook of 27 standing rules, named first in the SessionStart output of both
roots and referenced by the bootstrap's step 2; adapters point at it; a test holds all of that; the
live vault receives it by mirror + SEED merges; the working-memory stores then collapse to pointers.

## 1. Implementation

- [x] 1.1 Rebase the parked branch onto `main` (69 behind) — clean, no conflicts.
- [x] 1.2 Rewrite the runbook to the runbook format, `class: procedure`; content per the proposal's
      review table (29 → 27 rules; 17,045 → 14,317 bytes).
- [x] 1.3 SessionStart (both roots): `echo` the pointer FIRST, then `cat` the bootstrap. Executed:
      pointer is line 1, 210 bytes.
- [x] 1.4 `session-bootstrap-loader` step 2 points to the runbook; `last-validated` bumped.
- [x] 1.5 Adapters: `AGENTS.md` runbook list; `vault-template/CLAUDE.md`.
- [x] 1.6 Every `→` source memory confirmed to exist (18/18); changed cost lines re-taken from source.

## 2. Tests (observed to fail first)

- [x] 2.1 `tests/test_conduct_doc_registration.py` rewritten: 8 pass. Run against the parked design
      (the rebased `88beaa7` versions of the doc, both settings files and the bootstrap) it FAILS 3:
      pointer order, bootstrap step 2, rule numbering.
- [x] 2.2 CI `runbook-lint` (the job's own script): OK; on the parked doc, 6 problems.

## 3. Spec

- [x] 3.1 None — `skip_specs: true`. Conforms to the existing *Runbook Format* requirement
      (precedent: `session-bootstrap-loader`; flag precedent: `md-lint-phase-a-fix-sweep`).

## 4. Regression

- [x] 4.1 Full suite green — 553 passed.
- [x] 4.2 `openspec validate --all --strict` — 7 passed, 0 failed.
- [x] 4.3 markdownlint — 0 findings in CI's scope (a table separator fixed first).
- [x] 4.4 `tools/preflight.py .` → CLEAR.

## 5. Gate 4 — operator authorization

No `protects:`-tagged spec is touched. Surfaced for sign-off:

- **The rule set itself** — 27 rules that outrank ordinary task instructions in both roots; the review
  table in the proposal (4 revised, 2 merged, 1 removed, 1 added).
- **Delivery B** — a pointer, not injected content: it depends on the agent reading the file, backed by
  the bootstrap's step 2. Chosen over a CLAUDE.md `@import` to stay harness-agnostic.
- **Every session pays for it** — one 210-byte line at start, plus reading 14 KB.
- **Deploy-down** needs two SEED merges in the live vault, by the operator's hand or approval.

- [ ] 5.1 Surfaced; awaiting operator sign-off.

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff (generated after the archive commit).
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.

## 7. Deploy-down — the point of the change

- [ ] 7.1 Operator: `tools/template-mirror.py` — carries the new runbook and the bootstrap edit.
- [ ] 7.2 `tools/template-parity.py $VAULT_ROOT` → **0 drift**.
- [ ] 7.3 SEED merge, `$VAULT_ROOT/.claude/settings.json`: the SessionStart command — delivered as a
      described before/after edit (F44), never a heredoc.
- [ ] 7.4 SEED merge, `$VAULT_ROOT/CLAUDE.md`: the one pointer line.
- [ ] 7.5 Cold start in the vault: the pointer is visible in the SessionStart preview (operator-observed).

## 8. Close the record

- [ ] 8.1 Phase 3: collapse the conduct-bound working-memory entries to pointers — only after 7.5.
- [ ] 8.2 File the bootstrap's own SessionStart truncation as its own hardening-queue item.
