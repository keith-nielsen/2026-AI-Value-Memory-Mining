<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: retire-daily-close-cycle

**Change type:** `constitution-override`
**Principle(s) affected:** Touches four `protects:`-tagged specs — `maintenance`
(`protects: [INV-2, INV-3, INV-6]`), `access-control`
(`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`), `vault-structure`
(`protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12]`), and `naming-rules`
(`protects: [INV-11]`). **No Tier-0/Tier-1 element is overridden
or weakened**, but see the **CONST-04 rationale interaction** flagged below — it is surfaced for
explicit operator decision per constitution §5, not resolved unilaterally.
**Tier:** 1-adjacent (retires a fleet pair, a whole Requirement, a note type, and a vocabulary;
CONST-02's `10-Logbook/` silo is **retained**; §5 AI hard-stop honored — surfaced for sign-off at
Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-18)
**Date:** 2026-07-18
**ADR:** ADR-0032 (this change carries an ADR — the ADR-0028 retirement precedent, not the
conforming-amendment-without-ADR precedent, because a Requirement is removed whole and a real
sacrifice is stated)

---

## Why

ADR-0028 retracted the framework's pretence of being driven but **kept** the daily note. An audit on
2026-07-18 — prompted by the operator asking why a daily close exists at all once the cadence is
retired — found the daily surface in the kanban's condition, by a wider margin. Full argument in
**ADR-0032**; the load-bearing evidence:

- **12 dailies in 32 days, then 0 in 13** — a period covering 70 commits, v0.1.24→v0.1.30, ADRs
  0027–0031, and an entire fix program. The most productive stretch on record ran with no daily.
- **The last two dailies are empty in every section.** `2026-07-03`'s only content is a
  `## Carry-over` list — the artifact ADR-0028 already retired.
- **Zero inbound content citations.** No Site, Claim, or Treasury note cites a daily as a source.
- **`2026-06-29.md` says it was *"reconstructed from git"*.** Git was already the real log; the daily
  was a lossy duplicate, regenerated from the original the one time it lapsed.
- **Nothing automated could ever fill it** — the harness denies agents `10-Logbook/Daily/*.md` at the
  tool layer and `10-Logbook/` at the kernel. One `daily:` commit exists in all of history.

**Operating frame (operator, 2026-07-18):** an external harness (Hermes or equivalent) drives effort
cadence and populates; **this framework refines and banks**. VMM is a refinery with a defined intake.
Recorded in `30-Sites/vmm-strategy-roadmap/`.

## What Changes

- **`maintenance` spec:** REMOVE `Daily Close Lifecycle` whole; MODIFY `Script Inventory` (−2 rows),
  `One Mutation, One Commit (INV-2)` (re-exemplify), `Shared Fleet Plumbing (vault_lib)` (drop
  `is_closed` from the contract; re-exemplify bare-drive and gate-refusal; **remove** the YAML-typed
  `closed` scenario — no subject remains).
- **`access-control` spec:** MODIFY `OS/Harness-Enforced Agent Write Scope` (drop the
  `10-Logbook/Daily/*.md` tool rule and the sidecar carve-out; re-exemplify the drive path with a
  surviving script) and the config-key scenario (drop `DISPOSITIONS`).
- **`naming-rules` spec:** MODIFY `Token-Minimum Naming` — re-exemplify the silo-section-descriptor
  scenario on `effort-mold-blank`; retain the date-stem exemption with restated rationale.
- **`vault-structure` spec:** MODIFY the folder tree (`Daily/`, `daily-mold-blank.md`), the note-type
  table (`daily` row), the `closed` field paragraph, the runbook example, and — **pending operator
  decision** — the CONST-04 ordering rationale and its Scenario.
- **Retired:** `vault-template/99-Operations/scripts/daily-note-script.md`, `daily-close-script.md`
  and their deploy targets; `vault-template/97-Molds/daily-mold-blank.md`;
  `vault-template/96-Runbooks/daily-close-runbook.md`.
- **`vault_lib-script.md`:** remove `is_closed()` and the `DISPOSITIONS` self-check line.
- **`config.defaults.env`:** remove `DISPOSITIONS`.
- **`note-frontmatter-schema.md`:** remove the `daily` type.
- **`session-bootstrap-loader.md`:** drop the `daily-close-runbook` JIT pointer.
- **`.claude/settings.json` (template):** remove 4 dead references — `Edit(/10-Logbook/Daily/*.md)`
  and `excludedCommands` `~/bin/vault-close-day.py *`, `~/bin/vault-daily-note.py`,
  `~/bin/vault-daily-note.py *`.
