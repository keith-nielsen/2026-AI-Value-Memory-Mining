<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: commit-ownership-de-sweep

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**MODIFIES** "One Mutation, One Commit (INV-2)" (adds the ownership clause + three scenarios) and
"Script Inventory" (three purpose cells). **No principle is overridden or weakened — this change
makes two scripts *stop violating* INV-2** (they mutate with zero commits today) and removes the
last Python `git add -A` sweep. Conforming amendment per repo precedent.
**Tier:** 0-adjacent (INV-2 conformance; §5 AI hard-stop honored — Gate-4 human sign-off)
**Proposer:** Keith Nielsen (operator decision 2026-07-05: "B3 = (a) the recommended path";
drafted by Claude Code)
**Date:** 2026-07-05

---

## Why

INV-2's text is unambiguous: every automated mutation ends in exactly one commit, and producing
zero commits when a mutation occurred is a violation. Today `vault-daily-note.py` creates a note
and commits nothing, and `vault-refine-execute.py` writes Treasury notes, appends Catalog links,
and deletes proposals — committing nothing. Both were laundered by `vault-close-day.py`'s
`git add -A` sweep, which made the sweep **load-bearing**: it could not be removed (its removal
was flagged and deferred in `add-shared-vault-lib`) until the orphan mutations got owners. The
sweep itself is the F3/F4/F5 accident class — it commits whatever the working tree happens to
hold, including unrelated operator content (observed live 2026-07-05: an uncommitted
`.claude/settings.json` would have been swept into a close commit).

The operator chose option (a): every mutation owns its commit; the close seals only what it
seals.

## What Changes

- **`daily-note-script.md`:** a created note is committed immediately — `daily: opened <date>`,
  scoped to the note; the `exists` path stays commit-free.
- **`bank-execute-script.md`:** each banked proposal is **one atomic scoped commit** —
  `bank: <stem>` containing the knowledge note, its Catalog index links, and the consumed
  proposal's deletion. (Verb per CONST-01: banking is what this script executes after the human
  gate.)
- **`daily-close-script.md`:** the `add -A` sweep is replaced by
  `commit_paths(VAULT, [daily, sidecar], …)` — exactly the sealed daily plus the consumed
  worklist sidecar; message becomes `close: <day> daily — N items dispositioned`. `subprocess`
  import dropped.
- **`vault-lib-script.md` (`commit_paths` tolerance):** consumed paths — deleted and never
  tracked (an untracked sidecar or proposal a script just unlinked) — are filtered out before
  `git add`, which would otherwise refuse the pathspec; tracked deletions are staged normally.
  Within the existing requirement's contract (no spec change to the vault_lib requirement).
- **`maintenance` spec:** MODIFY "One Mutation, One Commit (INV-2)" — ownership clause + three
  scenarios (daily-note commit, atomic bank, scoped seal); MODIFY "Script Inventory" — three
  purpose cells.
- **CHANGELOG** `[Unreleased]`. **No ADR** (executes INV-2 as written + the operator's recorded
  B3 decision; no new principle).

**Explicitly NOT in this change:** B4 bank-execute transactional hardening (schema validation /
pre-flight — the atomic commit added here is its anchor, the hardening is its own change); the
shell pair `site-slag`/`spoil-dump` (their `add -A` follows a `git mv`, so it is near-scoped in
practice — but they get env-freedom + explicit scoping in their own small change);
`runtime:` enum alignment; runbook edits.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: MODIFIED "One Mutation, One Commit (INV-2)"; MODIFIED "Script Inventory".

## Impact

- Spec delta (synced at archive): `maintenance`, two requirements. **Archive order:**
  `fix-commit-gate-env-guard` → `wave-2-vault-lib-adoption` → this change (each restates
  requirement text the previous one introduced).
- **Branch stacking:** built on `ops/wave-2-vault-lib-adoption` (the scoped seal *depends* on
  wave-2's pathspec-scoped `commit_paths` — under the old bare `git commit`, pre-staged operator
  content would still leak into the seal). Merge wave-2 first; this PR then shows only B3
  commits.
