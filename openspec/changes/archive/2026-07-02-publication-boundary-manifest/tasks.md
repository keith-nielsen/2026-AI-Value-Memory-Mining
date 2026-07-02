## 1. Spec deltas

- [ ] 1.1 `access-control` — ADDED "Publication Boundary — Path-Level Manifest for Public Remotes (INV-14)"; MODIFIED Secrets scenario (config defaults/instance split)
- [ ] 1.2 `maintenance` — MODIFIED Script Inventory (`push-guard-script` path-gate; `publish-manifest.json` schema)

## 2. Enforcement rails

- [x] 2.1 **Live vault (ratify-in-place):** `publish-manifest.json`; `push-guard-script.md` path-gate → rendered `pre-push`; `config.defaults.env` + gitignored `config.env` + `config.env.example`; `PUBLIC_REMOTE_ALLOWLIST=""`
- [ ] 2.2 **Repo `vault-template/` mirror (forks inherit):** same artifacts into the template
- [ ] 2.3 `PUBLIC_REMOTE_ALLOWLIST` added to `config.defaults.env` (template + example)
- [x] 2.4 `.github/scripts/validate-scripts.sh` — sandbox instantiates `config.env` from `config.env.example` (config-split regression fix)
- [x] 2.5 `.github/workflows/ci.yml` — `vocabulary-lint` reads `config.defaults.env` (was the removed `config.env`)

## 3. Docs

- [ ] 3.1 `docs/USING-THIS-TEMPLATE.md` — config defaults/instance split + `PUBLIC_REMOTE_ALLOWLIST` + publish-manifest
- [ ] 3.2 `README.md` — counts (invariants unchanged at 14; ADR count +1)

## 4. Regression

- [x] 4.1 push-guard dry-runs (live vault): private→public blocked; public/empty allowed; non-allowlisted denied; guard-off allowed; private-backup allowed
- [ ] 4.2 `openspec validate publication-boundary-manifest --strict` + `--all --strict`
- [ ] 4.3 `constitution-lint` + `vocabulary-lint`; CI green

## 5. Gate 4 + release (human-gated)

- [ ] 5.1 Gate-4 sign-off recorded in `proposal.md`
- [ ] 5.2 `openspec/adr/0020-publication-boundary-manifest.md` → Accepted
- [ ] 5.3 Archive (sync specs) + CHANGELOG + tag
