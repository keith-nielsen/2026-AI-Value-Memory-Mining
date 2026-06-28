## Context

Molds conform (v0.1.7) and the ≥3-token rule is ratified (v0.1.8 / ADR-0015). This change brings the
three remaining system-artifact families — scripts, schema docs, Catalog indexes — to the
`silo-section-descriptor` form. Bundled into one conforming amendment because the families are
interdependent (the `refine-prompt` schema file holds the `index_links` pattern the index rename
changes, and that pattern also lives in the `agent-integration` spec).

## Goals / Non-Goals

**Goals:** rename the 3 families' `.md` artifacts to the convention; sync the 3 spec deltas; repoint
all references.

**Non-Goals:** `.py`/`.sh` binary renames (deferred — deploy targets unchanged); mechanical
enforcement of the ≥3 floor (separate later change); the sub-3-token *content* names (#7).

## Decisions

- **Bundle**, not three changes — the interdependency (refine-prompt ↔ index_links ↔ agent-integration)
  is cleanest resolved in one pass.
- **Scripts: `.md` notes only.** `deploy_target` frontmatter unchanged → deployed `~/bin/vault-*.py`
  names unchanged; `commit-gate-script` keeps `deploy_target: …/hooks/pre-commit` (git requires the
  hook file be named `pre-commit`). Canonical verbs (dig/slag/dump/refine→ore/bank/reprospect) keep
  `vocabulary-lint` green.
- **Schema docs render to themselves** (their `deploy_target` is their own path) → rename the note
  **and** its `deploy_target` frontmatter in lockstep.
- **Indexes**: `<pillar>-domain-index` (D2 scope token) + `home-master-index`; repoint the master's
  links and every `index_links` / `[[…-index]]` reference.

## Risks / Trade-offs

- Large multi-file apply → `validate-scripts.sh` renders + smoke-tests **every** script in a sandbox;
  `openspec validate --all`; a residual-name grep gate before commit.
- Schema `deploy_target` self-reference → rename note + target together; the render smoke-test catches a miss.
- Missed link repoint (home-index / index_links) → grep all `[[…-index]]`, `[[home-index]]`, and
  `Catalog/<pillar>-index` references before commit.

## Migration Plan

Scripts → schemas → indexes; repoint references; re-render; `reconcile` zero-drift. Forks/live vaults
run the same. Then Gate-4 + ADR + archive + tag + live-vault mirror (scripts + indexes).

## Open Questions

- None blocking. Mechanical enforcement of the floor remains a separate later change.
