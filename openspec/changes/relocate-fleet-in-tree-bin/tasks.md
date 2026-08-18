<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — relocate-fleet-in-tree-bin (Change B of two)

**Depends on Change A — `add-fleet-inventory-conformance` — being merged first.** B assumes the
inventory, cadence, settings-resolution and coverage instruments already exist and are green. B is
the first change that could ever break the settings-resolution check, which is the point of the split.

**Marker contract:** `[ ]` not started · `[~]` **built, untested** · `[x]` **tested — the check was
observed to FAIL without the change, and its evidence is cited.**

**Evidence rule (constitution §3 Gate 3):** every result is evidenced by **its command and output** —
a tally with its denominator, a diff, or an exit status. Never a prose assertion, never a
shell-printed verdict string. An `echo "ok"` proves nothing: the shell knows only an exit code.

**Phases map onto the constitutional gates**, they do not replace them:

| Constitution §3 | Phase here |
|---|---|
| Gate 1 — CHECK (impact analysis) | B0 + `blast-radius-transcript.md` |
| Gate 2 — PLAN (migration + regression) | this file |
| Gate 3 — EXECUTE + REGRESSION-TEST | B1 – B6 |
| Gate 4 — RE-CHECK + HUMAN SIGN-OFF | B7 – B9 |

---

## Who performs what — the write-scope partition

**Measured 2026-08-17.** Every engineering phase happens **in the framework repo**; the live vault
receives the change through mirror + deploy-down, never by hand-editing a protected path.

| Surface | Scope | Who |
|---|---|---|
| `vault-template/**` · `openspec/specs/` · `tools/` · `tests/` · `.github/` | **WRITABLE** | agent |
| live vault `99-Operations/**` · `.claude/**` · `40-Treasury/` · `96-Runbooks/` | **PROTECTED** | operator |
| `git push` · branch delete | capable; INV-14 **authority** is the operator's | agent runs, operator consents |
| `gh` mutations (PR, merge, release) | keyring unreachable from the session | **operator only** |
| vault `render` · `vault_naming.py` bare | writes protected paths | **operator only** |

CLAUDE.md restated: *a deployed vault carries no governance corpus of its own — framework changes are
made upstream and deployed down, never improvised in the vault.*

⚠ **Sequencing consequence.** The live vault does not hold the relocated fleet until B6's mirror and
render. **Every vault-side verification therefore runs after merge and ship**, in B7. Iteration
happens in the fixture vault (`tests/conftest.py` renders a complete throwaway vault from
`vault-template/` into an isolated `HOME`) — **iterate in the fixture, land once, verify the vault
after.** The protected zone admits one delivery per ceremony cycle; that is why B4 is atomic.

---

## B0 — CHECK: blast radius *(Gate 1)*

- [x] B0.1 Blast radius delivered as a **pasted, re-runnable command transcript** — the exact commands
      plus their full untruncated output, never a list composed from reasoning.
      **Evidence:** `blast-radius-transcript.md`, 5 commands, captured 2026-08-18.
      **Tally: 85 corpus files — 53 archived (frozen) + 19 vault dig-record (frozen) + 25 live.**
