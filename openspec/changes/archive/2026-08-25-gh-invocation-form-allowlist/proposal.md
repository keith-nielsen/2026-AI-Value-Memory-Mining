<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: gh-invocation-form-allowlist

Replace the enumerated `Bash(gh …:*)` deny entries with an **inverted rule** implemented as a
PreToolUse hook: `gh api` and `gh auth status` are permitted; **every other `gh` form is refused**,
and the refusal names the REST replacement that works.

**Decisions recorded in [ADR-0045](../../../adr/0045-gh-invocation-form-allowlist.md)** — context /
options / choice / consequence / **sacrifice**, per constitution §3 Gate 4.

## Why

### The defect this fixes is not "the agent uses the wrong `gh` form"

That is the symptom. The defect is that **every previous fix for it was a sentence** — a memory
entry, an imperative in a runbook, a caveat appended to an index line. The corpus already states the
governing reason, and it is the operator's framing rather than a new claim:

> **A rule which cannot refuse does not bind.**

The evidence for that is symmetric and was measured on 2026-08-20 rather than argued:

| Control | Form | Observed effect |
|---|---|---|
| memory line *"read with `gh api`, never a `gh pr *` subcommand"* | a sentence | **misled the agent twice**, by its own record, while loaded in context |
| the outbound-publish guard | a hook that returns `permissionDecision: deny` | refused twice in one session; the agent stopped both times |

The difference is not the agent's willingness. It is that one of them can say **no**.

### Layer 1 already works, and already demonstrates the reason it is not enough

The operator applied an enumerated deny list to the live vault on 2026-08-20:

```
"Bash(gh pr:*)", "Bash(gh issue:*)", "Bash(gh project:*)",
"Bash(gh repo view:*)", "Bash(gh api graphql:*)"
```

It was verified red-then-green in the same session, and the red is the important half:

```
$ gh pr list --limit 3
Permission to use Bash with command gh pr list --limit 3 has been denied.

$ gh api repos/keith-nielsen/2026-AI-Value-Memory-Mining/pulls --jq '.[] | "\(.number) \(.state) \(.title)"'
61 open deps(openspec): bump @fission-ai/openspec from 1.6.0 to 1.8.0
47 open deps(actions): bump actions/setup-python from 6 to 7
46 open deps(actions): bump actions/setup-node from 6 to 7
```

That the denial is a **control decision** and not a command failure is what makes it evidence.
`gh pr list` would have returned HTTP 401 regardless, because GitHub's GraphQL endpoint requires
authentication unconditionally and the session's `gh` credential measures `UNAUTHENTICATED`. A 401
would have proven nothing about the rule. The permission-layer message attributes the refusal to the
rule under test — the same red-before-green standard the fleet relocation established.

### Why the enumeration cannot be the end state — measured, not predicted

Two facts measured 2026-08-20 while verifying Layer 1:

1. **`vault-template/.claude/settings.json` carries the five `Edit(...)` denies and none of the five
   new `Bash(gh …)` denies.** The template is the seed for every deployed vault. So the fix is
   **vault-local on the day it was applied**, and every vault deployed from the template ships
   without it. This is not a future drift risk; the drift already exists.
2. **`value-memory-mining/.claude/settings.json` has no `permissions` block at all** — its top-level
   keys are `['hooks']`. A session started in the framework repo therefore has **no deny list
   whatsoever**, Layer 1 notwithstanding. The repo where framework changes are actually made is the
   one place the control is entirely absent.

Beyond the seeding gap, an enumeration is the wrong shape on its own terms. It lists the forms
already known to have gone wrong. `gh run`, `gh workflow`, `gh release view`, `gh search`,
`gh cache`, and every subcommand GitHub ships next are unlisted and therefore permitted, and each
will fail the same way for the same reason — GraphQL, or an unauthenticated keyring — and each will
be discovered by failing rather than by being refused.

