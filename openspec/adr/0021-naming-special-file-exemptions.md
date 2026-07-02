<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0021 — Special-file naming exemptions (extends INV-11 / ADR-0015)

**Status:** Accepted (Gate-4 sign-off: Keith Nielsen, 2026-07-02; drafted by Claude Code)
**Date:** 2026-07-02
**Relates:** `naming-rules` spec (INV-11) · `constitution.md` (Tier-0) · change `naming-special-file-exemptions` · **extends ADR-0015** (token-minimum naming) · ADR-0008 (frozen INV IDs — no new invariant)

## Context

ADR-0015 set the ≥3-token floor as convention-now / mechanical-enforcement-later (deferred, gated on
family conformance). A small set of filenames cannot conform because an external tool or universal
convention requires their exact name — `README.md`, `LICENSE`, `CLAUDE.md`, `AGENTS.md`, `MEMORY.md`,
the `.git*` files, `config.env`/`config.defaults.env`, `*.example`, and dailies (`YYYY-MM-DD`). Enabling
mechanical ≥3-token/kebab rejection without an exemption set would wrongly reject them and block commits.

## Decision

- **ADD a Special-File Exemptions requirement** to `naming-rules`: `exempt_names` (exact) + `exempt_globs`
  (basename patterns), matched on the filename via `is_exempt(filename)`; exempt files are skipped by the
  kebab/≥3-token rules. Editor state (`.obsidian/`) is out of scope via `.gitignore`, not exempted.
- **MODIFY the Language-Neutral Mirror requirement:** `naming-rules.json` gains `min_hyphen_tokens`,
  `exempt_names`, `exempt_globs`, `exempt_rationale_doc`.
- **Rationale doc:** `docs/naming-exemptions-rationale.md` justifies each entry by dependency class.
- **Enforcement stays deferred (ADR-0015):** the linter honors exemptions now; the ≥3-token/kebab
  rejection is staged/commented, so switching it on later is safe. No name renamed. No new invariant.

## Options considered

1. **No exemptions; rename tool-mandated files** — impossible (`CLAUDE.md`, `README.md`, dailies are bound by tools/conventions).
2. **Blanket-exempt anything sub-3-token** — rejected: a backdoor around the ≥3-token floor for ordinary content.
3. **Minimal, dependency-justified exemption set, basename-matched (chosen)** — narrow, auditable, makes deferred enforcement switch-on-safe.

## Consequences

- Mechanical ≥3-token/kebab enforcement can later be enabled without wrongly rejecting tool-mandated
  names; forks inherit the exemption set via the `vault-template/` mirror.
- **Sacrifice / honest limit:** none structural — additive/conforming; no rename, no principle weakened;
  enforcement remains deferred per ADR-0015. Cost: the exemption list must be maintained (deliberately,
  minimally, dependency-justified) as new tool-mandated names appear; a missing entry over-rejects
  (fail-closed toward stricter naming), surfacing loudly rather than leaking.
