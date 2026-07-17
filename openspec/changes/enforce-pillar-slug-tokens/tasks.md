<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec

- [ ] 1.1 Apply the `maintenance` delta: ADDED requirement *Pillar Vocabulary Tokens
      Are Kebab-Case Slugs* (4 scenarios)
- [ ] 1.2 `openspec validate` passes

## 2. Linter (`knowledge-lint-script.md`)

- [ ] 2.1 Add the vocabulary-integrity check immediately after `pillars = set(vocab("PILLARS"))`,
      i.e. **before** the Treasury frontmatter loop (spec scenario 4)
- [ ] 2.2 Validate each token with `is_valid_slug()` — already imported at line 30;
      do **not** apply `has_min_hyphen_tokens`
- [ ] 2.3 Violation message names the offending token and the `PILLARS` key
- [ ] 2.4 `render` the script to `~/bin/vault-lint.py`; `reconcile` reports zero drift

## 3. Config + docs (comments only — no value changes)

- [ ] 3.1 `config.defaults.env`: rewrite the pillar comment — rule becomes
      "lowercase kebab-case slugs, whitespace-separated"; show the multi-word form
      (`mental-health` = one pillar) explicitly
- [ ] 3.2 **Verify `export PILLARS="..."` is byte-identical to its pre-change value** —
      the live vault inherits this line; a change here re-pillars it
- [ ] 3.3 `config.env.example`: same rule restated on the commented `PILLARS` line
- [ ] 3.4 `docs/USING-THIS-TEMPLATE.md`: pillar-authoring rule + the alias pattern for
      display names (`[[mental-health-domain-index|Mental Health]]`)

## 4. ADR + README

- [ ] 4.1 Move `adr-0029-draft.md` (in this change dir) → `openspec/adr/0029-pillar-slug-tokens.md`
      and flip **Status: Proposed → Accepted**. The ADR is a **Gate-4** artifact
      (constitution §3), so it stays in the change dir until sign-off. Land it in the
      **same commit** as 4.2/4.3 — the file's mere presence fails `adr-count-lint`
      until the README counts are bumped.
- [ ] 4.2 `README.md`: `28 ADRs` → `29 ADRs` (2 occurrences: lines ~29, ~245)
- [ ] 4.3 `README.md`: `ADR-0001–0028` → `ADR-0001–0029` (line ~100)
- [ ] 4.4 `adr-count-lint` passes (checks the `\d+ ADRs` count AND that `0029`
      appears in README)

## 5. Regression

- [ ] 5.1 `tests/test_fleet.py`: malformed pillar token (`Mental_Health`) → lint exits
      `EXIT_VIOLATION` and names the token
- [ ] 5.2 `tests/test_fleet.py`: current six-token vocabulary → lint passes
- [ ] 5.3 `tests/test_fleet.py`: `mental-health` → passes, derives
      `mental-health-domain-index.md`
- [ ] 5.4 Full fleet tests green
- [ ] 5.5 CI green: `constitution-lint`, `vocabulary-lint`, `adr-count-lint`,
      `runbook-lint`, `openspec validate`

## 6. Verification (live vault, read-only)

- [ ] 6.1 `vault-lint.py` on the live vault → passes with the unchanged six pillars
- [ ] 6.2 `python3 -c "from vault_lib import vocab; print(len(vocab('PILLARS')))"` → `6`
      (the value never moved)
- [ ] 6.3 `vault-render.py reconcile` → zero drift

## 7. Ceremony

- [ ] 7.1 PR opened with the mandatory ```scope block
- [ ] 7.2 Human Gate-4 sign-off recorded
- [ ] 7.3 Archive the change to `openspec/changes/archive/2026-07-17-enforce-pillar-slug-tokens/`
- [ ] 7.4 CHANGELOG entry; tag; `gh release create` + `gh release view` parity check
- [ ] 7.5 Mirror to the live vault

## 8. Operator follow-up (out of scope — track separately)

- [ ] 8.1 Recommend pinning `PILLARS` explicitly in the live gitignored
      `99-Operations/config.env`, so a framework-repo edit to the *example* default
      can never silently re-pillar the live vault
