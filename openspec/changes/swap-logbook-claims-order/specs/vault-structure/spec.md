<!-- SPDX-License-Identifier: Apache-2.0 -->
## MODIFIED Requirements

### Requirement: Folder Structure

The vault root SHALL contain exactly these numbered top-level folders, ordered by touch
frequency (ascending number = higher daily-touch frequency, daily logs at top per
CONST-04), zero-padded for correct lexicographic sort, gapped by 10s for insertion
headroom.

```
00-Docs/
  README.md
  examples/
10-Logbook/
  Daily/
  Reviews/
20-Claims/
  _refine-proposals/
  _refine-approved/
30-Sites/
40-Treasury/
  Catalog/
50-Mint/             (deferred — folder exists as placeholder)
60-Forge/            (deferred — folder exists as placeholder)
70-Tailings/
71-Spoil/
80-Crucible/         (deferred — folder exists as placeholder)
97-Molds/
  daily.md
  effort.md
  knowledge.md
  moc.md
98-Warehouse/
99-Operations/
  config.env
  requirements.txt
  scripts/
  hooks/
  schemas/
```

Reserved number bands (folders NOT created until needed): 81–89 (Crucible-adjacent),
90–96 (future system).

Rationale for the order: the daily note in `10-Logbook/Daily/` is the orienting surface
a user opens first each session, so it sorts to the top per CONST-04. `20-Claims/` is
the capture inbox (an unordered queue), and carries the refine gate
(`_refine-proposals/`, `_refine-approved/`).

#### Scenario: Folder tree is complete after Phase 0
- **WHEN** Phase 0 build completes
- **THEN** every directory in the structure above exists, including `20-Claims/_refine-proposals/`, `20-Claims/_refine-approved/`, `99-Operations/hooks/`, and `99-Operations/schemas/`

#### Scenario: Daily logs sort above the capture inbox
- **WHEN** the vault root is listed in any file explorer
- **THEN** `10-Logbook/` sorts above `20-Claims/`, placing the daily cockpit at the top (CONST-04)

#### Scenario: No pillar subfolders in Treasury
- **WHEN** the linter runs against `40-Treasury/`
- **THEN** it reports no subdirectories other than `Catalog/` (INV-12 enforced)
