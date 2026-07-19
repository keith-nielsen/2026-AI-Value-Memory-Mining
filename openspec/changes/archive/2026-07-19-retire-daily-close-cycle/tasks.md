<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — retire-daily-close-cycle

Exit criteria: the daily note format, its two scripts, its Requirement, its vocabulary and its
harness rules are gone from the framework and the live vault; every surviving Requirement that used
them as a worked example is re-exemplified; CI green; `10-Logbook/` retained as a working area with
its kernel write-block untouched.

## 1. Governance artifacts

- [x] 1.1 ADR-0032 drafted (`openspec/adr/0032-retire-daily-close-cycle.md`)
- [x] 1.2 Proposal drafted with Gate-1 transcripts (blast radius + coupling probe)
- [x] 1.3 Spec deltas drafted — `maintenance` (1 REMOVED, 3 MODIFIED), `access-control`
      (1 MODIFIED + config-key scenario), `vault-structure` (2 MODIFIED), `naming-rules`
      (1 MODIFIED — added after a Gate-1 sweep **correction**: the original pattern omitted
      `daily-mold-blank`, hiding a fourth protected spec; recorded in the proposal, not patched away)
- [x] 1.4 CONST-04 decision recorded: **option (ii)** — keep the ordering, drop the daily rationale;
      `10-Logbook/` restated as "highest-touch by design / reserved", explicitly a reservation rather
      than an observation (operator, 2026-07-19)
- [x] 1.5 / 1.6 `openspec validate` green:

```
$ npx openspec validate retire-daily-close-cycle --strict
Change 'retire-daily-close-cycle' is valid

$ npx openspec validate --all --strict
Totals: 8 passed, 0 failed (8 items)
```

## 2. Framework removals (`vault-template/`) — DONE

- [x] 2.1–2.4 Deleted `daily-note-script.md`, `daily-close-script.md`, `daily-mold-blank.md`,
      `daily-close-runbook.md` (fleet 15 → **13** notes; molds 4 → **3**, both verified by listing)
- [x] 2.5 `vault-lib-script.md` — `is_closed()` removed from implementation, contract docstring and
      rationale prose; self-check key list now covers `SPOIL_STATUSES` (a real key it never covered)
      in place of `DISPOSITIONS`
- [x] 2.6 `config.defaults.env` — `DISPOSITIONS` block removed
- [x] 2.7 `note-frontmatter-schema.md` — `daily` type block removed
- [x] 2.8 `session-bootstrap-loader.md` — `daily-close-runbook` JIT pointer dropped
- [x] 2.9 `.claude/settings.json` — 4 dead refs removed; **`./10-Logbook` retained in `denyWrite`**
      (verified post-edit: JSON parses, `'./10-Logbook' in denyWrite` → `True`, daily refs → `[]`)
- [x] 2.10 `00-Docs/README.md` — tree line reworded, "create your first daily note" step removed
      (it also carried an ADR-0028 cron straggler), remaining steps renumbered 3/4

## 3. CI + tests — DONE

- [x] 3.1 `validate-scripts.sh` — `daily-note idempotent` check and the whole `close-daily lifecycle`
      section removed
- [x] 3.2 `tests/test_fleet.py` — `DAILY_TMPL`/`make_day` helpers and 5 cases removed (34 → 29 test
      functions). **Coverage preserved, not dropped:** the no-sweep assertion (unrelated dirty
      working-tree content must not be swept into a scoped commit) existed **only** in the retired
      close case — it is re-exemplified onto `vault-slag.sh`/`vault-dump.sh`. Fence-lint and
      bare-drive cases re-pointed at `ore-detect` / `refine-detect`.
- [x] 3.3 Fleet counts corrected (README tree already read 13 — it had been **stale at 13 while the
      fleet was 15**, and is now accurate rather than accidentally right)
- [x] 3.4 / 3.5 Green:

```
$ python3 -m pytest tests/ -q
....................................................                     [100%]
52 passed in 7.86s

$ bash .github/scripts/validate-scripts.sh
  ok    reconcile zero drift · lint clean (empty treasury) · refine-detect empty
  ok    executor rejects non-kebab target_note, no Treasury write
  ok    executor applies conforming proposal
VALIDATION OK
exit=0
```

## 4. Docs — DONE

- [x] 4.1 `README.md` — tree lines, `vault-daily-note.py` row (another cron straggler) removed,
      ADR count 31 → 32 in 3 places (verified: `ls openspec/adr/*.md | wc -l` → 32)
- [x] 4.2 `AGENTS.md` — sidecar/Daily paragraph rewritten, runbook bullet removed, drive-contract and
      auto-commit examples re-pointed at surviving scripts
- [x] 4.3 `docs/method.md`, `docs/obsidian.md`, `docs/USING-THIS-TEMPLATE.md`,
      `docs/naming-exemptions-rationale.md`. **The `YYYY-MM-DD.md` naming exemption is RETAINED** —
      the 12 existing dailies stay under the commit gate and `10-Logbook/` remains a manual working
      area; only its rationale changed (it had cited `vault-close-day.py`)
- [x] 4.4 `CHANGELOG.md` — `[Unreleased]` Removed + Added entries

## 5. Live-vault mirror — NOT STARTED (post-Gate-4, and operator-performed by construction)

Live state confirmed untouched: **15 script notes**, all four daily artifacts present.

**Every mirror target is behind INV-5 / ADR-0022 kernel denials** (`99-Operations/`, `97-Molds/`,
`96-Runbooks/`, `.claude/`, and `~/bin/` which is outside the vault). Only `00-Docs/README.md` is
agent-writable. This is the write-scope working as designed, not an obstacle to route around.

- [ ] 5.1 Mirror template deletions/edits into `$VAULT_ROOT` — **operator**
- [ ] 5.2 Delete deploy targets `~/bin/vault-daily-note.py`, `~/bin/vault-close-day.py` — **operator**;
      mandatory in the same apply (`reconcile` iterates notes, so an orphaned target is invisible to
      drift detection and persists as ungoverned operational code — ADR-0028 R8)
- [ ] 5.3 `vault-render.py reconcile` — zero drift
- [ ] 5.4 `tools/template-parity.py` green
- [ ] 5.5 Operator applies the live `.claude/settings.json` diff (identical to the template diff)
- [ ] 5.6 Confirm the 12 existing dailies + `## Close` manifests byte-identical afterwards

## 6. Rider — DONE

- [x] 6.1 **Standalone-vault lint** (triage #19) added as CI job `standalone-vault-lint`. Written
      **path-shaped**, not name-shaped: naming the origin repo in prose stays legal, depending on its
      paths does not (`openspec/`, `tools/ship-release|pr-state|template-parity`, absolute
      `Documents/repo/`). **Found 3 real F15 leaks on introduction** — `session-bootstrap-loader.md`
      ×2 (one citing `openspec/constitution.md` as the governance-first source, which a deployed vault
      does not have) and `00-Docs/README.md` ×1 — all fixed. Now `0 violation(s) across 63 template
      files`; ci.yml parses, 12 jobs. The check is proven discriminating: it failed before the fix and
      passes after.

## 7. Ship — PENDING GATE 4

- [ ] 7.1 PR opened with the ```scope block **in place before the push CI evaluates** (F21#1);
      archive-time paths (`openspec/changes/archive/…`, **all four** touched specs) declared from the
      start, plus the rider's CI surface as its own line
- [ ] 7.2 CI green on the PR
- [ ] 7.3 **Gate-4 human sign-off** (absolute proposal path + "reply Approved")
- [ ] 7.4 Archive; verify no duplicate `### Requirement:` headers; `--all --strict` green
- [ ] 7.5 Ship via `tools/ship-release.py v0.1.31` — walk it, never hand-compose