- Implementation: 4 template notes.
- Live vault (operator, out of band): included in the combined post-merge apply + `render`.
- **Behavioral deltas (enumerated):** (1) daily-note and bank-execute now commit — cron/CI
  observers see new commits (`daily:`, `bank:`); (2) **a close no longer collects the day's
  uncommitted operator content** — captures outside the daily note (e.g. loose files in
  `20-Claims/`) stay in the working tree until deliberately committed; this is the accepted
  meaning of option (a); (3) close commit message loses the word "sweep" (it isn't one anymore);
  (4) a mid-resolution *tracked* sidecar's deletion is staged into the seal; an untracked one
  simply disappears.
- **Honest residuals:** operator capture flows now need their own commit habit (or a future
  capture-commit helper — candidate for the queue); bank-execute is atomic in *commit* but not
  yet transactional in *apply* (B4).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** INV-2 is currently violated twice over — two scripts
mutate without committing, and the mechanism hiding that (the close sweep) is itself the
bundling hazard the failure catalogue records as F3/F4/F5. After this change, each mutation has
exactly one owner and one scoped commit; the close commits precisely what the close changes. The
spec's new ownership sentence writes down what INV-2 always meant. INV-3 followed (literate
notes, `render`); INV-6 untouched (no network, no LLM, no new deps).

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — two MODIFIED requirements (delta; sync at archive in
      order)
- [x] `vault-template/99-Operations/scripts/{daily-note,bank-execute,daily-close,vault-lib}-script.md`
- [x] `.github/scripts/validate-scripts.sh` — untouched; smoke exercises daily-note, close
      lifecycle, executor good-path (all now committing — verified green locally)
- [x] `CHANGELOG.md` — `[Unreleased]`
- [x] `constitution.md` / `project.md` / ADR index — untouched
- [x] `vocabulary-lint` — verbs `daily:`/`bank:`/`close:` conform to CONST-01 vocabulary

**Discrepancies surfaced for Gate 4:** (1) the operator-capture consequence (behavioral delta 2)
is the deliberate cost of option (a) — flagged so it is chosen twice, not discovered later;
(2) the shell pair's `git mv`-then-`add -A` pattern is out of scope here but queued;
(3) stacking/archive-order dependencies as listed under Impact.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** merge wave-2 → merge this → operator copies the combined changed notes →
`render` + `reconcile` → agent live probes.

**Regression tests that MUST pass before Gate 3 completes:**
- [ ] `openspec validate commit-ownership-de-sweep --strict` + `openspec validate --all --strict`
- [ ] `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [ ] Sandbox vault, env-free: daily-note creation → exactly one commit containing only the note;
      second run `exists`, no commit
- [ ] Bank probe with a **tracked** proposal: one commit containing note + Catalog index +
      proposal deletion; nothing else
- [ ] Close probe with a **tracked** sidecar and an unrelated staged file: seal commit contains
      exactly the daily + sidecar deletion; unrelated file still staged
- [ ] Consumed-path tolerance: close with an **untracked** sidecar (and bank with an untracked
      proposal) do not crash on the vanished path

**Live acceptance (post-apply, agent):** daily-note bare (creates + commits 2026-07-06 or next
missing day per operator timing); close of a backlog day when the operator runs it (their flow);
reconcile zero drift.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — 4 notes, spec delta, CHANGELOG
**All repo-side regression tests green (local, 2026-07-05):** ☑
- `openspec validate` strict: change ✓, `--all` 10/10 ✓ (coexists with both pending deltas)
- `validate-scripts.sh` → `VALIDATION OK` (smoke now exercises all three ownership commits)
- Sandbox battery, env-free: daily-note → one commit `daily: opened <date>` containing only the
  note, rerun `exists` with no new commit; tracked proposal → one commit `bank: good-insight`
  containing exactly note + Catalog index + proposal deletion; scoped seal → commit contains
  exactly the daily + tracked-sidecar deletion while a planted unrelated staged file stayed
  staged; untracked consumed sidecar tolerated (seal = daily only, no crash)
**CI green on this PR:** ☐ (runs on push — human)
**Live acceptance:** ☐ (post-apply, agent-executed)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑ (2026-07-05 — the four-commit
branch diff matches the Gate-1 list: maintenance delta, 4 template notes, CHANGELOG, ceremony
docs; no `protects:` frontmatter changed; the operator-capture consequence and ordering
dependencies are recorded above, not buried)
**Consequences explicitly accepted:**

> Sacrifice (proposed wording for sign-off): the close stops being a day-end collector — any
> uncommitted operator content outside the daily note stays uncommitted until the operator
> commits it deliberately; the convenience of the sweep is traded for the guarantee that no
> script commit ever contains anything but its own mutation. Two new commit streams appear
> (`daily:`, `bank:`) that any history-reading tooling must expect.

**ADR:** none (executes INV-2 as written + the operator's recorded B3-option-(a) decision)

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen
Date: 2026-07-05

> Provenance of this record: the operator explicitly chose this change's substance in-session —
> "B3 = (a) the recommended path." (2026-07-05) — and executed the Gate-4 publish sequence
> deliberately (PR #10, CI 20/20 green, human merge `2bc348c`). The sign-off block was left
> unfilled at merge time; the drafting agent recorded it post-merge. The operator's push of this
> record to origin is the confirming act — agents may not originate sign-off, and did not.