- **`.github/scripts/validate-scripts.sh`:** remove the `daily-note idempotent` check and the whole
  `close-daily lifecycle` section (lines ~68–104).
- **Docs:** `README.md`, `AGENTS.md`, `docs/method.md`, `docs/obsidian.md`,
  `docs/USING-THIS-TEMPLATE.md`, `docs/naming-exemptions-rationale.md`,
  `vault-template/00-Docs/README.md` — remove daily-cycle references and fix fleet counts (15 → 13).
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Deliberately out of scope.**
(a) **The `10-Logbook` kernel write-block stays.** `./10-Logbook` remains in
`sandbox.filesystem.denyWrite`. Removing it is a **write-scope widening** on the ADR-0025
(`permit-agent-claims-capture`) model with its own Gate-4 — not cleanup, and it must not ride in as a
side effect. Parked in `vmm-strategy-roadmap` at operator direction. *Interaction to note:* dropping
the tool-layer `Edit(/10-Logbook/Daily/*.md)` rule here is **cosmetic while the kernel block stands**.
(b) **The 12 existing dailies and their `## Close` manifests are untouched** — append-only provenance;
only future generation stops.
(c) **No successor driver.** Re-aiming total-disposition at the Sites harvest/discard cycle (the
RC-1a re-vehicle) is separate design work, not this change.
(d) **`10-Logbook/` and `20-Claims/` are not re-specified.** They are placeholder working areas
pending their tenant; designing a format for an unbuilt driver is ADR-0028's rejected option (c).

**External dependency being adopted: NONE.** This change only removes.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> `maintenance` protects INV-2/INV-3/INV-6; `access-control` protects CONST-02 and the INV-4/5
> write-scope rails; `vault-structure` protects CONST-02/CONST-04/CONST-05 and INV-1/INV-12. The
> daily pair is INV-3 literate script surface and INV-2 commit-owning drive path, so retiring it
> touches all three specs by construction. **CONST-02 is not engaged**: it protects `10-Logbook/` as a
> **Layer-2 silo**, and the silo is retained — only the note *format* and its scripts retire. INV-4/5
> are not weakened: no deny rule is loosened (the one rule removed targets a format that ceases to
> exist, and the kernel block is explicitly retained). The genuine interaction is **CONST-04**, below.

**Blast radius — enumerated by transcript (ADR-0031), not composed.**

```
$ grep -rln "daily-note\|daily-close\|vault-close-day\|vault-daily-note\|DISPOSITIONS\|is_closed" \
    openspec/specs/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md | sort
AGENTS.md
docs/method.md
docs/naming-exemptions-rationale.md
docs/obsidian.md
docs/USING-THIS-TEMPLATE.md
.github/scripts/validate-scripts.sh
openspec/specs/access-control/spec.md
openspec/specs/maintenance/spec.md
openspec/specs/vault-structure/spec.md
README.md
vault-template/00-Docs/README.md
vault-template/96-Runbooks/daily-close-runbook.md
vault-template/96-Runbooks/session-bootstrap-loader.md
vault-template/99-Operations/config.defaults.env
vault-template/99-Operations/schemas/note-frontmatter-schema.md
vault-template/99-Operations/scripts/daily-close-script.md
vault-template/99-Operations/scripts/daily-note-script.md
vault-template/99-Operations/scripts/vault-lib-script.md
vault-template/.claude/settings.json
```

19 files. **Two were missed by the pre-transcript scoping and are recorded as such** — the sweep is
why this change is correctly sized:

- **`openspec/specs/vault-structure/spec.md`** — a third protected spec, not previously in scope.
- **`.github/scripts/validate-scripts.sh`** — a live CI section that will fail on removal.

**Correction — the sweep above was itself incomplete (recorded, not quietly patched).** Its pattern
omitted the retired *mold*, so a fourth protected spec did not appear. Re-run with the mold included:

```
$ grep -rln "daily-mold-blank" openspec/specs/ vault-template/ docs/ .github/ README.md AGENTS.md
openspec/specs/naming-rules/spec.md
```

