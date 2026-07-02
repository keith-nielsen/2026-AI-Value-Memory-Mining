## 1. Spec delta

- [ ] 1.1 `naming-rules` — ADDED *Special-File Exemptions*; MODIFIED *Language-Neutral Mirror* (JSON gains `min_hyphen_tokens`, `exempt_names`, `exempt_globs`, `exempt_rationale_doc`)

## 2. Implementation

- [x] 2.1 **Live vault (ratify-in-place):** `naming-rules-script.md` (exemptions + `is_exempt`/`has_min_hyphen_tokens`); `knowledge-lint-script.md` honors `is_exempt` (≥3-token rejection staged/commented); regenerated `naming-rules.json`
- [ ] 2.2 **Repo `vault-template/` mirror:** the two meta-scripts into the template

## 3. Docs

- [ ] 3.1 `docs/naming-exemptions-rationale.md` (new — per-dependency-class rationale)
- [ ] 3.2 `docs/USING-THIS-TEMPLATE.md` — link the rationale doc

## 4. Regression

- [x] 4.1 naming sweep (live vault): every present special file `is_exempt`; `naming-rules.json` carries exemption fields; `vault-lint.py` exit 0
- [ ] 4.2 `openspec validate naming-special-file-exemptions --strict` + `--all --strict`
- [ ] 4.3 `constitution-lint` + `vocabulary-lint`; CI green

## 5. Gate 4 + release (human-gated)

- [ ] 5.1 Gate-4 sign-off recorded in `proposal.md`
- [ ] 5.2 `openspec/adr/0021-naming-special-file-exemptions.md` → Accepted
- [ ] 5.3 Archive (sync specs) + CHANGELOG + tag
