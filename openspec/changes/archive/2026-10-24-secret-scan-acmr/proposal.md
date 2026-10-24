# Proposal

## Why

The commit gate's INV-7 secret scan reads `git diff --cached --diff-filter=ACM`, which leaves out
`R`. A file moved and edited in one commit stays above git's rename-similarity threshold, is staged
as a rename, and is never scanned. A test showed it: a GitHub token went through the gate as a 96%
rename. The Phase 0 freeze brief (`docs/phase-0-freeze-brief.md` §2, finding F2) found the gap, and
the operator ruled on 2026-10-24 to fix it before the v0.1.57 freeze reference.

## What Changes

- The scanner's staged mode widens its filter from `ACM` to `ACMR`
  (`vault-template/99-Operations/scripts/secret-scan-script.md`).
- The commit-gate rationale (`commit-gate-script.md`) and ADR-0036 (by a dated amendment) say `ACMR`.
- A new behaviour test stages a rename plus edit carrying a HIGH-tier token and asserts the gate
  blocks it. It was run and seen to fail before the fix.
- **BREAKING (intended):** a commit that renames a file already holding a HIGH-tier credential
  format is now blocked, even with no edit. Measured on 2026-10-24: every tracked file in the live
  vault and in this repository returns 0 HIGH matches, so no existing file is affected.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `access-control`: "Secrets Prohibition Is Enforced at the Boundary" scans renamed files too, and
  gains the scenario "A renamed file is scanned".

## Nature of this change — ordinary, not a constitution-override

```constitutional-impact
touches: openspec/specs/access-control/spec.md
protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]
overrides: none
basis: access-control MODIFIED "Secrets Prohibition Is Enforced at the Boundary" — widens INV-7's
  enforcement; nothing is narrowed. The filter gains R; every existing sentence and scenario is
  kept, and one scenario is added. The constitution's section 5 hard stop was surfaced (principle,
  rationale, what breaks) and the operator confirmed it on 2026-10-24.
```

## Impact

- Code: one filter string and its docstring in the literate scanner note. The live vault picks it up
  at the next `template-mirror` and `render`.
- Tests: `tests/test_secret_scan.py` gains one test.
- Operators: renaming a file that holds a vendor-token format now needs the credential removed first,
  or an explicit `--no-verify`.
