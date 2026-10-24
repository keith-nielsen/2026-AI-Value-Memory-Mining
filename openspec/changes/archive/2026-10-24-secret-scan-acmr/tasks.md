# Tasks

## 1. Test first

- [x] 1.1 Add `test_gate_covers_a_renamed_and_edited_file` to `tests/test_secret_scan.py` and verify it fails against the
  `ACM` filter (it did: the token was committed as a 96% rename)

## 2. Fix

- [x] 2.1 Widen `scan_staged` in `secret-scan-script.md` to `--diff-filter=ACMR` and verify
  `pytest tests/test_secret_scan.py` passes (14 passed)
- [x] 2.2 Update the `commit-gate-script.md` rationale and the test comment to `ACMR`, and verify
  `grep -rn "diff-filter=ACM\b"` finds no live site outside the archive, the CHANGELOG history and the brief
- [x] 2.3 Add a dated amendment to ADR-0036 and verify markdownlint passes on it

## 3. Verify

- [x] 3.1 Run `openspec validate secret-scan-acmr --strict` and verify it passes
- [x] 3.2 Run `python3 tools/preflight.py . --body-file <body>` and verify it reports
  CLEAR, including the constitutional gate reading `overrides: none`
