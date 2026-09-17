# Prefer REST over GraphQL-routed forms, and detect the difference automatically

## Why

The lifecycle driver emits `gh pr create` at its pull-request step while the estate's own
invocation-form allowlist (ADR-0045) refuses that exact form. The same driver uses `gh api` with an
explicit REST path at three other steps, each with a written rationale for avoiding the subcommand.
**The rule existed, was applied three times, and was missed once** — and nothing compared the
emissions against the guard, so the gap persisted rather than being caught on the next run.

That is the shape of the whole problem: not a missing rule, but a rule with no instrument behind it.

**Measured 2026-09-18 rather than swept for.** An AST enumeration over 15 Python files in `tools/`,
`.claude/hooks/` and `.github/scripts/` (0 parse failures), plus a full read of both tracked `.sh`
files, all 40 `.yml`/`.yaml` files and all 15 literate meta-script notes, found **nine live `gh`
invocation sites — two conforming, seven not**:

| Site | Form | Kind |
|---|---|---|
| `tools/gh_read.py:112` | `gh api <path>` | executed — conforms |
| `tools/pr-flow.py:1420` | `gh auth status` | executed — conforms |
| `tools/pr-state.py:83` | `gh pr view --json` | executed |
| `tools/pr-state.py:168` | `gh run list --commit` | executed |
| `tools/pr-flow.py:1919` | `gh pr create` | **emitted to the operator** |
| `tools/ship-release.py:343` | `gh release create` | **emitted to the operator** |
| `.github/workflows/openspec-canary.yml:49,51,55` | `gh label create` · `gh issue list` · `gh issue create` | executed in CI |

**Which subcommands route through GraphQL is documented nowhere authoritative.** The `gh` manual
describes how a caller *chooses* an API; it never states which built-in commands choose for you. Any
claim that an audit has found them all is unfounded by construction — which is why previous attempts
kept surfacing another one.

It is, however, measurable. Per `gh help environment`, *"Set to `api` to additionally log details of
HTTP traffic."* Measured on `gh version 2.45.0 (2025-07-18 Ubuntu 2.45.0-1ubuntu0.3)`:

| Form | Endpoint actually hit |
|---|---|
| `gh pr list` · `gh issue list` · `gh pr view` | `POST /graphql` |
| `gh run list` | `GET /repos/{slug}/actions/runs` **and** `/actions/workflows` |

Two things that measurement settles, both of which would have been got wrong by reasoning:

- **`gh run list` is REST already.** A non-conforming *form* and a GraphQL *channel* are different
  findings, and only the second can fail silently. That site is owed conversion for conformance, not
  for risk.
- **The measurement cannot be carried forward.** It describes one binary on one date. The canary's
  three calls run on a GitHub Actions runner shipping a *different, newer* `gh`, so their channel is
  unmeasured and unknowable from here. **Where the channel depends on a binary you do not control,
  the form is the only thing you can pin.**

## What Changes

1. **The detector, built first and red first.** A test that enumerates every `gh` invocation in the
   tree by mechanism — AST for Python, `run:` blocks for workflows, code fences for the literate
   notes — and submits each form to `gh-invocation-guard.py`, **imported rather than restated**.
   Restating a gate's rule instead of importing it is the estate's class-9 defect and is what this
   change exists to stop repeating. Its first run must name exactly the non-conforming sites; that
   list, not a human sweep, becomes the conversion scope.
2. **Convert the seven.** `pr-state.py` ×2, the two emitted forms, the canary's three.
3. **`pr-state.py` REST-first read** — already built on this branch: `gh_read.pull_request` is tried
   first and `graphql` now means *"the GraphQL-only fields were actually read"* rather than "the
   channel was GraphQL".
4. **`mergeStateStatus` is populated from REST `mergeable_state`** instead of reported as
   `UNAVAILABLE (GraphQL-only)`. It is the same enum lowercased.
5. **Document surfaces, in this same change** — `docs/version-control-legal-moves.md` rows *Open a
   PR* and *Create a Release*, `AGENTS.md`, `CONTRIBUTING.md`, `docs/USING-THIS-TEMPLATE.md`, and the
   vault's `vmm-repo-github-card.md` (`CARD-VERSION` bumped). A converted driver with a stale table
   is two controls disagreeing, which is the defect being fixed, relocated.
