<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: add-fleet-inventory-conformance

Close the **spec → note** verification seam, and correct the five drifts that seam allowed. Change A
of two; `relocate-fleet-in-tree-bin` (B) depends on the instruments this change lands.

## Gate 4 — human sign-off

- [x] **Human sign-off recorded: Approved — Keith Nielsen, 2026-08-18.**
      The operator reviewed this proposal and its task list and replied `Approved`. Recorded by
      Claude Code per the standing Gate-4 format; the sign-off gate is human-only and not
      agent-delegatable (constitution §3 Gate 4, §5).

Scope of what was approved: the four ADDED requirements in `specs/`, the five corrections in A2, and
the phased task list in `tasks.md`. **No relocation is authorised by this sign-off** — every
`deploy_target` still points at `~/bin` when this change lands. Change B carries its own Gate 4.

## Why

Three checks govern the Layer-0 fleet today, and between them they leave one seam open:

| Check | Governs |
|---|---|
| `render` / `reconcile` | note → deployed |
| `template-parity` | template → live vault |
| **nothing** | **spec → note** |

A script can therefore ship, deploy, and enforce an invariant while remaining absent from the
specification that is supposed to govern it — indefinitely, and with every build green.

**That is not hypothetical. It happened, and it is live right now.** `secret-scan-script.md` →
`vault_secrets.py` enforces INV-7, shipped 2026-07-28 under ADR-0036, reconciles clean — and appears
**nowhere in `openspec/specs/maintenance/spec.md`**. The Script Inventory table lists 13 rows for a
14-note fleet. Simultaneously `README.md` heads its table *"Operational Scripts (13)"* and then
presents **10 rows**, for a fleet of 14 — wrong twice, in two directions, in one heading and its own
table.

These went unnoticed for three weeks because **an absence has no string to match.** A search-based
sweep for a path or a name cannot find a missing row. Only an enumeration compared against ground
truth can.

The wider pattern, which is the actual justification: **every drift found in this corpus is a
hand-maintained duplicate of a machine-checkable fact.** Two inventory tables, a count in a heading,
a runtime column. Each restates something derivable from the notes, and each drifted the moment
something shipped. The executable layer never drifted, because `reconcile` checks it.

A second seam is closed here for the same reason. `.claude/settings.json` carries an **exact-match**
command exclusion, and the string `excludedCommands` appears **nowhere** in `tests/`, `.github/` or
`tools/`. Nothing verifies that the exclusion names an artifact that exists. When the named artifact
moves, the entry does not error — it silently stops matching, and the resulting refusal is
indistinguishable from a genuine deny. The fleet's own tests cannot see this: they invoke scripts as
subprocesses and never traverse the harness.

## What Changes

**Instruments (new):**

- `tests/test_inventory_conformance.py` — the `maintenance` Script Inventory and the `README.md`
  operational-script table must each name **exactly** the current note set, and any stated count must
  equal the rows presented.
- `tests/test_settings_paths.py` — every script path in `.claude/settings.json` (repo and
  `vault-template/`) must resolve to a declared `deploy_target`.
- Cadence conformance — no live document states a schedule for a note whose `runtime:` is not `cron`.
- `tests/test_fleet.py` — behavioural coverage for **`vault-orphans.py`** and
  **`vault-reprospect.py`**, which today have **zero** coverage in pytest or `validate-scripts.sh`.

**Corrections the instruments catch:**

| # | Where | Claims | Reality |
|---|---|---|---|
| 1 | `maintenance/spec.md` inventory | 13 rows; `secret-scan` absent from the entire spec | 14 notes |
| 2 | `README.md:219` | heading "(13)", table has 10 rows | 14; missing `vault_secrets.py`, `vault_lib.py`, `pre-push`, `outbound-publish-guard.py` |
| 3 | `README.md:231` | `vault-refine-detect.py` schedule `0 6 * * *` | no note declares `schedule:` or `runtime: cron` — contradicts `maintenance/spec.md:118` |
| 4 | `USING-THIS-TEMPLATE.md:264` | "edit the `schedule:` field … re-run `render`" | nothing reads that field |
| 5 | `maintenance/spec.md:106` | `treasury-orphan` runtime "manual / weekly" | the note declares `runtime: manual` |

