# Resolve the lifecycle subject from the declared estate, as the capability probe already does

## Why

`tools/pr-flow.py` answers two different questions about two different subjects, and only one of them
was fixed.

`capabilities()` resolves its subject from the **declared estate** — `VAULT_ROOT` and
`FRAMEWORK_ROOT`, read from the environment (lines 1312–1313). Its own docstring records why:

> ⚠ The subject is the **estate**, never the current directory. This is a session-scoped question and
> it was previously answered with a repo-scoped subject — `git rev-parse --show-toplevel`, i.e.
> whichever directory the shell happened to be in. Run from the vault, as every cold session is, that
> measured the vault and reported four red channels for a repository that is *supposed* to have no
> remotes.

`main()` still does exactly what that paragraph describes as the defect (line 2176):

```python
r = git(["rev-parse", "--show-toplevel"])
root = r.stdout.strip()
```

So the **lifecycle** subject is still discovered from the working directory. The fix landed for the
probe and stopped there, in the same file, under a docstring explaining why it was wrong.

**This is reached by following the documented procedure, not by misuse.** `96-Runbooks/session-bootstrap-loader`
step 4 instructs a session to run `--plan`, and every cold session is vault-rooted by design. In that
configuration the driver measures the **vault**, which by INV-14 has no remotes.

### Measured, 2026-09-10

Identical command, identical arguments; only the working directory differs:

```
python3 tools/pr-flow.py --plan --branch fix/render-root-resolution --base main
```

| cwd | result |
|---|---|
| `$VAULT_ROOT` | `BLOCKED at 'base': could not fetch origin/main and no local copy exists — and the repository exists.` — 1 step measured, 13 PROJECTED |
| `$FRAMEWORK_ROOT` | steps 1–4 **MEASURED**; `base` = `contains origin/main`; `commits` = `5 over origin/main`; CURRENT step `pushed` |

Both refuse conditions at line 1673 hold in the vault, measured directly rather than inferred:

| condition | in `$VAULT_ROOT` | in `$FRAMEWORK_ROOT` |
|---|---|---|
| `git fetch --quiet origin main` | `rc=128`, *'origin' does not appear to be a git repository* | `rc=0` |
| `git rev-parse --verify --quiet origin/main` | `rc=1` | `82a9d581…` |

The message tail *"— and the repository exists."* is simply the last stderr line of the vault's fetch
failure, which is why it reads as a non-sequitur. Line 1402 already carries a comment about that
generic hint misattributing failures.

**The failure mode is the dangerous one: it does not crash.** It prints a well-formed 14-step route
with a plausible blocked line. Nothing distinguishes "this branch is not ready" from "I measured the
wrong repository". In this instance it also **concealed a real finding** — run against the correct
subject, step 1 reports `Gate 4 UNSIGNED`, which the vault-rooted run never reached.

⚠ **One escalation is plausible but NOT proven, and is not claimed here.** `openspec/specs/maintenance/spec.md`
already carries *"Scenario: A push is emitted from a session whose working directory is a deployed
vault"*, requiring the emitted push to carry an explicit effective-target redirect. With `root`
resolved to the vault that redirect would be `git -C <vault> push` — satisfying the letter while
naming the wrong tree. The vault run blocked at `base` before composing any command, so this was
never reached and is untested. It is recorded as the reason the existing scenario does not already
cover this defect: it constrains the emitted command's target, never the subject the driver measured.

## What Changes

1. **`tools/pr-flow.py`** — resolve the lifecycle subject the way `capabilities()` already does:
   `FRAMEWORK_ROOT` when declared, the working-directory toplevel only when it is not. On the
   fallback path, print that the subject was **discovered rather than declared**, matching the
   probe's existing behaviour of suggesting the export instead of silently substituting.
2. **`tools/pr-flow.py`** — add `--repo PATH` so a caller can name a subject explicitly and override
   both. Without it a declared `FRAMEWORK_ROOT` would hijack a deliberate invocation against some
   other repository, converting one silent wrong subject into another.
3. **Refuse legibly on disagreement.** When a declared `FRAMEWORK_ROOT` and the cwd toplevel are both
   git repositories and differ, the driver states which one it took and why, in the route output —
   not in a comment.
