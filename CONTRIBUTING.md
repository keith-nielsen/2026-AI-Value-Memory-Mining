<!-- SPDX-License-Identifier: Apache-2.0 -->
# Contributing to value-memory-mining

## The method IS the process

This repository is governed by OpenSpec SDD. **Every change — bug fix, enhancement,
new capability — originates as an OpenSpec change proposal.** There are no drive-by
edits to `vault-template/` or `openspec/specs/`. **One bounded exception exists** and is
stated below — see *When a change ships without a proposal*.

### Standard contribution flow

```
1. Fork and clone
2. /opsx:propose "what you want to change"
3. Fill out proposal + specs + design + tasks
4. /opsx:apply  (implement the tasks)
5. /opsx:archive (sync delta specs into main specs)
6. Open a PR — the PR template checklist will guide you
```

**Step 5 is not optional and does not come later — archiving happens on the feature branch, in the
same pull request that merges the change** (ADR-0040; `maintenance` — *A Change Is Archived On Its Own
Branch*). Archiving moves `openspec/changes/<slug>/` to `openspec/changes/archive/<YYYY-MM-DD>-<slug>/`
and applies the delta into `openspec/specs/`. A change that merges unarchived leaves
`openspec/specs/` describing a state the repo has already left, and **owes a second PR**.

**Archiving does NOT touch `CHANGELOG.md`** — `openspec archive` reports only *"Specs to update"* and
leaves the changelog alone. The changelog is stamped **at release**, in a single `release(vX.Y.Z)`
commit on the release branch. That is the practice without exception: measured across the history,
every commit that modifies `CHANGELOG.md` is a `release(...)` commit. This sentence previously
claimed archiving stamped it; it never did.

**The one exception:** where another in-flight change carries a delta against the **same** capability
spec, defer the archive and apply the deltas in merge order — otherwise the later archive can overwrite
the earlier one's requirements without a conflict, since the two touch the same file but not
necessarily the same lines. Name the change you are deferring to, so the second PR is a stated cost
rather than an unexplained one.

⚠ **If you are re-deriving this convention from history, use a pasted transcript over the merge graph —
never commit subjects.** A dedicated `archive(<slug>)` commit does **not** imply a separate PR; it
usually sits on the feature branch inside one PR. And use `--no-renames`: a directory *moved* into
`archive/` records as a rename, so `--diff-filter=A` silently omits every deferred archive. Both traps
produced confidently wrong answers on 2026-08-11 — see ADR-0040.

### When a change ships without a proposal

The rule above says *every* change originates as a proposal. Practice has not matched it: defect fixes
to maintainer tools in `tools/` have shipped with **no change directory** since PR #35 (also #39, #49,
#66–#69). That exception was real, load-bearing, and **written down nowhere** — which is the same shape
as the enforcement claims this repo has had to retract before: a documented absolute that practice
quietly contradicts teaches its readers that the document is approximate.

