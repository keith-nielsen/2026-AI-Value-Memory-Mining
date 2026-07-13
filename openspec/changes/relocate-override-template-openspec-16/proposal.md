<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: relocate-override-template-openspec-16

**Change type:** `constitution-override` (procedural — touches the `protects:`-tagged `maintenance` spec
[`protects: [INV-2, INV-3, INV-6]`] and pointer text in `openspec/constitution.md`; **NO Tier-0/1
element is overridden or weakened** — a tooling-hygiene refinement, run through the ceremony because it
edits `protects:`-tagged artifacts, per constitution §1/§3)
**Principle(s) affected:** none overridden. Adds a new `maintenance` requirement alongside INV-2/3/6;
CONST-01–05, INV-12, and every invariant keep their exact meaning.
**Tier:** procedural (no principle change)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-13)
**Date:** 2026-07-13

---

## Why

The constitution-override ceremony template — a blank scaffold with `<angle-bracket>` placeholders —
lived at `openspec/changes/templates/constitution-override/proposal.md`, **inside the `changes/` tree the
OpenSpec validator scans.** OpenSpec `1.6.0`'s improved change-discovery now enumerates that folder as a
real change (`change/templates`) and fails it against the pre-existing rule *"a change must have ≥1
delta"* — a template legitimately has no spec deltas. This blocked adopting `1.6.0` (Dependabot PR #18:
`OpenSpec validate` red). The `1.4.1` pin + weekly canary caught the forward-incompatibility exactly as
designed. The rule is not new — `1.4.1 --strict` already rejected the template when named; `1.6.0` merely
now *discovers* it by default. Root cause: a non-change artifact living where the validator treats every
folder as a change. That was latent debt `1.4.1`'s lenient discovery masked.

## What Changes

The ceremony template moves out of the scanned tree to `openspec/templates/constitution-override/proposal.md`
(minimal `changes/templates/` → `templates/` path swap; OpenSpec scans only `changes/` and `specs/`, so
`openspec/templates/` is invisible to it — verified empirically under 1.6.0). All 7 references and the CI
`test -f` guard move in lockstep. The `@fission-ai/openspec` pin advances `1.4.1 → 1.6.0` (bundled;
supersedes Dependabot #18). A new `maintenance` requirement codifies what was mere convention: governance
tooling is version-pinned, and ceremony templates live outside `openspec/changes/` — so this cannot recur.

---

## Gate 1 — CHECK (Impact Analysis)

**What is being changed (in my own words):**

> Nothing in the constitution's *principles* changes. A blank template file was sitting in the folder the
> validator treats as the change-set; a stricter validator started (correctly) reading it as a change and
> rejecting it for having no deltas. We move the template to a sibling folder the validator does not scan,
> repoint every reference, adopt the newer validator, and write down (as a spec requirement) the rule that
> keeps templates out of the change tree. No invariant loses its basis; the ceremony itself is unchanged —
> only the file that scaffolds it moved.

**Blast radius — every artifact referencing the template path or the pin:**

- [x] `openspec/changes/templates/constitution-override/proposal.md` — MOVE to
      `openspec/templates/constitution-override/proposal.md` (content unchanged)
- [x] `openspec/constitution.md` §3 (L149) — repoint template path (no principle text changed; all 5
      CONST entries intact → constitution-lint green)
- [x] `.github/workflows/ci.yml` (L77) — repoint the `test -f` template-exists guard
- [x] `AGENTS.md` (L17), `README.md` (L256), `CONTRIBUTING.md` (L28),
      `docs/USING-THIS-TEMPLATE.md` (L261), `.github/ISSUE_TEMPLATE/change-proposal.yml` (L11) — repoint
- [x] `package.json` (L8) — pin `1.4.1 → 1.6.0`; `package-lock.json` regenerated
- [x] `openspec/specs/maintenance/spec.md` — ADD requirement (spec delta in this change; applied at archive)
- [x] `README.md` — ADR count `25 → 26` in all 3 sites + range `ADR-0001–0026` (CI adr-count guard)
- [x] ADR-0026 (new); CHANGELOG `[Unreleased]`
- [ ] No live-vault / `vault-template/` change (this is repo-side dev tooling; not shipped to a deployed vault)
- [ ] No `protects:`-tagged INV-2/3/6 requirement is modified — the new requirement is additive

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. `git mv` the template out of `changes/` → `openspec/templates/constitution-override/`; remove the
   emptied `changes/templates/` dir.
2. Repoint all 7 references + the CI guard (mechanical `changes/templates/` → `templates/`).
3. `package.json` pin `1.4.1 → 1.6.0`; regenerate `package-lock.json` (`npm install`).
4. Spec delta: ADD `maintenance` requirement — tooling version-pinned + ceremony templates outside
   `changes/` (version-agnostic wording; the number lives in `package.json`).
5. `README.md` ADR count `25 → 26` (3 sites) + latest `0026`; CHANGELOG `[Unreleased]`; ADR-0026 (Proposed).

**Regression (must pass green before Gate 3 closes):**

- `openspec validate relocate-override-template-openspec-16 --strict` + `openspec validate --all --strict`
  **under 1.6.0** (proves the template is no longer scanned and the new change validates).
- `pytest tests/` (fleet suite unaffected).
- CI adr-count guard passes locally (26 == 26, latest 0026); constitution-lint green (5 CONST entries +
  template present at new path); markdown/link/spec/runbook lints green.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — template moved; 7 refs + CI guard repointed; pin bumped + lock
regenerated; spec delta; README count; ADR-0026; CHANGELOG.
**All regression tests green:** ☑ — `openspec validate --all --strict` (8 passed/0 failed); `pytest
tests/` (25 passed); adr-count guard (26/latest-0026); constitution-lint (5 CONST + template at new
path + 6 specs `protects:`); repointed README link resolves.
**CI green on this PR:** ☐ — filled after the PR runs.

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> The repo adopts OpenSpec 1.6.0 and its stricter default discovery. The ceremony template moves to
> `openspec/templates/` and is codified as living outside the change tree. **Sacrifice:** none material —
> a blank scaffold that was (incorrectly) inside the scanned tree is no longer there; every reference and
> the CI guard were updated in lockstep, so the ceremony is fully intact. The pin advances, keeping
> validation reproducible; the weekly `@latest` canary continues to flag future incompatibilities.

**ADR created:** `openspec/adr/0026-relocate-override-template-openspec-16.md` (Proposed) ☑ — flips to
Accepted at sign-off
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen (operator)
Date: 2026-07-13
Authorization: Gate-4 approved by the operator in session ("Approved", 2026-07-13); recorded by the agent
at the operator's standing direction — the human decided, the agent transcribed.
