# Tasks — preflight-refuses-wrong-interpreter

> Origin: hardening queue item 46, filed 2026-09-26 after preflight reported a wrong interpreter as a
> finding twice in one session. Operator decision (2026-09-26): draft it after
> `conduct-verification-agent-measured` (#136) lands. It landed as `203a598`.

## 0. END STATE

Preflight refuses, before running anything, an interpreter that lacks `tests/requirements.txt`, naming
the interpreter and what is missing, with exit 3 and no verdict. The right interpreter behaves exactly
as before plus one line. A spec requirement and six tests hold it.

## 1. Implementation

- [x] 1.1 Branch `change/preflight-refuses-wrong-interpreter` from `main` (`203a598`).
- [x] 1.2 Defect reproduced on unchanged `tools/preflight.py` with the live vault's venv: `fleet-pytest`
      FAIL, `No module named pytest`, counted as an issue "that would otherwise surface only AFTER a
      push", rc=1.
- [x] 1.3 `required_distributions()`, `interpreter_refusal()` and the child-process probe; an
      INTERPRETER section first in `main()`; exit 3; exit codes in the docstring.
- [x] 1.4 Design corrected mid-change: the first draft asked preflight's own process. Measured:
      under `-S` the jobs, as children, still found pytest. The probe now runs as a child.
- [x] 1.5 Callers of preflight's exit status enumerated:
      `grep -rn preflight --include=*.py --include=*.sh --include=*.yml tools .github`. There are 4
      hits outside `tools/preflight.py`, all docstrings or comments in `driver_handoff.py` and
      `pr-flow.py`. None reads the status.

## 2. Tests (observed to fail first)

- [x] 2.1 Five tests on unchanged `tools/preflight.py`: **5 failed**, 16 passed.
- [x] 2.2 Real geometry: a bare `venv.create(with_pip=False)` interpreter drives the real tool as a
      subprocess and must be REFUSED (exit 3, interpreter named, nothing run, no VERDICT).
- [x] 2.3 *The check sees what the jobs see*: under `-S` it must NOT refuse. A mutation that makes the
      probe see only the parent's packages makes it **fail**; it passes when restored.
- [x] 2.4 Over-refusal guard: an interpreter that has the requirements proceeds to a VERDICT.
- [x] 2.5 With the change: `tests/test_preflight.py` **22 passed**.
- [x] 2.6 Real invocations: the live vault's venv exits 3 ("lacks pytest"); `/usr/bin/python3` exits 3
      ("lacks python-frontmatter, pytest").

## 3. Spec

- [x] 3.1 `maintenance`, ADDED: *The Pre-Flight Refuses An Interpreter That Cannot Run The Suite*
      (3 scenarios). `constitutional-impact`: `overrides: none`, ADD-only.

## 4. Regression

- [x] 4.1 Full suite green — 557 on `main` → 563 passed.
- [x] 4.2 `openspec validate --all --strict` — 7 passed, 0 failed.
- [~] 4.3 `tools/preflight.py .` → CLEAR (INTERPRETER PASS, `ai-env`, 2 of 2; 13/16 CI jobs; CAN
      ARCHIVE). STEP 7b reads "no protected element touched" until the archive applies the delta —
      re-run at 6.3. STEP 7 `SKIP` until the body exists.

## 5. Gate 4 — operator authorization

No existing requirement is modified. `maintenance` carries `protects:`, so the change declares its
impact (ADD-only, `overrides: none`). Surfaced for sign-off:

- **A new refusal path and exit status 3** in the tool every landing runs first.
- **The over-refusal risk** and its two guarding tests.
- **The stated limits:** presence not version; the file is trusted.

- [x] 5.1 Surfaced; **Approved** — Keith Nielsen, 2026-09-27

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [x] 6.1 Archive on this branch (with the spec delta) — pinned `node_modules/.bin/openspec` 1.12.0.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff (generated after the archive commit).
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.

## 7. Close the record

- [ ] 7.1 Development store: close hardening queue item 46.
