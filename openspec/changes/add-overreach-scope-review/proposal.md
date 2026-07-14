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
`competitive-landscape-analysis-to-incorporate`, action N2) identified the merge-boundary gate
pattern via **OverReach** (MIT, `Naveja00/OverReach`): every PR declares its authorized surface
machine-readably; CI compares the actual diff against the declaration by set arithmetic — no LLM
anywhere in the decision path, holding identically regardless of which model authored the PR, at
what effort, or at what context length. After a supply-chain audit (the tool's `npx` invocation
resolves a **113-package floating transitive tree** at every CI run — the classic
flip-on-us-later vector), the operator directed a **clean-room, stdlib-only reimplementation of
the concept** (2026-07-14): the gate carries **zero runtime dependencies** and OverReach is
credited as concept source, not adopted as code.

The declaration is not a new concept: for ceremony changes it is the **Gate-1 blast radius**,
which this gate converts from prose into a machine-checked contract.

## What Changes

- **`maintenance` spec:** +1 ADDED Requirement — every PR carries a fenced ```scope declaration;
  CI extracts it (fail-closed), diffs against the merge base, and compares deterministically with
  a self-contained comparator; two-stage adoption (report-only burn-in → blocking flip as its own
  change); dependabot exempt.
- **`.github/workflows/ci.yml`:** +1 job `scope-review` (Phase A: `continue-on-error: true`;
  `permissions: contents: read` least-privilege token; no Node, no registry contact).
- **`.github/scripts/extract-declared-scope.py`** (new): PR body (via env, injection-safe) →
  `scope.json` (schema retained from the evaluated tool); rejects globs and non-path entries;
  fail-closed.
- **`.github/scripts/check-scope-findings.py`** (new): stdlib-only comparator — diff paths vs
  declared entries (exact / dir-prefix only, no fuzzy branches), added workflow env vars vs
  `env:` declarations, added manifest deps vs `dep:` declarations; undeclared file = medium,
  undeclared env/dep = high; any finding fails; malformed inputs fail closed.
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
- [x] `AGENTS.md` — +1 Operating-notes bullet (agent priming: the block is required, the gate is
      the process, `--body-file` bypasses the template — added at operator prompt, 2026-07-14)
- [x] `README.md` — one comment line
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `vault-template/` — **no change** (repo-side CI only; the deployed vault is untouched —
      standalone premise holds)
- [ ] Existing CI jobs — **no change** (new job is additive; runs only on `pull_request`)

**External dependency being adopted: NONE** (revised 2026-07-14 at operator direction, after the
supply-chain audit). The gate is two stdlib-only Python scripts owned by this repo — no registry
fetch, no install hooks, no floating transitive tree, nothing new in the trust ring. History of
the decision, kept for the record: the initial draft invoked `overreach@0.7.0` via `npx`; the
audit found the tool itself frozen (npm version immutability) but its 3 semver-ranged deps pull a
**113-package transitive tree resolved fresh every CI run** — the flip-on-us-later vector. The
tree audit was clean today (zero install hooks; telemetry init-only; LLM paths bypassed), but the
operator chose concept-extraction over dependency adoption. **Attribution:** the declared-scope
concept, the scope-JSON schema, and the severity taxonomy were learned from evaluating OverReach
(MIT, `Naveja00/OverReach`) — credited in the CHANGELOG; no code was copied (the comparator is a
clean-room implementation with deliberately stricter matching: exact/dir-prefix only, no
basename/substring/token/fuzzy branches).

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
- **Dogfood run 2 (2026-07-14, local, post-reimplementation): a second true positive** — the
  stricter stdlib comparator flagged `OVERREACH_TELEMETRY` as an undeclared workflow env var on
  this PR's own diff, a finding the evaluated tool had missed on the identical input. Resolved
  by the reimplementation itself (that env var existed only for the removed npx invocation).
  Unit matrix U1–U4 green (creep FAIL incl. manifest file, env detect, declared-env PASS,
  malformed fail-closed); real-diff dogfood PASS after the ci.yml rework.
- CI green on the PR = Gate 3 complete (recorded here when checks finish).

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [x] Blast radius re-checked against the final diff (10 files, all declared; scope-review PASS
      on the PR's own diff; CI 13/13 green on `62de747`)
- [x] Consequences explicitly accepted (per-PR scope-block ceremony added; two repo-owned
      stdlib scripts to maintain; **zero external runtime dependencies**)
- [x] Human sign-off recorded: **Approved — Keith Nielsen, 2026-07-14** (operator reviewed the
      proposal via read-only `view` and replied `Approved`; recorded by Claude Code per the
      standing Gate-4 ritual — the human decision is the operator's reply, the agent only
      transcribes it)
