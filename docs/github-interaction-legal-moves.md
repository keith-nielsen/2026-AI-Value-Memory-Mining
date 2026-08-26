<!-- SPDX-License-Identifier: Apache-2.0 -->
# GitHub interaction — the legal move set, and the barred paths

**Purpose.** Enumerate what a GitHub interaction in this estate may legally be, so the shape is
*known* rather than *rediscovered*. Every prior instance of the ceremonies below was correct; the
shape nonetheless lived only in merge history, and reconstructing it from there cost a wrong-branch
commit during the v0.1.53 ship.

⚠ **This document is prose, and prose goes stale silently.** Its own writing measured
`CONTRIBUTING.md` claiming `main` carried *no required status checks* while the live ruleset
enforced **16**. Every table below therefore carries **the command that re-measures it**. Where this
document and a live measurement disagree, **the measurement wins and the disagreement is a defect** —
fix it here rather than working around it. Last measured **2026-08-26**.

---

## 1. BARRED — check these first

### 1.1 Refused on the agent's channel (Layer 1: `permissions.deny`)

Re-measure: `python3 -c "import json;print(json.load(open('.claude/settings.json'))['permissions']['deny'])"`

| Form | Both roots |
|---|---|
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

**ASK** on `git push`, `git remote add|set-url`, `gh repo create`, `gh release create|edit|upload`,
`npm|yarn|pnpm publish`, `twine upload`, `docker push`, `cargo publish`, `gem push`.
**HARD DENY** when the effective target resolves to a deployed vault — including via `cd … &&`,
`git -C <path>`, or `gh … -R <owner/repo>`.

### 1.4 Refused by GitHub itself (server-side rulesets, `enforcement: active`)

Re-measure: `curl -s https://api.github.com/repos/<slug>/rulesets` (anonymous read works; **note
`branches/main/protection` returns 401** — read the rulesets endpoint, not branch protection).

| Ruleset | Applies to | Rules |
|---|---|---|
| `vmm-main-pr-and-checks-ADR-0034` (19666243) | `~DEFAULT_BRANCH` | pull request required · **16 required status checks** · no deletion · no non-fast-forward |
| `vmm-tag-immutability-v-ADR-0034` (19666225) | `refs/tags/v*` | no update · no deletion · no non-fast-forward |

**Consequences that bite in practice:**
- **Never commit to `main`.** It is PR-only. A CHANGELOG release cut takes its own branch.
- **A `v*` tag cannot be re-cut, moved or deleted.** Get the tag right the first time.
- `required_approving_review_count` is **0** — human review is convention here, not server-enforced.

### 1.5 Barred by ceremony, though the platform would allow them

| Form | Why | Use instead |
|---|---|---|
| `gh pr merge --delete-branch` | cannot express a head precondition; bypasses retargeting of stacked children (killed PR #29); non-atomic deletion under a success tick | `gh api -X PUT …/pulls/N/merge -f sha=…`, then delete the branch as a separate verified step |
| `gh pr edit --base` | **silently no-ops** behind the Projects-classic GraphQL deprecation (F21·3) | `gh api -X PATCH /repos/<slug>/pulls/N -f base=<ref>`, then **re-read the base** |
| `sleep` to await checks | burns wall-clock, hides state | `tools/pr-flow.py --ready …` (exit 0 ready / 2 waiting) |
| Force-push after opening a PR | a body-derived check reads the **push-time** event payload | rebase *before* pushing; to fix a body, **push**, never re-run the job |

---

## 2. LEGAL — the permitted move set

Re-measure the emitted forms: `grep -rhoE '"git -C \{root\}[^"]*"' tools/pr-flow.py | sort -u`

| Operation | Sanctioned form | Runs | Authority |
|---|---|---|---|
| Read any GitHub state | `gh api <REST path>` (via `tools/gh_read.py`) | agent | agent |
| Check credential | `gh auth status` | agent | agent |
| Read remote refs | `git ls-remote` · `git fetch` | agent | agent |
| Publish a branch | `git -C <root> push [-u] origin <branch>` | agent | **operator** (INV-14 ask) |
| Delete a merged branch | `git -C <root> push origin --delete <branch>` | agent | **operator** (INV-14 ask) |
| Push a tag | `git -C <root> push origin refs/tags/vX.Y.Z` | agent | **operator** (INV-14 ask) |
| Retarget a PR | `gh api -X PATCH /repos/<slug>/pulls/N -f base=<ref>` + re-read | agent | operator |
| Merge a PR | `gh api -X PUT /repos/<slug>/pulls/N/merge -f merge_method=merge -f sha=<sha>` | **operator** | operator |
| Open a PR | `gh pr create --base … --head … --title … --body-file …` | **operator** | operator |
| Create a Release | `gh release create vX.Y.Z --verify-tag --latest -t … --notes-file …` | **operator** | operator |
| Local branch ops | `git -C <root> switch <b>` · `git -C <root> branch -D <b>` | agent | agent |

**Why the `gh` mutations stay with the operator:** `gh` needs the OS keyring **and** no write token
is exported here by policy. Both, together — credential absence is the barrier the outbound rail
actually rests on. ⚠ Credential *reach* is a property of **which project directory the session
started in** (the `sandbox` block lives in per-root settings), so probe it; never recall it.

**`sha=` on the merge is a server-side precondition**, not decoration: if the head moved, GitHub
answers 409 and refuses rather than merging something unreviewed.

---

## 3. The ceremonies — legal sequences end to end

**Every ceremony is driven. Walk the driver; do not hand-compose the sequence.**

| Ceremony | Branch class | Sequence |
|---|---|---|
| Land a change | `change/` `feat/` `fix/` `docs/` | `preflight.py .` → `pr-flow.py` (14 steps) → archive on the branch **before** the PR → PR → checks → merge → delete remote + local |
| Ship a version | `release/vX.Y.Z` | **step 0: cut the branch and the `## [X.Y.Z]` CHANGELOG section, land it as a CHANGELOG-only PR** → `ship-release.py vX.Y.Z` → push tag → `gh release create` → re-run until the tag↔Release parity tally → `template-mirror.py <VAULT>` |
| Deploy down | (vault commit) | `template-mirror.py` (LOCKSTEP only) → `render` in the vault → **merge non-lockstep deltas by hand** → one `ops(deploy-down)` commit |

⚠ **Deploy-down's third step has no tool and no check.** `.claude/` is **not** lockstep, so
`template-mirror.py` never carries `settings.json`; mirror + render alone can deploy a hook that
**nothing loads**, while `template-parity` and `reconcile` both report 0 drift. For a non-lockstep
file the verb is **merge the delta**, never copy from template.

⚠ **A change directory archives on the feature branch BEFORE the PR opens.** Archiving syncs spec
deltas into the canonical specs; several checks are red until it happens and green after.
`openspec archive` names the directory from **UTC** — read the name back, never predict it — and it
moves files one level deeper **without rewriting relative links** (`../../adr/` → `../../../adr/`).

---

## 4. Before the first mutation of a ceremony you have not run

```
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
