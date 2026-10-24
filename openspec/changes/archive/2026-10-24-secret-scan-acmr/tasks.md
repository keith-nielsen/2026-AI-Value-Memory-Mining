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

## 4. Gate 4 — operator authorization (Tier-0 touch)

Archiving syncs this delta into `openspec/specs/access-control/spec.md`, which protects INV-7
(Tier 0). Surfaced to the operator on 2026-10-24, before the proposal was written:

- **Principle:** INV-7, no secrets in the vault, enforced at the commit boundary.
- **Rationale:** a file renamed and edited in one commit is staged as `R` and was never scanned.
- **What breaks:** renaming a file that already holds a HIGH-tier credential format now blocks the
  commit, even with no edit. Measured exposure: 0 HIGH matches across every tracked file in the live
  vault and in this repository.

- [x] 4.1 Tier-0 touch surfaced with its consequence; **Approved** — Keith Nielsen, 2026-10-24
      (transcribed by the agent from the operator's explicit reply; agents may not sign). The
      operator's words: *"Approved."*
