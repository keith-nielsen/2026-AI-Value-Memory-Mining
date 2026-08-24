<!-- SPDX-License-Identifier: Apache-2.0 -->

## ADDED Requirements

### Requirement: The Linter Refuses An Unresolvable Memory-Store Path

Where a deployment carries a harness settings file declaring a working-memory store directory, the
vault linter SHALL resolve the declared path and SHALL refuse where it does not resolve to a directory
inside the vault root.

The seed the framework ships carries a placeholder path that cannot exist. A placeholder is a comment
asking an installer to act, and this repository's standing finding is that a rule which cannot refuse
does not bind — so the seed SHALL be accompanied by the check that refuses it, and the check is what
makes shipping the placeholder verbatim a detected condition rather than a silent one.

The linter SHALL refuse in three distinct cases, and SHALL name which one it found: the declared path
does not exist; it exists but is not a directory; or it resolves outside the vault root. The third is
the case that matters most and looks least like an error — a path pointing at another vault's store,
or at a user-global directory, resolves perfectly well and silently merges two deployments' memory.

The linter SHALL treat the absence of the settings file, and the absence of the declaration within it,
as conformant. The store is optional; a deployment that does not use one is not defective, and a check
that demanded the file would convert an optional convenience into a requirement the specification does
not make.

The linter SHALL NOT read, validate or report on the contents of the store directory. Its jurisdiction
ends at whether the declared path is a real directory in this vault; the notes inside are harness-owned
and ungoverned by ADR-0032.

The linter SHALL NOT modify the settings file. Repairing the path requires knowing the operator's
intended vault root, which is exactly the judgement the refusal exists to hand back.

#### Scenario: The shipped placeholder was never edited
- **WHEN** the linter runs against a deployment whose declared store path is the shipped placeholder
- **THEN** it refuses, naming the unresolved path and the case it matched

#### Scenario: The declared path points outside the vault
- **WHEN** the declared path resolves to a directory outside the vault root
- **THEN** it refuses, naming the escape distinctly from a non-existent path

#### Scenario: A correctly configured store
- **WHEN** the declared path resolves to a directory inside the vault root
- **THEN** the linter passes, and reports nothing about the notes inside it

#### Scenario: No store is configured
- **WHEN** the settings file is absent, or carries no store declaration
- **THEN** the linter passes — the store is optional
