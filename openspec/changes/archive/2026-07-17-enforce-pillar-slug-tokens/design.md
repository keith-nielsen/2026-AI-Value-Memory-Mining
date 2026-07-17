<!-- SPDX-License-Identifier: Apache-2.0 -->
## Context

The triggering incident (2026-07-17) was an agent misreading `PILLARS` as five
pillars instead of six. The operator's first instinct — and the initially
requested fix — was an explicit delimiter, `;` over `,`, so that token boundaries
are demarcated rather than inferred.

Investigation of the consumers changed the analysis. Three facts decided it.

### Fact 1 — pillar values become filenames

Each pillar renders a Catalog index at `40-Treasury/Catalog/<pillar>-domain-index.md`
(`mental-domain-index.md` ships in the template; `home-master-index.md` links it).
The pillar token is interpolated into a machine-generated name directly, with no
transform. `naming-rules` (INV-11) forbids spaces in such names.

So "allow spaces in pillar names" is not a delimiter change. It is a delimiter
change **plus** a new pillar→slug transform in every consumer that derives an index
path (bank-execute, the linter, the refine-prompt contract, `agent-integration`,
the Catalog templates), **plus** a permanent display-name/slug-name split — two
identities per pillar, which is a fresh drift surface of exactly the kind the vault
exists to avoid.

### Fact 2 — the current format already expresses multi-word pillars

A two-word pillar is writable today as one kebab token: `mental-health`. That form
is not a workaround — it is precisely the form INV-11 already requires the derived
filename to take. The kebab token and the filename agree by construction, with no
transform between them.

### Fact 3 — the validator already exists

`is_valid_slug()` (`naming-rules-script`) is `slug_pattern` + `validate_name()`,
i.e. `^[a-z0-9]+(?:-[a-z0-9]+)*$` plus cross-platform-safety and reserved-name
checks. It deliberately does **not** apply `has_min_hyphen_tokens` (the ≥3-token
floor for `.md` stems), so single-word pillars like `mental` remain valid while
`Mental_Health`, `CON`, and `-lead` are rejected. Verified against all six live
tokens: all pass. The enforcement this change needs is an import away.

## Decision

**Pillar tokens MUST be valid kebab-case slugs. The delimiter stays whitespace.
`vocab()` is not modified.** Enforcement lands in the knowledge linter via the
existing `is_valid_slug()`.

Under this rule the misread that triggered the change becomes unavailable: a
multi-word pillar is `mental-health`, and there is no token boundary left for a
reader to invent. The demarcation the operator asked for is achieved — by making
the *token* self-delimiting rather than by changing the separator between tokens.

## Options considered

1. **Kebab tokens, whitespace delimiter (CHOSEN).** No parser change, no slug
   transform, no other vocabulary touched, no migration. Enforcement is an existing
   validator. Aligns the pillar token with the filename it produces.

2. **`;` delimiter, spaces still forbidden (rejected).** Would change `vocab()` —
   shared by all eight vocabularies — forcing every vocabulary to `;` (or creating a
   second parsing rule, which is worse). Yet with spaces still forbidden, the
   no-spaces rule is doing all the real work; the delimiter swap adds churn across
   eight values and every adopter's `config.env` for no safety the kebab rule does
   not already provide. Rejected as dominated by Option 1.

3. **`;` delimiter, spaces allowed (rejected).** The only option buying genuinely new
   capability — literal spaces in pillar names. Cost is Fact 1: a pillar→slug
   transform in every index-path consumer plus a permanent two-identity split per
   pillar. The capability is not wanted: `mental-health` already reads correctly and
   already matches its filename. Rejected as paying structural cost for cosmetics.

4. **Do nothing; treat it as reader error (rejected).** Defensible — the parser was
   never wrong. Rejected because the rule that made the read wrong is a comment, and
   an unenforced rule is a rule the next reader (human or agent) may also miss. The
   incident is cheap evidence that the comment is insufficient; the fix is six lines.

## Consequences

- `PILLARS` gains a mechanically-enforced well-formedness contract. Malformed tokens
  fail at lint, not silently at Catalog-write time.
- Adopters authoring a multi-word pillar are pushed to `mental-health`, which is the
  form their Catalog filename needs regardless.
- The other seven vocabularies remain unvalidated. This change deliberately does not
  generalise; a `vocab()`-wide well-formedness contract is a plausible follow-up but
  each vocabulary has a different token grammar (e.g. `DISPOSITIONS` values are also
  slug-shaped, but `GRADES` are ordered and their order is semantic). Out of scope.
- **Sacrifice:** literal spaces in pillar names become permanently unavailable, and
  the option is closed deliberately rather than left open. An adopter who wants the
  display form "Mental Health" must render it at the presentation layer (the Catalog
  index title, the wikilink alias — `[[mental-health-domain-index|Mental Health]]`,
  a pattern `home-master-index.md` already uses), not in the vocabulary. This is the
  cost of keeping one identity per pillar.
