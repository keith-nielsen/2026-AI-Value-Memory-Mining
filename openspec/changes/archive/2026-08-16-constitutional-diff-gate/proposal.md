<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: constitutional-diff-gate

## Why

PR #85 (`fix/constitution-enforcement-claims`) removed six false enforcement claims from
`constitution.md`. One of them was load-bearing, and §5 says so explicitly about its own removal:

> ⚠ This sentence previously also claimed the protocol was **"mechanically enforced (CI fails without
> the ceremony)"**. It is not, and never was — see §4. That claim is removed rather than softened,
> because it was the load-bearing argument for why this mechanism was chosen […] **Restoring the fifth
> means building the diff gate, not rewording this paragraph.**

This change builds it. It is the enforcement item #85 removed, recorded then as owed rather than
forgotten (hardening queue item 28).

### The inversion this closes

By `constitution.md` §2's own tier table, the protection is upside-down:

| Tier | Elements | Held by | Can it refuse? |
|---|---|---|---|
| **Tier 0 — Inviolable** | INV-1–8, INV-11, INV-14 | sandbox, hooks, CI runners, rulesets | **yes** |
| **Tier 1 — Foundational frame** | `CONST-01`–`05` + INV-12 | ceremony, review, the §5 agent hard stop | **no** |

Tier 1 is described in the same document as *"what the constitution most exists to protect."* It is
the only tier with no mechanism that can fail a change. **The layer treated as most precious has the
least real resistance**, and every argument for the current design rests on a check that was never
built.

### Why prose has already been tried

The corpus records the outcome of the prose approach twice, and this repo's standing finding is
`CONTRIBUTING.md:92` — *"a rule which cannot refuse does not bind."* F38 supplied the local evidence:
of three violations in one change, the two caught at the moment of the mistake were caught by
instruments that **refuse** (`openspec archive`, `scope-review`); the one that escaped to `main` was
governed by a prose rule its own author had written. Adding a fifth paragraph to §3 would be the
class-9 defect — a criterion restated rather than derived — inside the document that defines it.

## What Changes

- **ADDED requirement** (`maintenance`): *A Diff Touching A Protected Element Declares Its
  Constitutional Impact* — the gate, its subject set, its refusal condition, and its explicit
  non-goals. 6 scenarios.
- **ADDED requirement** (`maintenance`): *A Constitutional Declaration Is Read From The Tree, Not The
  Pull-Request Body* — the durability and tamper properties the declaration channel must have.
  3 scenarios.
- **ADDED** `.github/scripts/check-constitutional-impact.py` — stdlib-only, deterministic, no network.
- **ADDED** CI job `constitutional-diff-gate`, **Phase A `continue-on-error: true`** (see *Sequencing*).
- **MODIFIED** `openspec/templates/constitution-override/proposal.md` — it currently repeats three of
  the claims #85 retracted (see *A finding this change is obliged to fix*).
- **MODIFIED** `openspec/constitution.md` §4 — one row added to the enforcement table describing what
  the new job actually does, in the "point at the job, do not paraphrase it" form item 14 established.
- **ADDED** ADR-0042 — context / options / choice / consequence.

## The design question item 28 left open, answered

Item 28 states the question directly: *"'touches a `protects:`-tagged element' needs defining (the
whole spec file, or the tagged element within it?)"*.

**Answer: the whole file, and the gate does not attempt a semantic judgement at all.**

The gate **cannot** determine whether a diff overrides a principle — that is the human judgement §5
reserves. What it can determine is whether **the question was answered in writing**. So:

> **The gate refuses silence, not work.**

A diff touching a `protects:`-tagged spec must carry an explicit constitutional-impact declaration. If
the declaration says *no Tier-0/Tier-1 element is overridden*, the gate passes — it does not
second-guess that claim. If the declaration says an element **is** overridden, the gate requires a
`constitution-override` change directory with the four gate sections present. If there is **no
declaration at all**, the gate refuses.

This is deliberately the same shape as `scope-review`, which refuses a PR whose body declares no
scope and does not attempt to judge whether the declared scope is *wise*. Reusing a shape the repo has
already burned in is the point; a novel enforcement idea here would be a second thing to debug.

