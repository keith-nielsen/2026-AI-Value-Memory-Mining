<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: bank-execute-pre-flight

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDs** a Requirement ("Refine Executor Pre-Flight and Batch Isolation"). **No principle is
overridden or weakened**: the change enforces INV-9 pre-action (create never overwrites refined
value), strengthens the INV-11 boundary already in place, and adds no new invariant. Conforming
amendment per repo precedent. ADDED-only delta — no ordering constraint with the pending
`wave-2` / `commit-ownership` deltas beyond the existing queue.
**Tier:** 0-adjacent (§5 AI hard-stop honored — Gate-4 human sign-off)
**Proposer:** Keith Nielsen (operator direction 2026-07-05: "proceed with B4"; drafted by
Claude Code)
**Date:** 2026-07-05

---

## Why

The fleet review (R6) rated the refine executor the highest-stakes, least-defended script: it is
the sole automated writer of `40-Treasury/`, yet it validated only the target stem. Concretely,
before this change: a malformed proposal crashed the run mid-batch with a traceback (earlier
proposals already applied, later ones unprocessed); a missing Catalog index file raised *after*
the knowledge note was written — a half-applied proposal, not consumed, never committed;
`create` silently **overwrote** an existing Treasury note (automation destroying refined value —
exactly what INV-9 exists to prevent); `target_note`/`index_links` paths were never contained
(a `..` escape would write outside the Treasury); `grade`/`pillars` were trusted verbatim
(lint would flag the damage only after it was banked); and rejects never reached the exit code,
so a driver saw `0` regardless.

## What Changes

- **`bank-execute-script.md`:** a `check()` pre-flight validates each proposal whole (schema →
  containment → INV-11 stem → INV-9 collision / append-existence → `GRADES`/`PILLARS` vocab →
  link-target existence) and prints **all** reasons on rejection; writes begin only after a clean
  pass; unparseable JSON and bad `mode` become REJECT-and-continue instead of crashes (batch
  isolation); run exits `1` on any reject, `0` otherwise. The B3 atomic commit is unchanged and
  is the transaction boundary.
- **`maintenance` spec:** ADDED Requirement "Refine Executor Pre-Flight and Batch Isolation" +
  four scenarios.
- **CHANGELOG** `[Unreleased]`. **No ADR** (enforces existing invariants INV-9/INV-11 + completes
  the fleet-review blueprint item B4; no new decision).

**Explicitly NOT in this change:** proposal-schema versioning / a JSON-Schema file (revisit if
proposal producers multiply); mid-write I/O atomicity (staging + rename across files — the
pre-flight closes the realistic failure window; the scoped commit is the recovery boundary);
the shell pair; hygiene bundle items.

## Capabilities

### New Capabilities
- _(none — lands in the existing `maintenance` capability)_

### Modified Capabilities
- `maintenance`: ADDED Requirement "Refine Executor Pre-Flight and Batch Isolation".

## Impact

- Spec delta (synced at archive): `maintenance`, one ADDED requirement.
- Implementation: 1 template note.
- Live vault (operator, out of band): `cp` the note, `render`, `reconcile`; agent live probe.
- **Behavioral deltas (enumerated):** (1) a run with rejects exits `1` (was `0`) — drivers keying
  on the exit code now see violations; (2) malformed proposals no longer abort the batch;
  (3) `create` collisions are rejected (was: silent overwrite); (4) proposals with bad
  vocab/links/paths that previously half-applied or crashed are now cleanly rejected whole.
  Nothing legitimate relied on any of the old behaviors.
- **Honest residuals:** mid-write I/O failure (disk full, kill -9 between the note write and the
  commit) can still leave uncommitted files — detectable by `git status`, recoverable, and out of
  scope by declaration; the executor trusts the *human gate* (a validly-formed proposal in
  `_refine-approved/` is authorization — content review remains the human's).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** INV-9 says automation never destroys refined value — an
unguarded `create` overwrite is precisely that destruction, and it is now rejected before the
write. INV-11's boundary check was already here and stays. INV-2 is honored through the B3
atomic commit, unchanged. INV-6 holds: the pre-flight reads local files and config vocabularies
only. The Treasury's protection story becomes: OS sandbox denies everyone but the drive path;
the drive path's sole writer now refuses to write anything it has not fully validated.

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — ADDED requirement (delta; sync at archive)
- [x] `vault-template/99-Operations/scripts/bank-execute-script.md` — the hardening
- [x] `.github/scripts/validate-scripts.sh` — untouched; its INV-11 boundary smoke (bad + good
      proposal) exercises the new path and must stay green
- [x] `CHANGELOG.md` — `[Unreleased]`
- [x] `constitution.md` / `project.md` / ADR index — untouched
- [x] `vocabulary-lint` — no off-metaphor terms

**Discrepancies surfaced for Gate 4:** none new. (The smoke's `bad.json` rejection reason changes
from the single stem message to potentially multiple printed reasons — the smoke greps `REJECT`,
unaffected.)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** merge → operator copies the one note → `render` + `reconcile` → agent live probe
(reject-and-exit-1 path; the good-path bank happens at the operator's next real refine).

**Regression tests that MUST pass before Gate 3 completes:**
- [ ] `openspec validate bank-execute-pre-flight --strict` + `openspec validate --all --strict`
- [ ] `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [ ] Sandbox battery: malformed JSON REJECT + valid proposal still banked in the same run
      (rc 1); create-collision REJECT with target byte-identical; missing-link REJECT with no
      note created; `..` traversal REJECT; bad grade/pillars REJECT; append-to-missing REJECT;
      clean batch rc 0

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — note, spec delta, CHANGELOG
**All repo-side regression tests green (local, 2026-07-05):** ☑
- `openspec validate` strict: change ✓, `--all` 11/11 ✓
- `validate-scripts.sh` → `VALIDATION OK` (INV-11 boundary smoke green on the new path)
- Sandbox battery: malformed JSON rejected while the valid proposal in the same batch was banked
  atomically (rc 1); create-collision rejected `(INV-9)`, target byte-identical; missing Catalog
  link rejected pre-write, no note created; `..` traversal rejected, nothing written outside;
  bad `pillars` and `grade` both reported in one reject; append-to-missing rejected; clean empty
  batch rc 0
**CI green on this PR:** ☐ (runs on push — human)
**Live acceptance:** ☐ (post-apply, agent-executed)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑ (2026-07-05 — branch diff at
`da9d6b8` matches the Gate-1 list: maintenance ADDED delta, one template note, CHANGELOG,
ceremony docs; no `protects:` frontmatter changed)
**Consequences explicitly accepted:**

> Sacrifice (proposed wording for sign-off): none of substance — the executor loses the ability
> to overwrite, half-apply, or silently swallow malformed proposals, none of which anything
> legitimate used. The one real constraint: proposal authors must now produce fully valid
> proposals (schema, vocab, existing link targets) or see them rejected whole — friction accepted
> at the boundary of the vault's most protected area.

**ADR:** none (INV-9/INV-11 enforcement; fleet-review blueprint item B4)

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen
Date: 2026-07-05

> Provenance of this record: the operator directed the change explicitly ("proceed with B4"),
> executed the Gate-4 publish sequence deliberately (PR #11, CI green, human merge `cbfb6e7`),
> applied it live (`6e1fb8c`), and confirmed in-session. The sign-off block was left unfilled at
> merge time; the drafting agent recorded it post-merge. The operator's push of this record is
> the confirming act — agents may not originate sign-off, and did not.
