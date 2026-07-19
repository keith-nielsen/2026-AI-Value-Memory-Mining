<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — retire-daily-close-cycle

Exit criteria: the daily note format, its two scripts, its Requirement, its vocabulary and its
harness rules are gone from the framework and the live vault; every surviving Requirement that used
them as a worked example is re-exemplified; CI green; `10-Logbook/` retained as an empty reserved
silo with its kernel write-block untouched.

## 1. Governance artifacts

- [x] 1.1 ADR-0032 drafted (`openspec/adr/0032-retire-daily-close-cycle.md`)
- [x] 1.2 Proposal drafted with Gate-1 transcripts (19-file blast radius; coupling probe)
- [x] 1.3 Spec deltas drafted — `maintenance` (1 REMOVED, 3 MODIFIED), `access-control`
      (1 MODIFIED Requirement + config-key scenario), `vault-structure` (2 MODIFIED)
- [x] 1.4 CONST-04 decision recorded: **option (ii)** — keep the ordering, drop the daily rationale;
      `10-Logbook/` justified as "highest-touch by design / reserved", stated as a reservation not an
      observation (operator, 2026-07-19)
- [ ] 1.5 `openspec validate retire-daily-close-cycle --strict` green — transcript below
- [ ] 1.6 `openspec validate --all --strict` green — transcript below

## 2. Framework removals (`vault-template/`)

- [ ] 2.1 Delete `99-Operations/scripts/daily-note-script.md`
- [ ] 2.2 Delete `99-Operations/scripts/daily-close-script.md`
- [ ] 2.3 Delete `97-Molds/daily-mold-blank.md`
- [ ] 2.4 Delete `96-Runbooks/daily-close-runbook.md`
- [ ] 2.5 `99-Operations/scripts/vault-lib-script.md` — remove `is_closed()` from the implementation
      and the contract docstring; remove `DISPOSITIONS` from the `__main__` self-check key list
- [ ] 2.6 `99-Operations/config.defaults.env` — remove `DISPOSITIONS`
- [ ] 2.7 `99-Operations/schemas/note-frontmatter-schema.md` — remove the `daily` type block
- [ ] 2.8 `96-Runbooks/session-bootstrap-loader.md` — drop the `daily-close-runbook` JIT pointer
- [ ] 2.9 `.claude/settings.json` — remove 4 dead references: `Edit(/10-Logbook/Daily/*.md)`;
      `excludedCommands` `~/bin/vault-close-day.py *`, `~/bin/vault-daily-note.py`,
      `~/bin/vault-daily-note.py *`. **`./10-Logbook` in `denyWrite` STAYS** (out of scope, §Gate-1)
- [ ] 2.10 `00-Docs/README.md` — remove daily-cycle references

## 3. CI + tests

- [ ] 3.1 `.github/scripts/validate-scripts.sh` — remove the `daily-note idempotent` check (~L68–70)
      and the entire `close-daily lifecycle` section (~L77–104)
- [ ] 3.2 `tests/test_fleet.py` — remove daily-note and daily-close cases; confirm no surviving test
      imports `is_closed` or writes a daily fixture
- [ ] 3.3 Fleet-count assertions 15 → 13 wherever asserted
- [ ] 3.4 Full local `pytest` green — transcript below
- [ ] 3.5 `validate-scripts.sh` green in the sandbox harness — transcript below

## 4. Docs

- [ ] 4.1 `README.md` — fleet tree/count; ADR count 31 → 32 (adr-count-lint gate)
- [ ] 4.2 `AGENTS.md` — remove daily-cycle bullets
- [ ] 4.3 `docs/method.md`, `docs/obsidian.md`, `docs/USING-THIS-TEMPLATE.md`,
      `docs/naming-exemptions-rationale.md` — remove daily-cycle references
- [ ] 4.4 `CHANGELOG.md` — `[Unreleased]` entry

## 5. Live-vault mirror (lockstep — ADR-0028 R8)

- [ ] 5.1 Mirror the template deletions/edits into `$VAULT_ROOT`
- [ ] 5.2 **Delete the deploy targets** `~/bin/vault-daily-note.py` and `~/bin/vault-close-day.py`
      — mandatory in the same apply; `reconcile` iterates notes, so an orphaned target is invisible
      to drift detection and persists as ungoverned operational code
- [ ] 5.3 `vault-render.py reconcile` — zero drift, transcript below
- [ ] 5.4 `tools/template-parity.py` green — transcript below
- [ ] 5.5 **Operator applies the live `.claude/settings.json` diff** (agent is denied
      `Edit(/.claude/**)` and the path is sandbox-denied) — exact diff supplied at Gate 4
- [ ] 5.6 Confirm the 12 existing dailies + `## Close` manifests are byte-identical afterwards

## 6. Rider — decision pending

- [ ] 6.1 **Standalone-vault lint** (triage #19): CI grep failing the build if `vault-template/`
      references framework-repo-only paths (`tools/`, `openspec/`). Operator has not yet said whether
      it rides this release. If yes, declare it as its own surface in the PR ```scope block.

## 7. Ship

- [ ] 7.1 PR opened with the ```scope block **in place before the push CI evaluates** (F21#1 —
      amending after requires REST PATCH + a fresh push); archive-time paths
      (`openspec/changes/archive/…`, all three touched specs) included from the start
- [ ] 7.2 CI green on the PR
- [ ] 7.3 Gate-4 human sign-off recorded (absolute proposal path + "reply Approved")
- [ ] 7.4 Archive the change; verify no duplicate `### Requirement:` headers; `--all --strict` green
- [ ] 7.5 Ship via `tools/ship-release.py v0.1.31` — walk it, never hand-compose; run each emitted
      gated command visibly and re-invoke until the tag↔Release parity tally
