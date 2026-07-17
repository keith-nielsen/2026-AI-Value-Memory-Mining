<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: add-template-parity-check

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** one Requirement ("Template–Live Parity Check (Mirror Completeness)"). **No principle is
overridden or weakened**; the check is additive, detection-only, and deterministic. Conforming
amendment per repo precedent (every archived change touching a protected spec runs this ceremony,
including conforming ones — `add-overreach-scope-review` is the direct model; like it, this
conforming amendment ships **without a new ADR**).
**Tier:** 0-adjacent (adds a mirror-time verification surface aligned with INV-3 drift-detection and
INV-6 determinism; §5 AI hard-stop honored — surfaced for explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-18)
**Date:** 2026-07-18

---

## Why

The framework repo ships a `vault-template/`; a live vault is a deployed instance mirrored from it.
`vault-render.py reconcile` covers exactly one drift axis — a script note vs. its deployed `~/bin`
target (note → host). **Nothing covers the other axis: repo-shipped scaffold → live-deployed
scaffold** (template → vault). A governed change edits `vault-template/…`, and the post-merge mirror
is a manual `cp` step with no completeness check. The result is silent, recurring *unfinished
applies*: three were caught **by hand in a single day** (2026-07-17) —
`outbound-publish-guard-script.md` left pre-ADR-0027 in the live vault (`reconcile` reported a
standing `DRIFT:` for ~3 days; the running guard was correct, the *record* described a weaker one),
the `runtime:` enum in `note-frontmatter-schema.md`, and the ADR-0024 pending-catalog precondition.
The mirror deployed the file but not its INV-3 source, or missed a file entirely — an unfinished
apply masquerading as a fix. This check makes mirror completeness **mechanical and detection-only**,
the same shape and posture as `reconcile`.

**Scope is the whole design.** A naive full-tree diff of `vault-template/` against a live vault
yields **9 differs + 2 missing**, of which **10 are legitimate per-instance divergence** (CLAUDE.md,
`.claude/settings.json`, Catalog content, README) and exactly **1 is real drift**. Comparing
everything buries the signal. The check therefore compares only the **lockstep scaffold** — the
INV-3 source-of-truth files that flow repo → live via mirror and must never diverge — declared as an
explicit prefix allowlist (operator choice, 2026-07-18). Running the prototype against the real trees
surfaced a subtlety a blind spec would have missed: the whole-`schemas/` prefix sweeps in
`naming-rules.json`, which is **generated** into the live vault by `vault_naming.py` and legitimately
absent from the template (the standing "deliberate duplication — do not rationalize" list). Hence the
manifest carries an `exclude` for generated artifacts.

## What Changes

- **`maintenance` spec:** +1 ADDED Requirement — a repo-owned, stdlib-only, detection-only parity tool;
  lockstep prefixes + generated-file excludes in a manifest; byte-exact bidirectional comparison;
  prints the denominator; fleet exit contract (0/1/3).
- **`tools/template-parity.py`** (new): the comparator. Resolves `vault-template/` relative to itself
  and the live vault from `argv[1]`/`$VAULT_ROOT`; reads the manifest; reports
  `DIFFERS`/`MISSING-IN-LIVE`/`MISSING-IN-TEMPLATE`; never writes.
- **`tools/template-sync-manifest.json`** (new): `lockstep` = `99-Operations/scripts/`,
  `99-Operations/schemas/`; `exclude` = `99-Operations/schemas/naming-rules.json`.
- **`tests/test_template_parity.py`** (new): 6 subprocess-driven cases (clean / DIFFERS /
  MISSING-IN-LIVE / MISSING-IN-TEMPLATE / exclude-honored / blocked-no-vault).
- **`AGENTS.md`:** +1 Operating-notes bullet — after a post-merge mirror, run
  `tools/template-parity.py` to prove the apply is complete (the mechanism that makes the F21-class
  drift caught, not merely catchable).
