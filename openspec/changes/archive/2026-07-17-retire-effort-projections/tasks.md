<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — retire-effort-projections

## 1. Spec delta (`maintenance`, protects INV-2/3/6)

- [ ] 1.1 MODIFY **Script Inventory** — remove `dig-rollover-script.md` + `kanban-render-script.md`
      rows; `daily-note` and `ore-detect` `Runtime` → `manual`; add the no-effort-projection clause
      and the no-cron clause
- [ ] 1.2 MODIFY **Script Inventory** — ADD scenario *"Retiring a script removes its deploy target in
      lockstep"* (the R8 re-opening risk: `reconcile` iterates notes, so an orphaned `~/bin` artifact
      is invisible to it)
- [ ] 1.3 MODIFY **One Mutation, One Commit** — commit-format example `rollover:` → `bank:`; drop the
      two rollover scenarios (the surviving `daily-note` idempotence pair already exemplifies the
      one-commit and no-op halves)
- [ ] 1.4 MODIFY **Daily Close Lifecycle** — drop the "advancing (rollover / carry-over) is gated"
      clause (its subject is retired); keep capture-always-has-a-home + strict-order close; rewrite
      the *"Advancing is gated"* scenario as *"An open prior day is surfaced without gating capture"*
      (the `⚠ BLOCKED` banner survives in `daily-note`)
- [ ] 1.5 MODIFY **Shared Fleet Plumbing** — drive-path set drops `dig-rollover`/`kanban-render`;
      bare-drive exemplar → `~/bin/vault-daily-note.py`; gate-refusal exemplar → `vault-close-day.py`
- [ ] 1.6 MODIFY **Shared Fleet Plumbing** — narrow the `closed`-test scenario to `daily-note`.
      **Do not retain the "fleet-wide … no divergence between the two scripts" wording**: rollover was
      its second subject, and `daily-close` still carries a hand-rolled `split_fm`. Narrowing states
      what is true; retaining would assert what is not.
- [ ] 1.7 MODIFY **Shared Fleet Plumbing** — no-op scenario de-exemplified from kanban to "a
      committing fleet script"

## 2. Template fleet

- [ ] 2.1 DELETE `vault-template/99-Operations/scripts/dig-rollover-script.md`
- [ ] 2.2 DELETE `vault-template/99-Operations/scripts/kanban-render-script.md`
- [ ] 2.3 `daily-note-script.md` — `runtime: cron` → `manual`, drop `schedule:`; Rationale drops the
      "runs one minute before the roll-over script" coupling and the rollover cross-reference
- [ ] 2.4 `ore-detect-script.md` — `runtime: cron` → `manual`, drop `schedule:`
- [ ] 2.5 `daily-close-script.md` — Rationale: drop "rollover links, kanban" from the commit-owner
      enumeration
- [ ] 2.6 `vault-lib-script.md` — **keep** the "kanban same-day re-render lesson, 2026-07-05"
      citation: it is provenance for the no-op clause, not a dependency on a live script
- [ ] 2.7 `note-frontmatter-schema.md` — `runtime` enum drops `cron`; remove the `schedule:` field
      (no member declares either)

## 3. Template docs + config

- [ ] 3.1 `vault-template/96-Runbooks/daily-close-runbook.md` — "Parked `ore` … (the kanban /
      refine-queue is its home)" → refine-queue only
- [ ] 3.2 `vault-template/.claude/settings.json` — drop `~/bin/vault-rollover.py`,
      `~/bin/vault-kanban-render.py`, `Edit(/10-Logbook/kanban.md)` entries
- [ ] 3.3 `vault-template/00-Docs/README.md` — fleet description
- [ ] 3.4 VERIFY-ONLY `vault-template/99-Operations/schemas/refine-prompt-contract.md` — its
      `kanban_block(...)` is the **Hermes** kanban (Phase-3 harness); expected **no change**

## 4. Repo docs + CI

- [ ] 4.1 `.github/scripts/validate-scripts.sh` — remove the kanban render smoke check (it executes
      the script and asserts `10-Logbook/kanban.md` exists; would fail hard post-retirement)
- [ ] 4.2 `docs/method.md` — 4 sites: dashboard bullet, carry-over bullet, kanban projection section,
      fleet enumeration
- [ ] 4.3 `docs/USING-THIS-TEMPLATE.md`, `docs/obsidian.md`, `docs/naming-exemptions-rationale.md`,
      `README.md`, `AGENTS.md` — sweep references
- [ ] 4.4 VERIFY-ONLY `docs/glossary.md` — **do not touch.** Its `kanban` entries are the Hermes
      kanban (`kanban_complete`; "the human gate and the executor run outside the kanban flow"). The
      controlled term survives; only the Markdown board leaves.
- [ ] 4.5 `README.md` ADR count **27 → 28** in **both** places (≈ lines 29 and 100) — the
      `adr-count` CI guard asserts README count == `openspec/adr/` file count
- [ ] 4.6 `CHANGELOG.md` — entry under `[Unreleased]`

## 5. ADR

- [ ] 5.1 `openspec/adr/0028-retire-effort-projections.md` — context / options / choice /
      consequence / **sacrifice**; status `Proposed` until Gate 4

## 6. Gate 3 — regression (all green before Gate 4)

- [ ] 6.1 `openspec validate --all --strict`
- [ ] 6.2 `constitution-lint`
- [ ] 6.3 `vocabulary-lint` (with `kanban` retained in the glossary — Hermes term)
- [ ] 6.4 `adr-count` guard (README 28 == 28 files)
- [ ] 6.5 `.github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [ ] 6.6 `pytest` green
- [ ] 6.7 PR body carries a ```scope block — exact paths, dirs end `/`, **no globs**

## 7. Gate 4 — human sign-off (agent may NOT sign)

- [ ] 7.1 Operator reviews the sacrifice clause and signs the proposal

## 8. Post-merge apply — **operator only** (live vault is agent-write-denied)

- [ ] 8.1 `rm ~/bin/vault-rollover.py ~/bin/vault-kanban-render.py` — **explicit; `reconcile` cannot
      see an orphaned deploy target** (task 1.2)
- [ ] 8.2 `rm ~/Documents/Vault/10-Logbook/kanban.md`
- [ ] 8.3 `rm ~/Documents/Vault/99-Operations/scripts/{dig-rollover,kanban-render}-script.md`
- [ ] 8.4 `cp` the modified notes + schema + runbook from `vault-template/` into the live vault
- [ ] 8.5 `~/bin/vault-render.py render` then `reconcile` → **15/15 `ok:`**, exit 0
- [ ] 8.6 `~/bin/vault-lint.py` exit 0
- [ ] 8.7 Ship ceremony per ADR-0027: tag → `gh release create <tag> --verify-tag --latest` →
      `gh release view <tag>` parity → mirror
