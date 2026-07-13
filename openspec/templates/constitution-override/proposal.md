<!-- SPDX-License-Identifier: Apache-2.0 -->
<!--
  CONSTITUTION-OVERRIDE CHANGE TEMPLATE
  ======================================
  Use this template when your change touches a Tier-0 or Tier-1 constitutional
  element (see openspec/constitution.md §1–2).

  A constitution-override change MUST pass four gates IN ORDER before it may be
  merged. CI will reject the PR if any gate section is missing or incomplete.

  Replace all <angle-bracket placeholders> with your content.
  Remove the HTML comment blocks before submitting.
-->

# Constitution Override: <change-name>

**Change type:** `constitution-override`  
**Principle(s) affected:** <CONST-01 / CONST-02 / CONST-03 / CONST-04 / CONST-05 / INV-N>  
**Tier:** <0 / 1>  
**Proposer:** <name>  
**Date:** <YYYY-MM-DD>

---

## Why

<!-- Explain the motivation. What is broken or insufficient about the current principle?
     Why is the sacrifice (see Gate 1) worth making? -->

## What Changes

<!-- Describe the override at the principle level: what the principle currently says,
     what it will say after the override, and why the new formulation is better. -->

---

## Gate 1 — CHECK (Impact Analysis)

<!-- MANDATORY. CI will fail if this section is missing or has unchecked items. -->

**Principle(s) being overridden (restate in your own words):**

> <Restate the "what breaks" clause from constitution.md in the proposer's own words.
>  Do not copy-paste — demonstrate you understood it.>

**Blast radius — every artifact referencing this principle:**

- [ ] `openspec/specs/<cap>/spec.md` — <what changes>
- [ ] `openspec/constitution.md` — principle text
- [ ] `vault-template/99-Operations/scripts/<script>.md` — <what changes>
- [ ] `vault-template/97-Molds/<mold>.md` — <what changes if any>
- [ ] `docs/diagrams/<diagram>.md` — <what changes if any>
- [ ] `docs/glossary.md` — <vocabulary terms affected>
- [ ] `AGENTS.md` — <agent instructions affected>
- [ ] CI `vocabulary-lint` controlled glossary — <terms to add/remove>
- [ ] ADR reference (new ADR required — see Gate 4)

---

## Gate 2 — PLAN (Migration + Regression)

<!-- MANDATORY. CI will fail if this section is missing. -->

**Migration plan:**

<!-- Step-by-step description of how every artifact in the blast radius is updated
     in lockstep. No artifact may be left referencing the old principle. -->

1. <Step 1>
2. <Step 2>

**Regression tests that MUST pass before Gate 3:**

- [ ] `openspec validate` passes
- [ ] `constitution-lint` passes (after this PR's changes are applied)
- [ ] `vocabulary-lint` passes with updated glossary
- [ ] Acceptance tests: <list relevant A-tests from PRD §13>
- [ ] <Any additional tests specific to this override>

---

## Gate 3 — EXECUTE + REGRESSION TEST

<!-- Filled in by the implementer after completing the migration. -->

**Implementation complete:** ☐  
**All regression tests green:** ☐  
**CI green on this PR:** ☐  

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

<!-- MANDATORY. This section must be completed and signed by a human — not an agent.
     CI will reject a merge if SIGN-OFF is missing. -->

**Second review confirms blast radius was fully addressed:** ☐  
**Consequences explicitly accepted:**

> <State what is being sacrificed. What does this system no longer have that it had before?
>  What users/forks will be affected and how?>

**ADR created:** `openspec/adr/<NNNN>-<slug>.md` ☐  
**ADR captures:** context / options / choice / consequence / **sacrifice** ☐  

**SIGN-OFF** (human only — agents may not sign):  
Name: ___________________________  
Date: ___________________________  
