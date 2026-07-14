<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: GitHub Release Object Per Version Tag

Every published version tag `vX.Y.Z` SHALL have a corresponding GitHub **Release object**, created as a
mandatory, verified step of the ship ceremony. A git tag and a GitHub Release are distinct objects:
pushing a tag does NOT create a Release, and the "latest release" surfaces (the repository Releases page
and any profile mirror) reflect the newest Release object, not the newest tag. The ship ceremony
therefore SHALL, after a change is merged to `main`:

- create an annotated tag `vX.Y.Z`;
- create the GitHub Release for that tag (`gh release create <tag> --verify-tag --latest`) with a title
  and notes derived from the tag/CHANGELOG; and
- **verify parity** (`gh release view <tag>` resolves and is marked Latest) as an explicit ceremony
  step before the ship is considered complete.

Because release creation and verification are part of the same ceremony that cuts the tag, a tag can
never accumulate without its Release. This is a ceremony action (agent- or operator-run, gated by the
INV-14 outbound guard), **not** part of the deterministic offline script fleet — it legitimately calls
the authenticated `gh` CLI, so INV-6 (no network in the deterministic fleet) is not engaged. No CI job
performs a networked GitHub call to enforce parity; the guarantee is the mandatory verified ceremony
step.

#### Scenario: Shipping a version creates and verifies its Release
- **WHEN** a merged change is shipped as `vX.Y.Z`
- **THEN** the ceremony creates the annotated tag, creates the GitHub Release for it, and verifies with
  `gh release view vX.Y.Z` that the Release exists and is marked Latest before the ship is complete

#### Scenario: A tag without a Release is an incomplete ship
- **WHEN** a `vX.Y.Z` tag exists on the remote but `gh release view vX.Y.Z` does not resolve
- **THEN** the ship is not complete; the release-creation step is performed (backfilled) so tag/Release
  parity holds

#### Scenario: Release creation passes through the outbound hard stop
- **WHEN** the agent runs `gh release create` (or the tag push) during a ship
- **THEN** the INV-14 outbound guard raises the ASK hard stop, and the agent first presents an overview
  summary plus the absolute path to the governing `proposal.md`; the step proceeds only on explicit
  human approval
