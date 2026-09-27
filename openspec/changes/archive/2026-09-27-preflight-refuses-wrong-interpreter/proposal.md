<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: preflight-refuses-wrong-interpreter

## Why

`tools/preflight.py` runs every job under `sys.executable`, the interpreter that launched it, and never
checks that interpreter first. Launched by one that lacks the test suite's own requirements, it
reports the environment as a defect in the change. Measured on unchanged `main` (`203a598`),
2026-09-27, with the live vault's venv, the interpreter sourcing `config.env` puts first on `PATH`:

```text
  FAIL  fleet-pytest
          /home/administrator/Documents/Vault/.venv/bin/python3: No module named pytest
...
  2 issue(s) that would otherwise surface only AFTER a push:
    - openspec-validate: failed
    - fleet-pytest: failed
```

The `fleet-pytest` line is false: CI installs `tests/requirements.txt` into Python 3.12 and passes. (The
`openspec-validate` line is this change's own directory, before its delta existed.)

- **It breaks an existing requirement.** `maintenance` — *The Route Is Pre-Flighted Before A Mutation*
  — says a check that could not run SHALL be reported distinctly and SHALL NOT be counted as a
  finding. `verdict_for` recognises some environment limitations, but not a missing module, so it
  falls through to FAIL.
- **It recurs.** The same failure was measured on 2026-08-20, when an agent reported
  `No module named pytest` as a constitutional Gate-3 blocker, and was recorded as a prose warning in
  the operator's `config.env`. On 2026-09-26 it recurred twice in one session. Prose did not bind.
- **Per-job SKIP is not enough.** The interpreter is shared by every job. Skipping only `fleet-pytest`
  would still print CLEAR with the suite unrun, and a SKIP reads like a PASS (`CONTRIBUTING.md`
  §Landing step 0).

## What Changes

- **`tools/preflight.py`:** before any job, an INTERPRETER section reads the distribution names from
  `tests/requirements.txt` and probes the jobs' interpreter for them. If any is missing it prints
  REFUSED with the interpreter's path and the missing names, runs nothing, gives no verdict and exits
  **3** (0 CLEAR and 1 findings are unchanged). With no requirements file, it says so and proceeds.
- **The probe runs as a child process,** launched the way the jobs are, never asked of preflight's own
  process. Measured during this change: under `python3 -S` the parent had no site-packages while its
  child jobs found pytest and ran all 557 tests, so an in-process check would refuse a run that works.
- **`tests/test_preflight.py`:** 6 tests (below).
- **Spec:** one ADDED requirement in `maintenance`, *The Pre-Flight Refuses An Interpreter That Cannot
  Run The Suite*, with three scenarios.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only (a new pre-flight precondition; no existing requirement modified; the probe is local and offline, INV-6)
```

### The three design questions

1. **State lifetime.** None: the check holds no state beyond one invocation.
2. **Reachability.** It is the first statement of `main()` after argument parsing, so every real
   invocation reaches it. Proven by running the real tool as a subprocess under a bare venv, and by
   refusing the live vault's venv and `/usr/bin/python3` (both exit 3, naming what is missing).
3. **Exhaustiveness.** No file, or no names: proceed. Probe cannot run: refuse, naming the probe's
   error. All present: proceed. Some missing: refuse, naming them. These four cases partition.

### Stated limits

- **Presence, not version.** A version range such as `pytest>=8,<10` is not checked, since the standard
  library has no specifier parser. The measured failure is absence.
- **Only lines that begin with a distribution name** are read. `-r` and option lines are skipped.
- **It cannot catch a requirements file that is wrong.** It checks the interpreter against the file.

### Deliberately NOT in this change

- A repo-local virtualenv built from `tests/requirements.txt`. Building one needs package-index reach
  from the sandbox, which is unmeasured, and the refusal already catches a future break in the current
  environment.
- `verdict_for`'s patterns, which are unchanged. The interpreter case never reaches them now.
- The prose warning in the operator's `config.env`, which is the operator's file (INV-5).

## Impact

- **Behaviour:** a new refusal path and a new exit status. With the right interpreter, output gains one
  INTERPRETER line and nothing else changes. Nothing reads preflight's exit status programmatically
  (enumerated: `tools/` and `.github/` reference it only in docstrings).
- **Risk: over-refusal.** A check that is too strict blocks every local preflight. Guarded by two tests:
  the interpreter that has the requirements is not refused, and a parent that sees fewer packages than
  its jobs does not refuse.
- No vault-template file is touched, so there is no deploy-down.

## Verification

- On unchanged `main`, the defect reproduced with the live vault's venv (above).
- The new tests fail without the change: 5 of the first 5 fail on unchanged `main`. The sixth,
  *the check sees what the jobs see*, was proven by a mutation that makes the probe see only the
  parent's packages; it fails, and passes when restored.
- Full suite, `openspec validate --all --strict`, and preflight are recorded in `tasks.md` §4.