**Enumeration drift is the defect class the constitutional diff gate was built to catch.** Fixing an
enumeration-drift symptom with a new enumeration is the shape of the problem, not the fix.

## What Changes

- **A new PreToolUse Bash hook, `gh-invocation-guard`,** added as a literate meta-script note at
  `99-Operations/scripts/gh-invocation-guard-script.md` (INV-3) and rendered to
  `.claude/hooks/gh-invocation-guard.py`.
- **The rule is an allowlist.** `gh api …` and `gh auth status` are permitted. Every other `gh`
  invocation returns `permissionDecision: deny`.
- **The deny message names the replacement.** A refusal that does not teach the working form produces
  a retry, not a correction — see *design decisions*.
- **`vault-template/.claude/settings.json`** registers the hook and gains the Layer-1 deny entries,
  closing gap (1) above so the control seeds into new vaults instead of stopping at this one.
- **`value-memory-mining/.claude/settings.json`** gains a `permissions` block and the hook
  registration, closing gap (2) — the framework repo currently has neither.
- **The Layer-1 deny entries are RETAINED, not replaced.** See *design decisions*; this is
  deliberate and is the one place the change is belt-and-braces rather than minimal.

## Design decisions, and the reasoning

### A NEW hook, not an extension of the outbound-publish guard

**This reverses the assumption stated when the layered fix was first sketched**, and it reverses it
on evidence gathered afterwards by reading the guard rather than recalling it.

The case for extending it looked strong: `outbound-publish-guard.py` is already a PreToolUse Bash
hook, already parses raw command text, already emits `permissionDecision: deny`, and is already
seeded through the template. Reuse over duplication.

Reading it changes the answer. Its own docstring declares **"Two jobs"** and its module comments
name it as *"one of the two most security-relevant scripts in the fleet"* — it is AST-analysed by
`inv6-offline-check` specifically to prove it invokes no subprocess. It also rests on a stated
invariant that the change would sit directly beside:

> ⚠ **This function cannot cause a refusal.** That is the invariant the mechanism rests on: the
> record may only ever DOWNGRADE a confirmation to an allowance, never create one.

Adding an unrelated refusal class to that file means every future edit to `gh`-form policy is an
edit to the exfil guard, and every regression in `gh`-form policy is a regression in a file whose
correctness is load-bearing for INV-14. The blast radius of the most security-relevant script in the
fleet should not grow to accommodate an ergonomics rule about REST versus GraphQL.

A separate hook is also **independently testable**, which matters more here than it looks. Both
hooks are pure `stdin` JSON → `stdout` JSON contracts, so a second hook costs one more note, one
more render target, and one more test module — and buys a policy that can be exercised, changed and
reverted without touching the exfil path at all.

**Cost, stated plainly:** two hook processes now run per Bash tool call instead of one, and the
`PreToolUse` matcher array grows a second entry.

⚠ **Multi-hook decision precedence is NOT assumed by this proposal.** Whether Claude Code takes the
most-restrictive decision across several matching hooks, or the first, or the last, is harness
behaviour this change depends on and **has not been measured**. Task G1.1 measures it — with the
outbound guard's ASK and this guard's DENY raised by the same command — **before** any other task
proceeds. If precedence turns out to favour an earlier `allow`, the design falls back to extension
and the ADR records the reversal.

### The rule is an inversion, and that is the entire point

A deny-list answers *"which forms have burned us?"* An allowlist answers *"which forms are known to
work?"* — and the second list is short, stable, and derived from a measured platform constraint
rather than from incident history:

| Form | Disposition | Why |
|---|---|---|
| `gh api <REST path>` | **allow** | measured working against a repo the probe reports `private: false` |
| `gh auth status` | **allow** | the capability probe's own instrument; must not be refused by the thing it measures |
| everything else | **deny** | either routes through GraphQL (401 unconditionally) or needs a keyring the confined session measures `UNAUTHENTICATED` |

