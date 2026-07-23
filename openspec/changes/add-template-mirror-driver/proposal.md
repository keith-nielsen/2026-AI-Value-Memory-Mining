<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: add-template-mirror-driver

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** one Requirement ("Template→Live Mirror (Repo→Live Apply)"). **No principle is overridden or
weakened.** INV-4/5 (agent write-denial to `99-Operations/`/`40-Treasury/`) stay exactly as strict;
the *operator* remains the actor who runs the mirror — only *how* they run it changes, from a
hand-composed multi-arg `cp` to one reviewed invocation. Conforming amendment per repo precedent
(`add-template-parity-check` and `fix-operator-only-path-diagnostics` are the direct models — each
touched a protected spec, ran this ceremony, and shipped **without a new ADR**).
**Tier:** 0-adjacent (adds a mirror-time apply surface aligned with INV-3 GitOps and INV-6
determinism; §5 AI hard-stop honored — surfaced for explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-24)
**Date:** 2026-07-24

---

## Why

CONTRIBUTING's ship ceremony ends at step 5: *"Mirror any vault-template hook/guard change into the
live vault (operator action), then prove it: `tools/template-parity.py <VAULT_ROOT>`"* — a sentence
with **no vehicle behind it**. `ship-release.py` replaced hand-typed release commands with a guarded
driver; `template-parity.py` made mirror completeness a mechanical check; but the mirror *itself*
stayed a hand-composed `cp`. That is the exact gap F26 fell through (2026-07-20, the live-vault
determinism Site): denied write access to `99-Operations/`, the agent authored a ~500-character
multi-arg `cp` for the operator; their terminal wrapped it, bash split the fragments, and a truncated
2-arg `cp` silently **overwrote a live framework-repo file** instead of erroring. Recovered from git,
zero lasting damage — by luck of timing, not design.

The root cause generalizes: **every increment of write-denial (correctly) shrinks the agent's trusted
surface and correspondingly grows the surface of commands handed to the one actor the sandbox does not
bind — the operator's terminal — and that second surface was never costed.** A reviewed script invoked
by one short line cannot wrap into a different, destructive command. This change builds that vehicle:
`tools/template-mirror.py`, the write-capable counterpart to `template-parity.py`, applying the same
established pattern (`ship-release.py`, `template-parity.py`) to the one place the ceremony skipped it.

**Safe by construction, not by care.** The tool is one-directional (repo → live only, never the
reverse), never deletes, and never writes to the repo — so even a bug in it can at worst overwrite a
live file with the repo's already-reviewed bytes, recoverable by `git status` on the live vault
exactly as F26 was. It computes its own diff (never acts on an enumeration typed from memory — F17/F23)
and ends by re-deriving parity and printing the same denominator'd tally the parity check prints,
never a bare success word.

## What Changes

- **`maintenance` spec:** +1 ADDED Requirement — a repo-owned, stdlib-only, offline mirror tool;
  reuses the existing `template-sync-manifest.json`; repo → live only, never deletes; reports
  `MISSING-IN-TEMPLATE`, never resolves it; re-derives parity with a denominator; exit contract
  `0`/`2`/`3`; never `git add`/commits.
- **`tools/template-mirror.py`** (new): the driver. Defaults the live vault from `$VAULT_ROOT`
  (identical convention to `template-parity.py`); `MISSING-IN-LIVE` → copy, `DIFFERS` → overwrite,
  `MISSING-IN-TEMPLATE` → report only; re-walks and prints the shared tally.
- **`tools/template_sync.py`** (new): the tree-walk + comparison + tally logic factored out of
  `template-parity.py` into one module both tools import — one source of truth for what "in sync"
  means (byte-identical output to before).
- **`tools/template-parity.py`** (modified): refactored to import `template_sync`; output byte-identical
  to before (its 6 tests still green).
- **`tests/test_template_mirror.py`** (new): 8 cases (T1–T6 + blocked-no-vault), synthetic fixtures
  only — never the real `$VAULT_ROOT`.
