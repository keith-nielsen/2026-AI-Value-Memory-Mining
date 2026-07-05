<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `maintenance` — MODIFIED "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)":
      commit_paths pathspec + no-op clause; full-Python-fleet adoption paragraph; scenarios
      "repeated render is a clean no-op" + "scoped commit ignores unrelated staged content"

## 2. Implementation (vault-template)

- [x] 2.1 `vault-lib-script.md` — commit_paths: `diff --cached --quiet -- <paths>` no-op guard +
      pathspec-scoped commit; contract docstring + Rationale updated
- [x] 2.2 `knowledge-lint-script.md` — root, `vocab()` ×3 (required, no default), `fm()`,
      `EXIT_VIOLATION`
- [x] 2.3 `treasury-orphan-script.md` — root
- [x] 2.4 `tailings-reprospect-script.md` — root + `fm()`
- [x] 2.5 `ore-detect-script.md` — root + `vocab("REFINE_GATE_GRADES")` + `fm()`
- [x] 2.6 `naming-rules-script.md` — `__main__` mirror-writer resolves root via lazy `vault_lib`
      import; `--check`/module path dependency-free; rules byte-identical

## 3. Docs

- [x] 3.1 `CHANGELOG.md` — `[Unreleased]` entry

## 4. Regression (repo-side, before Gate 3 closes)

- [x] 4.1 `openspec validate wave-2-vault-lib-adoption --strict` + `--all --strict`
- [x] 4.2 `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [x] 4.3 Sandbox-vault env-free battery: lint clean rc 0 + seeded-violation rc 1; orphans;
      reprospect; refine-detect; naming mirror-writer under walked root
- [x] 4.4 No-op probe (kanban ×2 same-day → rc 0, no second commit) + scoped-commit probe
      (unrelated staged file untouched) + hook-path probe (`--check` works without vault_lib)

## 5. Gate 4 + publish + live apply (human-gated)

- [x] 5.1 [human] Gate-4 signed (explicit in-session approval, 2026-07-05; transcribed with provenance)
- [x] 5.2 [human] PR #9; CI green; merged `c3174b0` (2026-07-05)
- [ ] 5.3 [human] `cp` the 6 notes into live `99-Operations/scripts/`; `~/bin/vault-render.py
      render` + `reconcile` (zero drift)
- [x] 5.4 [agent] Live probes green (2026-07-05, env-free): lint rc 0 over live Treasury;
      orphans/reprospect/refine-detect rc 0; naming mirror-writer resolved the live root then was
      **correctly kernel-denied** writing `99-Operations/` (sandboxed, not excluded — the fence
      holds through the new code path; mirror-writer is operator tooling); kanban same-day →
      `ok: unchanged — no commit needed`, rc 0 (the Phase-1a closure defect, fixed live)
- [ ] 5.5 [human] Archive **after** `fix-commit-gate-env-guard` is archived (delta accretion
      order); CHANGELOG heading + tag per release cadence (push main before tagging)