6. **`tests/test_emitted_command_shape.py` changes premise.** It asserts `-R <slug>` on emitted `gh`
   commands; `gh api` takes the slug inline in the path, so that assertion dies with item 2 and must
   change in the same commit or fail looking like a regression. Its scope also widens: today it reads
   only `ship-release.py`'s `_emit_next(…)` sites and never sees `pr-flow.py`'s `emit(…)` sites,
   which is the second reason `gh pr create` stood unnoticed.

## Impact

- **The operator's pasted command changes shape.** `next.sh` will carry
  `gh api -X POST repos/{slug}/pulls …` instead of `gh pr create …`. Same step, same authority, same
  one invariant command to run.
- **Three conversion traps, recorded so they are not rediscovered.** `/issues` returns pull requests
  as well — every PR is an issue — so the canary's dedupe needs `select(.pull_request == null)` or it
  silently stops opening issues it should open. `gh api` returns one page unless `--paginate`, where
  the subcommands paged silently. And `gh run list` issues **two** requests, so a single
  `/actions/runs?head_sha=` call drops workflow names if any caller uses them — **determine that
  before converting**.
- **`gh label create` currently ends `2>/dev/null || true`**, so an auth failure is indistinguishable
  from "the label already exists". The REST replacement separates absent (404, create it) from broken
  (fail the step). This change therefore closes a live instance of the estate's catalogued
  `|| true` vacuity defect.
- **No new capability is granted.** Every replacement is the same operation through a different
  endpoint, by the same actor, under the same authority.

## Constitutional impact

Archiving syncs this delta into `openspec/specs/access-control/spec.md`, whose frontmatter carries
`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`. Checked against each rather than
asserted:

- **INV-14** (outbound rail) — **unchanged in reach, strengthened in form.** The same operations
  cross the same rail with the same authority; `gh` mutations remain the operator's, the INV-14 ask
  still fires on `git push`. No endpoint is added that was not already reachable.
- **INV-6** (deterministic scripts: no network, no LLM) — untouched. The detector is **offline and
  static**: it reads files and submits strings to a guard. It makes no network call, which is also
  why it can run in CI.
- **INV-7** (no secrets) — untouched; no credential handling changes.
- **INV-4 / INV-5** (write scope) — untouched; no new write target.
- **INV-8** (Crucible independence) — not engaged.
- **CONST-02** — engaged only in that the allowlist becomes enforceable rather than aspirational.

```constitutional-impact
touches: openspec/specs/access-control/spec.md
protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]
overrides: none
basis: ADDED requirements plus conversion of seven call sites to the already-permitted gh api form; no capability granted, no rail relaxed, no actor changed — the change makes an existing Accepted allowlist (ADR-0045) mechanically enforced rather than attention-enforced
```

**No new ADR is owed, and this is the load-bearing reading.** ADR-0045 is already Accepted with the
allowlist *"`gh api` and `gh auth status` permitted … every other form refused"*. The `gh pr create`
row in `version-control-legal-moves.md` is a **carve-out with no ADR behind it** — it survives on the
fact that a PreToolUse hook cannot reach the operator's terminal, not on any recorded decision that
the GraphQL channel is safe when a human types it. This change closes a conformance gap against a
decision already taken. ⚠ **This reading lowers the Gate 4 bar and should therefore be checked by the
operator against ADR-0045 §Decision before it is relied upon.**

## Verification

- **The detector is observed to fail first**, naming the non-conforming sites, before any conversion.
  A detector written after the fixes proves nothing.
- **Each converted site keeps a behavioural test**, not merely a form check — in particular the
  canary's dedupe count must be shown to exclude pull requests.
- **Channel evidence is dated and version-pinned** (`gh 2.45.0`), recorded in
  `gh-form-findings-ledger.md`, and explicitly not carried forward to the CI runner's binary.
- **Full suite green**; baseline on this branch measured 2026-09-18 at **424 passed** after rebase
  onto `a22c2ea`, with the REST-first `pr-state.py` refactor already applied.
