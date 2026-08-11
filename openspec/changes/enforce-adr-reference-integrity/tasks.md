<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [x] 1.1 `maintenance` ADDED: *An Architecture Decision Record Citation Resolves* (4 scenarios) — `openspec validate --all --strict` 7/7, exit 0
- [x] 1.2 Confirm nature is ordinary, not override — ADD-only, nothing weakened; `constitution.md` §2
      places conventions at Tier 2 ("no ceremony required"); §5's hard stop is about *modifying* a
      `protects:`-tagged element. Precedent: PR #53. **Not** derived from a green `constitution-lint`,
      which does no diff analysis

## 2. ADR-0039 — the missing record

- [x] 2.1 `openspec/adr/0039-flip-scope-review-blocking.md` — Context / Options / Decision /
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

**On the markers above:** 2.1 is `[x]` because the record's *absence* was observed to fail the check
(5.1) and its presence to pass it (5.2) — that is a test. **2.2–2.5 stay `[~]` deliberately: they are
claims about the ADR's *content*, verified by inspection against the two cited sources, not by any
test.** No check can confirm that a decision record faithfully represents the decision, and marking
them `[x]` would borrow credibility from 5.1's evidence for a claim it does not cover.

Resolved since first draft: the transient README/ADR-count mismatch closed when task 4 landed in the
same commit, and 5.1's evidence was reconstructed by moving the ADR aside rather than inferred from
the earlier grep.

## 3. Instrument — `spec-lint` in `.github/workflows/ci.yml`

- [x] 3.1 Replaced `EXPECTED = [... range(1, 9)]` with a **contiguity** assertion (`0001..max`, no gap,
      no duplicate), step renamed *Check ADR numbering is contiguous*. Evidence: 5.5
- [x] 3.2 Added *Check every cited ADR resolves*. Evidence: 5.1 / 5.2
- [x] 3.3 Scoped forward-reference policy implemented — permitted only under `openspec/changes/<slug>/`,
      **excluding** `archive/`. Evidence: 5.3 (pass) and 5.4 (fail), the two halves
- [x] 3.4 Reports `file:line` per unresolved citation. Evidence: 5.1 output names
      `.github/workflows/ci.yml:565`
- [x] 3.5 Stdlib-only (`collections`, `pathlib`, `re`, `sys`) — no third-party code added to the trust
      ring, consistent with the sibling `spec-lint` steps
- [~] 3.6 `node_modules`, `.git`, `.venv` excluded, and the sweep is suffix-filtered. Exclusion is
      **not independently asserted** by a test — the run completes and reports only expected findings,
      which is consistent with exclusion but does not prove it

## 4. Lockstep — `README.md` (enforced by the existing count check)

- [x] 4.1 `README.md:29` — "38 ADRs" → "39 ADRs"
- [x] 4.2 `README.md:100` — → "39 Architecture Decision Records (ADR-0001–0039)"
- [x] 4.3 `README.md:250` — → "39 ADRs: framework choice → declared-scope gate blocking"
- [x] 4.4 Existing *Check README ADR count matches actual* step run locally:
      `adr-count-lint OK: 39 ADRs, latest 0039`, exit 0. It asserts both the count and that the
      highest number appears, so a partial edit would have failed

## 5. Tests — observe the failure before the fix

Tests run against the **step text extracted from `ci.yml`**, not a retyped copy, so they exercise what
ships (`scratchpad/extract_step.py` pulls the `run:` heredoc by step name).

- [x] 5.1 ADR-0039 moved aside → **FAIL, exit 1**, `3 unresolved citation(s)`, naming
      `.github/workflows/ci.yml:565` (the original PR #58 citation) plus the two new comment references.
      Observed failing before the fix
- [x] 5.2 ADR-0039 restored → **PASS, exit 0**, `all cited ADRs resolve (39 records)`
- [x] 5.3 **Over-denial guard.** `ADR-0040` cited at `proposal.md:22` in this live change dir, still
      dangling → **exit 0**. The legitimate forward reference is not punished
- [x] 5.4 Same citation written under `openspec/changes/archive/zz-probe-temp/` → **exit 1**,
      `cites ADR-0040 but no such record exists`. Archive-is-a-record holds. Temp dir removed;
      `git status` confirmed no residue
- [x] 5.5 ADR-0037 moved aside → **exit 1**, `GAP: ADR-0037 is missing (highest is 0039)`; restored →
      **exit 0**, `adr-contiguity OK: 39 ADRs, 0001-0039`
- [x] 5.6 **The measurement that justifies replacement over extension:** with ADR-0037 *and* ADR-0039
      both absent and ADR-0039 cited in `ci.yml`, the old `range(1, 9)` check returns **PASS**. It was
      green while blind to every defect this change fixes

## 6. Regression

- [x] 6.1 `openspec validate --all --strict` — **7 passed, 0 failed, exit 0** (CLI `1.6.0` == pin)
- [x] 6.2 `spec-lint`'s four spec/ADR steps reproduced locally — all exit 0:
      `adr-contiguity OK: 39 ADRs, 0001-0039` · `adr-reference-integrity OK` ·
      `adr-count-lint OK: 39 ADRs, latest 0039` · expected-specs exit 0
- [x] 6.3 `ci.yml` parses as YAML after the edit (PyYAML `safe_load`, exit 0) — the edit is inside a
      workflow file, so malformed YAML would take the whole pipeline down, not just this job
- [ ] 6.4 `md-lint` / `link-check` — **NOT VERIFIABLE locally: `markdownlint-cli` is not installed**
      (CI installs it at job time). Deferred to CI; do not tick on inspection
- [x] 6.5 Strengthened `spec-lint` finds **no other** pre-existing violation across the corpus — the
      only unresolved citation is `ADR-0040`, correctly exempt as a live proposal

## 7. Gate 4 — human sign-off (not agent-delegatable)

- [x] 7.1 **Approved** — Keith Nielsen, 2026-08-11. Gate 3 complete: implementation done, regression
      evidence recorded above, with 6.4 (`md-lint`/`link-check`) honestly deferred to CI for absent
      local tooling and 3.6 / 2.2–2.5 left `[~]` rather than over-claimed

## 8. Ship

- [ ] 8.1 PR body declares the full scope — `scope-review` is blocking (ADR-0039, the record this
      change writes) and diffs the branch against the declared scope
- [ ] 8.2 Land via `tools/pr-flow.py --plan --branch BR` first, then the driven route. Never
      hand-compose the sequence
- [ ] 8.3 Archive as its own follow-up `chore/archive-enforce-adr-reference-integrity` PR — the #58
      shape, per the operator decision of 2026-08-11