- [x] B0.2 Baseline captured. **Evidence:** `baseline-preflight-record.md`.
- [x] B0.3 **Change A merged** — PR #97 into `main` at `093d9f5`, 2026-08-18T04:06:09Z, verified over
      REST by the driver (`LIFECYCLE COMPLETE`, exit 0). This branch was **rebased onto merged main**
      (was based on `dec7a01`, 8 commits stale and WITHOUT A's instruments). CONTRIBUTING: rebase
      before pushing, never after opening — B is not yet open, so now is the moment.
      **Evidence on this branch:** A's `test_inventory_conformance.py` + `test_settings_paths.py`
      present and green (10 passed); full suite **344 passed**; A archived at
      `openspec/changes/archive/2026-08-18-add-fleet-inventory-conformance/`.

⚠ **Scope-block lesson inherited from A — pre-declare, do not discover.** A's `Scope review` gate
failed because the ADR-0040 archive MUTATES THE PR DIFF after the scope block is written: it moves
the change directory to `openspec/changes/archive/<date>-<slug>/` and applies EACH capability delta
into `openspec/specs/`. B carries **three** deltas (`maintenance`, `access-control`, `naming-rules`),
so B's scope block must declare, from the start:
  - `openspec/changes/archive/<date>-relocate-fleet-in-tree-bin/`
  - `openspec/specs/maintenance/spec.md`
  - `openspec/specs/access-control/spec.md`
  - `openspec/specs/naming-rules/spec.md`
Validate it with `.github/scripts/extract-declared-scope.py` **and** a coverage check against
`git diff origin/main..HEAD --name-only` before the body is posted.

**GATE B0 —** transcript present and re-runnable; A merged.
*Falsifier: a blast radius stated as a table without its generating command.*

---

## B1 — Source changes, targets unmoved *(Gate 3 · repo · agent)*

- [x] B1.1 In the 5 notes carrying it, replace `pathlib.Path.home() / "bin"` with
      `pathlib.Path(__file__).resolve().parent` — `knowledge-lint`, `treasury-orphan`, `ore-detect`,
      `bank-execute`, `tailings-reprospect`. **Evidence:** transcript Command 4.
- [x] B1.2 Set `sys.dont_write_bytecode` at the entry point of each Python member importing a sibling.
- [x] B1.3 Amend `maintenance/spec.md:131-132`, which **codifies the `$HOME` hardcode** as spec'd
      behaviour. A spec change, not a code fix.

**GATE B1 —**
1. `pytest` green with its count.
2. **Adversarial:** a fleet script run with **`python3 -P` AND a broken `$HOME`** still imports and
   runs. ⚠ **`HOME=/nonexistent` alone is VACUOUS** — the interpreter already puts the script's own
   directory on `sys.path[0]`, so that form passes before and after. Measured 2026-08-18. Only `-P`
   (or importing rather than executing) removes the auto-prepend and makes the insert load-bearing.
3. Record the 5 new checksums; they supersede baseline for those files only.

**GATE B1 — PASSED 2026-08-18.**
1. Full suite **350 passed** (was 344; +6 new).
2. Adversarial `-P` + broken `$HOME` green across all 5 scripts. **Red demonstrated**: reverting
   `knowledge-lint` to the home-relative insert produced
   `ModuleNotFoundError: No module named 'vault_naming'`, then restored.
3. `grep -rc 'Path.home()' vault-template/99-Operations/scripts/` -> **none remaining** (5 code
   fences plus the `vault-lib` prose sentence that described the old mechanism).
4. `inv6-offline-check` -> 14 notes, 0 violations.
5. No `__pycache__` left in the deploy directory after a fleet run (new test).

⚠ **Severity correction recorded in `proposal.md`.** The claim that deleting `~/bin` would cause hard
`ImportError`s was FALSE. The obvious test (`HOME=/nonexistent` alone) passes before and after and
proved nothing; it was written first and discarded.

*Falsifier: any script still resolving `vault_lib` via `$HOME`.*

---

## B2 — The atomic move, ONE commit *(Gate 3 · repo · agent)*

**These land together or not at all.** The `settings.json` exclusion is an exact string match; a
non-match is indistinguishable from a deny, and no automated check can see it.

- [x] B2.1 `deploy_target` → `99-Operations/bin/<name>` in all **11** host notes. The 3 in-tree notes
      are **not** touched.
- [x] B2.2 `.claude/settings.json` — repoint the exclusion in **both** the repo's file and
      `vault-template/`.
- [x] B2.3 `tests/conftest.py` lines 43 (`run()`) and 91 (`_render_fleet()`).
- [x] B2.4 `.github/scripts/validate-scripts.sh` — 9 refs incl. `mkdir -p "$HOME/bin"`.
- [x] B2.5 `config.env` + `config.defaults.env` — **append** `$VAULT_ROOT/99-Operations/bin` to
      `PATH`, **idempotently**; fix the existing non-idempotent `.venv/bin` line in the same pass.
- [x] B2.6 `template-sync-manifest.json` — **do NOT add `99-Operations/bin/` to `lockstep`**. Record
      the reason in the manifest's own `_comment`. Grounds: the template ships the *generator*
      (`99-Operations/scripts/`, already lockstep), not its output — the category the existing
      `exclude` entry for `naming-rules.json` was created for. It would also fail forever:
      `files_under()` returns empty for an absent directory and `vault-template/` ships no `bin/`, so
      parity would report 11 permanent drift findings. **`reconcile` governs note → deployed.** Parity
      watches hand-maintained scaffold; reconcile watches generated output.
- [x] B2.7 **`.gitignore` — add `99-Operations/bin/` in BOTH trees**, commented as render output whose
      source is `99-Operations/scripts/`. Neither excludes it today, so the default is *tracked* — a
      decision by accident. ⚠ Ignore the generated output directory **specifically**, never one that
      also holds tracked scaffold.
- [x] B2.8 Extend `Standalone-vault lint (F15)` to fail on any `deploy_target` outside the tree.

**Surfaces B2 did not anticipate — found by running, not by reading:**
- [x] B2.9 **The git hooks invoke fleet members by `${HOME}/bin` path.** The hooks are in-tree targets
      that do not move, but their CODE called the relocated scripts. `commit-gate` now derives
      `BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/../bin" && pwd)"` and `site-slag`/`spoil-dump` call
      `"$(dirname "$0")/vault_naming.py"` — co-location, same principle as B1. **24 test failures.**
- [x] B2.10 **Eight tests hardcoded `fleet.home / "bin"`.** Replaced with a single `Fleet.bindir`
      property, so the layout has ONE definition and the next relocation is one edit, not eight.
- [x] B2.11 **The EROFS shim compared path STRINGS.** In-tree targets are vault-RELATIVE, so the
      prefix silently stopped matching and the shim never fired. Now resolves both sides. ⚠ This
      failure is invisible in the general case — the shim simply does nothing and the test passes
      for the wrong reason.
- [x] B2.12 **Change A's settings check was FALSE-NEGATIVE — it compared BASENAMES.** With the
      exclusion still at `~/bin/vault-refine-execute.py` and the target moved in-tree, it PASSED.
      **The proposal's claim that "B is the first change able to trip it naturally" was therefore
      false — B would not have tripped it either.** Now compares by path suffix (tolerating a
      `$CLAUDE_PROJECT_DIR/` prefix), demonstrated red on exactly that mismatch. Same defect family
      as everything this pair of changes exists to close: **a check that verifies the shape of a
      thing instead of the thing.**
- [x] B2.13 **Two `"$HOME"/bin/*.py` globs in `validate-scripts.sh`** used a different quote
      placement and survived the first rewrite. Caught by exit status, not by reading.

**GATE B2 — PASSED 2026-08-18. Repo-side only; the vault has received nothing yet.**
1. `pytest` **350 passed** — the bank tests resolve through the new location. They would have thrown
   `FileNotFoundError` had B2.3 been missed; that they pass **is** the evidence.
2. Change A's settings-resolution check green against the NEW paths — **after B2.12 made it able to
   fail at all.**
3. Change A's inventory check green — the relocation changed targets, not membership.
4. `validate-scripts.sh` **EXIT 0** (18 ok / 0 FAIL), status captured rather than its printed verdict.
5. `template-parity`: **2 prefixes** — `bin/` was NOT added to `lockstep`, so B2.6 held.
   ⚠ **CRITERION CORRECTED.** This originally read *"still 0 drift"*, which is **impossible between
   B2 and B6**: parity compares template -> LIVE VAULT, and the vault receives nothing until B6's
   mirror. It reports **12 drift**, which is exactly the 12 notes edited here (11 relocated +
   `commit-gate`), with `outbound-publish-guard` and `push-guard` correctly untouched. Drift here is
   the expected state, not a failure; the prefix COUNT is what proves the manifest decision.
6. B2.8 demonstrated **red on the pre-move tree (11 violations across 14 notes)**, green now (0).
7. `inv6-offline-check` static half clean — 14 notes, 0 violations.

*Falsifier: any `~/bin` reference left in the repo's running-code or verifier surface.*

---

## B3 — Document reconciliation, repo side *(Gate 3 · repo · agent)*

**Rule:** rewrite **live surface only**. Per the transcript, **53 archived + 19 dig-record files are
frozen** — they record what was true then, and rewriting them falsifies the audit trail.

- [ ] B3.1 Live specs: `maintenance` (incl. the inventory Deploy Target column), `access-control`,
      `naming-rules`.
- [ ] B3.2 `README.md` incl. line 222 *"deployed to `~/bin/` via `render`"* — also wrong today about
      the 3 in-tree targets.
- [ ] B3.3 `vault-template/00-Docs/README.md` — runnable bootstrap block + the deferred
      `vault-seed.py` / `vault-cleanup.py` paths. ⚠ **SEED, not lockstep** — the mirror will NOT carry
      this; targeted deploy-down in B6.
- [ ] B3.4 `AGENTS.md`, `docs/USING-THIS-TEMPLATE.md`, `docs/obsidian.md`, `docs/diagrams.md`.
- [ ] B3.5 `vault-template/96-Runbooks/render-reconcile-runbook.md`, `refine-pipeline-runbook.md`.
      ⚠ **Not a lockstep prefix** — targeted deploy-down in B6.
- [ ] B3.6 Codify the `vault-`/`vault_` executable prefix in `naming-rules`.
- [ ] B3.7 `CHANGELOG.md` entry (an ADD).

**GATE B3 —**
1. **Ghost check:** every `vault-*.py`/`.sh` named in a live doc either exists or is explicitly
   labelled deferred. Known-good: 3 labelled-deferred (`vault-seed.py`, `vault-cleanup.py`,
   `vault-promote.sh`). Any **new** ghost is a regression.
2. **Frozen-surface proof:** `git diff --stat` touches **zero** files under
   `openspec/changes/archive/` and zero vault dig-record paths. Assert by listing the diff.
3. The `README.md` bootstrap block runs **verbatim** in a scratch clone.

*Falsifier: any frozen path in the diff; any doc command that fails when run verbatim.*

---

## B4 — ADR *(Gate 4 prerequisite)*

- [ ] B4.1 **ADR-0044** capturing context / options / choice / consequence / **sacrifice** for the four
      architectural decisions: in-tree `bin/`; **no `$VAULT_BINS`**; render output git-ignored; the
      new prefix deliberately **not** lockstep. §3 Gate 4 requires an ADR; Change A has none because
      it weighed no options.

**GATE B4 —** ADR exists, is referenced from `proposal.md`, and states the sacrifice explicitly.
*Falsifier: an ADR that lists only benefits.*

---

## B5 — LAND *(Gate 4 · the OpenSpec ritual)*

Walk the driver; do not hand-compose the sequence.

- [ ] B5.1 **Human sign-off recorded in `proposal.md`** — human-only, not agent-delegatable (§5).
- [ ] B5.2 Branch from `main`.
- [ ] B5.3 `tools/preflight.py .` **before the first push** (ADR-0041). ⚠ **Run it from a shell where
      `config.env` has NOT been sourced** — sourcing puts the vault venv first on `PATH` and that venv
      has no pytest, which preflight miscategorises as `fleet-pytest: failed` while claiming
      `0 unrunnable`. From a clean shell it correctly reports PASS. Measured both ways 2026-08-18.
- [ ] B5.4 `tools/pr-flow.py --plan --branch BR` — the whole 14-step route first.
- [ ] B5.5 `tools/pr-flow.py --branch BR` → emits **one** command, exits 2.
- [ ] B5.6 **Run the emitted command VERBATIM** — no variables, no `timeout` prefix, no re-wrapping.
      Failure **class 10, stage 1**; recurred twice on 2026-08-17 alone.
- [ ] B5.7 Re-run `pr-flow.py` to verify the mutation landed. If NOT READY, poll `--ready`. **Never
      sleep.**
- [ ] B5.8 Repeat until `LIFECYCLE COMPLETE`, exit 0.
- [ ] B5.9 **Archive the change ON THE FEATURE BRANCH** (ADR-0040) — before merge.
- [ ] B5.10 Merge via the REST route carrying `sha`. **Never `gh pr merge --delete-branch`.**

**GATE B5 —** `LIFECYCLE COMPLETE`; archived on its branch; `main` carries the merge.

---

## B6 — SHIP + deploy down *(operator)*

- [ ] B6.1 `tools/ship-release.py vX.Y.Z` → tag → **Release object**. A tag and a Release are
      different objects. Repeat until the **tag↔Release PARITY TALLY with denominators** exits 0.
- [ ] B6.2 `tools/template-mirror.py <VAULT_ROOT>` — mirrors the **lockstep** prefixes repo → live,
      then proves parity. **This is how the 11 relocated notes reach the vault.**
- [ ] B6.3 **Targeted operator deploy-down** for what the mirror does not carry:
      `00-Docs/README.md` (SEED), `96-Runbooks/*.md` (not lockstep), `.claude/settings.json` (SEED).
      ⚠ Byte-identity with the template is **a finding to check, not a pass to assume.**
- [ ] B6.4 Operator runs `vault-render.py render` — deploys the fleet to `99-Operations/bin/`.
- [ ] B6.5 Operator runs `99-Operations/bin/vault_naming.py` bare to regenerate `naming-rules.json`
      (agent gets exit 4 here by design).

**GATE B6 —**
1. `reconcile` = 0 drift, 14 `ok:`, **zero `/home/` paths in the output**. The migration's central
   claim, testable for the first time here.
2. `template-parity` = 0 drift across 2 prefixes.
3. **`git status --porcelain` in the vault EMPTY after render** — proving B2.7 took and the artifacts
   are ignored, not merely uncommitted.
4. `99-Operations/bin/` holds exactly 11 artifacts and no `__pycache__`.

---

## B7 — RE-CHECK: vault verification *(Gate 4)*

### B7a — Content integrity, differential, **BLOCKING** *(agent)*

Operator decision 2026-08-17: **any delta blocks.** Compare against `baseline-preflight-record.md`
**by diff**, not by exit code.

- [ ] B7a.1 `vault_secrets.py --selftest` **FIRST** — `patterns fire, tiers are disjoint`. A clean scan
      from a broken scanner is indistinguishable from a clean tree; if this fails, B7a.6 is void.
- [ ] B7a.2 `vault-lint.py` — ⚠ **exits 1 today** on `30-Sites/.claude` (untracked; the linter walks
      the filesystem, not the index). **Exit 1 with that same single finding = PASS. Exit 0 =
      INVESTIGATE. Exit 1 with any second finding = FAIL.**
- [ ] B7a.3 `vault-orphans.py` — `0 orphan(s)`, exit 0.
- [ ] B7a.4 `vault-refine-detect.py` — `queued 0 for refining`, exit 0.
- [ ] B7a.5 `vault-reprospect.py` — no output, exit 0.
- [ ] B7a.6 `vault_secrets.py .` — `HIGH: 0`, `ADVISORY: 1`, still `secret-scan-script.md:202`.
- [ ] B7a.7 `pr-flow.py --capabilities` — `40-Treasury` / `96-Runbooks` / `99-Operations` all
      **PROTECTED** by real attempted write. Proves relocation did not widen scope.

**GATE B7a — BLOCKING.** Any delta halts until explained **in writing** in the change directory.

### B7b — Real hook paths, SCRATCH CLONE *(agent)*

Operator decision 2026-08-17. A rejected commit still leaves index state, and a violation attempt has
no place in vault history.

- [ ] B7b.1 `git clone` the vault to a scratch path; set `core.hooksPath 99-Operations/hooks`.
- [ ] B7b.2 **Negative control:** commit a non-conforming filename — MUST be refused.
- [ ] B7b.3 **Positive control:** commit a conforming file — MUST succeed. A refusal means nothing
      unless the hook can also accept.
- [ ] B7b.4 Confirm `outbound-publish-guard.py` still fires. This target does **not** move — proving
      it unaffected is the point.
- [ ] B7b.5 Destroy the scratch clone.

### B7c — Decommission `~/bin` *(operator)*

- [ ] B7c.1 Confirm `~/bin` holds only the 11 **stale** copies + `__pycache__`.
- [ ] B7c.2 **Adversarial:** `mv ~/bin ~/bin.parked`, re-run GATE B6 and B7a in full. All must pass.
      *The only check distinguishing "the `$HOME` dependency is gone" from "the `$HOME` dependency
      happens to be satisfied."*
- [ ] B7c.3 Operator removes `~/bin`.
- [ ] B7c.4 Confirm `~/.profile` **unmodified** — the `if [ -d "$HOME/bin" ]` block simply stops
      firing. This change must not edit shell profiles.

**GATE B7c — shell-mode proof.** After sourcing `config.env`, every fleet member runs in **both** a
login shell (`bash -lc`) **and a non-login shell** (`bash -c`). *The non-login case is the one
`~/bin` never satisfied — it is ground 5, and this is where it is proven fixed.*

---

## B8 — RE-CHECK: full estate *(Gate 4 completes)*

- [ ] B8.1 **Re-run every command in `blast-radius-transcript.md` and diff against it** — §3 Gate 4
      requires re-running the Gate-1 transcript, not re-reading the composed sections.
- [ ] B8.2 **Frozen counts UNCHANGED: 53 archived · 19 dig-record · `CHANGELOG` 8 hits.** A
      *reduction* means the audit trail was rewritten — a failure, not progress.
- [ ] B8.3 Live-surface count → **0** `~/bin` references.
- [ ] B8.4 Every Phase-B0 baseline measurement re-taken; **each delta explained in writing**.
- [ ] B8.5 Consequences explicitly accepted; sign-off and ADR-0044 archived as permanent record.

**GATE B8 —** all of B8.1–B8.5, plus a written statement naming anything that changed which this
proposal did not predict.

---

## B9 — The limit no gate closes *(operator)*

- [ ] B9.1 **One operator-run agent invocation of `vault-refine-execute.py` through Claude Code**,
      recorded. Change A's check proves the exclusion path *resolves*; only this proves it *matches*.
      Every automated gate above can pass with the exclusion silently broken.

---

## Known limits, stated rather than discovered

- **The pipeline is stalled upstream and this change does not address it.** 21 of 21 Sites at
  `status: dig`; `ore-detect` queues 0; both refine queues empty. `vault-refine-execute.py` has one
  verifiable script-produced run in vault history (`8728282`, 2026-06-25). Gates B7a and B2 pass on an
  idle pipeline — honest, not reassuring.
- **Three stale ADR headers** (0032, 0033, 0042) read "Proposed/pending" while signed, applied and
  archived. Out of scope; they touch no line this change edits.
- **Provenance ambiguity out of scope:** 3 of 4 `bank:` commits were hand-authored, so the log reads
  as 4 automated deposits when it is 1.
