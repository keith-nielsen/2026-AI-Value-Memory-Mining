<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: relocate-fleet-in-tree-bin

Relocate the rendered Layer-0 script fleet from the user-global `~/bin/` into
`99-Operations/bin/` inside the vault tree, and reconcile every surface that describes it.

**Change B of two. Depends on `add-fleet-inventory-conformance` (A) being merged first**, which lands
the inventory, cadence, settings-resolution and coverage instruments. B is the first change that
could ever break the settings-resolution check — that is the point of the split, and it is stronger
evidence than a check manufactured red inside the change that makes it green.

**Decisions recorded in [ADR-0044](../../adr/0044-relocate-fleet-in-tree-bin.md)** — context /
options / choice / consequence / **sacrifice**, per constitution §3 Gate 4. Five options were
weighed, including `~/.local/bin` (the systemd `file-hierarchy(7)` standard location, rejected
because it is still user-global and fixes only one of the five grounds).

## Why

**The operator's framing, which is the argument:**

> *"Things in `~/bin` are user-wide tools that could/would be used on other things in general, not
> restricted to a single package or tree. Maybe the design should have been to put the rendered
> scripts within a bin directory that was then within the repo itself — a forked user would be
> working with their own local repo containing the tools they needed for that repo that rendered
> there, rather than contaminating their own `~/bin` for something that should have been contained
> within the tree that needed it."*

Five independent grounds, four of principle and one of defect:

1. **It contradicts a principle this operation already codified.** F15's corrective is *"a deployed
   vault is standalone."* A vault whose entire operational fleet lives in `~/bin` is a tree plus a
   user-global side-load. There is a CI job named for it — `Standalone-vault lint (F15)` — but it
   only checks that `vault-template/` references no framework-repo path. **`~/bin` walks straight
   past the lint written to enforce standalone-ness.**
2. **Multi-vault version skew is unrepresentable.** Two vaults, or a vault plus a fork at a different
   version, share one `~/bin`. Whoever rendered last wins, silently, with no way to tell.
3. **Fork ergonomics** — a fork inherits a tree that already contains its own tools.
4. **It manufactures an authority problem.** `vault-render.py render` is operator-only *because* its
   targets sit outside the agent's write scope. Move the targets in-tree and, repo-side, that
   constraint dissolves. This **supersedes** the earlier "in-tree render-scope flag" idea —
   relocation removes the gap rather than routing around it.
