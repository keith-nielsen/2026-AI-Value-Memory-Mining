<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks: add-template-mirror-driver

## 1. Design (pre-implementation)
- [x] 1.1 Fable-spec'd design skeleton drafted (`mirror-driver-proposal-skeleton.md`, program item E1)
- [x] 1.2 Confirm the gap: CONTRIBUTING step 5 is prose "(operator action)" with no vehicle — the exact
      shape F26 fell through (hand-composed `cp` degraded into a destructive overwrite)
- [x] 1.3 Confirm the pattern already exists (`ship-release.py`, `template-parity.py`) — applying it,
      not inventing it

## 2. Implementation
- [x] 2.1 `tools/template_sync.py` — factor the tree-walk/compare/tally out of `template-parity.py`
      into one shared module (byte-identical output)
- [x] 2.2 `tools/template-mirror.py` — repo → live only, never deletes; `MISSING-IN-LIVE` → copy,
      `DIFFERS` → overwrite, `MISSING-IN-TEMPLATE` → report only; re-derives parity + denominator'd
      tally; never `git add`/commits; idempotent; exit 0/2/3
- [x] 2.3 `tools/template-parity.py` — refactor to import `template_sync`; output byte-identical
- [x] 2.4 `tests/test_template_mirror.py` — 8 cases against synthetic fixtures (see §3.1), never the
      real `$VAULT_ROOT`
- [x] 2.5 `tests/test_template_parity.py` — adjust for the shared module (+2 lines), 6 cases stay green
- [x] 2.6 Spec delta: `maintenance` +1 ADDED Requirement ("Template→Live Mirror"), 6 scenarios
- [x] 2.7 CONTRIBUTING.md step 5 → single invocation `tools/template-mirror.py <VAULT_ROOT>`
- [x] 2.8 AGENTS.md post-merge-mirror bullet rewritten (run the driver, never a hand-composed `cp`;
      names F26)
- [x] 2.9 README repo-structure `tools/` tree: add `template-mirror.py`
- [ ] 2.10 CHANGELOG `[Unreleased]` entry

## 3. Verification
- [x] 3.1 `tests/test_template_mirror.py` — 8 cases green: T1 no-op idempotency (tree byte-unchanged),
      T2 forward-mirror missing file, T3 forward-mirror differing content, T4 untracked-live-file
      safety (reported not deleted, exit 2), T5 excluded file never touched, T6 CONTRIBUTING step-5 is
      a single short line (no `&&`, no wrap — mechanically closes the F26 loop), blocked-no-vault
- [x] 3.2 Full suite green — **`63 passed in 8.44s`** (real run, recorded)
- [ ] 3.3 `openspec validate add-template-mirror-driver --strict` green
- [ ] 3.4 `openspec validate --all` green (CI-equivalent; 7/7 on branch)
- [ ] 3.5 PR CI green (its own standalone-vault scope-review PASS on the declared block)

## 4. Ceremony
- [ ] 4.1 Gate-4 human sign-off — **pending operator `Approved`** (record in proposal.md when given)
- [ ] 4.2 Open PR (branch already pushed: `origin/build/add-template-mirror-driver`, `588b0f8` +
      the change-artifact commit)
- [ ] 4.3 Merge; archive in merge order relative to `add-telemetry-segment` (both touch `maintenance`)
- [ ] 4.4 Ship via `tools/ship-release.py vX.Y.Z` — never hand-compose; tag + GitHub Release + parity
      verify (INV-14 outbound ASK)
- [ ] 4.5 **T8 dogfood:** run `tools/template-mirror.py <VAULT_ROOT>` for real as this release's own
      mirror, then confirm `tools/template-parity.py <VAULT_ROOT>` reports `0 drift`
