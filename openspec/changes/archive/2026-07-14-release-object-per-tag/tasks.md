<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec deltas

- [ ] 1.1 `maintenance` — ADD Requirement "GitHub Release Object Per Version Tag" + scenarios
- [ ] 1.2 `access-control` — reword the INV-14 harness-guard enforcement clause (effective-target
      scoping; all non-denied outward/publish ops ASK) + 3 scenarios (framework-repo release → ASK;
      framework-repo push → ASK; vault-outward push → DENY unchanged)

## 2. Guard implementation (byte-identical across three homes)

- [ ] 2.1 Rewrite `in_vault` to use the **effective target** (leading `cd`, `git -C`, `gh -R`, else cwd)
- [ ] 2.2 Job 2 fires on `OUTWARD or PUBLISH` (close the silent `git push` gap)
- [ ] 2.3 Generalize the ASK banner to read correctly for both push and publish
- [ ] 2.4 Apply identically to `.claude/hooks/outbound-publish-guard.py`,
      `vault-template/.claude/hooks/outbound-publish-guard.py`, and the ```python block in
      `vault-template/99-Operations/scripts/outbound-publish-guard-script.md`
- [ ] 2.5 Extend the meta-script note Rationale (effective-target fix + git-push ASK closure; dates)
- [ ] 2.6 `reconcile` / `render --check` reports zero drift across the three homes

## 3. Ceremony documentation

- [ ] 3.1 `CONTRIBUTING.md` — post-merge ship steps (tag → release → verify → mirror) after "Open a PR"
- [ ] 3.2 `AGENTS.md` — Operating-note: informed pause (summary + proposal.md path) + hard stop before
      any outward op; release-per-tag is a required ship step

## 4. Changelog + PR scope

- [ ] 4.1 `CHANGELOG.md` `[Unreleased]` entry
- [ ] 4.2 PR body carries the fenced ```scope block for this exact file set (v0.1.22 gate)

## 5. Local verification (Gate 3)

- [ ] 5.1 `openspec validate --all` green
- [ ] 5.2 Guard behavior matrix (local): framework-repo release → ASK; framework-repo push → ASK;
      vault-outward push → DENY; non-vault-target trigger-token mention → defer
- [ ] 5.3 Full lint/validator suite green (constitution-lint, spec/vocab/md-lint, link-check,
      naming-validator, validate-scripts, scope-review report-only)

## 6. Gate 4 + ship

- [ ] 6.1 Present overview summary + absolute `proposal.md` path; record operator `Approved`
- [ ] 6.2 Write ADR-0027; fill Gate 3/4 checkboxes; `/opsx:archive`
- [ ] 6.3 Merge PR; tag; `gh release create --verify-tag --latest`; `gh release view` parity check
- [ ] 6.4 Mirror guard update into the live vault (operator action)