5. **`~/bin` is not reliably on `PATH` — measured, and a live defect.** The two mechanisms that
   assemble it are disjoint and never both run:

   | Mechanism | Adds | Runs when |
   |---|---|---|
   | `~/.profile` | `~/bin`, `~/.local/bin` | **login** shells only |
   | `~/.bashrc` (guard at line 5) | venv, CUDA | **interactive** shells only |

   Measured from a clean `env -i`:

   ```
   bash -lc  (login, non-interactive) → /home/administrator/bin/vault-lint.py
   bash -ic  (interactive, non-login) → NOT-FOUND
   bash -c   (neither)                → NOT-FOUND
   ```

   The fleet is invisible to cron, systemd user units, `ssh host 'cmd'`, and any plain `bash -c`.
   The corpus has already flip-flopped on this question ("`~/bin` is not on PATH" → corrected to "IS
   on PATH") because **both readings are half-right**, and neither states the condition.

## What Changes

- **11 host targets** move from `~/bin/<name>` to `99-Operations/bin/<name>`. The **3 in-tree
  targets are untouched** (`99-Operations/hooks/pre-commit`, `99-Operations/hooks/pre-push`,
  `.claude/hooks/outbound-publish-guard.py`).
- **5 scripts stop hardcoding `$HOME`.** `vault-lint.py`, `vault-orphans.py`,
  `vault-refine-detect.py`, `vault-refine-execute.py`, `vault-reprospect.py` currently carry
  `sys.path.insert(0, str(pathlib.Path.home() / "bin"))` and become
  `sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))`.
- **`.claude/settings.json`** exact-match exclusion is repointed (both vault and template).
- **`config.env`** appends the new directory to `PATH`, idempotently.
- **`tests/conftest.py`** and **`.github/scripts/validate-scripts.sh`** are repointed.
- **`.gitignore`** in both trees gains `99-Operations/bin/` — the new directory holds render output,
  not source. `template-sync-manifest.json` is **not** extended; see *design decisions*.
- **Every live document** describing the fleet is reconciled to the post-move truth — 25 live files
  per the blast-radius transcript; the 72 frozen ones are untouched.
- **The `vault-`/`vault_` executable prefix is codified** in `naming-rules`. It is currently the sole
  reason the estate has zero name collisions across every directory on `PATH`, and it has never been
  written down.
- **`~/bin` is decommissioned.** The operator has already relocated `generate_image.sh` and
  `x11-monitor.sh` to `~/.local/bin` and deleted the orphaned `vault-se5-probe.py`; only the 11
  fleet members and a `__pycache__/` remain.

## Design decisions, and the reasoning

### `99-Operations/bin/`, deliberately inside protected Layer 0

INV-4/5 continue to deny the agent write access. That is **wanted** — the agent must not be able to
rewrite its own guards. Relocation buys containment, forkability and repo-side runnability; it does
**not** loosen protection. Vault-side `render` stays operator-only, and is correct as-is.

### No `$VAULT_BINS` variable

ADR-0023 exists *because* an env dependency broke the fleet: probe P5 crashed with
`KeyError: 'VAULT_ROOT'` in a fresh tool shell, and the exact-match exclusion forbade an env prefix,
which made SE-5 unprovable. The fix was root self-resolution, env-free. A new variable would
reintroduce precisely that, and in the more fragile direction: it is *derivable* from `$VAULT_ROOT`,
so it would be a **second SSOT for one location** — unset or skewed, it yields a silent wrong-tree
resolution, which is the multi-vault skew this change exists to end.

The scripts need no variable at all: each self-resolves its root by marker-walk, and co-located
modules resolve via the script's own directory. `config.env` uses the literal derived expression;
documents write `$VAULT_ROOT/99-Operations/bin/<name>`.

### `PATH` is appended, not prepended, and made idempotent

`config.env:4` is **not idempotent today** — sourcing it three times puts `.venv/bin` on `PATH`
three times (measured). This change adds a second entry, so the defect would compound. Append rather
than prepend: nothing in the fleet collides with a system binary, so precedence is unnecessary
surface. The `vault-`/`vault_` prefix is what makes that safe, and it is currently an unwritten
accident — this change **codifies it as a naming rule** (`vault` is a very commonly installed
binary name; the prefix is the only reason there are zero collisions).

### The new directory is not a lockstep prefix, and its contents are not tracked

Two decisions that look like one, taken 2026-08-17.

**`99-Operations/bin/` is NOT added to `template-sync-manifest.json`.** It is *generated output*, and
the manifest already states the rule for that category — its `exclude` list carries
`99-Operations/schemas/naming-rules.json` with the reason given verbatim: *"the live vault GENERATES
them (the template ships the generator, not its output)."* The generator here is
`99-Operations/scripts/`, which is already lockstep. Adding `bin/` would also fail permanently:
`files_under()` returns an empty set for an absent directory and `vault-template/` ships no `bin/`,
so parity would report 11 drift findings forever, and a check that is permanently red is a check
nobody reads.

The "unwatched path" concern that has bitten twice does **not** apply. Those two cases —
`96-Runbooks/` and the tracked guard hook — were hand-maintained files with no generator, so nothing
else watched them. Every artifact in `bin/` is governed by `reconcile` (note → deployed). The
division of labour is clean and worth stating because it is the thing that was previously unstated:
**parity watches hand-maintained scaffold; `reconcile` watches generated output.**

**`99-Operations/bin/` is git-ignored in both trees.** This question is created by the relocation —
`~/bin` sits outside every repository, so it never arose before — and neither `.gitignore` excludes
it today, which means the default is *tracked*: a decision by accident. Committing the rendered
artifacts would give one piece of code two homes, the note and the committed copy, which is exactly
the duplication the literate meta-script model exists to prevent (INV-3), and would make every
`render` a diff to review.

The cost is that a fresh clone has no fleet until `render` runs. That is acceptable and nearly free:
the bootstrap already extracts `vault-render.py` from its own note before anything else runs, so the
*shape* of that sequence is unchanged by this proposal — only the target path moves. A nonexistent
directory on `PATH` is harmless (measured: `/snap/bin` is absent from this host's `PATH` targets and
nothing is affected).

The ignore rule names the **generated output directory specifically**, never a directory that also
holds tracked scaffold — the discipline the vault `.gitignore` already documents for `.claude/`:
*"a blanket rule would silently hide the next hook or command that vault-render.py deploys."*

GATE 4 verifies both decisions rather than trusting them: `git status --porcelain` must be empty
after `render` (proving the artifacts are ignored, not merely uncommitted), and `template-parity`
must still report 0 drift across **2** prefixes (proving `bin/` was not added to `lockstep`).

### Bytecode is not written into governed space

Python writes `__pycache__/` beside an imported module. Today that litters `~/bin`; after relocation
it would write **inside protected Layer 0**. `~/bin/__pycache__/` currently contains
`vault-close-day.cpython-312.pyc` — bytecode for a script deleted on 2026-07-19 (ADR-0032) that
nothing swept, because `reconcile` iterates *notes* and the note was gone. That is exactly the R8
scenario ADR-0032 cites in its own Decision. The retirement got the `.py` and missed the `.pyc`.
This change sets `sys.dont_write_bytecode` at the fleet's entry points rather than inheriting the
same blind spot.

## The three questions

1. **State lifetime — what is the exit condition?** The only new persistent state is the
   `99-Operations/bin/` directory itself and its `PATH` entry. Exit condition for the directory:
   removal of the change. Exit condition for the `PATH` entry: the shell exits — the entry is
   process-scoped and added only by an explicitly sourced `config.env`, never by a shell profile.
   **This change adds nothing to `~/.profile` or `~/.bashrc`;** it reduces global surface rather
   than trading one global for another.
2. **Reachability — which real invocation reaches this line?** Traced, not assumed. The five
   `sys.path` lines are reached on every invocation of those five scripts. The `settings.json`
   exclusion is reached only through the Claude Code harness — **never** by any test, which is why
   it is the one path that can fail silently (see *Blast radius*). `conftest.py:43` is reached by
   all 33 fleet tests.
3. **Exhaustiveness — do the categories partition?** The 14 notes partition into 11 host + 3 in-tree
   with no remainder, verified by reading `deploy_target` from every note rather than by counting.
   Reference classes partition into live surface / frozen record, and the plan states the rule for
   each rather than treating all matches alike.

## Nature of this change — ordinary, not a constitution-override

CONST-02 describes Layer 0 and this change relocates Layer-0 machinery *within* Layer 0. No
principle is overridden, weakened or narrowed; the protection boundary is unchanged and the agent's
write scope is unchanged. It is an ADD/MOVE.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md, openspec/specs/access-control/spec.md, openspec/specs/naming-rules/spec.md
protects: [INV-2, INV-3, INV-6, CONST-02, INV-4, INV-5, INV-7, INV-8, INV-11, INV-14]
overrides: none
basis: MOVE of deploy targets within Layer 0 plus ADD of an inventory-conformance requirement; no existing requirement is modified, weakened or narrowed; agent write scope is byte-for-byte unchanged (99-Operations/ remains denied)
```

## Inherited inconsistencies — moved to Change A

Five pre-existing drifts were found while verifying live documents against deployed reality. **They
are corrected in Change A, not here**: a spec inventory missing `secret-scan` entirely, a README whose
heading says 13 above a 10-row table for a 14-note fleet, and three ADR-0028 cadence stragglers.

They were split out because they are independent of the relocation, and because their instruments
prove more when exercised on defects that already exist than on defects this change would introduce.

**Not corrected in either change, deliberately:** the three stale ADR headers (0032, 0033, 0042 all
read "Proposed / pending" while being signed, applied and archived). Real, but they touch no line
either change edits.

## The verification doctrine — the point of this change's shape

There is extensive evidence in this repo of *things that should have happened and did not*: a spec
inventory that lost a script for three weeks, a README that contradicts itself, three ADR headers
that never got flipped, a `.pyc` that outlived its `.py` by a month. Every one of them is a
hand-maintained duplicate of a machine-checkable fact.

Three rules follow, and the task list is built around them:

1. **Red before green.** No verification is ticked `[x]` until it has been **observed to fail on the
   pre-change tree**. A check that passes before and after proves nothing. This is the standing
   Definition of Done: `[~]` = built, `[x]` = tested.
2. **No step self-certifies.** Each phase is verified by an instrument that did not perform it —
   `reconcile` verifies deployment, `pytest` verifies behaviour, `template-parity` verifies the
   mirror, and Change A's inventory check verifies the documents. A step that checks its own work is
   a claim, not evidence.
3. **Evidence is a command and its output** (§3 Gate 3) — a tally with its denominator, a diff, or an
   exit status. Never a prose assertion, never a shell-printed verdict string. An `echo "ok"` proves
   nothing: the shell knows only an exit code, not the answer to the question asked.

**The seam that let this class of drift survive is closed by Change A**, which is why A lands first:
`render`/`reconcile` govern note → deployed and `template-parity` governs template → vault, but
nothing governed **spec → note**, and nothing verified that a harness exclusion named a real artifact.


### ⚠ Correction — this defect is narrower than first stated

An earlier draft of this proposal claimed the five hardcoded imports would produce **hard
`ImportError`s once `~/bin` is deleted**. **That is false, and was measured false on 2026-08-18.**

The interpreter already places a script's OWN directory at `sys.path[0]`. A fleet member executed
from its deploy directory therefore resolves its siblings from there regardless of `$HOME`, and
`HOME=/nonexistent python3 <script>` **passes both before and after this change**. The home-relative
insert has never been load-bearing under ordinary invocation — it is redundant, and it merely
*appears* to be the mechanism.

It stops being redundant exactly where it also stops being correct:

```
$ HOME=/nonexistent python3 -P /home/administrator/bin/vault-lint.py
ModuleNotFoundError: No module named 'vault_naming'
```

`python3 -P` disables the script-directory prepend; the same holds when a fleet member is **imported**
rather than executed, since `sys.path[0]` is then the importer's directory. In those modes the
home-relative path is the only resolver, and after relocation it names a directory the fleet no
longer occupies.

**So the fix is real but the severity was overstated.** The change removes a line that is misleading
under normal use and wrong under strict use — not one that would break the migration. The
corresponding test uses the `-P` form, because the obvious test is vacuous: it was written first, it
passed on the unmodified tree, and it proved nothing.

## Blast radius *(constitution §3 Gate 1)*

Delivered as a **pasted, re-runnable command transcript** — the exact commands plus their full,
untruncated output — in **`blast-radius-transcript.md`**, captured 2026-08-18. Five commands sweeping
the corpus set the gate names (`openspec/ vault-template/ docs/ .github/ README.md AGENTS.md
CONTRIBUTING.md`), plus the source-level `$HOME` imports and the authoritative note → `deploy_target`
partition.

An earlier draft of this proposal presented the blast radius as a table composed from those sweeps.
That is precisely what Gate 1 forbids — *"never a list composed from reasoning"* — and it is the
F23/F38 failure shape. The table is replaced by the transcript; **Gate 4 re-runs those same commands
and diffs the output against the file** rather than re-reading the prose.

### Tally, from the transcript

| Partition | Files | Disposition |
|---|---|---|
| corpus total | **85** | — |
| `openspec/changes/archive/` | **53** | **FROZEN** — immutable record |
| vault dig record (`30-Sites/`, `71-Spoil/`, `20-Claims/`, `10-Logbook/`) | **19** | **FROZEN** |
| live surface | **25** | editable by this change |

**Roughly 60% of all matches are immutable record.** A find-and-replace across the estate would
corrupt the audit trail. The rule is carried as a task with a diff assertion, not as an intention.

Ground truth for the change itself: `reconcile` exits 0 across 14 targets; 14 notes on disk; **11
host + 3 in-tree**, with no remainder.

### The atomicity requirement

`.claude/settings.json:50` carries an **exact-match** command exclusion:

```
"~/bin/vault-refine-execute.py *"
```

Change the deploy target without changing this and the exclusion **silently stops matching**. Per
ADR-0023's own history, a non-matching exclusion is indistinguishable from a genuine deny — the
false negative `vault-se5-probe.py` was written to detect. Nothing in CI would catch it, because the
tests invoke the script by `subprocess` and never traverse the harness.

**Four files must land in one commit:** the 11 notes, `.claude/settings.json` (×2 trees),
`tests/conftest.py`, `.github/scripts/validate-scripts.sh`. There is no partial state that works.

### Why the coverage gap forced the split

`vault-orphans.py` and `vault-reprospect.py` had **zero coverage** — no pytest, no
`validate-scripts.sh` — while both also carry the hardcoded `$HOME` import. Unverified code with a
hardcoded path to a directory being deleted was the highest-risk cell in the original single-change
plan, and it is the concrete reason this is now two changes rather than one.

**Change A lands their coverage first.** By the time B moves them, both are exercised as real
subprocesses with asserted outcomes, and B's GATE B1 adversarial run has something that can
actually fail.

By contrast `vault-refine-execute.py` is well covered — 12 adversarial tests including a real
end-to-end bank asserting the three-part atomic commit shape. No new behavioural test is needed for
it; only the harness-exclusion check above.

## Regression evidence

Each check below must be shown **failing without the change** before its task is ticked. Note what
the split bought: these are checks Change A already landed, so B is exercised by instruments that
existed and were green **before** B was written — not by instruments B ships alongside the behaviour
they certify.

| Check | Owner | Fails without B because |
|---|---|---|
| fleet import resolution | B | run any of the 5 scripts with **`python3 -P` and a broken `$HOME`** → `ModuleNotFoundError` on today's tree. ⚠ **`HOME=/nonexistent` ALONE PROVES NOTHING** — see the correction below |
| `settings.json` resolution | **A** | B repoints 11 targets; without B2.2 the exclusion names a path no note declares. **B is the first change that can break this check** |
| spec↔note inventory | **A** | must stay green — the relocation changes targets, not membership. A regression here means B edited the fleet roster by accident |
| standalone lint (F15) | B | all 11 targets are host paths today; the extended lint fails on the pre-change tree |
| render leaves a clean tree | B | without the `.gitignore` entry, `render` produces 11 untracked files |
| parity unchanged at 2 prefixes | B | a third prefix would appear if `bin/` were added to `lockstep` |

Row 2 is the strongest evidence in the change, and it exists only because of the split. Had the
`settings.json` check shipped inside B, its red state would have been **manufactured** — deliberately
pointing it at a nonexistent file — which proves the check can refuse but proves nothing about the
relocation. Landed in A against valid paths, it becomes a genuine tripwire that B is the first thing
in the repository's history to trip.

The corresponding honesty, carried in A's proposal rather than hidden: A's own red state for that
check **had** to be manufactured, because the tree was correct on the day it was written.

## Impact

- **Forks** get a self-contained tree. `git clone` + `render` yields a working vault with no
  user-global side-load and no `PATH` edit outside the repo.
- **Multi-vault skew becomes representable** — each vault carries its own fleet at its own version.
- **CI gains realism and loses a fiction**: `validate-scripts.sh` stops building a throwaway
  `$HOME/bin` and renders where the fleet actually ships. `conftest.py` loses an isolation axis —
  isolation comes from the throwaway vault alone rather than a fake `HOME`.
- **The `Standalone-vault lint (F15)` is extended** to fail on any `deploy_target` outside the tree,
  so the lint named for the principle can finally see this class of violation.
- **`~/bin` is decommissioned entirely.**
- **Operator action required:** `render` must be re-run by the operator after merge and deploy-down,
  because vault-side `render` writes to protected paths.

## Rollback

Every step is reversible and none destroys data.

- Revert the commit; run `render` to restore `~/bin` targets.
- The 3 in-tree targets never move, so the commit gate and publish guard are unaffected throughout.
- No Treasury, Tailings or Spoil content is touched (INV-9, INV-10 untouched).
- The only irreversible act is deleting `~/bin`, which is **last**, **operator-performed**, and
  gated on the full-estate re-verification passing. Until that point both locations may coexist.
