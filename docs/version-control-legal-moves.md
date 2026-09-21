<!-- SPDX-License-Identifier: Apache-2.0 -->
# Version control — the legal move set, and the barred paths

**Purpose.** Enumerate what a git or GitHub command in this estate may legally be, so the shape is
*known* rather than *rediscovered*. Every prior instance of the ceremonies below was correct; the
shape nonetheless lived only in merge history, and reconstructing it from there cost a wrong-branch
commit during the v0.1.53 ship.

⚠ **This document is prose, and prose goes stale silently.** Its own writing measured
`CONTRIBUTING.md` claiming `main` carried *no required status checks* while the live ruleset
enforced **16**. Every table below therefore carries **the command that re-measures it**. Where this
document and a live measurement disagree, **the measurement wins and the disagreement is a defect** —
fix it here rather than working around it. Last measured **2026-08-26**.

## What this document covers, and what it does not

**Covers:** commands that reach GitHub, the four control layers that can refuse them, the ceremonies
that sequence them, and the query to run before a ceremony you have not performed.

⚠ **Does NOT cover, and this gap has already bitten:** **local git operations that can destroy work
without touching the network** — `rebase`, `reset --hard`, `branch -D`, `checkout -- <path>`,
force-push. Section 2a now enumerates that class, but the enumeration is younger and thinner than the
rest of this page. **Absence from this document is not evidence that a command is outside the
workflow.** `git rebase` is emitted by `pr-flow.py` on a documented path and was absent from the
first version of this page.

**Also not covered:** the change-management flow itself — proposals, gates, sign-off, the
proposal threshold. That is `CONTRIBUTING.md`'s job; this page is the *move set*, not the *process*.
Where the two overlap (the ceremonies in section 3), `CONTRIBUTING.md` is authoritative and this page
is a summary that can go stale.

---

## 1. BARRED — check these first

### 1.1 Refused on the agent's channel (Layer 1: `permissions.deny`)

Re-measure: `python3 -c "import json;print(json.load(open('.claude/settings.json'))['permissions']['deny'])"`

| Form | Both roots |
| --- | --- |
| `gh pr …` · `gh issue …` · `gh project …` · `gh repo view …` · `gh api graphql …` | denied |

The **vault** additionally denies `Edit()` on `/.claude/**`, `/40-Treasury/**`, `/99-Operations/**`,
`/96-Runbooks/**`, `/97-Molds/**` — 10 entries total vs the framework repo's 5.

### 1.2 Refused by the `gh` invocation-form allowlist (ADR-0045)

Re-measure: pipe a payload into `.claude/hooks/gh-invocation-guard.py`.

**Permitted, and nothing else:** `gh api <REST path>` · `gh auth status`.
**Everything else is refused by default rather than permitted by omission**, including forms Layer 1
never listed (`gh run`, `gh workflow`, `gh release`, `gh cache`, …). `gh api graphql` is excepted
back into deny: GraphQL has failed non-deterministically here four times, each a **silent no-op**.

⚠ It binds the agent's **typed** channel only. A fleet tool calling `gh` in a Python subprocess is
invisible to it, and composition or indirection defeat the matcher. It is a **tripwire for a
cooperating agent**, not an anti-evasion control.

### 1.3 Stopped by the outbound guard (INV-14)

Re-measure: read `OUTWARD` / `PUBLISH` in `.claude/hooks/outbound-publish-guard.py`.

**ASK** on a **reversible branch push** (`git push <branch>`) whose target is not the vault — its ref
can be force-pushed or deleted, so the ASK's auto-mode limitation is tolerable. ⚠ **The ASK does not
hold in auto mode** — a `PreToolUse` ASK silently proceeds there (measured 2026-09-20); it is relied
on only for the branch push, whose failure is reversible.

