<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: ship-release-operator-steps

## Why

Item 37 (`deny-irreversible-outbound`) made the INV-14 outbound guard **hard-DENY** irreversible
outbound — a version-tag push, a release create — on the agent's channel: those are operator-only.
But `ship-release.py` still emitted its two irreversible steps via a bare `_emit_next`, whose prose
told the agent to "run this through the normal gated channel." Under item 37 the agent now hits the
DENY there and must recognise, mid-ceremony, that the step is operator-only and hand it over by hand —
a rough edge, and exactly the kind of ad-hoc manual handoff where relay drift (F43) and paste
mangling (F44) happen.

`pr-flow.py` already solved this for its operator steps: it writes a self-guarding `next.sh` and emits
the item-39 copy-whole relay block the agent copies verbatim (byte-checked by the item-40 Stop hook).
Item 41 gives ship-release the same clean handoff — and does it by **extracting** the shared machinery
into one module both drivers import, rather than duplicating ~50 lines into ship-release. A second copy
of the saved-plan / relay-block / emission-record format would fork the very bytes the outbound guard
and the relay-conformance hook compare against — the class-9 defect (a fork with no merge).

## What Changes

- **New shared module `tools/driver_handoff.py`.** The driver-agnostic operator-handoff machinery
  moves here: `PLAN_TTL_SECONDS`, `saved_plan_path`, `emission_record_path`, `relay_line_path`,
  `write_emission_record`, `discard_saved_plan`, `plan_history_suffix`, `write_saved_plan` (the
  saved-plan skeleton), and `emit_operator_handoff` (the `START COPY`/`END COPY` block + the
  `relay-line.txt` sidecar). Sibling-imported the way `gh_read.py` is.
- **`pr-flow.py` imports it.** Its moved functions become thin adapters that inject pr-flow's globals
  (`BODY_FILE`, `PR_NUMBER`) and its own pieces — the `--assert-preconditions` line and the
  `--after-mutation` verify tail — so every existing call site and test is unchanged. Behaviour is
  byte-preserved (the whole suite stays green).
- **`ship-release.py` emits operator handoffs.** Its `_emit_next` now writes a `next.sh` (with a
  ship-release re-invocation verify tail, which re-derives release state) and prints the copy-whole
  relay block, for both the tag-push and release-create steps. The raw command is still shown on a
  `NEXT:` line (the operator may run it directly, and the ceremony walk still reads it). Its old
  dynamic `pr-flow.py` import for the emission record is dropped in favour of the shared module.

## Impact

- No behaviour change to `pr-flow.py` (pure extraction; 514 → 514 tests green after it).
- ship-release's irreversible steps are now clean operator handoffs, byte-checked by the item-40 hook
  the same way pr-flow's are — completing the DENY-conversion item 37 deliberately deferred.
- No new control surface, no new refusal: the DENY that governs these already exists (item 37). This
  changes only how the ceremony HANDS the operator-only command over.
- `driver_handoff.py` is a repo tool, offline and stdlib-only (INV-6 posture): it writes files and
  formats strings; it spawns nothing.

## Constitutional impact

The delta MODIFIES one requirement in `openspec/specs/maintenance/spec.md`
(`protects: [INV-2, INV-3, INV-6]`), generalising "The Operator Handoff Is Emitted As A Copy-Whole
Block" from `pr-flow.py` to both lifecycle drivers via the shared module.

- **INV-6** — the new module is stdlib-only, offline, deterministic; untouched in substance.
- **INV-2 / INV-3** — untouched; no commit-structure or literate-note/render change.

Additive/refactor; engages none of the three, `overrides: none`. Surfaced for sign-off because it
touches a `protects:`-tagged spec.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: refactor + ADD-only (generalises an existing requirement; no invariant engaged)
```

## Verification

- The whole pre-existing suite stays green through the extraction (behaviour-preserving).
- New `tests/test_driver_handoff.py` drives the shared module directly: the saved-plan skeleton wraps
  the caller's verify tail, the assert line precedes the mutation, the empty-branch guard raises, the
  relay block equals its sidecar byte-for-byte, the history suffix takes an explicit target, and
  discard removes both plan and record.
- New ceremony test: ship-release emits a `next.sh` + `START COPY` block for the tag-push and
  release-create, the saved plan's VERIFY tail re-invokes ship-release (not pr-flow), the sidecar
  matches the block, and the raw `NEXT:` command is still runnable verbatim (the walk test's contract).
- Real-repo smoke: `ship-release.py v0.1.55` loads with the new import and refuses cleanly at the
  CHANGELOG guard.
- Full suite, `openspec validate --all --strict`, and markdownlint all clean.