`openspec/specs/naming-rules/spec.md` (`protects: [INV-11]`) uses **`daily-mold-blank` as the worked
example** for the `silo-section-descriptor` convention (L129) — an artifact this change deletes. It
is added to the delta set and re-exemplified on `effort-mold-blank` (ADR-0028's re-exemplify rule).
The same spec's date-stem exemption is **retained and its rationale restated**: pre-existing dailies
stay under the commit gate and `10-Logbook/` remains a manual working area, so the exemption must
survive the cycle that originally motivated it. **Lesson for Gate 4: a blast-radius sweep is only as
wide as its pattern — enumerate the artifacts being deleted, then search for each by name.**

Total: **20 files, four protected specs** (`maintenance`, `access-control`, `vault-structure`,
`naming-rules`).

**Functional-coupling probe — does the pipeline depend on the daily?**

```
$ grep -ln "is_closed\|closed" vault-template/99-Operations/scripts/*.md
daily-note-script.md
daily-close-script.md
vault-lib-script.md

$ grep -n "daily\|close" ore-detect-script.md bank-execute-script.md site-slag-script.md \
    spoil-dump-script.md tailings-reprospect-script.md treasury-orphan-script.md knowledge-lint-script.md
bank-execute-script.md:16:index links, and the consumed proposal's deletion (`bank: <stem>`); the close-day
```

**No pipeline script imports `is_closed`, reads a daily, or tests close state.** The single hit is one
prose clause. The coupling runs the other way (`daily-close`'s `LINK_RULES` observe the pipeline
silos). `Sites → Ore → Bullion → Treasury → Spoil` already runs standalone — this is a clean excision.

### ⚠ CONST-04 interaction — surfaced for operator decision (§5 hard-stop)

`vault-structure/spec.md` justifies CONST-04's touch-frequency folder ordering **by the daily note**:

- L101: *"the daily note in `10-Logbook/Daily/` is the orienting surface"* — the stated rationale for
  `10-Logbook/` sorting above `20-Claims/`.
- L115–117: `#### Scenario: Daily logs sort above the capture inbox` … *"placing the daily cockpit at
  the top (CONST-04)"*.

CONST-04's **principle** (zero-padded, gapped, touch-frequency order) is untouched — but its
**worked rationale and one Scenario name an artifact that will not exist.** Three ways forward; the
agent does not choose:

- **(i) Re-exemplify the rationale, keep the ordering (recommended).** `10-Logbook/` remains the
  highest-touch silo under the operating frame — it is where the external harness writes the effort
  audit trail. Restate the rationale on that basis and rewrite the Scenario without "daily cockpit".
  Consistent with ADR-0028's re-exemplify rule. **Honest caveat:** it justifies the ordering by a
  *future* tenant, which is weaker evidence than a present one.
- **(ii) Keep the ordering, drop the rationale to "reserved, highest-touch by design".** Least
  claimed; admits the ordering is now a reservation rather than an observation.
- **(iii) Re-order the silos.** Rejected by the agent as out of scope and disproportionate — CONST-04
  is Tier-1 and its blast radius is "every script, spec, and diagram references the numbered paths".
  Recorded only so the null-of-the-null is visible.

## Gate 2 — PLAN (Migration + Regression)

- **Removal-only; no migration.** Existing dailies in any deployed vault are untouched.
- **Lockstep deploy-target deletion is mandatory** (ADR-0028's R8 scenario): `reconcile` iterates
  *notes*, so `~/bin/vault-daily-note.py` and `~/bin/vault-close-day.py` must be deleted from the host
  in the same apply, or they persist as ungoverned operational code invisible to drift detection.
- **CI:** `validate-scripts.sh` loses its daily sections; `fleet-pytest` loses the daily cases in
  `tests/test_fleet.py`; fleet-count assertions drop 15 → 13. All other jobs must stay green
  (`openspec validate --all --strict`, constitution-lint, vocabulary-lint, spec-lint,
  naming-validator, md-lint, link-check, adr-count-lint, scope-review).
- **`adr-count-lint`:** ADR-0032 lands → README/tree ADR counts increment 31 → 32.
- **Mirror:** the live vault is a deployed instance — script notes, mold, runbook, schema, and
  `config.defaults.env` mirror down; `tools/template-parity.py` proves completeness. **The live
  `.claude/settings.json` is operator-applied** (agent is denied `Edit(/.claude/**)` and the path is
  sandbox-denied) — the exact diff is supplied, the operator pastes it.
- **Rollback:** revert the single PR; restore the two deploy targets by re-rendering from the restored
  notes.

## Archive mechanism — a named, deliberate override (operator-approved 2026-07-19)

**This change is archived with `openspec archive --skip-specs`; the four spec files are applied by
hand in the same commit.** That is a deliberate override of the archiver's automatic path, recorded
here rather than performed quietly.

**Why the tool cannot do it.** OpenSpec 1.6.0 has no way to express an *intentional scenario
removal*. Its `MODIFIED` path calls `findMissingCurrentScenarios`, which is strictly **name**-matched
(`specs-apply.js:298`) and aborts if any current scenario is absent from the incoming block.
`REMOVED` + `ADDED` of the same Requirement name would work in the applier (order is
RENAMED→REMOVED→MODIFIED→ADDED) but is rejected by the **validator**: *"Requirement present in both
ADDED and REMOVED"*. Renaming the Requirements is the third exit and is refused here because
`Script Inventory` is cited by ADR-0020, ADR-0028, ADR-0032 and `CHANGELOG.md` — renaming orphans
historical references.

**The four scenarios removed, each because its subject ceases to exist:**

| Scenario | Requirement | Subject deleted |
|---|---|---|
| `A created daily note is committed by its creator` | One Mutation, One Commit (INV-2) | `vault-daily-note.py` |
| `A close seals with a scoped commit, never a sweep` | One Mutation, One Commit (INV-2) | `vault-close-day.py` |
| `Daily note creator is idempotent` | Script Inventory | `vault-daily-note.py` |
| `The closed test is YAML-typed` | Shared Fleet Plumbing (vault_lib) | `vault_lib.is_closed()` |

All four are inherently daily-named; retaining them would leave the spec asserting the behaviour of
scripts that no longer exist — the exact dishonesty ADR-0028 set out to end ("the spec afterwards
describes the system that exists").

**The guard is sound and is not being disparaged.** It caught a real defect in this very change: the
first `vault-structure` delta silently dropped **five** scenarios that were never meant to be
touched. The override is scoped to the four rows above and to nothing else.

**Compensating verification** (the guard's purpose is met by other means):
- The hand-applied spec edits land in the same commit and are fully visible in the diff.
- `openspec validate --all --strict` must pass on the **result**.
- A post-apply scenario census is pasted in Gate 3: every Requirement's scenario set before and
  after, so that any drop beyond the four declared rows is visible as a number, not a claim.

## Gate 3 — EXECUTE + REGRESSION-TEST

*(To be completed on the branch — transcripts pasted here per ADR-0031.)*

- [ ] `openspec validate retire-daily-close-cycle --strict` green
- [ ] `openspec validate --all --strict` green
- [ ] full local `pytest` green after daily cases removed
- [ ] `.github/scripts/validate-scripts.sh` green in the sandbox harness
- [ ] `tools/template-parity.py` green after mirror
- [ ] CI green on the PR

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [x] Blast radius re-checked — and the re-check **found a gap in the Gate-1 sweep itself**: the
      original pattern omitted `daily-mold-blank`, hiding `openspec/specs/naming-rules/spec.md`
      (`protects: [INV-11]`), which used that mold as its worked example. Corrected in Gate 1 above
      rather than silently patched; the delta set grew from three protected specs to **four**.
- [x] **CONST-04 rationale decision recorded: option (ii)** — keep the ordering, drop the
      daily-based rationale. `10-Logbook/` is restated as "highest-touch by design / reserved",
      **explicitly a reservation rather than an observation**, so the spec does not assert a
      justification that is not yet true (operator, 2026-07-19).
- [x] Consequences explicitly accepted (ADR-0032 "Consequence / sacrifice"): the vault loses its
      dated capture surface and total-disposition at day granularity — a real safety net, given up
      because it was stretched under an empty stage; RC-1a loses its only working reference
      implementation, **extracted first** to
      `30-Sites/determinism-failure-modes-claude/sidecar-typed-slot-pattern.md`; `10-Logbook/`
      becomes an empty reserved silo; fleet 15 → 13, molds 4 → 3.
- [x] Human sign-off recorded: **Approved — Keith Nielsen, 2026-07-19** (operator reviewed the
      proposal and ADR-0032 and replied `Approved`; recorded by Claude Code per the standing Gate-4
      ritual — the human decision is the operator's reply, the agent only transcribes it)