- **`README.md`:** repo-structure tree gains the `tools/` line.
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Deliberately out of scope.** (a) The check does NOT cover per-instance seed, so it does **not**
subsume the ADR-0024 apply (`40-Treasury/Catalog/pending-catalog-index.md` is seed, INV-9) — that
remains its own carry-forward item. (b) No CI job — CI has no live vault to compare against; this is a
mirror-time local tool. (c) Lockstep is scripts + schemas only; molds/runbooks are not included until
drift is observed there (solve the proven problem, don't speculatively widen).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> The `maintenance` spec governs the deterministic tooling surface: INV-2 (one mutation, one commit),
> INV-3 (literate scripts; drift **detected, never auto-fixed** — a human re-runs the deploy), INV-6
> (deterministic tooling is offline, no LLM). This parity check *extends* the INV-3 drift-detection
> posture to a second axis (template → live) that `reconcile` never covered, honoring the same
> never-auto-fix rule; it runs offline with no network and no model (INV-6); and it mechanically
> backstops the mirror step so an unfinished apply is surfaced instead of lingering as a false "done".
> Nothing existing is relaxed; a new detection-only check is added.

**Blast radius — every artifact this change touches:**

- [x] `openspec/specs/maintenance/spec.md` — ADDED Requirement (spec delta in this change)
- [x] `tools/template-parity.py` — new
- [x] `tools/template-sync-manifest.json` — new
- [x] `tests/test_template_parity.py` — new
- [x] `AGENTS.md` — +1 Operating-notes bullet (run parity after a mirror)
- [x] `README.md` — repo-structure tree gains `tools/`
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `vault-template/` — **no change** (repo-side maintenance tool only; the deployed vault is
      untouched — the standalone premise holds, F15)
- [ ] `.github/workflows/ci.yml` — **no change** (no CI job; CI has no live vault)
- [ ] `openspec/adr/` + README ADR count — **no change** (conforming amendment ships without an ADR,
      per the `add-overreach-scope-review` precedent; the ADR-count guard is untouched)

**External dependency being adopted: NONE.** The tool is one stdlib-only Python file owned by this
repo — no registry fetch, no install hooks, nothing new in the trust ring.

## Gate 2 — PLAN (Migration + Regression)

- Additive change: no migration of existing artifacts; no lockstep updates beyond the blast list.
- **Coexistence with the in-flight `add-telemetry-segment` change** (also MODIFIES `maintenance`):
  this change only ADDS a Requirement and touches no requirement telemetry touches, so there is no
  header collision. At archive time, honor **batch-archive-in-merge-order** so the cumulative
  superset lands last (verify: no duplicate `### Requirement:` headers, `openspec validate --all`
  clean).
- Regression: all existing CI jobs stay green (`openspec validate --all --strict`, constitution-lint,
  vocabulary-lint, spec-lint, naming-validator, md-lint, link-check, validate-scripts, adr-count-lint,
  fleet-pytest). New test module `tests/test_template_parity.py` green.
- Rollback: delete `tools/` + the test + the spec delta + the AGENTS/README/CHANGELOG lines (single
  revert; no data migration).

## Gate 3 — EXECUTE + REGRESSION-TEST

- Implementation in this PR. Prototype was proven against the **real** repo template vs. the **real**
  live vault before the spec was written: clean case `19 lockstep files checked (1 excluded) — 0
  drift` (exit 0); injected-drift case correctly flagged a hand-edited script (`DIFFERS`) and a
  deleted schema (`MISSING-IN-LIVE`) (exit 1); the run also surfaced the generated-`naming-rules.json`
  exclusion the spec now encodes.
- `tests/test_template_parity.py` — **6 passed** locally (`clean / DIFFERS / MISSING-IN-LIVE /
  MISSING-IN-TEMPLATE / exclude-honored / blocked-no-vault`).
- `openspec validate add-template-parity-check --strict` green (recorded when run).
- CI green on the PR = Gate 3 complete (recorded here when checks finish).

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [x] Blast radius re-checked against the final diff (7 surfaces, all declared; `git status` on the
      branch = AGENTS.md + CHANGELOG.md + README.md modified, `tools/` + `tests/test_template_parity.py`
      + `openspec/changes/add-template-parity-check/` new — nothing undeclared)
- [x] Consequences explicitly accepted (one repo-owned stdlib tool + manifest to maintain; the
      lockstep set is scripts+schemas and widens only by a deliberate manifest edit; **zero external
      runtime dependencies**)
- [x] Human sign-off recorded: **Approved — Keith Nielsen, 2026-07-18** (operator reviewed the
      proposal and replied `Approved`; recorded by Claude Code per the standing Gate-4 ritual — the
      human decision is the operator's reply, the agent only transcribes it)
