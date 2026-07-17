<!-- SPDX-License-Identifier: Apache-2.0 -->
## Why

ADR-0015 (2026-06-27) established the **≥3-hyphen-token floor** for `.md` stems and chose
**convention now, mechanical enforcement later**, because turning on rejection while
non-conforming names existed "would block all commits until every family is renamed." It
named the enforcement as *"a **separate later change**"*, gated on **full conformance**.

**That change was never written.** Today the whole pending item is one sentence in an ADR
and three commented-out lines at `knowledge-lint-script.md:91-93`. It has no proposal, no
task, and nothing tracking it.

**The gate it was waiting on is satisfied.** Measured across the whole live vault:

```
118 .md files | 15 exempt | 103 subject to a strict rule
  fail is_valid_slug   : 0
  fail >=3-token floor : 0
```

Every family conformed incrementally exactly as ADR-0015 predicted — molds in v0.1.7, then
scripts, runbooks, indexes, content. Nobody went back to switch enforcement on, because the
thing that would have noticed was a comment.

**Three findings make this cheaper than it looks:**

1. **`has_min_hyphen_tokens` is called by nothing.** Its only references are its own
   definition (`naming-rules-script:72`), the linter's import, and the commented-out `elif`.
   ADR-0015's rule is enforced **nowhere**. The floor is dead code.
2. **The commit gate's grandfathering fear never applied to it.** The hook reads
   `git diff --cached --diff-filter=AR` — added/renamed only, explicitly commented *"existing
   names are grandfathered"*. It structurally cannot touch an existing name. The fear was
   about the **linter** (which sweeps everything), and there conformance is now total.
3. **The exemption list already covers the awkward names** — `README.md`, `CLAUDE.md`,
   `AGENTS.md`, `MEMORY.md`, dailies (`[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md`),
   `*.example`, config files. A strict gate does not block them.

This is the same defect the vault caught this morning in `PILLARS`, one level up: **a rule
that lives as a comment, enforced by nothing.** ADR-0015's grandfathering was the reason for
the comment; that reason has expired.

## What Changes

### Modified Capabilities

- `naming-rules`: the ≥3-token floor and the kebab rule become **mechanically enforced** for
  newly added / renamed content names, at two points:
  - **`vault_naming.py`** gains `--check-strict FILENAME` — exemption-aware, applying
    `is_exempt` → `validate_name` → `is_valid_slug` → `has_min_hyphen_tokens`. The existing
    `--check STEM` (cross-platform safety only) is unchanged, so nothing that calls it moves.
  - **`commit-gate` hook** calls `--check-strict` on the **basename** (exemptions match on the
    full filename) instead of `--check` on the stem. Still `--diff-filter=AR`: existing names
    stay grandfathered.
- `maintenance`: the linter's **staged `elif` is switched on** for `20-Claims`, `10-Logbook`,
  `40-Treasury/Catalog`; the floor is additionally applied to Treasury stems and effort folder
  slugs, which today get `is_valid_slug` but no floor.

### Explicitly Not Changed

- `min_hyphen_tokens: 3` and `slug_pattern` are unchanged — this change enforces the existing
  rule, it does not redefine it.
- `--check` keeps its current contract. No caller is migrated implicitly.
- Existing names are **not** renamed. Nothing is renamed by this change at all — conformance
  is already 100%, which is *why* the switch can flip.

## Impact

| Artifact | Change |
|---|---|
| `openspec/specs/naming-rules/spec.md` | Requirement MODIFIED: enforcement is live, not staged (delta) |
| `openspec/specs/maintenance/spec.md` | Requirement MODIFIED: linter applies the floor (delta) |
| `vault-template/99-Operations/scripts/naming-rules-script.md` | `--check-strict` added |
| `vault-template/99-Operations/scripts/commit-gate-script.md` | hook calls `--check-strict` on basename |
| `vault-template/99-Operations/scripts/knowledge-lint-script.md` | staged `elif` enabled; floor on Treasury + effort folders |
| `tests/test_fleet.py` | regression: gate blocks sub-3 adds, allows exempt + renames of existing |
| `openspec/adr/0030-*.md` | new ADR (Gate-4 artifact; drafted in-change) |
| `README.md` | ADR count → 30 (adr-count-lint) |

**Migration: none.** 0 offenders across 118 live `.md` files. No rename, no grandfathering step.

**Behaviour change for the operator — this is the real cost.** After this, a *newly added*
content note must be named with ≥3 kebab tokens. `xrp.md` or `kanban.md` would be **BLOCKED at
commit**. That is precisely ADR-0015's intent, but it is a live workflow constraint and is the
thing to accept or reject at Gate 4.

## Ceremony

**`constitution-override`, conforming** — touches `naming-rules` (`protects: [INV-11]`) and
`maintenance` (`protects: [INV-2, INV-3, INV-6]`). **No Tier-0/1 element is overridden or
weakened**; INV-11 is *strengthened* from convention to mechanism, which is what its own ADR
called for. Same posture as the `retire-effort-projections` ceremony (PR #26).