So the exception is stated here, and bounded. **The bound is the point** — an unwritten exception has
no edges, and on 2026-08-14 it was stretched to cover a 204-line change that added a command-line flag,
a module-level state variable, a new guard and new exit semantics (PR #67). That change shipped three
defects, all of which a proposal's design pass would have surfaced on paper.

**A change may ship without a proposal only if it is a defect fix to a maintainer tool AND none of
these is true.** Any single trigger means it takes a proposal:

| Trigger | Why it disqualifies |
|---|---|
| Adds or changes a **command-line flag** or any other caller-visible surface | callers bind to it; removing it later is a breaking change |
| Introduces **persistent state** — a module-level variable, an on-disk file, anything outliving one call | state has a lifetime, and a lifetime has an *exit* condition that must be designed, not discovered |
| Changes **exit semantics**, or adds a guard that can **refuse** work | the caller's control flow changes; a guard that over-denies costs more than the defect it prevents |

Fixing wrong behaviour in existing code, with no new surface, no new state and no new refusal, is a
defect fix. Everything else is a capability change wearing a defect fix's clothes.

Applied to the four pull requests of 2026-08-14, the test sorts them: **#66 and #68 ship bare**
(behaviour corrections within existing structure); **#67 and #69 take a proposal** (both added flags
and module state; #67 added a refusing guard).

#### The three questions a proposal is for

The design pass is not paperwork. These three questions are answerable **on paper, before any code**,
and each maps to a defect that shipped for want of asking it:

1. **State lifetime — what is the exit condition?** A new state variable was given an entry condition
   and no exit, so a post-mutation guard kept suppressing after the mutation it verified had been
   confirmed, blocking correct work (PR #68 fixed it).
2. **Reachability — which real invocation reaches this line?** Answer it by tracing call sites, not by
   intent. A retry sat behind a branch no real invocation took and was dead code from the day it
   shipped (PR #69 fixed it). Its own unit tests passed throughout, because a unit test supplies the
   input that production computes.
3. **Exhaustiveness — do the categories partition?** A tally counted two of three outcome values, so a
   report's footer contradicted the table above it.

#### Status of this rule

**Prose, unenforced.** Nothing in continuous integration checks it, and this repo's own record is that
a rule which cannot refuse does not bind. It is written here because that is where it is read at the
moment it applies; it is not written as a spec requirement because a requirement and its guard ship
together or not at all. The candidate enforcement point, if this proves worth mechanising, is the
driver's `approval` step: a diff that adds a flag, a module-level assignment or an exit-code change
while carrying no change directory is the case to flag.

### Landing a change (branch → PR → merge → cleanup)

The lifecycle *before* a ship is driven by `tools/pr-flow.py`, the sibling of the ship driver. Walk
it; do not hand-compose the sequence:

```
0. tools/preflight.py . [--body-file PATH] # RUN THIS BEFORE THE FIRST PUSH (ADR-0041). ONE command
                                           # reproducing 12 of 15 CI jobs locally, plus the route
                                           # steps CI cannot judge: declared scope against the real
                                           # merge-base diff, a trial merge, and a SIMULATED archive.
                                           # It prints its own coverage — what it ran, what it could
                                           # not run, and what it does not reproduce. A clear result
                                           # is NOT a promise the remote will be green.
   tools/pr-flow.py --plan --branch BR     # THE WHOLE ROUTE FIRST — 14 steps, each with its
                                           # executor, its authority, and whether the guard was
                                           # MEASURED or is only PROJECTED. Do this before writing
                                           # a plan of your own; that is what it is for.
   tools/pr-flow.py --capabilities         # who runs what, MEASURED not recalled, plus read budget
1. tools/pr-flow.py --branch BR [--base main] [--body-file PATH] [--title STR]
                                           # proves each guard, then EMITS the next single command
                                           # with runs: / authority: / consent: and exits 2
2. Run exactly the emitted command. If it is yours to run, it is also written to
   .git/pr-flow/next.sh — paste `bash .git/pr-flow/next.sh`, which re-asserts the state you were
   shown and aborts if GitHub moved (it also expires after 24h).
3. Re-run tools/pr-flow.py — it verifies the mutation actually landed before advancing
4. If it says NOT READY, poll `tools/pr-flow.py --ready …` (exit 0 ready / 2 waiting). Never sleep.
5. Repeat until it prints LIFECYCLE COMPLETE and exits 0
```

Like the ship driver, it **never executes an outward mutation** — the INV-14 guard text-matches the
command the caller runs, so a wrapper would bypass the rail.

**Authority is not the same as typing.** Where the agent is measured capable, it runs the command and
your role is consent, discharged through the INV-14 ask at execution time — `git push` and the
post-merge branch deletion work that way. What stays yours to run are the `gh` mutations, and for two
reasons together: `gh` needs the OS keyring, *and* no write token is exported here by policy, because
credential absence is the barrier the outbound rail actually rests on.

**`gh pr merge --delete-branch` is never used.** It cannot express a head precondition, it bypasses
GitHub's retargeting of stacked children (so they are closed instead — this is how PR #29 died), and
its deletion is non-atomic while still printing `✓ Merged`. The merge goes through the REST endpoint
carrying `sha`, so a raced head is refused by the server with 409. Two further standing hazards:
**a stale base makes a pull request's checks report on something other than its own change** — rebase
before pushing, never after opening; and **a body-derived check reads the event payload as of push
time**, so after correcting a body you must PUSH, not re-run the job.

`main` currently carries **no `required_status_checks`** (ADR-0034's follow-on is pending), so a red
check does not block a merge. Until that lands, this driver is the gate.

### Shipping a version (tag → release → mirror)

After a change is merged to `main`, the ship is **not complete** until a GitHub **Release object**
exists for the new version. A git tag and a GitHub Release are different objects — pushing a tag does
**not** create a Release, and the Releases page / profile badge track the newest *Release*, not the
newest tag. The ceremony is driven by the guarded state machine `tools/ship-release.py`:

```
1. tools/ship-release.py vX.Y.Z      # proves merge-ancestor + CHANGELOG entry, refuses stale
                                     # tags naming the true cause, cuts + verifies the local tag,
                                     # then EMITS the next single outward command and exits 2
2. Run exactly the emitted command (git push origin refs/tags/vX.Y.Z, later
   gh release create vX.Y.Z --verify-tag --latest …) through the normal gated channel
3. Re-run tools/ship-release.py vX.Y.Z — it verifies the mutation actually landed
   (per layer: remote-tag, release-object) before emitting the next step
4. Repeat until it prints the tag↔Release PARITY TALLY with its denominators and exits 0
5. tools/template-mirror.py <VAULT_ROOT>   # mirror LOCKSTEP repo→live, then prove parity
```

The driver deliberately **never executes the outward commands itself** — `git push` and
`gh release create` are ASK-gated by the INV-14 outbound guard, and the operator approves each
deliberately after reviewing the overview summary + `proposal.md`. Because release creation and
verification are steps the driver refuses to skip, a tag can never again accumulate without its
Release (the drift that stranded the Releases page at v0.1.13 while tags ran to v0.1.22 — and the
F10 record of seven false starts in one hand-driven ship is why the guards exist).

### Touching a constitutional element?

If your change modifies anything tagged `protects:` in the spec files, or touches
`openspec/constitution.md` itself, you must use the **Informed-Upheaval Protocol**
instead of the standard flow. Read `openspec/constitution.md` §3 carefully, then:

```
Use the template at: openspec/templates/constitution-override/proposal.md
Change type must be: constitution-override
All four gates must be satisfied before the PR can merge.
```

CI will fail if a `protects:`-tagged file is modified without the ceremony.

### What makes a good contribution

- **Specs before code.** The proposal explains *why*; the spec captures *what changes*;
  the design explains *how*. Implementation without these is incomplete.
- **One change, one purpose.** Don't bundle unrelated capabilities.
- **Preserve invariants.** INV-1 through INV-13 are not negotiable via a normal change.
  If you believe an invariant is wrong, that is a constitutional override.
- **No vendored dependencies.** Third-party tools (Obsidian, n8n, Hermes, Ollama) are
  orchestrated, not embedded. If a component is embedded, verify its license first.
- **Apache hygiene.** New files get the SPDX header: `<!-- SPDX-License-Identifier: Apache-2.0 -->`.

### Reporting bugs

Use the **Bug Report** issue template. Include the INV ID of the invariant violated,
if applicable.

### Proposing a new capability

Use the **Change Proposal** issue template to discuss before opening a PR, especially
for larger changes.

## License

By contributing, you agree that your contributions are licensed under the
Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