`gh api graphql` is denied **as a `gh api` special case**, not by falling through — it is the one
`gh api` form that carries the failure the rule exists to prevent, and Layer 1 already enumerates it.

New GitHub subcommands are refused by default rather than permitted by omission. That is the
property an enumeration cannot have at any length.

### The deny message names the REST replacement

A refusal that says only *"denied"* leaves the agent to re-derive the working form at exactly the
moment it has already demonstrated it cannot. The outbound guard learned this the expensive way and
recorded it in `_unresolved_redirect_hint`:

> A guard that reports only its verdict makes its reader derive the cause at the moment they have
> already shown they cannot.

So the message carries the mapping — `gh pr list` → `gh api repos/{owner}/{repo}/pulls`,
`gh pr view N` → `gh api repos/{owner}/{repo}/pulls/N`, `gh issue list` →
`gh api repos/{owner}/{repo}/issues` — and states the reason once: **GraphQL requires auth
unconditionally; REST does not.**

### The Layer-1 deny entries are retained

They are redundant with the hook on the happy path, and that is precisely why they stay.

**A hook that crashes exits 0, and exit 0 means defer — which means allow.** That is the documented
contract of both guards (*"Exit 0 always (silent = defer to normal flow)"*). A malformed JSON
payload, a missing interpreter, an unrendered hook after a fresh clone — every one of those fails
**open**. The `permissions.deny` list is enforced by the harness itself and does not depend on a
Python process starting successfully.

So the two layers have genuinely different failure directions: the hook is **general but fails
open**, the deny list is **enumerated but fails closed**. Keeping the enumerated entries for the five
known offenders costs five lines and covers the hook's own outage. This is the one deliberate
redundancy in the change, and it is recorded here so a later reader does not "simplify" it away.

## The three questions *(CONTRIBUTING threshold rule)*

1. **State lifetime — what is the exit condition?** The hook introduces **no persistent state**. It
   reads one JSON object from `stdin`, writes one to `stdout`, and exits; it opens no file, keeps no
   record, and has nothing to expire — unlike the emission record in the outbound guard, which is
   the reason that guard needed a lifetime answer and this one does not. Exit condition for the
   mechanism as a whole: removal of the hook registration.
2. **Reachability — which real invocation reaches this line?** Every Bash tool call reaches the hook
   entry point; the `gh` branch is reached by any command whose text contains a `gh` invocation.
   Unlike the harness *exclusion* studied in the relocation change — which no test can traverse —
   this hook **is** reachable by test, because its contract is `stdin`/`stdout` JSON and a test can
   feed it a payload directly. The one path no test reaches is registration itself: whether
   `settings.json` actually loads the hook is verified only by invoking a denied form through the
   real harness, which is why that is an explicit operator step (G4.2) and not a unit test.
3. **Exhaustiveness — do the categories partition?** The rule partitions `gh` invocations into
   allow / deny with no third bucket, and leaves non-`gh` commands untouched. But the categories
   that matter are **the states the matcher itself creates**, not the inputs GitHub offers:
   bare `gh`, an absolute path (`/usr/bin/gh`), a leading environment assignment
   (`GH_TOKEN=x gh …`), `gh` in a compound command (`cmd && gh pr list`), `gh` inside a quoted
   string or heredoc where it is data rather than a command, and `gh` reached through a shell
   variable or alias. Each is enumerated as a test case in `tasks.md` with its intended disposition
   stated **before** implementation, because the failure that matters here is a matcher that reports
   coverage it does not have.

## Nature of this change

It **adds** a refusal. No existing requirement is modified, weakened or narrowed; agent write scope
is unchanged; the outbound guard is untouched. It is strictly a narrowing of what the agent may run.

```constitutional-impact
touches: openspec/specs/access-control/spec.md, openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-4, INV-5, INV-6, INV-14]
overrides: none
basis: ADD of a refusal on an agent-invoked command form; agent write scope is byte-for-byte unchanged; the outbound-publish guard is not edited. The `maintenance` touch is the Script Inventory row the new fleet note obliges - a MODIFIED requirement that ADDS one table row and alters no sentence, no scenario and no SHALL; all three of its scenarios are preserved verbatim. No existing requirement is weakened or narrowed in either spec.
```