**What this buys, stated honestly:** it does not make a false declaration impossible. It makes a
**silent** one impossible, converts an unanswerable review question (*"did the author consider the
constitution?"*) into a checkable one (*"is the answer in the diff?"*), and puts a signed claim in
version control where Gate 4 can re-read it. That is the whole claim. It is smaller than
"mechanically enforced" and should never be described as more.

## Measured, not assumed

Three numbers decided the design. Each is a re-runnable command, run 2026-08-16 on `main` @ `a9df354`.

### 1. The subject set is 6 files — and a grep-based gate would fire on 23

```
for f in $(grep -rl "protects:" . --include=*.md | grep -v '/.git/' | grep -v archive | sort); do
  head -5 "$f" | grep -q "^protects:" && echo "FRONTMATTER $f" || echo "PROSE-ONLY  $f"; done
```

| | Count | Files |
|---|---|---|
| **FRONTMATTER** (the real protected set) | **6** | the six capability specs: `access-control`, `agent-integration`, `maintenance`, `naming-rules`, `value-pipeline`, `vault-structure` |
| **PROSE-ONLY** (false positives) | **17** | `AGENTS.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `.github/pull_request_template.md`, `.github/workflows/ci.yml`, `README.md`, nine ADRs, **and `openspec/constitution.md` itself** |

**Therefore the gate reads YAML frontmatter, never a substring match.** A `grep protects:`
implementation would refuse a `CHANGELOG.md` edit, refuse edits to the CI file that *implements* the
gate, and refuse the constitution — the last of which is a bootstrap deadlock. This is the concrete
form of the over-denial risk item 28 flags, and it is one design decision away rather than
hypothetical.

### 2. The gate fires on 4 of the last 25 merges — 16%

```
git log --merges -25 --format=%H main   # then, per merge:
git diff --name-only --no-renames <sha>^1 <sha> -- openspec/specs/*/spec.md
```

| Result | Count | Which |
|---|---|---|
| Would fire | **4** | #87 `feat/estate-scoped-capability-probe`, #80 `feat/preflight-route-before-mutation`, #79 `fix/trust-write-evidence-over-stale-read`, #64 `chore/archive-enforce-adr-reference-integrity` |
| Quiet | 21 | every release PR, every `tools/` defect fix, every docs change |

All four touched `openspec/specs/maintenance/spec.md` and **only** that file. A 16% firing rate on a
gate that asks for one declaration is proportionate; a gate firing on most PRs would be the RC-E
bypass-training risk item 28 names.

### 3. The declaration channel is available 4-for-4

```
git diff --name-only <sha>^1 <sha> | grep -c 'openspec/changes/'
```

Every one of the four firing PRs carries an `openspec/changes/…` directory **in the same diff** (4
paths each). There is no case in 25 merges where a protected spec was touched with no change directory
present to hold the declaration. **The gate therefore never demands something the author cannot
supply** — which is the property that separates a guard from an obstacle.

Note the fourth: `chore/archive-*`. **Archive PRs sync deltas into the specs and so touch protected
files by construction.** A gate that did not handle them would refuse a routine ceremony step ~every
release cycle. Handled explicitly in the spec (the declaration is read from the change directory in
either its live or its archived path).

## Where the declaration lives — and why not the PR body

`scope-review` reads its declaration from `github.event.pull_request.body`. **This gate deliberately
does not**, and the divergence needs its reason stated:

| | PR body (`scope-review`) | In-tree (this gate) |
|---|---|---|
| Survives scratchpad/body loss | no — bodies have been lost and regenerated in this operation | yes, versioned |
| Mutable after checks pass | **yes** — editing a body does not re-trigger checks | no — a change re-triggers CI |
| Available to Gate 4's re-read | only via the API | yes, in the diff under review |
| Available to `preflight.py` locally | no (no PR exists yet) | yes |

The second row is disqualifying for a **constitutional** claim. A declaration that can be edited to
say something else after the green check is not evidence of anything, and this repo has already had to
retract one enforcement claim for describing protection it did not have. A constitutional declaration
must be as durable as the thing it certifies.

**Format:** a fenced `constitutional-impact` block in the change's `proposal.md`, machine-readable,
with the tagged IDs enumerated:

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only; no existing requirement modified, weakened or narrowed
```

`overrides: none` passes. Any ID in `overrides:` requires a `constitution-override` change directory
carrying the four gate sections. The `basis:` line is free text and is **not** parsed — it exists for
the human reviewer, and the gate makes no claim about it.

## A finding this change is obliged to fix

`openspec/templates/constitution-override/proposal.md` still carries **three** of the claims PR #85
retracted from `constitution.md`:

| Line | Claim in the template | Reality (`constitution.md` §4, post-#85) |
|---|---|---|
| 9 | *"CI will reject the PR if any gate section is missing or incomplete"* | CI checks only that the template **file exists** |
| 39, 70 | *"MANDATORY. CI will fail if this section is missing or has unchecked items"* | nothing reads a proposal's sections |
| 105 | *"CI will reject a merge if SIGN-OFF is missing"* | no check reads the sign-off |

Item 14's standing rule — *"when fixing false claims in a table, verify EVERY row, not the ones the
ticket names"* — was applied within `constitution.md` and stopped at its boundary. The template is the
file an author actually reads while performing the ceremony, so it is the **worst** remaining place
for the claim to survive.

This change makes claim 1 partially true (the gate does check for the four gate sections when
`overrides:` is non-empty) and leaves 2 and 3 false. **They are corrected to describe what the gate
does, not deleted and not left standing.** Reviewing the template was not in item 28's text; it is in
scope because building the gate without reconciling the document that describes the gate would
reproduce the exact defect this change exists to close.

## Design decisions worth your dissent

**1. `constitution.md` itself is NOT in the subject set.**

It carries no `protects:` frontmatter (measured above — it is a PROSE-ONLY hit). Including it would
mean every typo fix, every §4 correction like #85's, and every edit to the enforcement table demands a
declaration — including the edits that *reduce* false claims. Excluding it means `CONST-01`–`05` can
be edited with no gate.

**I recommend excluding it, and closing the gap a different way:** `constitution-lint` already asserts
`CONST-01`–`05` are all present. The cheap, precise addition is a **content hash** of the five
principle sections, so an edit to a principle's text fails the lint and must be consciously
re-baselined, while prose corrections elsewhere in the file pass untouched. That is a separate,
smaller change and is deliberately **not** bundled here (task 7). If you would rather have blunt
coverage now, say so and I will fold `constitution.md` into the subject set instead — the cost is
friction on exactly the corrective edits this operation has needed most.

**2. Phase A is report-only, and the flip is a separate governed change.**

Not caution for its own sake: today **zero** existing proposals carry a `constitutional-impact` block,
so a blocking gate on day one refuses 100% of legitimate spec changes until the format is adopted.
ADR-0039 established the pattern (`scope-review` burned in over 14 consecutive merged PRs before the
flip) and the hardening queue records why the flip must be its own change (F29 — do not fold). Same
sequencing here, with the burn-in threshold stated up front rather than discovered: **flip when the
gate has reported `pass` on 5 consecutive PRs that touched a protected spec** — at the measured 16%
rate that is roughly 30 PRs, so this will be a slow burn-in and should be.

**3. The gate does not fire on the change that carries the override.**

Stated as a requirement rather than left to the implementation, because it is the failure that would
discredit the gate fastest: a guard that refuses the very ceremony it demands.

## Nature of this change — ordinary, not a constitution-override

Following the same test PR #53, #80 and #87 applied, and following their precedent rather than
re-deriving it:

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the test matters.
- This change is **ADD-only** against that spec. No existing requirement is modified, weakened or
  narrowed. There is no sacrifice to accept, which is what Gate 4 exists to record.
- Adding enforcement to a principle is not overriding it. Nothing in `CONST-01`–`05` or INV-1–14
  changes meaning; the gate makes an existing obligation checkable.
- Therefore: **ordinary OpenSpec change.**

⚠ As with its predecessors, `constitution-lint` performs no diff analysis today, so a green CI run is
**not** evidence this classification is right. It stands on the reasoning above. That this change is
the one that finally makes such a classification machine-visible is noted without being relied upon.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only; two new requirements; no existing requirement modified, weakened or narrowed
```

## Blast radius (swept 2026-08-16, re-runnable)

```
grep -rn "constitution-lint\|constitution-override\|Informed-Upheaval" \
  --include=*.md --include=*.yml --include=*.py . | grep -v node_modules | grep -v changes/archive
```

| Reference | Action |
|---|---|
| `.github/workflows/ci.yml` — `constitution-lint` job | **no change** — the new gate is a **separate job**; leaving the existing lint untouched keeps its check-context name stable (ADR-0039's renaming trap) |
| `openspec/constitution.md` §4 enforcement table | **UPDATE** — one row for the new job, pointing at it rather than paraphrasing |
| `openspec/templates/constitution-override/proposal.md` | **UPDATE** — three retracted claims, above |
| `CONTRIBUTING.md:59-73` proposal-threshold table | **no change** — this change *is* trigger 3 and takes a proposal; the table already covers it correctly |
| `tools/preflight.py` | **UPDATE** — register the new job so it runs locally before every push (ADR-0041) |
| `AGENTS.md`, `README.md` prose mentions | **no change** — they describe the ceremony, which is unchanged |

## Regression evidence

Nothing is built. Every task is `[ ]`. Per the standing Definition of Done, `[~]` means built and
`[x]` means a test was **observed to fail without the change**.

The tests that matter here are the **over-denial** ones, because a gate's dangerous failure is
refusing correct work, and those states are ones the mechanism itself creates:

- an archive PR that syncs a delta into a protected spec **passes**;
- a legitimate `constitution-override` change **is not refused by its own gate**;
- a `CHANGELOG.md` / `ci.yml` / `constitution.md` edit **does not fire** (the 17 false positives above,
  as a fixture);
- a protected-spec diff with **no** declaration **fails**, and the failure message names the file, the
  tags it carries, and the exact block to add.

A test suite that only proves the last of these would be the vacuous pass the Definition of Done names.

## Impact

No behaviour change for any existing job in Phase A — the new job cannot fail a build until the flip.
No schema changes. No existing requirement modified. `constitution-lint`, `vocabulary-lint` and
`scope-review` are untouched, and no check context is renamed.
