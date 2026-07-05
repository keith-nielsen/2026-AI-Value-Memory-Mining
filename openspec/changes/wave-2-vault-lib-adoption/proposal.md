<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: wave-2-vault-lib-adoption

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**MODIFIES** the Requirement "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)"
(commit_paths hardening + full-fleet adoption + two scenarios). **No principle is overridden or
weakened** — this change makes `commit_paths` conform *more closely* to INV-2's own text (the
no-op clause) and completes the adoption the requirement already scheduled ("remaining scripts
SHOULD adopt as they are next modified"). Conforming amendment per repo precedent.
**Tier:** 0-adjacent (implementation of Tier-0 invariants; §5 AI hard-stop honored — Gate-4
human sign-off)
**Proposer:** Keith Nielsen (drafted by Claude Code at Keith's direction, 2026-07-05 — "proceed
with the wave-2 queue")
**Date:** 2026-07-05

---

## Why

Two drivers, both from the 2026-07-05 live runs:

1. **The kanban no-op defect (Phase-1a closure finding):** a same-day identical re-render stages
   nothing and `git commit` refuses the empty index — the script crashes rc 1 where the
   maintenance spec's INV-2 text explicitly blesses a silent no-op. The defect lives in
   `commit_paths`, so one guard there fixes every committing script at once, present and future.
2. **Wave-2 adoption was already scheduled:** `knowledge-lint`, `treasury-orphan`,
   `tailings-reprospect`, and `ore-detect` still crash on a missing `VAULT_ROOT`, and the
   `naming-rules` mirror-writer shares the same defect in its `__main__`. The
   `add-shared-vault-lib` proposal explicitly deferred these to "as next modified" — this is that
   modification.

While hardening `commit_paths`, the commit is also made **pathspec-scoped**: `git commit -m … --
<paths>` commits exactly the named paths even when unrelated content happens to be staged. The
current behavior (bare `git commit` after a scoped add) would sweep any pre-staged operator
content into a fleet commit — the F3/F4/F5 accident class, previously mitigated only by the
"clean staging area" convention. This closes it structurally.

## What Changes

- **`vault-lib-script.md` (`commit_paths`):** after the scoped add, `git diff --cached --quiet --
  <paths>` detects an unchanged result → informative `ok:` line, no commit, exit 0; otherwise
  commit with an explicit pathspec so unrelated staged content stays staged and uncommitted.
- **Adoption, four scripts:** `knowledge-lint-script.md` (root + `PILLARS`/`GRADES`/
  `KNOWLEDGE_STAGES` via `vocab()`, `fm()`, `EXIT_VIOLATION`), `treasury-orphan-script.md` (root),
  `tailings-reprospect-script.md` (root + `fm()`), `ore-detect-script.md` (root +
  `REFINE_GATE_GRADES` via `vocab()` + `fm()`).
- **`naming-rules-script.md`:** the no-args mirror-writer resolves the root via a **lazy**
  `vault_lib` import inside `__main__`; `--check` and module import remain dependency-free (the
  pre-commit hook's path is untouched). **The naming rules themselves are byte-identical** — this
  change does not enter naming-SSOT governance territory (ADR-0013/0015/0016/0021 lineage
  untouched).
- **`maintenance` spec:** MODIFY the vault_lib requirement — commit_paths bullet (pathspec +
  no-op), adoption paragraph (full Python fleet; shell pair explicitly pending), two new
  scenarios (repeated render is a clean no-op; scoped commit ignores unrelated staged content).
- **CHANGELOG** `[Unreleased]`. **No ADR** (extends ADR-0023's decision; no new decision).

**Explicitly NOT in this change:** the shell pair `site-slag`/`spoil-dump` (bash — env guard +
`add -A` sweep; belongs with B3); B3 close-day de-sweep + commit ownership (operator decision
pending); B4 bank-execute hardening; `runtime:` enum alignment; any runbook edit.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: MODIFIED Requirement "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)".

## Impact

- Spec delta (synced at archive): `maintenance`, one requirement. **Archive-order dependency:**
  this delta restates the requirement *including* the governance-hook clause introduced by
  `fix-commit-gate-env-guard` (merged `23e0198`, not yet archived) — archive that change first,
  then this one, so the canonical text accretes in order.
- Implementation: 6 template notes (1 lib + 4 adoptions + naming `__main__`).
- Live vault (operator-applied, out of band): `cp` the 6 notes, `render`, `reconcile` zero
  drift; agent then probes bare no-env runs + the kanban same-day no-op.
- **Behavioral deltas (enumerated):** (1) unchanged-state fleet commits are now clean no-ops
  (exit 0 + message) instead of a crash (kanban) — nothing previously *relied* on the crash;
  (2) fleet commits can no longer capture unrelated pre-staged content — anything depending on
  that sweep behavior (nothing known; close-day's own `add -A` is internal to its script and
  unaffected) must stop; (3) lint/refine-detect vocabularies now readable from config files in
  bare shells — env still wins; (4) lint exits `EXIT_VIOLATION` (value unchanged: 1).
- **Honest residuals:** the shell pair still requires env; `daily-note`/`bank-execute` still
  produce no commits of their own (B3 decision pending); close-day's internal `add -A` sweep
  remains (B3).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** INV-2 says one mutation → one commit, and its own text
says a no-op on unchanged state is acceptable — `commit_paths` previously *crashed* there, and
now honors the clause; the pathspec commit narrows every fleet commit to exactly its declared
mutation, which is INV-2's intent stated operationally. INV-3 is followed (all changes are
literate-note edits deployed via `render`). INV-6 holds (no network, no LLM, no new deps; the
naming mirror-writer's lazy import runs the same deterministic resolution the fleet already
uses). The naming SSOT's *rules* are untouched — only where the mirror file lands is resolved
differently.

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — MODIFIED requirement (delta now; sync at archive,
      after `fix-commit-gate-env-guard`)
- [x] `vault-template/99-Operations/scripts/vault-lib-script.md` — commit_paths hardening
- [x] `vault-template/99-Operations/scripts/{knowledge-lint,treasury-orphan,tailings-reprospect,ore-detect,naming-rules}-script.md` — adoption
- [x] `.github/scripts/validate-scripts.sh` — untouched; exercises lint, refine-detect, kanban,
      naming, and every smoke commit
- [x] `CHANGELOG.md` — `[Unreleased]`
- [x] `constitution.md` / `project.md` / ADR index — untouched
- [x] `vocabulary-lint` — no off-metaphor terms

**Discrepancies surfaced for Gate 4:** (1) archive-order dependency on
`fix-commit-gate-env-guard` (above); (2) the pre-commit hook calls `vault_naming.py --check` —
verified untouched by the naming edit (lazy import is `__main__`-only), but the reviewer should
confirm; (3) `pillars` in config are single space-separated tokens (`mental health …` parses as
six pillars) — pre-existing semantics, preserved exactly by `vocab()`, flagged because it reads
ambiguously in the config file.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** merge → operator copies 6 notes → `render` + `reconcile` → agent probes live.

**Regression tests that MUST pass before Gate 3 completes:**
- [ ] `openspec validate wave-2-vault-lib-adoption --strict` + `openspec validate --all --strict`
- [ ] `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [ ] Sandbox vault, env-free: bare `vault-lint.py` (rc 0 clean + rc 1 with a seeded violation),
      `vault-orphans.py`, `vault-reprospect.py`, `vault-refine-detect.py`, `vault_naming.py`
      (mirror written under the walked root) all succeed with no `VAULT_ROOT`
- [ ] No-op probe: kanban twice same-day → second run `unchanged — no commit needed`, rc 0
- [ ] Scoped-commit probe: stage an unrelated file, run a committing script → commit contains
      only the script's paths; unrelated file still staged
- [ ] Hook untouched probe: `vault_naming.py --check` works with `vault_lib.py` absent from
      `~/bin` (dependency-free path preserved)

**Live acceptance (post-apply, agent):** bare env-free runs of the four adopted scripts; kanban
same-day no-op; reconcile zero drift.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — lib hardening, 5 adoptions, spec delta, CHANGELOG
**All repo-side regression tests green (local, 2026-07-05):** ☑
- `openspec validate` strict: change ✓, `--all` 9/9 ✓ (coexists with the pending
  `fix-commit-gate-env-guard` delta on the same requirement)
- `validate-scripts.sh` → `VALIDATION OK`
- Sandbox battery, all env-free: lint rc 0 clean / rc 1 with seeded violation (`type`,
  `pillars` both flagged); orphans, reprospect, refine-detect rc 0; naming mirror written under
  the walked root; kanban ×2 → second run `ok: unchanged — no commit needed`, rc 0; scoped-commit
  probe → commit contains exactly `10-Logbook/kanban.md`, unrelated staged file left staged;
  `vault_naming.py --check` rc 0 with `vault_lib.py` removed (hook path dependency-free)
**CI green on this PR:** ☐ (runs on push — human)
**Live acceptance:** ☐ (post-apply, agent-executed)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☐
**Consequences explicitly accepted:**

> Sacrifice (proposed wording for sign-off): fleet commits lose the ability to carry unrelated
> pre-staged content (the pathspec scope) — a capability nothing legitimate used, whose absence
> closes the F3/F4/F5 accident class; unchanged-state runs now succeed quietly instead of failing
> loudly, so anything that (wrongly) keyed on the crash must re-key on the `unchanged` message or
> the absence of a new commit. The naming mirror-writer gains a lazy dependency on `vault_lib`
> for its no-args path only — accepted because `--check` (the hook path) and module import remain
> dependency-free.

**ADR:** none (extends ADR-0023; no new decision)

**SIGN-OFF** (human only — agents may not sign):
Name: ______________________
Date: ______________________
