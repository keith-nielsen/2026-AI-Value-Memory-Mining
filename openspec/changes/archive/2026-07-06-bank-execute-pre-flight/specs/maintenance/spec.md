<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Refine Executor Pre-Flight and Batch Isolation

The refine executor SHALL validate every approved proposal whole, before any write. It is the
sole automated writer of `40-Treasury/` (`bank-execute-script` → `~/bin/vault-refine-execute.py`),
and its pre-flight MUST cover:

- **Schema:** required fields present with correct types (`target_note`, `mode`, `insight_md`,
  `provenance_md`, `index_links`; `frontmatter` for `create`); unparseable JSON is a rejection,
  not a crash.
- **Containment:** the target resolves inside `40-Treasury/`; every index link resolves inside
  `40-Treasury/Catalog/`. Path escapes are rejected.
- **INV-11 boundary:** the target stem is a valid kebab slug.
- **INV-9 pre-action:** `create` SHALL NOT overwrite an existing note — a collision is a
  rejection; `append` requires the target to exist.
- **Vocabularies:** `grade` and `pillars` validate against the config SSOT (`GRADES`, `PILLARS`).
- **Link targets:** every named Catalog index file exists.

A proposal failing any check is REJECTed with all reasons printed and **no partial write** — the
note, the index links, and the proposal file are all untouched. Rejection is **batch-isolated**:
remaining proposals are still processed. A run with any rejection exits `1` (`EXIT_VIOLATION`,
fleet contract); a fully applied (or empty) batch exits `0`. Rejected proposals remain in
`_refine-approved/` for correction — the executor never deletes what it did not bank.

#### Scenario: A malformed proposal is rejected without stopping the batch
- **WHEN** the executor runs over a batch containing an unparseable or schema-incomplete proposal
  followed by a valid one
- **THEN** the bad proposal is REJECTed with reasons, nothing of it is written, and the valid
  proposal is still banked with its atomic commit; the run exits `1`

#### Scenario: Create never overwrites refined value
- **WHEN** a `create` proposal targets a note that already exists in `40-Treasury/`
- **THEN** the proposal is REJECTed (`INV-9`) and the existing note is byte-identical afterwards

#### Scenario: A missing Catalog target rejects the whole proposal pre-write
- **WHEN** a proposal names an `index_links` entry that does not exist
- **THEN** the proposal is REJECTed and the knowledge note is NOT created — no half-applied state

#### Scenario: A path escape is rejected
- **WHEN** a proposal's `target_note` resolves outside `40-Treasury/` (e.g. via `..`) or an index
  link resolves outside `40-Treasury/Catalog/`
- **THEN** the proposal is REJECTed with a containment reason and nothing is written
