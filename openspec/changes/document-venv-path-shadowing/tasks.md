<!-- SPDX-License-Identifier: Apache-2.0 -->

# Tasks — document-venv-path-shadowing

> **Marker discipline.** `[~]` = built · `[x]` = tested. Never the same marker.

## Who performs what

| Actor | Steps |
|---|---|
| **agent** | 1–3, 5 |
| **operator** | 4 (Gate-4 sign-off), 6.4–6.6 (ship), 7 (merge the delta into the live `config.env`) |

## 1. The measurement this change rests on

- [x] 1.1 Reproduce both invocations in one shell and record the disagreement. Recorded in
      `proposal.md`: `python3 -m pytest` → `No module named pytest`; bare `pytest` → `9.1.1`,
      measured 2026-08-20. **This is the evidence, not an illustration** — the Requirement cites it.
- [x] 1.2 State the limit: this was measured on one machine with one venv layout. The mechanism
      (prepend shadows the interpreter) is general; the specific tool and version are not.

## 2. The environment file

- [x] 2.1 `vault-template/99-Operations/config.env.example` — comment block at the point of the
      `PATH` prepend, naming both invocation forms and what each resolves to, citing the measurement.
- [x] 2.2 Placed **at the prepend**, not in the file header — the reader arrives here from an error
      message, and a note at the top is read before the behaviour it explains has happened.

## 3. Spec

- [x] 3.1 `maintenance` — ADDED: *An Environment File States The Resolution It Changes*.
- [x] 3.2 `maintenance` — ADDED: *A Shadowed Import Failure Is Not A Missing Tool*, with the
      three scenarios including the genuinely-absent case, so the rule cannot be read as
      "never report a tool missing".
- [x] 3.3 Constitutional-impact declaration in `proposal.md` — `overrides: none`.

## 4. Gate 4 — human sign-off *(operator; not agent-delegatable)*

- [x] 4.1 **Approved** — Keith Nielsen, 2026-08-25
      **Provenance of this line.** The operator gave the approval in session, verbatim: *"Stated:
      Aproved. record it."* The decision is the operator's; the agent typed the line at their
      explicit direction. Recorded because a sign-off whose authorship is ambiguous is worth less
      than one that says who approved and who wrote it down.

## 5. Validation

- [x] 5.1 `openspec validate document-venv-path-shadowing --strict` — transcript.
- [x] 5.2 `openspec validate --all --strict` — transcript.
- [x] 5.3 `pytest -q` green — no code changes, so this is a regression guard, not coverage.
- [x] 5.4 `tools/preflight.py .` — CLEAR.
- [x] 5.5 `CHANGELOG.md` `[Unreleased]` entry.

## 6. Landing

- [ ] 6.1 Branch `docs/config-env-venv-path-note`, already cut from `main`.
- [ ] 6.2 `tools/pr-flow.py --plan --branch docs/config-env-venv-path-note`, then drive it.
      ⚠ The driver emits `gh pr create`, a `gh pr *` form on the deployed vault's deny list. Hand the
      operator the REST equivalent alongside it and let them choose; do not relay the denied form
      silently.
- [ ] 6.3 Archive **on the feature branch** before merge (ADR-0040).
- [ ] 6.4 **operator** — `tools/ship-release.py vX.Y.Z`. ⚠ It **refuses** unless `## [X.Y.Z]` already
      exists on `main`, so the CHANGELOG stamp is its own `release/*` PR **first**. The shipper does
      not write the heading.
- [ ] 6.5 **operator** — confirm the Release object exists (ADR-0027) and parity holds.
- [ ] 6.6 **operator** — confirm the CHANGELOG carries the shipped version.

## 7. Deploy-down — merge the delta, never copy *(operator)*

- [ ] 7.1 `config.env.example` is **SEED**, not lockstep (`tools/template-sync-manifest.json`), so
      `template-mirror.py` will not carry it and `template-parity.py` will not report it. The live
      `99-Operations/config.env` is instance-owned.
- [ ] 7.2 **Merge the delta by hand into the live `config.env`.** Never copy the template over it —
      the live file holds machine-specific values (`VAULT_ROOT`, `FRAMEWORK_ROOT`, `PILLARS`) that a
      copy would destroy.

## 8. Deliberately NOT in this change

- [ ] 8.1 Changing the `PATH` prepend. It is correct; the defect was silence.
- [ ] 8.2 A lint asserting the comment exists — theatre, and it would refuse a legitimately
      rewritten SEED file.

## Evidence (transcripts, 2026-08-25)

```
$ openspec validate document-venv-path-shadowing --strict
Change 'document-venv-path-shadowing' is valid

$ openspec validate --all --strict
Totals: 7 passed, 0 failed (7 items)

$ python3 -m pytest -q
359 passed in 80.58s

$ python3 tools/preflight.py .
CLEAR - 12/16 CI jobs reproduced, 0 unrunnable here, 4 not reproduced by design
```

Task 1.2's stated limit: the measurement was taken on one machine with one venv layout. The mechanism
- a PATH prepend shadowing the interpreter - is general; the specific tool and version are not, and
the Requirement is written against the mechanism rather than against pytest.