**HARD DENY (operator-only, every mode)** on all other outbound — it is **irreversible** and DENY is
not subject to the auto-mode silent-proceed: `git push … refs/tags/…` (a `v*` tag is frozen by the
ruleset), `git remote add|set-url` (incl. the `git -C … remote add` form), `gh repo create`,
`gh repo edit --visibility public`, `gh release create|edit|upload`, a REST write to a release
endpoint (`POST …/releases`, `PATCH|DELETE …/releases/{id}` — derived from §2b), anything touching
`uploads.github.com`, `npm|yarn|pnpm publish`, `twine upload`, `docker push`, `cargo publish`,
`gem push`. The operator runs these in their own terminal (via the ceremony), where the hook does not
fire.
**HARD DENY** also when the effective target resolves to a deployed vault — including via `cd … &&`,
`git -C <path>`, or `gh … -R <owner/repo>`.

### 1.4 Refused by GitHub itself (server-side rulesets, `enforcement: active`)

Re-measure: `curl -s https://api.github.com/repos/<slug>/rulesets` (anonymous read works; **note
`branches/main/protection` returns 401** — read the rulesets endpoint, not branch protection).

| Ruleset | Applies to | Rules |
| --- | --- | --- |
| `vmm-main-pr-and-checks-ADR-0034` (19666243) | `~DEFAULT_BRANCH` | pull request required · **16 required status checks** · no deletion · no non-fast-forward |
| `vmm-tag-immutability-v-ADR-0034` (19666225) | `refs/tags/v*` | no update · no deletion · no non-fast-forward |

**Consequences that bite in practice:**

- **Never commit to `main`.** It is PR-only. A CHANGELOG release cut takes its own branch.
- **A `v*` tag cannot be re-cut, moved or deleted.** Get the tag right the first time.
- `required_approving_review_count` is **0** — human review is convention here, not server-enforced.

### 1.5 Barred by ceremony, though the platform would allow them

