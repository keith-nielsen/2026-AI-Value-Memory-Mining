## Context

ADR-0015 set the ≥3-token naming floor as convention now, mechanical enforcement later (deferred, gated
on family conformance). Some filenames can never conform because an external tool or universal
convention binds their exact name (`README.md`, `CLAUDE.md`, `.gitignore`, dailies, `*.example`, …). To
turn on mechanical ≥3-token/kebab rejection safely, the ruleset needs an exemption set first. This was
implemented in the live vault ahead of the ceremony (ratify-in-place); this record documents/ratifies it
and mirrors it into `vault-template/`.

## Goals / Non-Goals

**Goals:** a small, dependency-justified exemption set in the `naming-rules` SSOT + JSON mirror, honored
by the linter now, so the deferred enforcement is switch-on-safe. No name renamed.

**Non-Goals:** turning on mechanical ≥3-token rejection (still deferred per ADR-0015); exempting content
stems (grandfathering, not exemption, governs pre-existing sub-3 names); governing `.obsidian/` (out of
scope via `.gitignore`).

## Decisions

- **Additive under existing INV-11 — no new invariant, no rename.** The exemption gate only *narrows*
  what the future enforcement would reject; base safety + kebab-slug rules unchanged.
- **Match on basename, not path.** `is_exempt(filename)` compares the filename against `exempt_names`
  (exact) and `exempt_globs` (basename patterns). Path-shaped globs are intentionally absent: they
  wouldn't match a basename, and the one candidate (`.obsidian/*.json`) is handled by `.gitignore`
  instead. (Dead path-glob caught + removed during implementation.)
- **Dependency-justified, minimal list.** Each entry names what depends on the exact string
  (harness auto-load, git, config sourcing, daily-notes/close pipeline, GitHub/SPDX convention,
  `*.example` setup idiom) — documented in `docs/naming-exemptions-rationale.md`.
- **Enforcement stays deferred (ADR-0015).** The ≥3-token/kebab rejection is wired but staged/commented;
  only the exemption *honoring* is active, so switching rejection on later cannot wrongly block a
  tool-mandated name.

## Risks / Trade-offs

- **Maintenance:** new tool-mandated filenames must be added deliberately (fail-closed toward stricter
  naming — a missing exemption over-rejects rather than under-rejects, surfacing loudly at enforcement).
- **Scope discipline:** the list must stay minimal and dependency-justified, not a backdoor to dodge the
  ≥3-token floor for ordinary content (guarded by the rationale doc requirement).
