<!-- SPDX-License-Identifier: Apache-2.0 -->
<!--
  CONSTITUTION-OVERRIDE CHANGE TEMPLATE
  ======================================
  Use this template when your change touches a Tier-0 or Tier-1 constitutional
  element (see openspec/constitution.md §1–2).

  A constitution-override change MUST pass four gates IN ORDER before it may be
  merged.

  WHAT CI ACTUALLY CHECKS (corrected 2026-08-16, ADR-0042 — this block previously
  claimed CI would reject a PR with a missing or incomplete gate section, which
  was never true; the same false claim was retracted from constitution.md by
  PR #85 and survived here, in the file an author reads WHILE performing the
  ceremony):
    - `constitutional-diff-gate` reads the diff. If your change modifies a spec
      whose frontmatter carries `protects:`, it requires a committed
      `constitutional-impact` declaration, and — where that declaration names an
      overridden Tier-0/Tier-1 element — a change directory of this type whose
      four `## Gate N` headings are all present.
    - It checks that the gate SECTIONS EXIST. Nothing reads what you wrote in
      them, nothing verifies a checkbox is ticked, and nothing validates the
      sign-off.
    - It is REPORT-ONLY during burn-in and cannot currently fail a build.
  The gates below bind through ceremony and human review. A green CI run is not
  evidence that you completed them.

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

<!-- MANDATORY by the protocol. CI checks only that this heading EXISTS; it does not
     read the content and does not verify the checkboxes. Unchecked items pass CI. -->

**Principle(s) being overridden (restate in your own words):**

> <Restate the "what breaks" clause from constitution.md in the proposer's own words.
>  Do not copy-paste — demonstrate you understood it.>

**Blast radius — every artifact referencing this principle:**

**Enumeration transcript (mandatory — the checklist below is derived from it, and Gate 4
re-runs it):**

```transcript
$ <search command(s) sweeping openspec/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md>
<full, untruncated output — never head/tail-truncated>
```

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

<!-- MANDATORY by the protocol. CI checks only that this heading EXISTS; nothing
     validates the migration plan or the named regression tests. -->

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

**Verification transcripts attached for every named test (tally/diff/exit status — no prose verdicts):** ☐

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

<!-- MANDATORY by the protocol. This section must be completed and signed by a human
     — not an agent. NOTHING IN CI READS THE SIGN-OFF: no check verifies it is present,
     filled in, or human. It binds through review and the §5 agent hard stop alone. -->

**Second review confirms blast radius was fully addressed:** ☐  
**Gate-1 transcript re-run; output diffed clean against the proposal:** ☐

**Consequences explicitly accepted:**

> <State what is being sacrificed. What does this system no longer have that it had before?
>  What users/forks will be affected and how?>

**ADR created:** `openspec/adr/<NNNN>-<slug>.md` ☐  
**ADR captures:** context / options / choice / consequence / **sacrifice** ☐  

**SIGN-OFF** (human only — agents may not sign):  
Name: ___________________________  
Date: ___________________________  