## Why this is Change A and not part of the relocation

Splitting is not packaging convenience; it changes what the tests prove.

1. **The instruments are proven against defects that already exist**, not against defects the
   relocation introduces. A check first exercised by the change that motivated it is weak evidence.
2. **Change B's diff becomes purely the relocation** — which is what a reviewer needs in order to
   judge a move touching Layer 0.
3. **A rollback of B does not lose these fixes.** They are independently valuable.
4. **The `settings.json` check gets a genuine subject.** Landed here against today's valid paths, B
   becomes the first thing that could ever break it — a far stronger test than manufacturing a red
   state inside the same change that goes green.

This follows the corpus's own precedent for staged adoption (`wave-2-vault-lib-adoption`; ADR-0023's
*"incremental adoption … the rest adopt as next touched"*).

## The three questions

1. **State lifetime — what is the exit condition?** No new persistent state. The instruments are
   pure functions of the tree, computing ground truth per run and holding nothing between runs.
2. **Reachability — which real invocation reaches this line?** Traced, not intended. Inventory and
   cadence conformance run in `fleet-pytest` on every pull request. The settings check runs in the
   same job. The two new behavioural tests run as real subprocesses through the existing `fleet`
   fixture, the same path the other 328 tests take. ⚠ **The settings check verifies that a path
   RESOLVES; it cannot verify the exclusion MATCHES at the harness layer** — no test traverses Claude
   Code. That limit is stated in the spec text, not left to be discovered.
3. **Exhaustiveness — do the categories partition?** The inventory check compares two sets and
   reports both directions: a note with no row, and a row with no note. A check that only detects
   omissions would pass on a table naming a script deleted last month.

## Nature of this change — ordinary

Cadence declarations are named in the constitution's **Tier 2 — Conventions** ("cron schedules"),
whose override path is explicitly *"ordinary OpenSpec change — no ceremony required."* The remainder
is ADD-only: new requirements and new tests, with no existing requirement modified, weakened or
narrowed.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md, openspec/specs/access-control/spec.md
protects: [INV-2, INV-3, INV-6, CONST-02, INV-4, INV-5, INV-7, INV-8, INV-11, INV-14]
overrides: none
basis: ADD-only — three new conformance requirements plus corrections to five statements that contradict the tree; no existing requirement is modified, weakened or narrowed; the cadence corrections are Tier-2 conventions per constitution §2
```

## Regression evidence — every check red before green

Per the standing Definition of Done, no task is ticked `[x]` until its check has been **observed
failing on the pre-change tree**.

| Check | Required pre-change failure |
|---|---|
| inventory — spec | FAIL: 13 rows vs 14 notes; `secret-scan-script.md` absent |
| inventory — README | FAIL: heading says 13, table has 10, reality 14 |
| cadence | FAIL: `README.md:231` carries `0 6 * * *` |
| `vault-orphans` / `vault-reprospect` | FAIL: no such test exists — recorded as *absent*, never as a passing run |
| settings paths | **Cannot fail naturally — today's path is valid.** Red must be manufactured (point the exclusion at a nonexistent artifact), observed, and both runs recorded. |

The last row is stated rather than glossed. A check that has never been seen to refuse is an
assumption, and recording that its red state was manufactured is the difference between evidence and
a green tick.

Per constitution §3 Gate 3, every result is evidenced **by its command and output** — a tally with
its denominator, a diff, or an exit status — never by a prose assertion or a shell-printed verdict
string. An `echo "ok"` proves nothing: the shell knows only an exit code, not the answer to the
question asked.

## Impact

- The spec → note seam closes. A script cannot again ship ungoverned by its own specification.
- A harness exclusion naming a moved artifact becomes a test failure rather than a silent deny.
- Fleet coverage rises from 9 of 11 members to 11 of 11.
- `README.md` and `maintenance/spec.md` become accurate about the fleet for the first time since
  2026-07-28.
- **Change B is unblocked**, with its instruments already landed and proven.

## Rollback

Revert the commit. The instruments are detection-only and write nothing; the corrections are
documentation. No deployed artifact, no vault content, and no protected path is touched.
