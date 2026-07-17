<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0029 — Pillar tokens are kebab-case slugs; the `PILLARS` delimiter stays whitespace

**Status:** Accepted
**Date:** 2026-07-17
**Relates:** `maintenance` spec · change `enforce-pillar-slug-tokens` · constitution §2 (Tier 2 — pillar names) · extends ADR-0013 (naming-and-identity), ADR-0016 (system-artifact-naming) · constrained by ADR-0015 (≥3-token floor — deliberately **not** applied to pillar tokens)

## Context

`PILLARS` is a whitespace-delimited string parsed by `vocab()` via a bare
`val.split()`. On 2026-07-17 an agent read the shipped value —
`"mental health financial social technology calling"` — and reported it as five
pillars, having welded `mental` and `health` into one. The governing rule
("lowercase, no spaces, space-separated") sat three lines above the value in the
same file, and was still missed. The operator caught it from a comma in prose.

Nothing was modified; `vocab()` has always returned six tokens. The parser was
never wrong. But the format permits a reader to infer a token boundary the format
forbids, and the prohibition was a comment enforced by nothing — `Mental_Health`,
`CON`, or `-lead` would all be accepted and flow into a Catalog index filename.

The instinctive fix was an explicit delimiter (`;`). Consumer analysis rejected it.

## Decision

**Pillar tokens MUST satisfy `is_valid_slug()`** — `^[a-z0-9]+(?:-[a-z0-9]+)*$` plus
cross-platform-safety and reserved-name checks. **The delimiter stays whitespace;
`vocab()` is unmodified.** Enforcement lands in the knowledge linter. A multi-word
pillar is one hyphenated token (`mental-health`).

The ≥3-token floor (ADR-0015) does **not** apply: a pillar token is a fragment
interpolated into a stem (`<pillar>-domain-index`), and the resulting stem clears the
floor on its own. `mental` stays valid.

This delivers the demarcation the operator wanted by making the **token**
self-delimiting, rather than by changing the **separator**. Under the rule, the
misread that triggered this ADR is unavailable: there is no boundary left to invent.

## Options considered

1. **Kebab tokens, whitespace delimiter (CHOSEN).** No parser change, no transform,
   no other vocabulary touched, no migration — all six live tokens already conform.
   Uses a validator that already exists. Aligns the token with the filename it
   produces.

2. **`;` delimiter, spaces still forbidden (rejected).** `vocab()` is shared by all
   eight vocabularies, so this forces every vocabulary to `;` — or creates a second
   parsing rule, which is worse. With spaces still forbidden the no-spaces rule does
   all the real work; the swap adds churn across eight values and every adopter's
   `config.env` for no safety Option 1 lacks. Dominated.

3. **`;` delimiter, spaces allowed (rejected).** The only option buying new
   capability — literal spaces in pillar names. But a pillar token is interpolated
   *directly* into `40-Treasury/Catalog/<pillar>-domain-index.md`, so spaces require a
   pillar→slug transform in every index-path consumer plus a permanent
   display-name/slug-name split: two identities per pillar, a fresh drift surface.
   The capability is unwanted — `mental-health` already reads correctly and already
   matches its filename.

4. **Do nothing; reader error (rejected).** Defensible; the parser was never wrong.
   Rejected because an unenforced rule is one the next reader may also miss, and the
   incident is cheap evidence the comment is insufficient. The fix is six lines.

## Consequences

- `PILLARS` gains a mechanically-enforced well-formedness contract; malformed tokens
  fail at lint rather than silently at Catalog-write time.
- Adopters authoring a multi-word pillar are pushed to the form their filename needs
  anyway.
- Enforcement activates immediately with **no grandfathering** — the contrast with
  ADR-0015, which had to land as convention-only because non-conforming names already
  existed. Here nothing non-conforming exists.
- The other seven vocabularies remain unvalidated; generalising is a plausible
  follow-up but each has a different token grammar (`GRADES` is ordered and its order
  is semantic). Deliberately out of scope.
- **Sacrifice:** literal spaces in pillar names are permanently unavailable, closed
  deliberately rather than left open. Display forms move to the presentation layer via
  the wikilink alias — `[[mental-health-domain-index|Mental Health]]`, the pattern
  `home-master-index.md` already uses for `[[mental-domain-index|Mental]]`. The cost is
  borne to keep exactly one identity per pillar.
- **Not a constitutional change.** Constitution §2 places pillar names at Tier 2
  ("ordinary OpenSpec change — no ceremony required"); this is narrower still,
  constraining only a token's lexical form. CONST-05 (membership via metadata +
  Catalog, never folders) and INV-12 are untouched, as is the pillar set itself.