| Form | Why | Use instead |
| --- | --- | --- |
| `gh pr merge --delete-branch` | cannot express a head precondition; bypasses retargeting of stacked children (killed PR #29); non-atomic deletion under a success tick | `gh api -X PUT …/pulls/N/merge -f sha=…`, then delete the branch as a separate verified step |
| `gh pr edit --base` | **silently no-ops** behind the Projects-classic GraphQL deprecation (F21·3) | `gh api -X PATCH /repos/<slug>/pulls/N -f base=<ref>`, then **re-read the base** |
| `sleep` to await checks | burns wall-clock, hides state | `tools/pr-flow.py --ready …` (exit 0 ready / 2 waiting) |
| Force-push after opening a PR | a body-derived check reads the **push-time** event payload | rebase *before* pushing; to fix a body, **push**, never re-run the job |

---

## 2. LEGAL — the permitted move set

Re-measure the emitted forms: `grep -rhoE '"git -C \{root\}[^"]*"' tools/pr-flow.py | sort -u`

| Operation | Sanctioned form | Runs | Authority |
| --- | --- | --- | --- |
| Read any GitHub state | `gh api <REST path>` (via `tools/gh_read.py`) | agent | agent |
| Check credential | `gh auth status` | agent | agent |
| Read remote refs | `git ls-remote` · `git fetch` | agent | agent |
| Publish a branch | `git -C <root> push [-u] origin <branch>` | agent | **operator** (INV-14 ask) |
| Delete a merged branch | `git -C <root> push origin --delete <branch>` | agent | **operator** (INV-14 ask) |
| Push a tag | `git -C <root> push origin refs/tags/vX.Y.Z` | agent | **operator** (INV-14 ask) |
| Retarget a PR | `gh api -X PATCH /repos/<slug>/pulls/N -f base=<ref>` + re-read | agent | operator |
| Merge a PR | `gh api -X PUT /repos/<slug>/pulls/N/merge -f merge_method=merge -f sha=<sha>` | **operator** | operator |
| Open a PR | `gh api -X POST /repos/<slug>/pulls -f title= -f head= -f base= -F body=@FILE` | **operator** | operator |
| Create a Release | `gh api .../git/ref/tags/vX.Y.Z && gh api -X POST /repos/<slug>/releases -f tag_name= -f make_latest=true -F body=@FILE` | **operator** | operator |
| Local branch ops | `git -C <root> switch <b>` · `git -C <root> branch -D <b>` | agent | agent |

**Why the `gh` mutations stay with the operator:** `gh` needs the OS keyring **and** no write token
is exported here by policy. Both, together — credential absence is the barrier the outbound rail
actually rests on. ⚠ Credential *reach* is a property of **which project directory the session
started in** (the `sandbox` block lives in per-root settings), so probe it; never recall it.

**`sha=` on the merge is a server-side precondition**, not decoration: if the head moved, GitHub
answers 409 and refuses rather than merging something unreviewed.

### 2b. The sanctioned write set — machine-readable, and the source of truth

`gh api` is a **wider** permission than the subcommands it replaces: `gh api -X DELETE /repos/o/r`
is permitted by form alone. `GET` is therefore unconstrained, and every **write** method reaches only
the endpoints enumerated here. This block is the one copy; the guards carry it because they must run
in roots that have no `docs/` (INV-6, stdlib-only, no runtime file reads), and an equality test fails
CI if any copy drifts. **Edit this block, never a guard's list alone.**

Fields are `method | endpoint | runs | authority | precondition | outbound`. `outbound: yes` means
reaching it publishes, so the INV-14 guard must raise its ask — a property of the *endpoint*, not of
the command's spelling, which is how the subcommand-shaped matcher missed the REST release form.

```gh-write-endpoints
POST   | /repos/{slug}/pulls             | operator | operator | none            | no
PATCH  | /repos/{slug}/pulls/{n}         | agent    | operator | re-read-base    | no
PUT    | /repos/{slug}/pulls/{n}/merge   | operator | operator | sha             | no
POST   | /repos/{slug}/releases          | operator | operator | tag-exists      | yes
DELETE | /repos/{slug}/releases/{id}     | operator | operator | none            | yes
POST   | /repos/{slug}/labels            | ci       | ci       | label-absent    | no
POST   | /repos/{slug}/issues            | ci       | ci       | issue-absent    | no
```

What the preconditions mean, and why each is not decoration:

- **`sha`** — the merge carries the head it was reviewed at; a moved head gets a 409, not a merge.
- **`tag-exists`** — `GET /repos/{slug}/git/ref/tags/{tag}` **before** the POST. This replaces
  `--verify-tag`, which has no REST equivalent. Without it, `target_commitish` defaults to a branch
  and the API **creates** the tag at that head — measured, so the precondition is the only thing
  standing between a typo'd version and a tag pointing at whatever `main` happened to be.
- **`re-read-base`** — the retarget is read back, because the GraphQL-era form silently no-opped.
- **`label-absent` / `issue-absent`** — a read decides whether the write happens at all, replacing a
  `2>/dev/null || true` that made an auth failure look identical to "already exists".

⚠ **`runs: ci`** names the Actions runner, where **no hook runs at all**. Those two rows are governed
only by the detector, and nothing at runtime will refuse them.

#### Deliberately excluded — decided, with the reasoning attached

Absence from the set above is already a refusal: every write is refused by default rather than
permitted by omission. These endpoints are listed anyway, because an endpoint left out **by decision**
and one left out **by oversight** are indistinguishable from the set alone — and the next reader who
needs one of these will otherwise re-derive the argument from scratch, or quietly add the row.

```gh-write-endpoints-excluded
PUT    | /repos/{slug}/rulesets/{id}  | control-plane-write
PATCH  | /repos/{slug}/rulesets/{id}  | control-plane-write
DELETE | /repos/{slug}/rulesets/{id}  | control-plane-write
```

**`control-plane-write` — why these stay out (decided 2026-09-19):**

1. **They edit the control plane, not content.** Every sanctioned row acts on a pull request, a
   release, a label or an issue. These act on §1.4's rulesets — `19666243` (main: PR required, 16
   required checks, no deletion, no non-fast-forward) and `19666225` (`v*` tags frozen).
