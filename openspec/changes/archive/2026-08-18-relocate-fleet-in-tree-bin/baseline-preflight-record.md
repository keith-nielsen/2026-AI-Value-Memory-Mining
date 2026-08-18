<!-- SPDX-License-Identifier: Apache-2.0 -->
# Baseline pre-flight record — relocate-fleet-in-tree-bin

**Captured 2026-08-17, pre-migration. Every value here was produced by an executed command.**

This file is the comparison set for GATE 6b and GATE 7. **Quoting a number from memory rather than
from this file is a protocol breach** — the whole point is that a post-migration reading is compared
against a recorded measurement, not against an expectation.

## Anchors

| Anchor | Value |
|---|---|
| Vault `HEAD` | `5960803f1e8891c36929a43fdc82c9bca58defde` — *ops(deploy-down): adopt the v0.1.49 emission-record guard downgrade* |
| Repo `HEAD` | `dec7a01e95a2c204d543fb22c62bfda773562fa0` — *Merge pull request #96 from keith-nielsen/release/v0.1.49* |
| Vault remotes | none (INV-14 holding) |
| openspec | 1.6.0 (matches the `package.json` pin) |

## Note → `deploy_target` map (14 notes; 11 host + 3 in-tree)

| Note | Deploy target |
|---|---|
| `bank-execute-script.md` | `~/bin/vault-refine-execute.py` |
| `knowledge-lint-script.md` | `~/bin/vault-lint.py` |
| `naming-rules-script.md` | `~/bin/vault_naming.py` |
| `ore-detect-script.md` | `~/bin/vault-refine-detect.py` |
| `render-reconcile-script.md` | `~/bin/vault-render.py` |
| `secret-scan-script.md` | `~/bin/vault_secrets.py` |
| `site-slag-script.md` | `~/bin/vault-slag.sh` |
| `spoil-dump-script.md` | `~/bin/vault-dump.sh` |
| `tailings-reprospect-script.md` | `~/bin/vault-reprospect.py` |
| `treasury-orphan-script.md` | `~/bin/vault-orphans.py` |
| `vault-lib-script.md` | `~/bin/vault_lib.py` |
| `commit-gate-script.md` | `99-Operations/hooks/pre-commit` **(in-tree — does not move)** |
| `push-guard-script.md` | `99-Operations/hooks/pre-push` **(in-tree — does not move)** |
| `outbound-publish-guard-script.md` | `.claude/hooks/outbound-publish-guard.py` **(in-tree — does not move)** |

## Deployed artifact checksums (SHA-256, first 12)

| Artifact | Digest |
|---|---|
| `vault-dump.sh` | `82d66e880d0c` |
| `vault_lib.py` | `c04038750d5a` |
| `vault-lint.py` | `f2be2f26c5b0` |
| `vault_naming.py` | `3d191a63cb27` |
| `vault-orphans.py` | `f2cc61343516` |
| `vault-refine-detect.py` | `ae650aaa06d7` |
| `vault-refine-execute.py` | `c49c42965126` |
| `vault-render.py` | `495373c3524e` |
| `vault-reprospect.py` | `31f98a8815ad` |
| `vault_secrets.py` | `fadf0d44e4ae` |
| `vault-slag.sh` | `b853b7e68330` |

Post-migration these digests must be **identical** at the new location. The migration relocates
artifacts; it does not rewrite them. Any digest change is a content change and must be explained.
(Exception: the 5 scripts amended in Phase 3 change **before** Phase 4, and their new digests are
recorded at GATE 3.)

## Instrument baselines

| Instrument | Exit | Output |
|---|---|---|
| `vault-render.py reconcile` | `0` | 14 × `ok:` |
| **`vault-lint.py`** | **`1`** ⚠ | **1 finding:** `LINT .../30-Sites/.claude: effort folder not a kebab slug: ['starts with a dot']` |
| `vault-orphans.py` | `0` | `0 orphan(s)` |
| `vault-refine-detect.py` | `0` | `queued 0 for refining` |
| `vault-reprospect.py` | `0` | *(no output)* |
| `vault_secrets.py --selftest` | `0` | `selftest: patterns fire, tiers are disjoint` |
| `vault_secrets.py .` | `0` | `HIGH: 0 match(es)` · `ADVISORY: 1 match(es)` → `[assignment-secretish] 99-Operations/scripts/secret-scan-script.md:202` |
| `template-parity.py` | `0` | `18 lockstep files checked across 2 prefixes (1 excluded) — 0 drift` |
| `pytest -q` | `0` | **328 passed** (~95 s) |
| `validate-scripts.sh` | `0` | `VALIDATION OK` |
| `pr-flow.py --capabilities` | `0` | `40-Treasury` / `96-Runbooks` / `99-Operations` = **PROTECTED** |

