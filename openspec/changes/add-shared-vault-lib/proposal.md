<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: add-shared-vault-lib

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDs** a Requirement ("Shared Fleet Plumbing and Exit-Code Contract") and **MODIFIES** the Script
Inventory (one new row: `vault-lib-script.md`). **No principle is overridden or weakened.** The
change *strengthens* the protected invariants: INV-2 gains a scoped-commit helper that makes the
one-mutation-one-commit shape the path of least resistance; INV-3 is followed to the letter (all
code ships as literate meta-script notes, deployed only via `render`); INV-6 is preserved (the
library is deterministic — local files and env only, no network, no LLM, no shell evaluation).
**Tier:** 0-adjacent (extends the *implementation* of Tier-0 invariants; §5 AI hard-stop honored —
surfaced to the operator with explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at Keith's explicit direction, 2026-07-05 —
"proceed with the intended proposal as outlined … up to the Constitutional ceremony gate")
**Date:** 2026-07-05

---

## Why

Two independent evidence streams converge on the same defect class:

1. **The Phase-1a burn-in** (live-vault Site `protocol-harness-framework`,
   `phase-1a-acceptance-probes`) proved the drive-path contract unusable as shipped: probe **P5**
   — the bare exact invocation `~/bin/vault-kanban-render.py` that the sandbox exclusion list
   requires — crashes with `KeyError: 'VAULT_ROOT'` because a fresh tool shell carries no
   environment and the exact-match exclusion forbids an env prefix. The failure is safe (dies
   pre-write) but blocks the driver-invocation contract, and leaves SE-5 (does the exclusion
   actually lift the sandbox?) unprovable — the crash is identical either way.
2. **The fleet review** (live-vault Site `ops-script-runbook-review`, findings R1–R10) found the
   ~530-line Python fleet healthy but running on three or four competing idioms: three frontmatter
   parsers that give **opposite answers** to "is this day closed" on `closed: false` (R2); a gate
   refusal that **exits 0** so no driver or model can distinguish it from success (R3, rollover);
   config vocabulary with three homes so a `config.env` change silently doesn't propagate (R4,
   kanban hardcodes grades); and mixed commit scoping (R5).

The fixes share one shape: a small shared module. Per-script patches would fix P5 six times in six
slightly different ways and leave R2/R3/R4 divergence in place.

## What Changes

- **`maintenance` spec:** ADD Requirement "Shared Fleet Plumbing and Exit-Code Contract
  (vault_lib)" — root resolution (env-first, marker-walk fallback), config vocabulary precedence
  (process env > `config.env` > `config.defaults.env` > code default), YAML-typed `is_closed`,
  scoped `commit_paths`, fleet exit codes (`0` ok · `1` violation · `2` needs-input ·
  `3` gate-blocked). MODIFY Script Inventory: add `vault-lib-script.md` → `~/bin/vault_lib.py`.
- **`vault-template/99-Operations/scripts/`:** NEW `vault-lib-script.md`; ADOPT in the drive-path
  set + render:
  - `render-reconcile-script.md` — inline copy of the root-resolution contract (bootstrap
    exception: it deploys `vault_lib.py`, so it must not import it).
  - `daily-note-script.md` — root + `is_closed` (YAML-typed; the previous regex counted the
    *string* `false` as closed).
  - `dig-rollover-script.md` — root, `is_closed`, `commit_paths`; gate refusals now exit **3**
    (previously **0** — indistinguishable from success).
  - `kanban-render-script.md` — root, `fm`, `commit_paths`; grades/statuses now from the config
    SSOT (`GRADES` reversed to value-descending; `EFFORT_STATUSES`) instead of hardcoded lists.
  - `daily-close-script.md` — root + `DISPOSITIONS` via `vocab()` (env still wins; code default
    retained); gate refusals (missing note, strict-order) exit **3** (previously **1**).
    Classification internals and commit scope untouched.
  - `bank-execute-script.md` — root only; all other behavior untouched.
- **New ADR-0023** (drafted as Proposed; Accepted at Gate 4).
- **CHANGELOG** `[Unreleased]` entry (drafted with the change, not after — F10 lesson).

