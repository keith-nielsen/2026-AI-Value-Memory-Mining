<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: add-overreach-scope-review

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** one Requirement ("Scope-Review CI Gate — Declared Scope"). **No principle is overridden
or weakened**; the gate is additive and deterministic. Conforming amendment per repo precedent
(every archived change touching a protected spec ran this ceremony, including conforming ones —
`fix-commit-gate-env-guard` et al.).
**Tier:** 0-adjacent (adds a CI enforcement surface aligned with INV-6 determinism; §5 AI
hard-stop honored — surfaced for explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-14)
**Date:** 2026-07-14

---

## Why

The determinism failure record (vault Site `determinism-failure-modes-claude`, F1–F15) contains a
class with no mechanical counter anywhere in the stack: **class-3 wandering** — an agent doing
work beyond what was asked — plus the F4/F5 commit-bundling class, countered today only by local
staging discipline. The 2026-07-14 competitive landscape analysis (vault Site
`competitive-landscape-analysis-to-incorporate`, action N2) selected **OverReach**
(MIT, `Naveja00/OverReach`) in its deterministic scope-injection mode as the merge-boundary gate:
every PR declares its authorized surface machine-readably; CI compares the actual diff against the
declaration by set arithmetic — no LLM anywhere in the decision path, holding identically
regardless of which model authored the PR, at what effort, or at what context length.

The declaration is not a new concept: for ceremony changes it is the **Gate-1 blast radius**,
which this gate converts from prose into a machine-checked contract.

## What Changes

- **`maintenance` spec:** +1 ADDED Requirement — every PR carries a fenced ```scope declaration;
  CI extracts it (fail-closed), diffs against the merge base, runs the pinned checker offline, and
  enforces a fail-on-MEDIUM-or-higher threshold; two-stage adoption (report-only burn-in → blocking
  flip as its own change); dependabot exempt.
- **`.github/workflows/ci.yml`:** +1 job `scope-review` (Phase A: `continue-on-error: true`).
- **`.github/scripts/extract-declared-scope.py`** (new): PR body (via env, injection-safe) →
  OverReach internal-shape `scope.json`; rejects globs and non-path entries; fail-closed.
- **`.github/scripts/check-scope-findings.py`** (new): applies the MEDIUM+ threshold to the JSON
  result (OverReach's own exit code fires only on HIGH — an out-of-scope file is MEDIUM and would
  pass silently; probed 2026-07-14); fails closed on malformed output.
- **`.github/pull_request_template.md`:** +Declared-scope section and checklist line.
- **`README.md`:** CI comment line gains `+ scope-review`.
- **`CHANGELOG.md`:** `[Unreleased]` entry, including the attribution hat-tip to every project
  evaluated in the landscape analysis (operator attribution policy, 2026-07-14).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> The `maintenance` spec governs the deterministic tooling surface: INV-2 (one mutation, one
> commit), INV-3 (literate scripts, drift detected never auto-fixed), INV-6 (deterministic
> tooling is offline, no LLM calls). The scope-review gate *extends* this posture to the CI merge
> boundary: the checker runs offline with no keys, the decision path is set arithmetic, and the
> gate mechanically backstops the INV-2 discipline (an undeclared file riding a PR is a named
> finding). Nothing existing is relaxed; a new deny-by-default check is added.

**Blast radius — every artifact this change touches:**

- [x] `openspec/specs/maintenance/spec.md` — ADDED Requirement (spec delta in this change)
- [x] `.github/workflows/ci.yml` — +`scope-review` job
- [x] `.github/scripts/extract-declared-scope.py` — new
- [x] `.github/scripts/check-scope-findings.py` — new
- [x] `.github/pull_request_template.md` — +section, +checklist line
- [x] `README.md` — one comment line
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `vault-template/` — **no change** (repo-side CI only; the deployed vault is untouched —
      standalone premise holds)
- [ ] Existing CI jobs — **no change** (new job is additive; runs only on `pull_request`)

**External dependency being adopted:** `overreach@0.7.0` (MIT), exact-pinned, invoked via `npx`
in CI only. Probed 2026-07-14: `--scope` injection makes the run LLM-free and offline; no repo
writes in this mode; telemetry fires only on `overreach init` (never run in CI) and
`OVERREACH_TELEMETRY=0` is set regardless. Known limitations accepted and encoded: no glob
support (extract script rejects globs); path matching has lenient branches (extract script
requires path-shaped entries to stay in the strict branch); pre-1.0 single-maintainer project —
treated as an additive quality gate, not a security rail; nothing existing depends on it.

## Gate 2 — PLAN (Migration + Regression)

- Additive change: no migration of existing artifacts; no lockstep updates beyond the blast list.
- Two-stage adoption mirrors the access-control spec's burn-in pattern: **Phase A** report-only
  (`continue-on-error: true`) for ≥3–5 PRs to measure false-positive rate on a markdown-heavy
  repo; **Phase B** (its own governed change) removes `continue-on-error`.
- Regression: all existing CI jobs must stay green (`openspec validate --all`, constitution-lint,
  vocabulary-lint, spec-lint, naming-validator, md-lint, link-check, validate-scripts,
  fleet-pytest). New-script determinism: local test matrix T1–T6 + end-to-end clean-path run
  (recorded in the vault Site, 2026-07-14) — extract (valid/missing/glob/tokenish), threshold
  (MEDIUM+→1, garbage→2, clean→0).
- Rollback: delete the job + scripts + template section (single revert; no data migration).

## Gate 3 — EXECUTE + REGRESSION-TEST

- Implementation in this PR. Local pre-push: `openspec validate --all` green; script test matrix
  T1–T6 + E2E green (2026-07-14).
- The PR itself dogfoods the gate: its body carries the Declared-scope block for this exact
  file set; the `scope-review` job must report PASS on it.
- **Dogfood run 1 (2026-07-14): the gate correctly failed its own PR** — `[HIGH] scope.env:
  Added environment variable "PR_BODY"` (the job's own workflow env var, undeclared). True
  positive, and it exposed a declaration-language gap: only files were declarable. Fixed in this
  change: prefixed non-file entries (`env:` / `dep:` / `endpoint:`) added to the extract script,
  template, and spec delta; this PR's block declares `env: PR_BODY`. Recorded as evidence the
  detector catches non-file smuggling (the F8/F9 blast-radius-miss class).
- CI green on the PR = Gate 3 complete (recorded here when checks finish).

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**PENDING operator sign-off.** Per §5, this change is not merged until the operator has reviewed
the consequences above and replied **Approved**.

- [ ] Blast radius re-checked against the final diff
- [ ] Consequences explicitly accepted (new external dev-dependency in CI, pre-1.0, pinned;
      per-PR scope-block ceremony added)
- [ ] Human sign-off recorded here