2. **A ruleset `PUT` replaces the entire `rules` array**, so a hand-written payload silently drops
   `pull_request`, `deletion` or `non_fast_forward` (ADR-0038, Application). The damage needs no
   malice and announces nothing.
3. **The ruleset cannot protect itself.** `bypass_actors` is empty and `current_user_can_bypass` is
   `never`, so nobody can *evade* it — but an admin token can *rewrite* it. Its integrity is
   procedural, and this exclusion is the procedure.
4. **Layer ordering.** ADR-0034 establishes rulesets as *"the only control in the stack that runs
   server-side"*, binding agent, operator and admin identically. Sanctioning them here would let the
   agent-channel allowlist authorize edits to the layer that backstops every other layer — the
   weakest-bound channel gaining a documented path to dismantle the strongest control.
5. **Excluding them costs nothing that exists.** This allowlist binds the **agent's typed channel**;
   the operator runs `next.sh` in their own terminal, where no hook runs. ADR-0038 already scopes the
   command to the operator and carries the verified recipe (fetch the live ruleset → mutate only the
   contexts list → send it back → re-read to confirm). Two ruleset writes exist in the estate's whole
   record: the 2026-07-24 provisioning and the ADR-0038 completion.
6. **Reads are unaffected, and reads are what the estate is actually short of.** `GET` is
   unconstrained; measured 2026-09-19, anonymous `GET …/rulesets` returns **200**. Nothing here
   blocks the observation capability ADR-0038 says is owed.

⚠ **The ground is AUTHORITY, not capability.** ADR-0038's *"the agent cannot authenticate to perform
this"* was measured false on 2026-08-26 (`0b07ddc`): a session rooted in `$FRAMEWORK_ROOT` reaches the
keyring and `gh` authenticates. Whether that token carries repo-administration rights is **unmeasured**
— and the exclusion must not depend on the answer. A boundary resting on "it would fail anyway"
evaporates the moment the environment shifts, silently and with no event to observe.

⚠ **This is a known gap, not a closed question.** Nothing observes the live rulesets, and GitHub can
change ruleset parameters **without bumping `updated_at`**, so any future check must compare content,
never timestamps (ADR-0038, Residual). The exclusion keeps the write off the agent's channel; it does
**not** detect a ruleset that drifted, was edited in the web UI, or was rewritten by a token outside
this estate. **That detection is `github-state-reconcile`'s to build** — and when it exists, revisit
whether a reconciler needs a sanctioned write path to repair what it finds, which is the one plausible
reason these rows would ever be admitted.

---

## 2a. LOCAL commands that can destroy work without touching the network

**No control in section 1 sees these.** The deny list, the `gh` allowlist and the outbound guard all
key on *outward* mutation; the server-side rulesets protect `main` and `v*` tags, not your working
tree. These are refused by **nothing**.

| Command | Risk | Discipline |
| --- | --- | --- |
| `git rebase <base>` | rewrites local history; can conflict mid-way and leave a half-finished state that silently blocks branch deletion later | run it only when the branch genuinely lacks the base — **verify, do not assume** |
| `git reset --hard` | discards uncommitted work irrecoverably | commit or stash first |
| `git branch -D` | deletes an unmerged branch without warning (`-d` refuses; `-D` does not) | confirm the commits are ancestors of the base first: `git merge-base --is-ancestor <sha> origin/main` |
| `git checkout -- <path>` | discards local edits to that path | never on a path you have not just inspected |
| `git push --force-with-lease` | rewrites a **remote** branch; the outbound guard ASKs, but the destructive part is what it replaces | only on your own unmerged branch, never on `main` (the ruleset refuses it there) |