**Explicitly NOT in this change:** wave-2 adoption (`knowledge-lint`, `treasury-orphan`,
`tailings-reprospect`, `ore-detect`, `vault_naming`'s `__main__`) — they adopt as next modified;
the daily-close `git add -A` de-sweep (review item B3 — requires a commit-ownership decision for
`daily-note`/`bank-execute` first, because the sweep currently launders their uncommitted writes);
`bank-execute` transactional hardening (B4); the argparse/`main()` skeleton (B2 full form); any
runbook change; any live-vault file (live `99-Operations/scripts/` is operator-applied
post-Gate-4, out of band of this repo).

## Capabilities

### New Capabilities
- _(none — lands in the existing `maintenance` capability)_

### Modified Capabilities
- `maintenance`: ADD Requirement "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)";
  MODIFY Requirement "Script Inventory" (one added row + shared-module import note).

## Impact

- **Spec delta (synced at archive):** `maintenance` (ADDED + MODIFIED as above). `protects:`
  frontmatter unchanged (no new invariant).
- **Implementation (vault-template):** 1 new + 6 modified meta-script notes.
- **New ADR-0023.**
- **Live vault (operator-applied, out of band):** copy the 7 notes into live
  `99-Operations/scripts/`, run `render`, verify `reconcile` zero drift; agent then re-runs the
  P5/SE-5 probes in-session (bare invocation must now succeed and prove the exclusion lifts the
  sandbox).
- **Behavioral deltas (accepted, enumerated):** (1) rollover gate refusal exits 3, not 0;
  (2) close-day gate refusals exit 3, not 1; (3) `closed: false` now reads as *open* in
  daily-note (regex previously said closed — rollover already said open; this removes the
  divergence, it does not invent a semantic); (4) kanban vocabulary follows `config.env`;
  (5) `DISPOSITIONS` may now come from config files (process env still wins).
- **Honest residuals:** wave-2 scripts still crash without `VAULT_ROOT` until adopted; the
  close-day sweep (`git add -A`) remains (B3); a `vault_lib` defect now affects all adopters at
  once (mitigated: CI renders and smoke-tests the fleet on every push; the module is ~120 lines,
  stdlib + lazy `frontmatter` only).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** Nothing constitutional is overridden. INV-3 says Layer-0
code lives as literate notes and reaches the host only through `render` — this change adds one
note and edits six, all deployed exactly that way; drift stays detectable by `reconcile`. INV-2
says every automated mutation is exactly one structured commit — the new `commit_paths` helper is
that rule as a function, and the two scripts that already committed correctly now share one
implementation of it. INV-6 says scripts are deterministic and offline — `vault_lib` reads local
files and process env, performs no shell evaluation of config values, and its only third-party
import (`frontmatter`) is unchanged from current fleet practice. The exit-code contract exists for
the same reason the OS sandbox does (ADR-0022): drivers and future models must key on structure,
not on trusting prose.

**Blast radius:**

- [x] `openspec/specs/maintenance/spec.md` — ADDED + MODIFIED Requirements (delta now; canonical
      sync at archive)
- [x] `vault-template/99-Operations/scripts/vault-lib-script.md` — NEW
- [x] `vault-template/99-Operations/scripts/{render-reconcile,daily-note,dig-rollover,kanban-render,daily-close,bank-execute}-script.md` — modified (code + Rationale + `updated:`)
- [x] `.github/scripts/validate-scripts.sh` — **unchanged**, but exercises every touched path
      (bootstrap render, py_compile all rendered scripts incl. `vault_lib.py`, fresh-vault smoke,
      close lifecycle, INV-11 executor boundary) — must stay green
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [x] ADR-0023 (new, Proposed → Accepted at Gate 4)
- [x] `vocabulary-lint` — no off-metaphor terms introduced
- [x] Live-vault probe docs reference this change for P5/SE-5 closure (Site-side, out of band)
- [x] `constitution.md` / `project.md` — untouched (no new INV; frozen-ID rule not implicated)

**Discrepancies surfaced for Gate 4 (decide, don't bury):**

1. **`runtime:` enum vs. hook notes (pre-existing).** The Literate Meta-Script Format requirement
   says `runtime: cron | manual`, but the inventory and the two hook notes use `git hook`
   (and `commit-gate-script.md` says `manual` while `push-guard-script.md` says `git hook`).
   Not fixed here — flagged for a vocabulary-alignment follow-up.
2. **Smoke-test invocation form.** CI invokes scripts as `python3 ~/bin/<script>` with `VAULT_ROOT`
   exported — the env-first path. The bare-no-env path is covered by the library's design and the
   live P5 re-run, not yet by CI. A CI case invoking one drive-path script bare could be added in
   a follow-up (kept out to leave `validate-scripts.sh` untouched in a governed change).
3. **`is_closed` on malformed frontmatter:** `frontmatter.load` on a file with no frontmatter
   returns empty metadata → *open* — same verdict the old regex gave; no divergence, noted for
   completeness.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. Spec delta: `maintenance` ADDED + MODIFIED (this change's `specs/maintenance/spec.md`).
2. `vault-template`: add `vault-lib-script.md`; adopt in the six notes (exact diffs in this
   branch; each note's `updated:` bumped and Rationale states its behavioral deltas).
3. ADR-0023 (Proposed). CHANGELOG `[Unreleased]`.
4. Live vault (operator, post-Gate-4): copy the 7 notes into `99-Operations/scripts/`; run
   `vault-render.py render`; `vault-render.py reconcile` → zero drift; cron entries unchanged
   (same deploy targets).
5. Agent (in-session, after apply): re-run probe P5 — `~/bin/vault-kanban-render.py` bare, no env
   → must render + produce exactly one scoped commit (closes SE-5: the exclusion demonstrably
   lifts the sandbox); run `vault_lib.py` self-check; run the rollover gate against an unclosed
   prior day → exit 3; append verdicts to `phase-1a-acceptance-probes.md`.
6. Wave-2 adoption, B3 de-sweep (+ commit ownership), B4 hardening: separate follow-up changes.

**Regression tests that MUST pass before Gate 3 completes:**

- [ ] `openspec validate add-shared-vault-lib --strict`
- [ ] `openspec validate --all --strict`
- [ ] `bash .github/scripts/validate-scripts.sh` green locally (render bootstrap → py_compile all
      rendered scripts including `vault_lib.py` → bash/shellcheck → fresh-vault smoke →
      close-daily lifecycle (strict-order gate message unchanged: `BLOCKED`) → INV-11 executor
      boundary)
- [ ] `vault_lib.py` self-check exits 0 against the template sandbox vault (root + six vocab keys)
- [ ] Bare no-env invocation check: a drive-path script run with `VAULT_ROOT` unset, cwd inside
      the sandbox vault, resolves the root and behaves identically
- [ ] Gate-refusal exit codes: rollover on unclosed prior day → rc 3; close-day strict-order →
      rc 3; message prefix `BLOCKED:` in both
- [ ] `vocabulary-lint` preconditions (no off-metaphor terms; config keys present)

**Live acceptance (after operator apply — agent-executed in-session):**

- [ ] `~/bin/vault-kanban-render.py` bare, no env prefix → renders + one scoped commit (P5 ✓,
      SE-5 closed)
- [ ] `vault_lib.py` bare → self-check `ok` lines, exit 0
- [ ] `vault-render.py reconcile` → zero drift
- [ ] Rollover against unclosed prior day → `BLOCKED:` + exit 3

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — spec delta; 1 new + 6 modified template notes; ADR-0023
(Proposed); CHANGELOG `[Unreleased]`
**All repo-side regression tests green (local, 2026-07-05):** ☑
- `openspec validate add-shared-vault-lib --strict` ✓ · `openspec validate --all --strict` ✓ (8/8)
- `.github/scripts/validate-scripts.sh` → `VALIDATION OK` (render bootstrap, py_compile ×12 incl.
  `vault_lib.py`, `bash -n` ×3, fresh-vault smoke, close lifecycle, INV-11 executor boundary)
- Bare no-env checks on a rendered sandbox vault: `vault-render.py render` bare rc 0 (inline
  bootstrap resolution); `vault_lib.py` self-check rc 0, all six vocab keys resolved from config
  files; `vault-daily-note.py` bare rc 0 with `⚠ BLOCKED` banner; rollover refusal `BLOCKED` +
  **rc 3**; close-day strict-order refusal `BLOCKED` + **rc 3**; `closed: false` → `is_closed
  = False`; `vault-kanban-render.py` bare no-env → rc 0, exactly one scoped commit while unrelated
  untracked files stayed untracked (the P5 shape, sweep-free)
- Vocabulary grep clean (no off-metaphor terms in new/changed files)
**CI green on this PR:** ☐ (runs on push — human)
**Live acceptance probes:** ☐ (run in-session after the operator applies the live notes — see
migration step 5)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☐
**Consequences explicitly accepted:**

> Sacrifice (proposed wording for sign-off): the fleet gains a single shared dependency — a defect
> in `vault_lib.py` now touches every adopting script at once, where before each script failed
> alone; this concentration is accepted in exchange for one correct implementation of five
> previously-improvised concerns (mitigation: CI renders and smoke-tests the whole fleet on every
> push). Five behavioral deltas are accepted knowingly: rollover and close-day gate refusals
> change their exit codes (0→3 and 1→3 respectively — anything keying on the old codes must
> re-key); `closed: false` now uniformly means *open*; kanban vocabulary follows `config.env`
> rather than the script text; `DISPOSITIONS` gains a config-file source below the environment.
> Wave-2 scripts remain un-adopted until their own change — the fleet is deliberately
> two-idiom during the transition, which is accepted as documented, not silent.

**ADR created:** `openspec/adr/0023-shared-vault-lib-plumbing.md` (Proposed) ☑ — flips to
Accepted at sign-off
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: ______________________
Date: ______________________
