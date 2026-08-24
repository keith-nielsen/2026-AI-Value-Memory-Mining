<!-- SPDX-License-Identifier: Apache-2.0 -->

## MODIFIED Requirements

### Requirement: Folder Structure

The vault SHALL use the numbered folder structure below. `10-Logbook/` retains `Daily/` and
`Reviews/` as **working areas**; the framework no longer generates a dated note format for either
(ADR-0032).

```
00-Docs/
  README.md
  examples/
10-Logbook/
  Daily/
  Reviews/
  vmm-working-memory/        # optional; harness-owned, git-ignored
20-Claims/
  _refine-proposals/
  _refine-approved/
30-Sites/
40-Treasury/
  Catalog/
70-Tailings/
71-Spoil/
96-Runbooks/
97-Molds/
  effort-mold-blank.md
  knowledge-mold-blank.md
  index-mold-blank.md
98-Warehouse/
99-Operations/
  hooks/
  schemas/
  scripts/
```

Rationale for the order: `10-Logbook/` is the **highest-touch silo by design** and sorts to the top
per CONST-04. The framework does not itself generate its contents (ADR-0032 retired the daily note);
the silo is **reserved**, and the ordering is a reservation rather than a present observation —
stated as such rather than justified by an artifact that no longer exists. `20-Claims/` is the
capture inbox (an unordered queue), and carries the refine gate (`_refine-proposals/`,
`_refine-approved/`).

The three `97-Molds/` files are named on the `silo-section-descriptor` convention
(`<note-type>-mold-blank.md`) so each mold is self-identifying in any flat / search /
migrated view and never collides with content (e.g. the Catalog `<pillar>-domain-index.md` notes).

`96-Runbooks/` holds **runbooks** — literate, schema-validated procedure notes (spec-as-code)
for repeatable, error-prone operations (e.g. `provenance-seal-runbook`). It is operational
machinery (Layer-0-adjacent, like `97-Molds`/`99-Operations`), sorts in the infra region per
CONST-04, and conforms to the numbering scheme — it does not override it.

#### Scenario: Folder tree is complete after Phase 0
- **WHEN** Phase 0 build completes
- **THEN** every directory in the structure above exists, including `20-Claims/_refine-proposals/`, `20-Claims/_refine-approved/`, `99-Operations/hooks/`, and `99-Operations/schemas/`

#### Scenario: Logbook sorts above the capture inbox
- **WHEN** the vault root is listed in any file explorer
- **THEN** `10-Logbook/` sorts above `20-Claims/` per CONST-04 — the touch-frequency ordering is
  unchanged, and no claim is made about what occupies the silo

An agent harness MAY maintain a working-memory store under `10-Logbook/`; the conventional path is
`10-Logbook/vmm-working-memory/`. Where such a store is present it SHALL be git-ignored, and the
framework SHALL NOT generate, read, validate or police its contents. This follows ADR-0032: the
framework owns no artifact in the silo, and a store the framework does not own is a store it does not
govern. The directory is named in the structure above so that a deployment which has one is not
reading an undeclared folder, never to require that a deployment have one.

The store SHALL NOT be tracked. Its contents are machine-local and rewritten many times per session,
so tracking produces either noise commits or a permanently dirty tree, and an INV-14 vault has no
remote for tracking to reach — durability comes from the filesystem backup, not from git.

#### Scenario: Runbooks sort in the infra region
- **WHEN** the vault root is listed in any file explorer
- **THEN** `96-Runbooks/` sorts below `80-Crucible/` and above `97-Molds/`, keeping operational procedures in the low-touch infra band (CONST-04 upheld)

#### Scenario: No pillar subfolders in Treasury
- **WHEN** the linter runs against `40-Treasury/`
- **THEN** it reports no subdirectories other than `Catalog/` (INV-12 enforced)

#### Scenario: Molds are self-identifying folder-notes
- **WHEN** the three `97-Molds/` files are listed flat (graph, search, or migration)
- **THEN** each stem reads `<note-type>-mold-blank` and none collides with a content stem such as `index`

#### Scenario: Warehouse shelves take human-friendly names
- **WHEN** a Warehouse shelf folder (e.g. `Books`, `Pictures`) is created or listed
- **THEN** it must only satisfy the universal path-component rule (cross-platform-safe characters, no reserved device names); the kebab-case / ≥3-token convention does not apply to it, because that convention is scoped to `.md` stems and to `30-Sites/`/`70-Tailings/` effort folders and `40-Treasury/` stems

#### Scenario: A harness working-memory store is present
- **WHEN** a deployment carries `10-Logbook/vmm-working-memory/`
- **THEN** the directory is git-ignored, and no framework script generates, validates or reports on
  the notes inside it

#### Scenario: No harness working-memory store exists
- **WHEN** a deployment carries no such directory
- **THEN** the vault is conformant — the store is optional and its absence is not a finding