⚠ **A driver's emitted command is not exempt.** `pr-flow.py` emits `git rebase {base_ref}` at its
`base` guard. That guard keys on `is_outward_mutation`, and rebase is **local** — a scoping the
driver's own source calls *"correctly built, scoped to the wrong axis for this failure"*
(`tools/pr-flow.py:544`, hardening item 26, measured on PR #76). On a branch whose PR has just
merged, the guard can emit a rebase onto the commit that merged it. **Measured: that particular
rebase is a no-op** — git drops the commits as already upstream and fast-forwards. The lesson is not
that the driver is unsafe; it is that it can print a **false instruction**, and

> **the driver states its premise in its own `why:` line — verify that premise, and stop if it is
> false.** Here it was checkable in one command:
> `git merge-base --is-ancestor <sha> origin/main`.

## 3. The ceremonies — pointer, not a second copy

**`CONTRIBUTING.md` is authoritative for the ceremonies.** It owns "Landing a change",
"Shipping a version" (including step 0, the `release/vX.Y.Z` branch) and "Touching a constitutional
element". This page deliberately does **not** restate them.

An earlier version of this page did restate them, and that was a mistake of exactly the kind this
estate keeps paying for: a second copy of a procedure drifts from the first, silently, and a reader
cannot tell which is current. This session found a paragraph in `CONTRIBUTING.md` that had been
wrong for months — *"a red check does not block a merge"* against a ruleset enforcing 16 required
contexts. **Two documents describing one process is how that happens.**

What belongs here instead is the single fact the ceremonies depend on and the move set supplies:

| Ceremony | Branch class | Read |
| --- | --- | --- |
| Land a change | `change/` `feat/` `fix/` `docs/` `ops/` | CONTRIBUTING, "Landing a change" |
| Ship a version | `release/vX.Y.Z` | CONTRIBUTING, "Shipping a version" — **note step 0** |
| Deploy down | (vault commit) | CONTRIBUTING, plus the ⚠ below |

⚠ **One deploy-down step has no tool and no check, so it is stated in both places on purpose.**
`.claude/` is **not** lockstep, so `template-mirror.py` never carries `settings.json`; mirror and
render alone can deploy a hook that **nothing loads**, while `template-parity` *and* `reconcile` both
report 0 drift. For a non-lockstep file the verb is **merge the delta**, never copy from template.

## 3a. Branch names are the precedent record — re-read them before the first push

Branch prefixes are the class marker (`release/` `change/` `docs/` `fix/` `feat/` `ops/`), and the
merged name is written permanently into `Merge pull request #N from <owner>/<branch>`. That commit
line is what the shape query below reads. **Scope drifts during work; names do not — so before the
first push, rename the branch if it no longer describes what it delivers** (`git branch -m`, free
and history-preserving while unpushed; effectively frozen once the PR exists).

## 4. Before the first mutation of a ceremony you have not run

```bash
git log --oneline --merges          # unscoped; the shape, not the contents
```

Then open the previous PR **of that class** and read it end to end. Branch prefixes are the class
marker. Ask the **shape** question, not a content question: `git log <tag>..main --merges` excludes
the release PR by construction, which is precisely how step 0 above went missing.

**A procedure documented from step 1 is not evidence there is no step 0.**

**Any query that establishes scope is untruncated or reports its denominator.** Count before
slicing; a first-string match answers *"does one exist"* and is never an enumeration.

---

## 5. What has no guard at all

Stated plainly, because a document listing controls is read as a list of things that will stop you.

- **The framework repo has no client-side git hooks** (`core.hooksPath` unset; `.git/hooks/` is all
  `.sample`). Nothing local refuses a commit on `main` — only the ruleset does, at push time, after
  the work. The vault *does* have them (`core.hooksPath = 99-Operations/hooks`).
- **`pr-flow.py` is an emitter, not an interceptor.** It refuses to *advance*; it cannot prevent an
  action taken between invocations.
- **Nothing verifies hook registration** in either root — see the hardening queue.
- **`md-lint` is vacuous** (`|| true`), and `validate-scripts.sh` discards `vault_naming.py`'s exit
  code (no `set -e`), so its `ok` line prints unconditionally.
