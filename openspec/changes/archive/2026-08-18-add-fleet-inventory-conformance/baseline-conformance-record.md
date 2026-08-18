<!-- SPDX-License-Identifier: Apache-2.0 -->
# Baseline conformance record — add-fleet-inventory-conformance (task A0)

**Captured 2026-08-18. Every value produced by an executed command, pasted below with that command.**

This is the comparison set for GATE A2 and GATE A5. Constitution §3 Gate 4 requires the re-check to
**re-run these commands and diff the output**, not to re-read the composed sections. **Quoting a
number from memory rather than from this file is a protocol breach.**

---

## A0.1 — The note set (the denominator every conformance check compares against)

```
$ ls -1 vault-template/99-Operations/scripts/*.md | xargs -n1 basename | sort
```

```
bank-execute-script.md              site-slag-script.md
commit-gate-script.md               spoil-dump-script.md
knowledge-lint-script.md            tailings-reprospect-script.md
naming-rules-script.md              treasury-orphan-script.md
ore-detect-script.md                vault-lib-script.md
outbound-publish-guard-script.md
push-guard-script.md
render-reconcile-script.md
secret-scan-script.md
```

**COUNT = 14.** This is ground truth. Every enumeration in the corpus must equal it.

## A0.2 — Test suite baseline

```
$ ~/ai-env/bin/python3 -m pytest -q
328 passed in 95.46s (0:01:35)
EXIT=0
```

⚠ **The condition is precise, and was measured 2026-08-18.** A bare `python3` resolves to
`~/ai-env/bin/python3`, which *has* pytest. **Sourcing `config.env` puts the vault venv first on
`PATH`, and that venv has no pytest** — so any command run after sourcing it fails to import pytest.

```
$ python3 -c 'import pytest'                          -> OK   (~/ai-env/bin/python3)
$ source .../config.env && python3 -c 'import pytest'  -> ModuleNotFoundError
```

Consequence for `tools/preflight.py`: run from a **config.env-sourced** shell it reports
`fleet-pytest: failed` while claiming `0 unrunnable` — a missing tool miscategorised as a test
failure. Run from a clean shell it correctly reports `fleet-pytest PASS`. **Do not source
`config.env` before running preflight**, and verify pytest independently either way.

⚠ An earlier draft of this file stated the warning without its precondition, implying preflight was
unconditionally unreliable on pytest. It is not — the shell it inherits decides.

## A0.3 — The three drifting enumerations, verbatim

### A0.3a — `openspec/specs/maintenance/spec.md`

```
$ grep -cE '^\| `[a-z0-9-]+-script\.md`' openspec/specs/maintenance/spec.md
13
$ grep -c 'secret-scan' openspec/specs/maintenance/spec.md
0
```

**13 rows for a 14-note fleet, and `secret-scan` appears ZERO times in the entire specification.**
Not merely missing from the table — absent from the document that governs it. INV-7 enforcement
(ADR-0036, accepted 2026-07-28) has been ungoverned for 21 days.

### A0.3b — `README.md`

```
$ grep -n 'Operational Scripts' README.md
219:## Operational Scripts (13)
$ sed -n '224,236p' README.md | grep -cE '^\| `'
10
```

**Heading says 13. Table has 10 rows. Reality is 14.** Wrong twice, in two directions, within one
section. Missing: `vault_secrets.py`, `vault_lib.py`, `pre-push`, `outbound-publish-guard.py`.

### A0.3c — The cadence claims

```
$ grep -n '0 6 \* \* \*' README.md
231:| `vault-refine-detect.py` | `[script]` | `0 6 * * *` | Queue ore that has cleared the grade gate |
$ grep -n 'schedule:' docs/USING-THIS-TEMPLATE.md
264:| Cron schedules | Edit the `schedule:` field in the relevant `99-Operations/scripts/*.md` note, re-run `render` |
$ grep -n 'manual / weekly' openspec/specs/maintenance/spec.md
106:| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` | manual / weekly | Report Treasury notes not linked from any Catalog index |
```

All three contradict `maintenance/spec.md:118`, which states correctly that no script declares a
`cron` runtime or a `schedule:`, and that nothing reads such a field. Verified independently: 14
notes, **0** carry `schedule:`, **0** carry `runtime: cron`. `treasury-orphan-script.md` declares
`runtime: manual`.

These are **Tier-2 conventions** ("cron schedules", constitution §2) — ordinary change, no ceremony.

## A0.4 — Fleet coverage per member

```
$ for s in <11 members>; do
    tests=$(grep -rl "$s" tests/ | wc -l); validate=$(grep -c "$s" .github/scripts/validate-scripts.sh)
  done
```

| Member | tests/ | validate-scripts.sh | State |
|---|---|---|---|
| `vault-render` | 2 | 3 | covered |
| `vault_naming` | 2 | 1 | covered |
| `vault-lint` | 1 | 1 | covered |
| **`vault-orphans`** | **0** | **0** | ⚠ **UNCOVERED** |
| `vault-refine-detect` | 1 | 1 | covered |
| `vault-refine-execute` | 1 | 2 | covered |
| **`vault-reprospect`** | **0** | **0** | ⚠ **UNCOVERED** |
| `vault_secrets` | 1 | 0 | covered |
| `vault-dump` | 1 | 0 | covered |
| `vault-slag` | 1 | 0 | covered |
| `vault_lib` | 1 | 0 | covered |

**Baseline: 9 of 11 covered.** Target after A1.5/A1.6: **11 of 11**.

⚠ Measuring one harness alone is misleading — an earlier pass over `validate-scripts.sh` only
suggested six uncovered members. Four of those are covered by pytest. **Coverage is the union**, and
`vault-orphans` / `vault-reprospect` are uncovered in *both*.

---

## Cross-check against Change B's baseline

`relocate-fleet-in-tree-bin/baseline-preflight-record.md` (2026-08-17) recorded the same suite at
**328 passed** and the same 14-note set. Both remain true on 2026-08-18. Change A must leave every
value in that file unchanged except the pytest count, which rises by the number of tests A adds —
stated as a number at GATE A2, never as "more tests pass".
