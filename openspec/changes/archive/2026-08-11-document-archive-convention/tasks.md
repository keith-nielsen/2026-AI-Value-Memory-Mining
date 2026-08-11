<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [x] 1.1 `maintenance` ADDED: *A Change Is Archived On Its Own Branch* (3 scenarios)
- [x] 1.2 Requirement carries the **exception** (concurrent change on the same capability spec, applied
      in merge order, naming the change deferred to) — not just the default
- [x] 1.3 Requirement carries the **derivation constraint**: a re-derivation must be a pasted transcript
      over merge history, never an inference from commit subjects. This is the trap that fired twice
- [x] 1.4 Confirm ordinary, not override — ADD-only; `constitution.md` §2 Tier 2 ("no ceremony
      required"); §5 hard stop concerns *modifying*. **Not** derived from a green `constitution-lint`

## 2. ADR-0040

- [x] 2.1 `openspec/adr/0040-archive-on-the-feature-branch.md` — Context / Options / Decision /
      Consequences / Sacrifice / Follow-on, matching ADR-0037's structure
- [x] 2.2 Record all **three** flawed methods by name, so the next re-derivation recognises them
- [x] 2.3 State the method of record with its runnable commands and the `--no-renames` requirement
- [x] 2.4 Denominator stated honestly: **14**, with the 32 pre-workflow changes excluded and *said* to
      be excluded — not silently absorbed
- [x] 2.5 Sacrifice section states plainly that **enforcement is not shipped**

## 3. `CONTRIBUTING.md`

- [x] 3.1 State the rule at the flow block, where the decision is made
- [x] 3.2 State the exception with its reason (last-writer-wins across two deltas to one spec file)
- [x] 3.3 Note the consequence of skipping it: a second archive PR is owed

## 4. Lockstep — `README.md`

- [x] 4.1 Three ADR-count sites: 39 → 40; range → `ADR-0001–0040`
- [x] 4.2 Verified by the existing *Check README ADR count matches actual* step

## 5. Tests / verification

- [x] 5.1 `openspec validate --all --strict` — **7 passed, 0 failed, exit 0**
- [x] 5.2 `spec-lint` ADR steps — `adr-contiguity OK: 40 ADRs, 0001-0040` · `adr-reference-integrity OK (40 records)` · `adr-count-lint OK: 40 ADRs, latest 0040`, all exit 0
- [x] 5.3 **Reference-integrity check against the archived form of this change** — simulated the
      archive before performing it: **exit 0**, `all cited ADRs resolve (40 records)`. Its ADR-0040
      citations resolve because this change writes ADR-0040
- [x] 5.4 Simulated archiving `enforce-adr-reference-integrity` with ADR-0040 present → **exit 0**.
      Its 9 previously-unresolved `ADR-0040` citations now resolve, so this change unblocks PR #62's
      owed archive. Both simulations restored; `git status` confirmed no residue
- [ ] 5.5 `md-lint` / `link-check` — **NOT VERIFIABLE locally: `markdownlint-cli` is not installed.**
      Deferred to CI; not ticked on inspection

## 6. Archive — on this branch, per the rule this change documents

- [x] 6.1 Move `openspec/changes/document-archive-convention/` →
      `openspec/changes/archive/2026-08-11-document-archive-convention/`
- [x] 6.2 Apply the delta into `openspec/specs/maintenance/spec.md`
- [x] 6.3 CHANGELOG entry
- [x] 6.4 Confirm the exception does **not** apply: `estate-scoped-capability-probe` carries a
      `maintenance` delta but is unimplemented and parked on another branch, so there is no concurrent
      archive to order against

## 7. Gate 4 — human sign-off (not agent-delegatable)

- [x] 7.1 **Approved** — Keith Nielsen, 2026-08-11, for ADR-0040 as written and this change archived on
      its feature branch. Gate 3 complete; 5.5 (`md-lint`/`link-check`) deferred to CI for absent local
      tooling and left unticked.

⚠ **Provenance note.** `pr-flow.py` will report this branch's approval as *"recorded in
`openspec/changes/enforce-adr-reference-integrity/tasks.md`"* — **the wrong change**.
`approval_state`'s **live** path (`tools/pr-flow.py:539-548`) globs every unarchived change directory
unkeyed to the branch and returns on the first signed one, never reaching the branch-keyed archive
lookup (`:555-565`) where this change's sign-off actually lives. **The authorization recorded on 7.1 is
the real one.** The driver's string becomes correct once PR #62's archive removes that live directory.

## 8. Ship

- [ ] 8.1 PR body declares the full scope (`scope-review` is blocking)
- [ ] 8.2 Land via `tools/pr-flow.py --plan --branch BR` first, then the driven route
- [ ] 8.3 **Then** open the owed archive PR for `enforce-adr-reference-integrity` (PR #62), which this
      change unblocks

## 9. Owed after this change

- [ ] 9.1 Mechanical enforcement of the archive step — ADR-0040's follow-on. **Blocked on an open
      design question**: the naive guard would have failed PR #58's legitimate deferral, and a body
      marker is an unverifiable claim. Do not ship a guard until the exception is decidable from
      repository state
