# Prefer REST over GraphQL-routed forms, and constrain the channel that replaces them

## Why

The lifecycle driver emits `gh pr create` at its pull-request step while the estate's own
invocation-form allowlist (ADR-0045) refuses that exact form. The same driver uses `gh api` with an
explicit REST path at three other steps, each with a written rationale. **The rule existed, was
applied three times, and was missed once** — and nothing compared the emissions against the guard, so
the gap persisted rather than being caught on the next run.

That is the shape of the problem: not a missing rule, but a rule with no instrument behind it.

### What the 2026-09-18/19 investigation established

**Nine live `gh` invocation sites, measured by AST over 15 Python files (0 parse failures) plus a
full read of both `.sh` files, all 40 `.yml` files and all 15 literate notes. Two conform, seven do
not.** The detector built in this change names exactly those seven.

**Channel is not form.** Measured under `GH_DEBUG=api` on `gh 2.45.0`: `gh pr view`, `gh pr list` and
`gh issue list` reach `POST /graphql`; **`gh run list` is REST already**. A non-conforming *form* and
a GraphQL *channel* are different findings and only the second fails silently. Scoping this work by
"which commands use GraphQL" would have left `gh run list` unaddressed and the canary miscounted.

**Which subcommands route through GraphQL is documented nowhere authoritative**, and the measurement
does not carry: it describes one binary on one date, and the canary runs on an Actions runner with a
different, newer `gh`. **Where the channel depends on a binary we do not control, the form is the
only thing we can pin.** That is the argument for an allowlist over an audit — an audit expires.

### What the prior-art survey changed — the reframing

