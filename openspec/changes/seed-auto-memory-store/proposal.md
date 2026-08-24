<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: seed-auto-memory-store

## Why

Commit `a4deb6e` added `vault-template/.claude/settings.local.json.example` and said so itself:

> **NOT YET GOVERNED.** This adds a file to `vault-template/`, i.e. it changes what deploys to a new
> vault, so it takes an OpenSpec change before it lands: a `vault-structure` delta for
> `10-Logbook/vmm-working-memory/`, and a decision on whether the deploy-down step should prompt for
> the absolute path rather than leaving a placeholder a first installer may ship verbatim.

This change is that governance. It lands the artifact already on the branch, adds the two pieces the
branch is missing, and answers the open decision.

### What the arrangement is

A deployed vault keeps its Claude Code auto-memory store in-tree at `10-Logbook/vmm-working-memory/`,
activated by one `autoMemoryDirectory` key. That key cannot live in the tracked
`.claude/settings.json`: its value is a machine-specific absolute path (the setting expands neither
`$VAULT_ROOT` nor any other variable), and `settings.json` is reconciled against the template, so the
path would report as drift on every deploy-down. It therefore belongs in `.claude/settings.local.json`
— which is git-ignored, and a git-ignored file cannot be seeded by the mirror. Hence an example to
copy from.

### What the branch is missing

1. **`vault-template/.gitignore` has no rule for the store.** The deployed reference vault has one; the
   template does not. A fresh deployment would therefore **track** the memory store — noise commits or
   a permanently dirty tree. That the reference vault got the rule and the template did not is itself
   the vault-side improvisation pattern this repository forbids, and fixing it here is the point.
2. **No `vault-structure` delta.** The canonical structure block does not mention the store, so a
   conformant deployment currently contains a directory the specification does not declare.
3. **The open decision, unanswered.**

## The decision, answered

**A guard in `vault-lint.py`, not a prompt and not a comment.** The linter refuses when the harness
settings file declares a store path that does not resolve to a directory inside the vault root.

The rejected alternatives, and why:

- **Placeholder plus documentation only.** This is the option the corpus has already measured. F27 is
  recorded as proving *"a prose-ENFORCE bin is not enforcement"*, and `CONTRIBUTING.md:92` states
  *"a rule which cannot refuse does not bind."* The seed's comments are good comments; they are not a
  mechanism, and an unresolvable `autoMemoryDirectory` fails quietly rather than loudly.
- **Prompt at deploy-down.** Strongest at the moment of installation, but it needs new operator-side
  machinery (the file is git-ignored, so `template-mirror.py` cannot seed it), and it fires **only** on
  a fresh deploy — it can never catch a vault that already has the value wrong. The lint guard catches
  both, at every run, in the place the mistake lives.

The guard's third case is the one that motivated choosing a check over a prompt: a path that resolves
**outside** the vault root is not an error a human notices. It works. It silently points one
deployment at another deployment's memory, or at a user-global directory — the cross-contamination the
whole project-scope arrangement exists to prevent. A placeholder check would not see it; a resolution
check does.

## What Changes

- **`vault-template/.gitignore`** — ignore `/10-Logbook/vmm-working-memory/`, with the narrowness note
  the neighbouring `99-Operations/bin/` rule already carries: the rule ignores the store directory
  only, never a parent that also holds tracked scaffold.
- **`vault-structure` spec** — MODIFIED `Folder Structure`: the store appears in the tree marked
  optional and harness-owned, with a paragraph stating that the framework neither generates nor
  polices its contents (ADR-0032), and that its absence is conformant.
- **`maintenance` spec** — ADDED Requirement for the linter guard, with its three refusal cases and
  its explicit jurisdiction limit.
- **`99-Operations/scripts/knowledge-lint-script.md`** (or the linter's owning literate note) — the
  guard itself, under the ADR-0023 exit-code contract.
- **`vault-template/.claude/settings.local.json.example`** — already committed on the branch; this
  change governs it rather than re-adding it.

## Nature of this change — ordinary, not a constitution-override

```constitutional-impact
touches: openspec/specs/vault-structure/spec.md, openspec/specs/maintenance/spec.md
protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12, INV-2, INV-3, INV-6]
overrides: none
basis: vault-structure MODIFIED Folder Structure — additive only. One optional, harness-owned,
  git-ignored directory is declared under an existing silo; the layer model (CONST-02), the
  touch-frequency ordering (CONST-04), the numbered structure itself (CONST-05), the Markdown +
  frontmatter format rule (INV-1) and the Treasury no-subfolder rule (INV-12) are each restated
  unchanged, and no existing scenario is modified, weakened or narrowed. The linter change NARROWS
  the framework's reach rather than widening it: notes inside the store stop being validated, which
  upholds ADR-0032 (the framework owns no artifact in 10-Logbook/) rather than overriding anything.
  maintenance ADDED Requirement — new guard, no existing requirement touched; INV-2 (one commit per
  change), INV-3 (literate note is the source, render produces the target) and INV-6 (no network, no
  LLM calls — the guard does filesystem resolution only) are all upheld by construction.
```

The diff touches `vault-template/`, two specs, and one fleet script. Both specs carry `protects:`
frontmatter, so ADR-0042's gate applies and the declaration above is required rather than optional.

⚠ **Sequencing, measured 2026-08-25.** `tools/preflight.py .` currently reports *"constitutional-diff-
gate: no protected element touched — not applicable"*. That is correct and temporary: the gate reads
`protects:` **frontmatter**, and the deltas under `changes/*/specs/` carry none. The gate becomes
applicable when archiving syncs the deltas into `openspec/specs/` **on the feature branch**
(ADR-0040), at which point the PR diff touches both tagged files. Today's "not applicable" is not
"no declaration needed".

## Deliberately NOT in this change

- **The uncommitted `vault-template/99-Operations/config.env.example` edit** on the same branch — a
  comment about the venv PATH prepend changing what `python3 -m` resolves to. Unrelated to the memory
  store, and F29 is the precedent for refusing to fold an unrelated governed change into a live
  ceremony. It needs its own change; it is left in the working tree untouched.
- **Mirroring the reference vault's `.gitignore` edit back down.** The deployed vault already has the
  rule. Reconciling live-vault drift against the template is the deploy-down step's job, not this
  change's.
- **Any claim that the framework supports harnesses other than Claude Code.** The spec language is
  deliberately harness-neutral ("an agent harness MAY maintain a working-memory store"), but this
  change ships a seed for one harness and does not pretend to have tested another.

## Impact

- `vault-template/.gitignore` · `vault-template/.claude/settings.local.json.example` (already present)
- `openspec/specs/vault-structure/spec.md` — 1 MODIFIED Requirement (+2 scenarios)
- `openspec/specs/maintenance/spec.md` — 1 ADDED Requirement (4 scenarios)
- the vault linter's literate note + rendered target
- `CHANGELOG.md` — `[Unreleased]` entry