- **`tests/test_template_parity.py`** (modified): +2 lines, adjusted to the shared module.
- **`CONTRIBUTING.md`:** step 5 rewritten from the "(operator action)" prose to the single invocation
  `tools/template-mirror.py <VAULT_ROOT>`.
- **`AGENTS.md`:** the post-merge-mirror Operating-notes bullet rewritten — run the driver, never a
  hand-composed `cp` (naming F26); it ends by printing the parity tally, so `template-parity.py` alone
  remains the check-only path.
- **`README.md`:** repo-structure `tools/` tree gains the `template-mirror.py` line.
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Deliberately out of scope.** (a) **No manifest widening.** `vault-template/99-Operations/hooks/` and
`.claude/{hooks,commands}` are visibly present and NOT covered by `template-sync-manifest.json` — a
real gap, but its own decision with its own blast radius (it changes what counts as "governed
scaffold"). It is **not** folded in here (open item G2, below). (b) **No merge with `ship-release.py`**
— mirroring triggers on template changes, shipping on version bumps; different cadences, different
blast radii. The `parity`/`mirror` read/write split mirrors the proven `pr-state`/`ship-release`
split. (c) **No rollback subsystem** — the live vault is a git repo; recovery is `git status` +
restore, literally how F26 was fixed. (d) **No loosening of INV-4/5** — the fix makes the operator's
one action safe; it does not remove the operator from the loop.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> The `maintenance` spec governs the deterministic Layer-0 tooling surface: INV-2 (one mutation, one
> commit), INV-3 (literate scripts, GitOps render/reconcile), INV-6 (deterministic tooling is offline,
> no LLM). This mirror driver *applies* the INV-3 repo → live deploy direction as a reviewed
> invocation instead of hand-composed shell; it runs offline with no network and no model (INV-6); and
> it deliberately does NOT commit — that stays the operator's explicit INV-2 step. Nothing existing is
> relaxed; a new apply tool is added alongside the existing detection-only parity check, sharing its
> manifest and comparison logic.

**Blast radius — every artifact this change touches** (grepped, not enumerated from memory;
`grep -rn "template-mirror" --include=*.md --include=*.py --include=*.json --include=*.yml .`):

```
CONTRIBUTING.md:37:5. tools/template-mirror.py <VAULT_ROOT>   # mirror LOCKSTEP repo→live, then prove parity
AGENTS.md:175:- **Post-merge mirror into the live vault: run `tools/template-mirror.py <VAULT_ROOT>`, never a
tools/template_sync.py:4:Both `template-parity.py` (detect drift) and `template-mirror.py` (fix drift) operate on
README.md:117:│                                #   template-mirror.py: repo→live mirror driver; ship-release.py: guarded
tools/template-mirror.py:33:Usage:  tools/template-mirror.py [LIVE_VAULT]     # LIVE_VAULT defaults to $VAULT_ROOT
tools/template-parity.py:11:`template-mirror.py` driver) re-runs the mirror to resolve drift (same posture as reconcile /
tools/template-parity.py:18:`template-mirror.py` via `template_sync.py` — one source of truth for what "in sync" means.
tests/test_template_mirror.py:  (new module, 8 cases)
```

- [x] `openspec/specs/maintenance/spec.md` — ADDED Requirement (spec delta in this change)
- [x] `tools/template-mirror.py` — new
- [x] `tools/template_sync.py` — new (shared walk/compare/tally, factored out of `template-parity.py`)
- [x] `tools/template-parity.py` — modified (imports `template_sync`; byte-identical output)
- [x] `tests/test_template_mirror.py` — new (8 cases, synthetic fixtures)
- [x] `tests/test_template_parity.py` — modified (+2 lines for the shared module)
- [x] `CONTRIBUTING.md` — step 5 → single invocation
- [x] `AGENTS.md` — post-merge-mirror Operating-notes bullet rewritten (names F26)
- [x] `README.md` — repo-structure `tools/` tree gains `template-mirror.py`
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `tools/template-sync-manifest.json` — **no change** (G2 deferred; no new keys, no widened
      prefixes)
- [ ] `vault-template/` — **no change** (repo-side maintainer tool only; the deployed vault is
      untouched — the standalone premise holds, F15)
- [ ] `.github/workflows/ci.yml` — **no change**. The standalone-vault-lint regex (`ci.yml:358`,
      `tools/(ship-release|pr-state|template-parity)`) does NOT list `template-mirror` — a known
      cosmetic gap, flagged NOT fixed: it only bites if some future `vault-template/` file were to name
      the tool, which none does. Deliberately left rather than widened silently.
- [ ] `openspec/adr/` + README ADR count — **no change** (conforming amendment ships without an ADR,
      per the `add-template-parity-check`/`fix-operator-only-path-diagnostics` precedent; the ADR-count
      guard is untouched)

**External dependency being adopted: NONE.** `template-mirror.py` + `template_sync.py` are stdlib-only
Python owned by this repo — no registry fetch, no install hooks, nothing new in the trust ring.

## Gate 2 — PLAN (Migration + Regression)

- Additive change: no migration of existing artifacts. `template-parity.py` is refactored to import
  the shared module; its observable output is byte-identical and its 6 tests stay green — a pure
  internal factoring, not a behavior change.
- **Coexistence with the in-flight `add-telemetry-segment` change** (also has a `maintenance` spec
  delta): this change only ADDS a Requirement and touches no requirement telemetry touches, so there
  is no `### Requirement:` header collision. At archive time, honor **batch-archive-in-merge-order** so
  the cumulative superset lands last (verify: no duplicate headers, `openspec validate --all` clean).
- Regression: CI runs `openspec validate --all` (non-strict) — currently 7/7 on this branch. (A
  latent `--strict`-only nit exists on `maintenance` requirement 17 on `main` today, unrelated to and
  untouched by this change — CI does not run `--strict`.) All existing jobs stay green; the new module
  `tests/test_template_mirror.py` green.
- Rollback: delete `tools/template-mirror.py` + `template_sync.py` + the new test + the spec delta +
  revert `template-parity.py`/`test_template_parity.py`/AGENTS/CONTRIBUTING/README/CHANGELOG — single
  revert, no data migration.

## Gate 3 — EXECUTE + REGRESSION-TEST

- Implementation is on this branch (`build/add-template-mirror-driver`), Fable-spec'd
  (`mirror-driver-proposal-skeleton.md`), Opus-executed, independently re-verified.
- **Full suite: `63 passed in 8.44s`** locally (real run on this branch, recorded — not from memory),
  including the 8 new `test_template_mirror.py` cases and the unchanged 6 `test_template_parity.py`.
- `openspec validate add-template-mirror-driver --strict` — recorded green when run below.
- `openspec validate --all` — 7/7 on this branch (CI-equivalent).
- CI green on the PR = Gate 3 complete (recorded when checks finish).
- **Dogfood (T8) at ship time:** run `template-mirror.py` for real once to perform this release's own
  mirror into the live vault, then confirm `template-parity.py` reports `0 drift` — as
  `ship-release.py`/`pr-state.py` were proven.

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [x] Blast radius re-checked against the final diff (`git diff --name-only
      main..build/add-template-mirror-driver` = 12 files, every one declared above: AGENTS.md,
      CHANGELOG.md, CONTRIBUTING.md, README.md, the three `openspec/changes/add-template-mirror-driver/`
      artifacts, `tests/test_template_mirror.py`, `tests/test_template_parity.py`,
      `tools/template-mirror.py`, `tools/template-parity.py`, `tools/template_sync.py` — nothing
      undeclared; `template-sync-manifest.json` and `vault-template/` untouched as promised)
- [x] Consequences explicitly accepted (two repo-owned stdlib files to maintain; `template-parity.py`
      now depends on the shared `template_sync.py`; the manifest is unchanged and widens only by a
      deliberate future edit; **zero external runtime dependencies**; INV-4/5 unchanged)
- [x] Human sign-off recorded: **Approved — Keith Nielsen, 2026-07-24** (operator reviewed the proposal
      and replied `Approved`; recorded by Claude Code per the standing Gate-4 ritual — the human
      decision is the operator's reply, the agent only transcribes it)
