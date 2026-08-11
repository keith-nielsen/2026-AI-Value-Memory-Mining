<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [ ] 1.1 `maintenance` ADDED: *An Architecture Decision Record Citation Resolves* (4 scenarios)
- [ ] 1.2 Confirm nature is ordinary, not override — ADD-only, nothing weakened; `constitution.md` §2
      places conventions at Tier 2 ("no ceremony required"); §5's hard stop is about *modifying* a
      `protects:`-tagged element. Precedent: PR #53. **Not** derived from a green `constitution-lint`,
      which does no diff analysis

## 2. ADR-0039 — the missing record

- [~] 2.1 `openspec/adr/0039-flip-scope-review-blocking.md` — Context / Options / Decision /
      Consequences / Sacrifice / Follow-on, matching ADR-0037's structure
- [~] 2.2 Content consolidated from the `ci.yml:505-519` comment block and
      `flip-scope-review-blocking`'s proposal — **not** reconstructed from memory. Cite both
- [~] 2.3 Record the provenance honestly: dated 2026-08-06 (the decision), written 2026-08-11, and say
      why — the citation preceded the record
- [~] 2.4 Preserve the load-bearing ordering fact: the job name dropped ", burn-in" **while the context
      was still UNREQUIRED**, because the name IS the check-context identity and renaming a required
      context deadlocks merges
- [~] 2.5 Carry the open follow-on with its trigger: `Scope review` joins `required_status_checks` once
      the `skipped`-conclusion question resolves (undecidable on this plan — ADR-0034)

⚠ **2.x is `[~]` — written, not verified.** Two consequences of writing the ADR ahead of the rest,
recorded rather than left to be discovered:

- **`spec-lint` is now knowingly red locally.** 39 ADR files exist while `README.md` still claims 38
  in three places, so the existing *Check README ADR count matches actual* step fails until task 4
  lands. Nothing is committed; tasks 2 and 4 must land together.
- **Test 5.1's evidence must now be reconstructed, not observed in place.** The pre-fix measurement
  (`ADR-0039` dangling, `ci.yml:513`) was captured before the file was written and is quoted in
  `proposal.md`; the new check must still be run against a tree with the ADR moved aside. Untracked,
  so this is reconstructible — but it is weaker than having run the check first, and is not to be
  ticked `[x]` on the strength of the earlier grep alone.

## 3. Instrument — `spec-lint` in `.github/workflows/ci.yml`

- [ ] 3.1 Replace `EXPECTED = [... range(1, 9)]` with a **contiguity** assertion over the records
      present: `0001..max`, no gap, no duplicate. Defect 1 — the current check validates 8 of 38 and
      is green regardless
- [ ] 3.2 Add the **reference-integrity** check: every `ADR-[0-9]{4}` cited in the repo resolves
- [ ] 3.3 Apply the scoped forward-reference policy: unresolved citations permitted **only** under
      `openspec/changes/`, **excluding** `openspec/changes/archive/`
- [ ] 3.4 Report **file and line** per unresolved citation — an identifier alone does not locate the
      assertion needing correction
- [ ] 3.5 Keep it stdlib-only Python, consistent with the sibling `spec-lint` steps and the standing
      trust-ring constraint (no third-party code added)
- [ ] 3.6 Exclude `node_modules/` from the sweep

## 4. Lockstep — `README.md` (enforced by the existing count check)

- [ ] 4.1 `README.md:29` — "38 ADRs" → "39 ADRs"
- [ ] 4.2 `README.md:100` — "38 Architecture Decision Records (ADR-0001–0038)" → 39 / `ADR-0001–0039`
- [ ] 4.3 `README.md:250` — "38 ADRs: framework choice → required check contexts" → 39, and extend the
      summary to the new endpoint
- [ ] 4.4 Verify against the existing *Check README ADR count matches actual* step — it asserts both
      the count and that the highest number appears in README, so a partial edit fails

## 5. Tests — observe the failure before the fix

- [ ] 5.1 **Observe the check failing without ADR-0039** — it must fail naming
      `.github/workflows/ci.yml:513`. ⚠ The ADR is already written (2.x), so run this with the file
      moved aside; a check that has only ever been run against a tree where it passes proves nothing
- [ ] 5.2 Run it again after ADR-0039 lands → passes
- [ ] 5.3 `ADR-0040` in `estate-scoped-capability-probe/tasks.md:106` → **passes** (live change dir).
      This is the adversarial case for over-denial; write it before the confirming one
- [ ] 5.4 Same citation relocated under `openspec/changes/archive/` → **fails**. Exercises the
      archive-is-a-record rule, a state the mechanism itself creates
- [ ] 5.5 Contiguity: synthesise a corpus missing one number → fails naming the gap; and confirm the
      real corpus (0001–0038, verified contiguous) passes
- [ ] 5.6 Confirm the old `range(1, 9)` check would have passed every one of 5.1–5.5 — the measurement
      that justifies replacing it rather than extending it

## 6. Regression

- [ ] 6.1 `openspec validate --all --strict` (CLI `1.6.0` == `package.json` pin)
- [ ] 6.2 Full `spec-lint` job reproduced locally, all steps
- [ ] 6.3 `md-lint` and `link-check` — README and a new ADR are both in their scope
- [ ] 6.4 Confirm the strengthened `spec-lint` finds **no other** pre-existing violation; if it does,
      that is a real defect to fix or log, **never** a reason to weaken the rule

## 7. Ship

- [ ] 7.1 PR body declares the full scope — `scope-review` is blocking (ADR-0039, the record this
      change writes) and diffs the branch against the declared scope
- [ ] 7.2 Land via `tools/pr-flow.py --plan --branch BR` first, then the driven route. Never
      hand-compose the sequence
- [ ] 7.3 Archive as its own follow-up `chore/archive-enforce-adr-reference-integrity` PR — the #58
      shape, per the operator decision of 2026-08-11
