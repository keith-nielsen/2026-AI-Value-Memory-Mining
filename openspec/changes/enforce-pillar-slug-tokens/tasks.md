<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec

- [ ] 1.1 Apply the `maintenance` delta: ADDED requirement *Pillar Vocabulary Tokens
      Are Kebab-Case Slugs* (4 scenarios)
- [ ] 1.2 `openspec validate` passes

## 2. Linter (`knowledge-lint-script.md`)

- [x] 2.1 Add the vocabulary-integrity check immediately after `pillars = set(vocab("PILLARS"))`,
      i.e. **before** the Treasury frontmatter loop (spec scenario 4)
- [x] 2.2 Validate each token with `is_valid_slug()` — already imported at line 30;
      do **not** apply `has_min_hyphen_tokens`
- [x] 2.3 Violation message names the offending token and the `PILLARS` key
- [ ] 2.4 **Deferred to 7.5 (mirror) — must NOT run from this branch.** `render` deploys to
      `~/bin/vault-lint.py`, the *live vault's* fleet. Rendering repo-branch code there would
      leave the live vault's own `knowledge-lint-script.md` disagreeing with its deployed
      binary — manufacturing the very drift `reconcile` exists to detect. The tests render
      into a sandbox `HOME` (`tests/conftest.py::_render_fleet`), which is the right isolation.

## 3. Config + docs (comments only — no value changes)

- [x] 3.1 `config.defaults.env`: rewrite the pillar comment — rule becomes
      "lowercase kebab-case slugs, whitespace-separated"; show the multi-word form
      (`mental-health` = one pillar) explicitly
- [x] 3.2 **Verify `export PILLARS="..."` is byte-identical to its pre-change value** —
      the live vault inherits this line; a change here re-pillars it
- [x] 3.3 `config.env.example`: same rule restated on the commented `PILLARS` line
- [x] 3.4 `docs/USING-THIS-TEMPLATE.md`: pillar-authoring rule + the alias pattern for
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

- [x] 5.1 `tests/test_fleet.py`: malformed pillar token → lint exits `EXIT_VIOLATION` and
      names the token. Parametrised over three grammars: `Mental_Health` (uppercase +
      underscore), `CON` (reserved device name), `-lead` (leading hyphen)
- [x] 5.2 `tests/test_fleet.py`: current six-token vocabulary → lint passes
- [x] 5.3 `tests/test_fleet.py`: `mental-health` → passes as **one** token.
      **CORRECTED from "derives `mental-health-domain-index.md`" — nothing derives it.**
      `index_links` are *supplied* by the refine proposal (`bank-execute-script` L80/L125);
      the `<pillar>-domain-index.md` convention is honoured by the agent per the
      prompt contract (ADR-0016 / `agent-integration` L53), not computed by any script.
      The test proves single-token parsing via the **subset check** instead: a note with
      `pillars: [mental-health]` only passes if the vocabulary parsed it as one token.
- [x] 5.3b `tests/test_fleet.py`: a malformed vocabulary reports as ONE violation and does
      not cascade into per-note frontmatter failures (spec scenario 4)
- [x] 5.3c `tests/test_fleet.py`: `"mental health"` is **inexpressible** as a pillar — it
      parses as two tokens and a note claiming it fails the subset check. This is the
      protection the design leans on, replacing a test that wrongly assumed the linter
      rejects a space-bearing Catalog index name (see finding below)
- [x] 5.4 Full fleet tests green — `pytest tests/test_fleet.py` **32 passed**; `.github/scripts/validate-scripts.sh` **VALIDATION OK**
- [ ] 5.5 CI green: `constitution-lint`, `vocabulary-lint`, `adr-count-lint`,
      `runbook-lint`, `openspec validate` (verifiable only after push)

## 5b. Finding surfaced by 5.3 (no action in this change)

A test asserting that `40-Treasury/Catalog/mental health-domain-index.md` fails the linter
**failed** — it passes today. Two facts, both verified:

- `validate_name()` does **not** forbid spaces. `forbidden_chars` is ``[ ] # ^ | \ / : * " ? < >`` —
  a space is cross-platform-legal. Only `is_valid_slug()` (via `slug_pattern`) rejects it.
- The linter checks `40-Treasury/Catalog` with the **weak** `validate_name` only. The kebab
  check for that area is **staged behind the commented flag** (`knowledge-lint-script` L71-73),
  deferred by ADR-0015 until every family conforms.

This does **not** weaken the proposal: its claim was that a space-bearing name violates
`naming-rules/spec.md` (INV-11), which is **spec-true** — the *Kebab-Case Slug* requirement
governs machine-generated names. It is simply not yet *mechanically* enforced for Catalog
stems. The design holds regardless, because ADR-0029 keeps the filename-hostile value out of
the vocabulary entirely (test 5.3c), rather than relying on a downstream gate that is off.

- [ ] 5b.1 Out of scope here: the ADR-0015 staged-enforcement switch for Catalog/Claims/Logbook
      stems remains queued. Note that when it flips, `<pillar>-domain-index` stems become
      kebab-enforced and this change's rule is then guarded at both ends.

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
