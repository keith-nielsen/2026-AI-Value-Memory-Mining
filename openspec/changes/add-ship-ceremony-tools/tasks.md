<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks: add-ship-ceremony-tools

## 1. Probe (pre-implementation)
- [x] 1.1 Re-read the governing corpus: `failure-modes-root-cause-synthesis` (RC-2a/RC-3a),
      the F10 entry (7 false starts) and F21 entry (5 stumbles, per-layer fix) in the live
      vault's Site, the maintenance spec's Release-object requirement, CONTRIBUTING's ship
      section
- [x] 1.2 Read the deployed INV-14 guard: it text-matches `git push` / `gh release create` in
      the command the agent runs → a wrapper executing them internally would bypass the ASK
      rail → the driver's core contract is EMIT, never execute, outward commands
- [x] 1.3 Confirm the `template-parity` precedent (repo-only tool, +Requirement in
      `maintenance`, conforming amendment, no ADR) and the in-flight `add-telemetry-segment`
      change (DEFERRED; no header collision)

## 2. Implementation
- [x] 2.1 `tools/ship-release.py` — re-entrant guarded state machine (ancestor proof →
      CHANGELOG proof → per-layer reads → local tag + re-read verify → emit push → verify →
      emit release create → verify → parity tally with denominators); exit 0/1/2/3
- [x] 2.2 `tools/pr-state.py` — per-layer reporter (pr-state-machine / branch /
      check-aggregation / workflow-run / event-payload advisory), LAYERS-DISAGREE signal,
      HAZARD lines for deleted base + stale head oid; exit 0/3
- [x] 2.3 `tests/test_ceremony_tools.py` — 11 cases; real git against a local bare origin,
      stub `gh` serving reads from fixture files
- [x] 2.4 Spec delta: `maintenance` +2 ADDED Requirements, 7 scenarios
- [x] 2.5 CONTRIBUTING.md ship section re-anchored on the driver
- [x] 2.6 AGENTS.md: ship + mirror bullets point at the driver; +1 per-layer reporter bullet
- [x] 2.7 README.md `tools/` tree line names the three tools
- [x] 2.8 CHANGELOG.md `[Unreleased]` entry

## 3. Verification (transcripts — ADR-0031)

- [x] 3.1 New test module green:

```
$ python3 -m pytest tests/test_ceremony_tools.py -q
...........                                                              [100%]
11 passed in 1.80s
```

- [x] 3.2 Change validates strict:

```
$ npx openspec validate add-ship-ceremony-tools --strict
Change 'add-ship-ceremony-tools' is valid
```

- [x] 3.3 Full local regression:

```
$ npx openspec validate --all --strict
- Validating...
✓ spec/access-control
✓ change/add-ship-ceremony-tools
✓ change/add-telemetry-segment
✓ spec/agent-integration
✓ spec/maintenance
✓ spec/naming-rules
✓ spec/value-pipeline
✓ spec/vault-structure
Totals: 8 passed, 0 failed (8 items)

$ python3 -m pytest -q
........................................................                 [100%]
56 passed in 8.38s
```
- [ ] 3.4 PR CI green (scope-review PASS on the declared block)

## 4. Ceremony
- [ ] 4.1 Gate-4 re-check: re-run the Gate-1 sweep on the final branch and diff against the
      proposal (transcript recorded here)
- [ ] 4.2 Gate-4 human sign-off (operator reviews proposal.md, replies Approved; recorded in
      proposal.md)
- [ ] 4.3 Merge; archive (batch-archive-in-merge-order relative to `add-telemetry-segment` if it
      ever activates — it is DEFERRED and stays in place)
- [ ] 4.4 Tag v0.1.30 + GitHub Release + parity verify — **dogfood: walk it with
      `tools/ship-release.py v0.1.30`** (each emitted outward command runs through the INV-14
      ASK as designed); nothing to mirror (repo-only tools), record `template-parity` as n/a
