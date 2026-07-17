<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Catalog Linking Is Idempotent

When the refine executor banks a proposal, it SHALL append a Catalog index link
(`- [[<stem>]]`) to an `index_links` target only if that index does not already carry the link.
`create` mode is unaffected (a new note is in no index yet); `append` mode extends a note that is
usually already catalogued, so an unconditional write would duplicate the note's existing bullet.
Idempotent linking lets `append` extend a note without polluting its Catalog index, while a
genuinely new index named in `index_links` is still linked. INV-12 reachability is preserved: every
banked note remains reachable via ≥1 Catalog index.

#### Scenario: Appending to an already-catalogued note does not duplicate its link
- **WHEN** an `append` proposal names an `index_links` index that already contains `- [[<stem>]]`
- **THEN** the executor extends the note and leaves that index unchanged — the bullet appears once,
  not twice — and the bank still produces its one atomic commit

#### Scenario: A new index is still linked
- **WHEN** a proposal names an `index_links` index that does NOT yet contain `- [[<stem>]]`
- **THEN** the executor appends `- [[<stem>]]` to that index, so the note is reachable from it
