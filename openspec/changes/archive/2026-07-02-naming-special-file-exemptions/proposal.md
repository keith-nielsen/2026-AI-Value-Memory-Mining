<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: naming-special-file-exemptions

**Change type:** `constitution-override`
**Principle(s) affected:** `naming-rules` spec — `protects: [INV-11]`. **Conforming amendment** — additive: defines the special-file exemption set that the (deferred) mechanical ≥3-token/kebab enforcement MUST honor. **Strengthens INV-11's correctness; weakens nothing.** Extends **ADR-0015** (token-minimum naming) and its "mechanical enforcement deferred, gated on conformance" clause.
**Tier:** 0 (INV-11) — additive/conforming
**Proposer:** Keith Nielsen (drafted by Claude Code; authorized by Keith)
**Date:** 2026-07-02

> **Ratify-in-place note.** Implemented in the live vault ahead of this ceremony (Gate-3 preceded
> Gates 1–2); nothing pushed. This change documents and ratifies it; repo `vault-template/` mirror +
> regression + ADR + Gate-4 sign-off remain outstanding below.

---

## Why

ADR-0015 established the ≥3-token floor as **convention now, mechanical enforcement later** (deferred,
gated on family conformance). A small set of filenames **cannot** conform because an external tool or
universal convention requires their **exact** name — `README.md`, `LICENSE`, `CLAUDE.md`, `AGENTS.md`,
`MEMORY.md`, `.gitignore`/`.gitkeep`/`.gitattributes`, `config.env`/`config.defaults.env`, `*.example`,
dailies (`YYYY-MM-DD`). Turning on mechanical ≥3-token/kebab enforcement without an exemption set would
wrongly reject them. This change codifies the exemptions **before** enforcement is switched on — exactly
the sequencing ADR-0015 anticipated.

## What Changes

- **ADD** a *Special-File Exemptions* requirement to `naming-rules`: `exempt_names` (exact filenames) +
  `exempt_globs` (basename patterns: `*.example`, daily `YYYY-MM-DD.md`), matched on the **filename
  (basename)** via `is_exempt(filename)`; exempt files are skipped by the kebab/token rules. Editor
  state under `.obsidian/` is out of scope via `.gitignore` (not a naming exemption).
- **MODIFY** the *Language-Neutral Mirror* requirement: `naming-rules.json` now also contains
  `min_hyphen_tokens`, `exempt_names`, `exempt_globs`, `exempt_rationale_doc`.
- Add `docs/naming-exemptions-rationale.md` (per-dependency-class rationale) + link from `USING-THIS-TEMPLATE`.
- **Mechanical enforcement remains deferred** (ADR-0015): the linter *honors* exemptions now (the
  ≥3-token/kebab rejection is wired but staged/commented), so enabling it later is safe. No name renamed.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `naming-rules`: ADD *Special-File Exemptions*; MODIFY *Language-Neutral Mirror* (JSON gains the exemption fields).

## Impact

- **Spec delta:** `naming-rules` (one ADDED requirement + one MODIFIED requirement).
- **Implementation (live vault — DONE, ratify-in-place):** `naming-rules-script.md` (`exempt_names`/`exempt_globs`/`min_hyphen_tokens` + `is_exempt`/`has_min_hyphen_tokens`); `knowledge-lint-script.md` honors `is_exempt` (min-token check staged/commented); regenerated `naming-rules.json`.
- **Implementation (repo `vault-template/` — TODO):** same two meta-scripts mirrored.
- **Docs:** `docs/naming-exemptions-rationale.md` (new); `docs/USING-THIS-TEMPLATE.md` link.
- **New ADR-0021** (Gate 4).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** INV-11 (Tier-0) requires every name to conform to the ruleset,
enforced deterministically at the boundary (commit-gate + refine executor). **What breaks if
mishandled:** unsafe/illegible names — or, specifically here, mechanical ≥3-token enforcement wrongly
rejecting tool-mandated names whose exact strings external tools require, blocking commits. This change
is **purely additive**: it introduces an exemption set that only ever *narrows* what the future
enforcement rejects (never widens it), on the basename only, and renames nothing. The base
cross-platform-safety and kebab-slug (Treasury/effort) rules are **unchanged**; existing sub-3 names stay
grandfathered per ADR-0015. INV-11 is reinforced (enforcement becomes switch-on-safe), not weakened.

**Blast radius (checked off in Gate 3):**

- [ ] `openspec/specs/naming-rules/spec.md` — ADDED *Special-File Exemptions*; MODIFIED *Language-Neutral Mirror*
- [ ] `vault-template/99-Operations/scripts/naming-rules-script.md` + `knowledge-lint-script.md`
- [ ] `docs/naming-exemptions-rationale.md` (new); `docs/USING-THIS-TEMPLATE.md` link
- [ ] `openspec/adr/0021-naming-special-file-exemptions.md` (new)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** additive. The base validator and commit-gate are unchanged; `is_exempt` is honored in the
linter's "all other content" branch, and the ≥3-token/kebab rejection stays **staged/commented** (ADR-0015
keeps mechanical enforcement deferred until families conform). No name renamed. The live vault was
migrated this session; the `vault-template/` mirror lands here so forks inherit it.

**Regression that MUST pass before Gate 3:** `openspec validate naming-special-file-exemptions --strict`
+ `--all --strict`; `constitution-lint`; `vocabulary-lint`; naming sweep (every present special file is
`is_exempt`; `naming-rules.json` carries the exemption fields; `vault-lint.py` exit 0 — all green in the
live vault this session); CI green.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — live vault + `vault-template/` mirror + docs DONE
**All regression tests green (local suite):** ☑ — `validate-scripts.sh` VALIDATION OK; `openspec validate --all --strict` 9/9; naming sweep + lint green
**CI green on this PR:** ☐ (runs on push)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> Sacrifice: none structural — additive/conforming; no name renamed, no principle weakened; mechanical
> enforcement stays deferred (ADR-0015). Cost = maintaining the exemption list as new tool-mandated
> names appear.

**ADR created:** `openspec/adr/0021-naming-special-file-exemptions.md` ☑ (Accepted)
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen — "Authorized." (transcribed by Claude Code at Keith's explicit instruction; the decision is the human's)
Date: 2026-07-02