## Blast radius *(constitution §3 Gate 1)*

To be delivered as a pasted, re-runnable command transcript in `blast-radius-transcript.md` at
Gate 1 execution — **not composed from reasoning**, per the standing rule. The sweeps it must carry:

- every `gh ` invocation across `tools/`, `tests/`, `.github/`, `docs/`, `openspec/` and
  `vault-template/`, partitioned into live surface versus frozen record;
- every consumer of `gh` inside the fleet — `pr-flow.py` and `ship-release.py` are both known to
  invoke `gh`, and **`ship-release.py` is already recorded as using raw `gh` for reads**, which this
  rule would refuse. That interaction is the highest-risk cell in the change and is why the
  transcript is a gate rather than a formality;
- the `PreToolUse` registrations in all three `settings.json` files.

**Known non-trivial interaction, stated up front:** this rule constrains the **agent's** Bash
channel. A fleet script that shells out to `gh` from inside a Python process is not intercepted by a
PreToolUse hook at all — the hook sees the command that launched the script, not the subprocesses it
spawns. So the rule binds the agent typing `gh pr list` and does **not** bind `pr-flow.py` calling
`gh` internally. That asymmetry must be stated in the spec rather than discovered later; it is
recorded as a scenario, not left as a footnote.

## Regression evidence

Each check is ticked `[x]` only after being **observed to fail without the change**.

| Check | Fails without the change because |
|---|---|
| harness precedence probe (G1.1) | no assertion exists today about multi-hook decision precedence |
| denied form is refused | `gh run list` is unlisted in Layer 1 and runs today |
| allowed form is untouched | `gh api repos/…/pulls` must still exit 0 — a rule that breaks the replacement is worse than no rule |
| `gh auth status` is untouched | the capability probe calls it; refusing it would break the instrument that measures the channel |
| deny message names the replacement | asserted on message **content**, not merely on the decision — a refusal that does not teach is a retry generator |
| template seeds the control | `vault-template/.claude/settings.json` has no hook registration and no `Bash(gh …)` entries today — **measured 2026-08-20** |
| framework repo has a deny list | its `settings.json` top-level keys are `['hooks']` today — **measured 2026-08-20** |

## What this change does NOT fix — stated because the honesty is load-bearing

- **It does not stop the agent proposing a denied command in prose.** The hook intercepts execution,
  not suggestion. Proposing `gh pr list` to the operator remains possible and remains wrong.
- **It is a text matcher, so a compound or obfuscated command can pass it.** This is the same
  limitation the corpus already records for the INV-14 matcher, and it is not incidental — it is the
  accepted threat model: **a tripwire for a cooperating agent.** The failure being defended against
  is *forgetting*, not *evading*. A control that assumes an adversarial agent inside its own harness
  is a different and much larger change, and this proposal does not pretend to be it.
- **It fails open if the hook process dies** — which is why Layer 1 is retained rather than replaced.

## Impact

- The recurring `gh pr *` → 401 → re-derive-the-REST-form loop is refused at the point of execution
  instead of being re-learned from a memory line that has already failed twice.
- New vaults inherit the control from the template; the framework repo gains one for the first time.
- New GitHub subcommands are refused by default rather than permitted by omission.
- **Operator action required:** `render` must be re-run by the operator after merge and deploy-down,
  because vault-side `render` writes to protected paths.

## Rollback

Fully reversible, destroys nothing. Revert the commit and re-run `render`; the hook file is generated
output and is removed with its note. The outbound guard is not edited by this change, so INV-14
enforcement is unaffected at every point during and after rollback. No Treasury, Tailings or Spoil
content is touched (INV-9, INV-10 untouched).
