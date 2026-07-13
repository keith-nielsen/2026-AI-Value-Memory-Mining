<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0026: Relocate the ceremony template out of the change tree; adopt OpenSpec 1.6.0

- **Status:** Accepted (Gate-4, 2026-07-13; operator-approved in session)
- **Date:** 2026-07-13
- **Change:** `relocate-override-template-openspec-16` (`constitution-override`, procedural — touches the
  `protects:`-tagged `maintenance` spec [`protects: [INV-2, INV-3, INV-6]`] and pointer text in
  `constitution.md`; **no Tier-0/1 element overridden**)
- **Relates:** supersedes Dependabot PR #18 (`@fission-ai/openspec 1.4.1 → 1.6.0`); the `1.4.1` pin +
  weekly canary were established in PR #17 (ADR context for the version-watch)

## Context

The constitution-override ceremony template — a blank scaffold with `<angle-bracket>` placeholders —
lived at `openspec/changes/templates/constitution-override/proposal.md`, **inside the `changes/` tree the
OpenSpec validator scans.** OpenSpec `1.6.0` hardened change-discovery so that `validate --all` now
enumerates that nested folder as a change (`change/templates`) and fails it against the pre-existing rule
*"a change must have ≥1 delta."* A template has no deltas, so `1.6.0` (and `1.4.1 --strict` when the
template was named explicitly) rejects it. This blocked adopting `1.6.0`: PR #18's `OpenSpec validate`
check went red. The version pin plus weekly `@latest` canary — the compatibility gate — worked exactly as
designed, catching the forward-incompatibility before it reached `main`. Root cause: a non-change artifact
stored where the validator treats every folder as a change — latent debt that `1.4.1`'s lenient discovery
had masked.

## Decision

Move the template out of the scanned tree to `openspec/templates/constitution-override/proposal.md`
(OpenSpec scans only `changes/` and `specs/`; `openspec/templates/` is invisible to it — verified
empirically: `validate --all --strict` under `1.6.0` returns 7 passed / 0 failed with the template no
longer enumerated). Repoint all 7 references and the CI `test -f` guard in lockstep. Advance the
`@fission-ai/openspec` pin `1.4.1 → 1.6.0` (bundled into this change; supersedes #18). Codify the rule as
a new `maintenance` requirement so templates cannot drift back into the change tree.

## Options considered

- **(a) Relocate the template + adopt 1.6.0 + codify the rule (chosen).** Correct regardless of version —
  templates do not belong in `changes/`. Unblocks the pin advance; prevents recurrence via a spec
  requirement + CI assertion. Cost: 7 references + one CI guard path updated in lockstep.
- **(b) Give the template a dummy spec delta so it validates.** Rejected: it would surface as a permanent
  phantom pending-change in `openspec change list` and is semantically false (a template is not a change).
- **(c) Stay pinned at 1.4.1 indefinitely.** Rejected: zero work now, but the debt persists and grows
  (`1.4.1 --strict` already rejects the template), and the repo falls behind the tool it depends on.
- **(d) An OpenSpec ignore mechanism.** No `.openspecignore`-style config exists in the repo; not available.

## Consequence / sacrifice

The repo adopts OpenSpec `1.6.0` and its stricter default discovery; validation stays reproducible via the
pin, and the weekly canary continues to flag future incompatibilities. The ceremony template now lives at
`openspec/templates/constitution-override/proposal.md`, codified as residing outside the change tree. The
ceremony, its four gates, and every constitutional principle are **unchanged** — only the file that
scaffolds a proposal moved, with all references and the CI guard updated together. **Sacrifice:** none
material; this removes an inconsistency rather than trading anything away.
