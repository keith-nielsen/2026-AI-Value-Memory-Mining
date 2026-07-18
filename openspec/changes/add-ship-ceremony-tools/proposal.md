<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: add-ship-ceremony-tools

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** two Requirements ("Ship-Release Driver" and "PR State Is Reported Per Layer"). **No
principle is overridden or weakened**; both tools are additive and repo-only, and the driver is
designed so the INV-14 outbound ASK rail keeps firing (it never executes an outward mutation
itself). Conforming amendment per repo precedent (`add-template-parity-check` is the direct
model; like it, this ships **without a new ADR**).
**Tier:** 0-adjacent (mechanizes the already-governed ship ceremony — the "GitHub Release Object
Per Version Tag" requirement — and the F21 per-layer discipline; §5 AI hard-stop honored —
surfaced for explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-18)
**Date:** 2026-07-18

---

## Why

This is **item 3 of the failure-modes fix program** (RC-2a + RC-3a in the live vault's
`failure-modes-root-cause-synthesis`): move GitHub knowledge out of agent recall and into tools,
because hazards stored in memory are demonstrably not consulted at the point of action (F21 re-hit
two hazards already written in loaded memory; F10's tag-before-merge was documented the turn
before it happened). Two builds:

- **`tools/ship-release.py`** — the ship ceremony (CONTRIBUTING "Shipping a version") currently
  costs a multi-turn ad-hoc `git`/`gh` composition per release; F10 recorded **seven false starts**
  in one ship, including a tag on the wrong commit reaching the remote and a guard mis-reporting
  its own failure cause. The driver makes every documented hazard a refusing guard clause:
  merge-ancestor proof before any tag exists, CHANGELOG-entry proof, stale-tag refusal that names
  the true cause with both commits, post-mutation verification per layer, and a closing
  tag↔Release parity tally with denominators. It is re-entrant (state re-derived from the world
  each run) and — the load-bearing design constraint — **never executes an outward mutation**: the
  INV-14 guard ASK-gates `git push`/`gh release create` by text-matching the command the agent
  runs, so a wrapper that ran them internally would silently bypass the rail. The driver emits the
  next single gated command and exits `2`; the caller runs it visibly and re-invokes.
- **`tools/pr-state.py`** — F21's five stumbles shared one root: treating GitHub as a single
  oracle when it is six layers that disagree while all being correct. The reporter prints PR state
  with the answering layer named on every line, flags layer disagreement as a `LAYERS-DISAGREE:`
  signal rather than confusion, prints the irreversible-hazard warnings (deleted base branch →
  retarget stacked children first) at the point of observation, and serves as the designated
  post-mutation re-read (a GraphQL mutation can fail silently where REST succeeds).

Both are also the program's biggest token-wastage reducers: a ship that cost N stumbling turns
becomes guarded single invocations plus the human gates.

## What Changes

- **`maintenance` spec:** +2 ADDED Requirements (7 scenarios) — the driver's guard/refusal/emit
  contract and the reporter's per-layer contract.
- **`tools/ship-release.py`** (new): the driver. Exit `0` ship complete · `1` refused · `2` next
  gated command emitted · `3` blocked.
- **`tools/pr-state.py`** (new): the reporter. Exit `0` report delivered · `3` blocked.
- **`tests/test_ceremony_tools.py`** (new): 11 subprocess-driven cases over a real work repo +
  local bare origin (all git layers real, offline); only `gh` is stubbed, and only for reads —
  the tools never execute `gh` mutations.
- **`CONTRIBUTING.md`:** the "Shipping a version" numbered ceremony is re-anchored on the driver
  (run it; run each emitted command through the gated channel; re-run until the parity tally).
- **`AGENTS.md`:** the ship bullet and the mirror bullet point at the driver; +1 bullet for the
  per-layer reporter as the first move on any confusing PR state and the mandatory re-read after
  a `gh` mutation.
- **`README.md`:** the `tools/` tree line names all three tools.
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Deliberately out of scope.** (a) No change to the INV-14 guard or its 3 deployed homes — the
driver is designed around the existing rail, not into it. (b) No CI job — both tools need an
authenticated `gh` and a live remote; CI has neither. (c) The close-cycle driver respec (program
item 4, RC-1a) is separate — this change is the two GitHub wrappers only. (d) No vault-template
change: the deployed vault is standalone (F15) and does not ship these repo-ceremony tools.

