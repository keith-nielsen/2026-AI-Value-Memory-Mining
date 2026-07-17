<!-- SPDX-License-Identifier: Apache-2.0 -->
## Why

`PILLARS` is a whitespace-delimited string parsed by `vocab()` with a bare
`val.split()`. The shipped value is:

```
export PILLARS="mental health financial social technology calling"
```

To the parser this is unambiguous — six tokens, always. To a *reader* it is not.
On 2026-07-17 an agent (Claude) read this value during session bootstrap and
reported it back as five pillars, having silently welded `mental` and `health`
into a single "mental health" pillar. The config states the governing rule three
lines above the value ("lowercase, no spaces, space-separated"), and the agent
still misread it. The operator caught the error only because the comma in the
agent's prose looked wrong.

No file was modified and no consumer was ever affected — `vocab()` has always
returned six tokens. The defect is **not** a parser bug. It is that the format
lets a reader invent a token boundary that the format itself forbids, and the
prohibition lives in a comment that nothing enforces.

Two properties make this worth fixing rather than filing as reader error:

1. **The rule is unenforced.** Nothing validates that a `PILLARS` token is
   well-formed. `Mental_Health`, `CON`, or `-lead` would all be accepted silently
   and then flow into a Catalog index filename.
2. **The failure is silent and upstream.** A misread pillar set is a premise, not
   an output. It would sit in an agent's context and shape every subsequent
   pillar-assignment decision, with no artifact to contradict it.

## What Changes

### Modified Capabilities

- `maintenance`: the knowledge linter gains a **vocabulary-integrity** check —
  every `PILLARS` token MUST be a valid kebab-case slug per the `naming-rules`
  `slug_pattern`, validated with the existing `is_valid_slug()`. A non-conforming
  token fails the lint with the offending token named.

- `config.defaults.env`: the pillar comment is rewritten to state the rule as
  **kebab-case slugs, whitespace-separated**, and to show the multi-word form
  explicitly (`mental-health`, one token) so the shape is demonstrated rather
  than described.

The delimiter stays whitespace and `vocab()` is **not** touched.

### Explicitly Not Changed

- **The pillar set does not change.** `PILLARS` keeps its exact current value.
  All six live tokens already pass `is_valid_slug()` (verified). This change adds
  a guard around the value; it does not rename, merge, split, or reorder a pillar.
- `vocab()` and the other seven vocabularies (`GRADES`, `REFINE_GATE_GRADES`,
  `KNOWLEDGE_STAGES`, `EFFORT_STATUSES`, `SPOIL_STATUSES`, `DISPOSITIONS`) are
  untouched. See `design.md` for why the semicolon-delimiter alternatives were
  rejected.

## Impact

| Artifact | Change |
|---|---|
| `openspec/specs/maintenance/spec.md` | +1 ADDED requirement (delta in `specs/`) |
| `vault-template/99-Operations/scripts/knowledge-lint-script.md` | +~6 lines; `is_valid_slug` already imported |
| `vault-template/99-Operations/config.defaults.env` | comment only — **value unchanged** |
| `vault-template/99-Operations/config.env.example` | comment only |
| `docs/USING-THIS-TEMPLATE.md` | pillar-authoring rule restated |
| `openspec/adr/0029-pillar-slug-tokens.md` | new ADR (records the rejected `;` options) — drafted here as `adr-0029-draft.md`; it is a Gate-4 artifact and moves at sign-off |
| `README.md` | ADR count 28 → 29, range → `ADR-0001–0029` (adr-count-lint) |
| `tests/test_fleet.py` | +1 regression: malformed pillar token fails the lint |

**Migration: none.** The live vault inherits `PILLARS` from `config.defaults.env`
(its `config.env` overrides only `VAULT_ROOT` and `PATH`), and every current token
already conforms. Enforcement can be turned on immediately — unlike ADR-0015, there
is no grandfathering step, because there is nothing non-conforming to grandfather.

**Ceremony: ordinary OpenSpec change.** Constitution §2 classifies pillar names as
**Tier 2 — Conventions → "Ordinary OpenSpec change — no ceremony required."** This
change is narrower still: it constrains the *lexical form* of a pillar token and
does not touch CONST-05 (pillar membership via metadata + Catalog, never folders),
INV-12, or the pillar set itself. No Informed-Upheaval Protocol is triggered.

## Operator note (separate, recommended)

The live vault does not pin `PILLARS`; it inherits the framework's *example*
default. That means a future edit to `config.defaults.env` in this public repo
would silently re-pillar the live vault. Pinning `PILLARS` explicitly in the
gitignored `99-Operations/config.env` decouples the two. That is a live-vault
operator action, out of scope for this repo change — raised here because this
change is the moment the coupling became visible.
