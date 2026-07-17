<!-- SPDX-License-Identifier: Apache-2.0 -->
> **Stacked on `impl-pillar-slug-tokens` (PR #28)**, not on `main`. Both changes edit
> `knowledge-lint-script.md`; branching from `main` would have collided. Rebase onto `main`
> once #28 merges.

## 1. Conformance measurement (the ADR-0015 precondition)

- [x] 1.1 Whole-vault sweep: **118 `.md`, 15 exempt, 103 subject, 0 failing** kebab or floor
- [x] 1.2 Per-family sweep: Treasury stems 4/0 · Sites 17/0 · Spoil 2/0 · scripts 15/0 ·
      molds 4/0 · runbooks 5/0 · Claims+Logbook+Catalog 25/0 — nothing to grandfather
- [x] 1.3 Confirm `has_min_hyphen_tokens` has **no production caller** (definition + import +
      commented `elif` only) — the rule was enforced nowhere

## 2. `vault_naming.py` — `--check-strict`

- [x] 2.1 Add `check_strict(filename)`: `is_exempt` → `validate_name` → `slug_pattern` →
      `has_min_hyphen_tokens`; takes the **basename** (exemptions match full filenames)
- [x] 2.2 Wire `--check-strict` into `__main__`; leave `--check` contract **unchanged**
- [ ] 2.3 Deferred to mirror: `render` to `~/bin/vault_naming.py` (live fleet — must not run
      from this branch; see the pillar change's task 2.4 for the same hazard)

## 3. Commit gate

- [x] 3.1 Hook calls `--check-strict "$base"` instead of `--check "$stem"`
- [x] 3.2 Keep `--diff-filter=AR` — existing names stay grandfathered
- [x] 3.3 Rationale prose updated: exemption-aware, floor enforced, grandfathering explained

## 4. Refine executor (**required** — found by failing tests, not by reasoning)

- [x] 4.1 Import `has_min_hyphen_tokens`; pre-flight rejects a sub-3 `target_note`
- [x] 4.2 Rejection happens **before any write** — a sub-3 stem passing pre-flight would be
      written and then blocked at commit, stranding the executor half-applied

## 5. Linter

- [x] 5.1 Enable the staged `elif` for `20-Claims`, `10-Logbook`, `40-Treasury/Catalog`
- [x] 5.2 Apply the floor to Treasury stems (had kebab, no floor)
- [x] 5.3 Apply the floor to effort folder slugs (had kebab, no floor)
- [x] 5.4 Do **not** apply the floor to pillar tokens (ADR-0029 — fragments, not stems)

## 6. Regression

- [x] 6.1 Gate blocks a newly added sub-3 name (`20-Claims/sample-claim.md`), message names the floor
- [x] 6.2 Gate allows a conforming add (`sample-conforming-claim.md`)
- [x] 6.3 Gate exempts `README.md` + dailies
- [x] 6.4 Gate grandfathers an existing name on **modify** (status `M`, not `A`/`R`)
- [x] 6.5 Executor rejects a sub-3 `target_note` with **no** Treasury write
- [x] 6.6 Fixtures `good-insight` → `good-durable-insight`, `existing-note` →
      `existing-durable-note` (both were 2-token — the fixtures violated the repo's own
      documented convention)
- [x] 6.7 Full suite green — **37 passed**; `validate-scripts.sh` **VALIDATION OK**

## 7. ADR + README (Gate-4 — do NOT land early)

- [ ] 7.1 Move `adr-0030-draft.md` → `openspec/adr/0030-*.md`; flip Status → Accepted.
      Land in the **same commit** as 7.2/7.3 — its presence alone fails `adr-count-lint`.
- [ ] 7.2 `README.md`: ADR count → **30** (2 occurrences)
- [ ] 7.3 `README.md`: range → `ADR-0001–0030`
- [ ] 7.4 `adr-count-lint` green

## 8. Ceremony

- [ ] 8.1 PR with the ```scope block
- [ ] 8.2 **Gate-4 human sign-off** — the operator accepts the live workflow constraint:
      **newly created** content names must carry ≥3 kebab tokens. No existing artifact is
      affected (corpus measures 0 offenders; the gate is `--diff-filter=AR` regardless) — the
      constraint applies only to names not yet made.
- [ ] 8.3 Archive → `openspec/changes/archive/2026-07-17-enforce-naming-token-floor/`
- [ ] 8.4 CHANGELOG; tag; `gh release create` + `gh release view` parity
- [ ] 8.5 Mirror to the live vault (renders `vault_naming.py`, the hook, the linter, the
      executor together — partial mirroring would leave the gate enforcing a floor the
      executor does not pre-flight)