4. **`tests/test_pr_flow.py`** — the discriminating case is two real trees: subject declared as A
   while cwd is B. A test that runs with cwd == subject passes against the defect and is worth
   nothing; if one is kept for coverage it is labelled non-discriminating in its own docstring.
5. **Spec delta** — one ADDED requirement in `maintenance`, asserting the subject is declared rather
   than discovered, and that a discovered subject is announced.

## Impact

- **Behaviour change is a correction of subject, not a widening of reach.** The driver acts on the
  repository the estate declares. No caller gains authority, no step is skipped, no guard is relaxed.
- **`--repo` is new surface** and is why this takes a proposal rather than shipping bare
  (`CONTRIBUTING.md` — a flag, persistent state, or exit semantics takes a proposal). Its three
  design questions: **state lifetime** — none, it is per-invocation and never persisted; **reachability**
  — it can only narrow the subject to a path the caller already names, and grants nothing the caller
  could not reach by `cd`; **exhaustiveness** — three sources (flag, declared estate, discovered cwd)
  with a stated total order and no silent fourth.
- **The route contract is unchanged.** Step names, executor/authority columns, exit codes and the
  `next.sh` single-slot discipline are untouched.
- ⚠ **Sequencing.** `fix/render-root-resolution` is in flight at step `pushed` and carries the same
  root-resolution disease one tool over (`vault-render.py`). These are independent branches and this
  one is deliberately cut from `main` so neither blocks the other, but the driver fix changes the
  instrument that lands the other branch. Landing order is an operator decision, recorded in tasks.

## Constitutional impact

Archiving syncs this delta into `openspec/specs/maintenance/spec.md`, whose frontmatter carries
`protects: [INV-2, INV-3, INV-6]` — all **Tier 0 (Inviolable)** per `constitution.md` §2. The
`AGENTS.md` hard stop therefore applies and the sign-off is human-only.

Checked against each protected invariant rather than asserted:

- **INV-2** (*one automated change, exactly one commit*) — untouched. No commit ceremony is altered.
- **INV-3** (*operational scripts are literate meta-script notes, rendered to the host, drift detected
  never auto-fixed*) — **not engaged.** `tools/pr-flow.py` is a repo-owned tool, not a
  `99-Operations/scripts/` meta-script note, and is not deployed into a vault by `render`. Nothing
  here edits a rendered file or adds auto-fix behaviour.
- **INV-6** (*deterministic scripts: no network, no LLM*) — the driver's existing network reads are
  unchanged in kind and number; this change adds no I/O. Resolving a path from an environment
  variable is not network access.

**The change narrows rather than widens.** After it, the driver measures exactly one repository —
the declared one — instead of whichever tree the shell stood in. No authority is granted.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADDED requirement plus a subject-resolution defect fix; INV-3 not engaged (repo tool, not a rendered meta-script note), INV-6 unchanged (no I/O added), INV-2 untouched; the driver's subject narrows to the declared estate and no authority is granted
```

## Verification

**Not yet built. No red proof exists, and none is claimed.** Per the estate's Definition of Done,
`[x]` means observed to fail without the change; every task in this change is `[ ]`.

The red proof this change is required to produce, stated in advance so it cannot be retrofitted:

| | fixed | broken (today) |
|---|---|---|
| subject declared A, cwd B | measures A | measures B ← the defect |
| subject undeclared, cwd B | measures B **and says it discovered it** | measures B silently |

The first row must **fail against the current code** before the fix, or the test is not
discriminating and does not count.

## Relationship to the standing root-cause finding

This is a seventh instance of the class already established by measurement: **a control that cannot
fail reports success.** The six recorded instances — `reconcile` comparing two trees, the UAT harness
measuring the live vault, a test passing against its own target defect, a compounded mutation matrix,
`template-parity` reporting 0 drift past 41 missing lines, `md-lint` silenced by `|| true` — share
this one's shape exactly: a well-formed confident report about the wrong subject, caught by a human
happening to look rather than by any other control.

It is also the *same defect family* as the branch already in flight: `vault-render.py` resolved notes
from one root and `deploy_target` from another. Two tools, one disease, found five weeks apart by
inspection rather than by instrument.

⚠ **This proposal does not claim to address that root cause.** It is a tactical fix, and the
established finding is that tactical fixes regress. It is offered as a defect fix on its own merits;
whether the control-registry approach is adopted is a separate and open decision.