**External dependency being adopted: NONE.** Two stdlib-only Python files that shell out to the
`git`/`gh` binaries already required by the ceremony they mechanize.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> The `maintenance` spec protects INV-2 (one mutation, one commit), INV-3 (Layer-0 literate
> scripts; drift detected, never auto-fixed) and INV-6 (the deterministic fleet is offline).
> These tools join the spec's existing repo-only ceremony/maintenance surface (the
> `template-parity` precedent): they are NOT fleet scripts, NOT literate notes, NOT deployed to
> the vault, and the Release-object requirement already carves out ceremony actions as
> legitimately networked — so INV-6 is not engaged and INV-3's note→host contract is untouched.
> INV-2 is untouched (the driver's only mutation is a local git tag; it makes no commits). The
> real hazard a naive build would introduce is INV-14 erosion — a wrapper executing `git push` /
> `gh release create` internally would slip past the text-matching ASK guard — and the design
> makes the opposite choice its core contract: outward commands are emitted, never executed.

**Blast radius — enumerated by transcript (ADR-0031), not composed.** Sweep for the new tool
names across the whole repo (proves no existing artifact references or collides with them):

```
$ grep -rn "ship-release\|pr-state" openspec/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md --include='*' | grep -v "changes/add-ship-ceremony-tools/"
$ echo "exit=$?"
exit=1
```

Zero hits (exit 1 = no matches) — the names are fresh; no artifact outside this change references
them. Sweep for the surfaces that describe the ship ceremony these tools mechanize:

```
$ grep -rln "gh release create" openspec/specs/ vault-template/ docs/ .github/ README.md AGENTS.md CONTRIBUTING.md
vault-template/99-Operations/scripts/outbound-publish-guard-script.md
openspec/specs/access-control/spec.md
openspec/specs/maintenance/spec.md
CONTRIBUTING.md
AGENTS.md
```

Disposition of every hit:

- `vault-template/99-Operations/scripts/outbound-publish-guard-script.md` — **not edited.** The
  hit is the guard describing its own ASK trigger; the driver is designed to keep routing through
  it unchanged.
- `openspec/specs/access-control/spec.md` — **not edited.** The hit is the guard's
  effective-target scenario (ASK on a sibling-repo `gh release create`); behavior unchanged.
- `openspec/specs/maintenance/spec.md` — **edited via this change's spec delta at archive time**
  (+2 ADDED Requirements; the existing Release-object requirement is untouched).
- `CONTRIBUTING.md` — **edited here** (ship section re-anchored on the driver).
- `AGENTS.md` — **edited here** (ship + mirror bullets point at the driver; +1 reporter bullet).

Change surfaces (each declared in the PR scope block):

- [x] `openspec/changes/add-ship-ceremony-tools/` — this proposal + tasks + spec delta
- [x] `tools/ship-release.py` — new
- [x] `tools/pr-state.py` — new
- [x] `tests/test_ceremony_tools.py` — new
- [x] `CONTRIBUTING.md` — ship section
- [x] `AGENTS.md` — 3 bullets
- [x] `README.md` — `tools/` tree line
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `openspec/adr/` + README/tree ADR counts — **no change** (conforming amendment, no ADR;
      the adr-count guard is untouched)
- [ ] `.github/workflows/ci.yml` — **no change** (no CI job; the new test module is collected by
      the existing fleet-pytest job automatically)
- [ ] `vault-template/` — **no change** (repo-only tools; nothing to mirror, F15 standalone
      premise holds)

## Gate 2 — PLAN (Migration + Regression)

- Additive: no migration, no renames, no lockstep mirror step (repo-only tools).
- **Coexistence with the in-flight `add-telemetry-segment` change** (also MODIFIES
  `maintenance`, and is explicitly DEFERRED): this change only ADDS Requirements with fresh
  headers — no header collision; honor batch-archive-in-merge-order at archive time and verify no
  duplicate `### Requirement:` headers, `openspec validate --all --strict` clean.
- Regression: all existing CI jobs stay green (`openspec validate --all --strict`,
  constitution-lint, vocabulary-lint, spec-lint, naming-validator, md-lint, link-check,
  validate-scripts, adr-count-lint, scope-review, fleet-pytest — the last collects
  `tests/test_ceremony_tools.py`).
- Rollback: revert the single PR (two tools + one test module + doc lines + spec delta); no
  deployed state to unwind.

## Gate 3 — EXECUTE + REGRESSION-TEST

- `tests/test_ceremony_tools.py` — **11 passed** locally (transcript in tasks.md §3): the full
  ceremony walk (guards → local tag → emitted push → verified remote tag → emitted release →
  parity `0` missing), unmerged-target refusal with no tag left behind, missing-CHANGELOG
  refusal, stale-local-tag refusal naming both commits (and NOT mis-reporting "not merged"),
  remote-tag-wrong-commit refusal, parity-gap detection; reporter layer coverage,
  LAYERS-DISAGREE, deleted-base HAZARD, blocked-PR-not-found.
- `openspec validate add-ship-ceremony-tools --strict` green (transcript in tasks.md §3).
- Full local `pytest` green; CI green on the PR = Gate 3 complete.

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [ ] Blast radius re-checked against the final diff by re-running the Gate-1 transcript and
      diffing (recorded in tasks.md §4 before merge)
- [ ] Consequences explicitly accepted (two repo-owned stdlib ceremony tools to maintain; the
      ship ceremony's documented procedure moves from prose into a guarded driver whose refusals
      operators will now encounter; **zero external runtime dependencies**)
- [ ] Human sign-off recorded: pending