Three public implementations of command-layer enforcement were surveyed
(`navikt/cplt`, `stSoftwareAU/VibeCoder` #1371, `honnibal.dev`). The consensus is unanimous, and two
of them say it about their own shipped code: **a PATH shim or argv guard is a soft barrier against
accident, not a boundary against intent.** cplt: *"This is Layer 3, a soft barrier … For a hard
boundary, lean on the kernel sandbox and server-side branch protection."* Every one of them moved
**down a layer** to fix it — scoped credentials, egress control, kernel sandboxing, server-side
protection.

**This estate already operates at that layer, more completely than any of them:** no write token is
exported, so `gh` measures `UNAUTHENTICATED`; egress is a single filtering proxy; INV-4/5 are
OS-enforced read-only mounts, measured PROTECTED every session.

⚠ **Therefore the `gh`-form guard is a CORRECTNESS control, not a security boundary** — which
ADR-0045's corrected Context already states: GraphQL is refused *"for non-determinism, not for
authentication"*, and the authentication-based ground was **measured false**. Two proposals were
raised and **rejected** on this basis: a thirty-three-entry `permissions.deny` expansion, and a `gh`
PATH shim. Both are enforcement machinery for a boundary the credential layer already holds.

### The consequence that this change must answer

**`gh api` is a *wider* permission than the seven subcommands it replaces.**
`gh api -X DELETE /repos/{owner}/{repo}` is permitted by form. Executed calls are harmless here — the
agent holds no credential — but **emitted** commands are pasted by the operator **with a real
credential**. Converting to `gh api` without constraining its content moves the risk to the one path
where consequence is highest.

Unlike the `gh` subcommand space, which grows with every release, **the write-side endpoint set is
finite, small, and already enumerated** in `docs/version-control-legal-moves.md`. So the answer is
not another blocklist: it is to make that existing table the thing the controls read.

## What Changes

1. **The detector** (`tests/test_gh_form_conformance.py`) — built and observed red first, naming
   exactly seven sites. Enumerates by mechanism (AST, workflow `run:` blocks, note fences), runs the
   shipped guard as the oracle, and **designs out two of the guard's blind spots**: it unwraps command
   substitution, and treats unlexable input as a finding rather than a skip.
2. **Convert the seven** to `gh api`, each with its measured trap.
3. **Split the `gh api` permission by METHOD.** `GET` stays unconstrained — reads are the safe
   majority and enumerating them is the ocean again. **Writes (`-X POST|PATCH|PUT|DELETE`) are
   restricted to an enumerated endpoint set**, about seven entries for the estate's entire lifecycle.
4. **One source of truth for that set, carried in the guard note and pinned to the doc by a test.**
   The guard must stay self-contained — it renders into roots that have no `docs/` — so it carries the
   list, and a CI test asserts the table in `version-control-legal-moves.md` and the guard's list are
   the same. Drift fails the build. Restating a rule without an equality test is the class-9 defect.
5. **`pr-state.py` REST-first read** — already built on this branch — plus populating
   `mergeStateStatus` from REST `mergeable_state` instead of reporting it unavailable.
6. **Server-side preconditions on emitted mutations.** `sha=` on merge already; an explicit
   `GET .../git/ref/tags/{tag}` before `POST .../releases`, replacing `--verify-tag`. A precondition
   enforced at GitHub is the only control that survives being pasted into a shell we do not control.
7. **Document surfaces in the same change**, because a converted driver with a stale table is two
   controls disagreeing — the defect being fixed, relocated.

## Impact

- **The operator's pasted command changes shape** — `gh api -X POST repos/{slug}/pulls …` in
  `next.sh` instead of `gh pr create …`. Same step, same authority, same one invariant command.
- **A new refusal exists.** Both the guard and the detector can now refuse a write to an
  unsanctioned endpoint. If the enumeration is wrong in the strict direction, it blocks work that was
  fine.
- **Three measured conversion traps**, recorded so they are not rediscovered: `/issues` returns pull
  requests (the canary's dedupe needs `select(.pull_request == null)` or it silently stops opening
  issues); `gh api` returns one page without `--paginate`; and `gh run list` issues **two** requests,
  so collapsing it to one drops workflow names unless no caller uses them.
- **A live defect is closed incidentally**: the canary's `gh label create … 2>/dev/null || true`
  makes an auth failure indistinguishable from "already exists" — the estate's catalogued `|| true`
  vacuity defect, in CI.
- **No new capability is granted.** Every replacement is the same operation, by the same actor, under
  the same authority, through a documented endpoint.
- **Estate consistency:** the guard is a literate note under `vault-template/`, so the change reaches
  the framework repo, the vault template and the deployed vault by render + mirror, with
  `template-parity` proving the deploy-down. ⚠ **The vault has no CI**, so vault-side conformance
  rests on the deployed hook and parity, never on the detector — stated so it is not assumed.

## Constitutional impact

Archiving syncs this delta into `openspec/specs/access-control/spec.md`, whose frontmatter carries
`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`. Checked against each:

- **INV-14** — **narrowed, never widened.** The same operations cross the same rail with the same
  authority; `gh` mutations remain the operator's. The method split makes the outbound surface
  *smaller* than `gh api` alone allows today.
- **INV-6** — untouched. The detector is offline and static; the guard remains stdlib-only with no
  network call, which is why both can run in CI.
- **INV-7** — untouched; no credential handling changes.
- **INV-4 / INV-5** — untouched; no new write target.
- **INV-8** — not engaged.
- **CONST-02** — engaged only in that an existing allowlist becomes mechanically enforced rather than
  attention-enforced.

```constitutional-impact
touches: openspec/specs/access-control/spec.md
protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]
overrides: none
basis: ADDED requirements, conversion of seven sites to the already-permitted gh api form, and a METHOD-based narrowing of that form so writes reach only documented endpoints; no capability granted, no rail relaxed, the outbound surface strictly smaller than today
```

**No new ADR appears owed.** ADR-0045 is already Accepted with the allowlist *"`gh api` and
`gh auth status` permitted … every other form refused"*; the `gh pr create` row in
`version-control-legal-moves.md` is a carve-out with no ADR behind it. ⚠ **This reading lowers the
Gate 4 bar and should be checked by the operator against ADR-0045 §Decision before it is relied
upon.** If the method split is judged a *new* decision rather than an enforcement of an existing one,
it needs its own ADR and this proposal should be split.

## Verification

- **The detector was observed to fail first** — red, naming exactly seven sites, before any
  conversion. Recorded verbatim in `tasks.md` §1.
- **Each converted site keeps a behavioural test**, not merely a form check; in particular the
  canary's dedupe count must be shown to exclude pull requests.
- **The doc/guard equality test must be observed failing** on a deliberately divergent table.
- **Channel evidence is dated and version-pinned** (`gh 2.45.0`) in the vault's
  `gh-form-findings-ledger.md`, and explicitly not carried forward to the Actions runner's binary.
- **Full suite green.** Baseline on this branch measured 2026-09-18 at **424 passed** after rebase
  onto `a22c2ea`.
