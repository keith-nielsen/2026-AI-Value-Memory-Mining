<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Governance Tooling Is Pinned and Ceremony Templates Live Outside the Change Tree

The OpenSpec CLI (`@fission-ai/openspec`) SHALL be pinned to an exact version in `package.json` so that
`openspec validate` is reproducible across contributors and CI. A weekly canary MAY validate the corpus
against `@latest` to surface incompatibilities before the pin advances.

Ceremony scaffolds — blank templates such as the constitution-override proposal template — SHALL live
**outside** `openspec/changes/` and `openspec/specs/` (the directories the validator scans), because a
template has no spec deltas and the validator treats every folder under `changes/` as a change. The
constitution-override ceremony template SHALL exist at `openspec/templates/constitution-override/proposal.md`,
and CI SHALL assert its presence at that path.

#### Scenario: The pinned CLI makes validation reproducible
- **WHEN** a contributor or CI runs `openspec validate --all --strict` after `npm install`
- **THEN** the `@fission-ai/openspec` version resolved is exactly the one pinned in `package.json`
- **THEN** the pin advances only through a change that re-proves the corpus validates green under the new version

#### Scenario: A ceremony template is not enumerated as a change
- **WHEN** `openspec validate --all` runs against the repository
- **THEN** the constitution-override template at `openspec/templates/constitution-override/proposal.md` is
  NOT enumerated as a change and cannot fail the "change must have ≥1 delta" rule
- **THEN** no blank scaffold resides under `openspec/changes/`

#### Scenario: CI asserts the ceremony template exists at its fixed path
- **WHEN** the constitution-lint CI job runs
- **THEN** it fails if `openspec/templates/constitution-override/proposal.md` is absent
- **THEN** every reference to the template across specs, docs, and workflows points at that same path