### ⚠ `vault-lint.py` exits 1 on a clean tree — read this before the post-migration run

`30-Sites/.claude` is an **untracked** directory (not in `git ls-files`); the linter walks the
filesystem, not the index. The finding is **pre-existing and unrelated to this migration**.

| Post-migration reading | Verdict |
|---|---|
| exit `1`, that same single finding | **PASS** |
| exit `0` | **INVESTIGATE** — something changed this migration did not intend |
| exit `1` with any second finding | **FAIL** |

The same applies to `vault_secrets.py`: `ADVISORY: 1` must remain exactly one, on that same line.

## Instrument-validity controls (negative controls)

These must **fail** to prove the instrument can refuse. An instrument never observed refusing is an
assumption, not a check.

| Control | Expected |
|---|---|
| `vault_naming.py --check-strict ab` | exit `1` — `fewer than 3 hyphen-tokens (INV-11 floor)` |
| `vault_naming.py --check has/slash` | exit `1` — `forbidden char(s): /` |
| `vault_naming.py --check has:colon` | exit `1` — `forbidden char(s): :` |
| `vault_naming.py --check CON` | exit `1` — `reserved device name: CON` |
| `vault_naming.py --check 'trailing.'` | exit `1` — `leading/trailing space or trailing dot` |
| `vault_naming.py --check 'ok-three-token'` | exit `0` (positive control) |

## Invocation notes that cost time to learn

- **`vault_naming.py --check` requires a NAME.** `--check` bare falls through to the regeneration
  path and returns `BLOCKED (exit 4)` — an operator-only write, not a defect and not a check result.
  Its dispatch is `len(sys.argv) >= 3 and sys.argv[1] == "--check"`.
- **`--check` is cross-platform safety only.** `'bad name!'` passes — an interior space and `!` are
  not in the forbidden set. The INV-11 token floor lives in `--check-strict`.
- **`vault_secrets.py` bare exits `2` (bad usage).** It needs `--staged`, a PATH, `--history`, or
  `--selftest`.
- **`vault_naming.py` bare exits `4`** for the agent — operator-only by design (ADR-0022 write
  scope). Note `4` is outside the ADR-0023 fleet contract (`0/1/2/3`).
- **`pytest` is not on the `config.env` PATH.** The vault venv has no pytest; use
  `~/ai-env/bin/python3 -m pytest`. `tools/preflight.py` reports this condition as
  `fleet-pytest: failed` while simultaneously claiming `0 unrunnable` — **do not trust preflight's
  verdict on pytest.** Verified independently: 328 passed.
- **`inv6-offline-dynamic` is unrunnable in a confined session** — it needs `unshare -n`. Not a
  failure; CI runs it properly.

## Frozen-surface counts (must be UNCHANGED at GATE 7)

| Class | Files carrying a `~/bin` reference |
|---|---|
| `openspec/changes/archive/` | 53 |
| Vault dig record (`30-Sites/`, `71-Spoil/`, `20-Claims/`, `10-Logbook/`) | 19 |
| `CHANGELOG.md` | 1 file, 8 hits |

These are immutable record. At GATE 7 these counts must be **identical**. A reduction means the
audit trail was rewritten — a failure, not progress.

## Known-good ghost references (labelled deferred — not regressions)

`vault-seed.py`, `vault-cleanup.py` (`00-Docs/README.md`, both trees) and `vault-promote.sh`
(`docs/method.md`, `docs/obsidian.md`) name scripts that do not exist and are **explicitly labelled
deferred/roadmap**. They are correct as written. Any *new* ghost at GATE 5 is a regression.

## Pipeline state (context — not a gate)

21 of 21 Sites at `status: dig`; `ore-detect` queues 0; `_refine-proposals/` and `_refine-approved/`
both empty; 4 Treasury bullion notes + 6 Catalog indexes. `vault-refine-execute.py` has **one**
verifiable script-produced run in vault history (`8728282`, 2026-06-25). Gates 6b and D will pass on
an idle pipeline — that is honest, not reassuring.
