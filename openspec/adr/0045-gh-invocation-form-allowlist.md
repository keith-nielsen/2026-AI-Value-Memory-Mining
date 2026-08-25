<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0045 — `gh` invocation form is governed by an allowlist in its own hook

- **Status:** Proposed *(flip to Accepted on merge — tasks G5.2; ADRs 0032, 0033 and 0042 are the recorded reason this is a task)*
- **Date:** 2026-08-20
- **Change:** `gh-invocation-form-allowlist`

## Context

The estate has repeatedly established that GitHub must be read and mutated through `gh api` with an
explicit REST path, never through a `gh pr` / `gh issue` subcommand, **because the GraphQL endpoint
those subcommands route through is non-deterministic and therefore unsuitable to task in a
production system.** Its failure signature is the worst kind: a **silent no-op** — the command
reports nothing actionable and changes nothing, so a caller trusting its exit status proceeds on a
false belief.

Four recorded instances, all resolved by moving to REST:

| Date | Instance |
|---|---|
| 2026-07-18 | `add-ship-ceremony-tools` — *"a GraphQL mutation can fail silently where REST succeeds"* |
| 2026-07-19 | **F21** — `gh pr edit --body-file` exit 1 behind the Projects-classic deprecation, body unchanged |
| 2026-08-04 | **F21·3** — `gh pr edit --base` silently no-opped; the driver moved to `gh api -X PATCH` + re-read |
| 2026-08-24 | `seed-auto-memory-store` — *"changed nothing, while reporting nothing actionable"* |

The cost is already sunk and visible in `AGENTS.md`, which mandates a re-read after **every**
`gh`/GraphQL mutation. That is a standing workaround for a channel that cannot be trusted to have
acted, and it is cheaper to prohibit the channel than to keep paying for it.

⚠ **Correction, 2026-08-26 — this Context previously argued from authentication.** It read: *"because
GitHub's GraphQL endpoint requires authentication unconditionally while the confined session's `gh`
credential measures `UNAUTHENTICATED`. REST reads work; GraphQL reads 401."* The first clause is a
true platform fact; the second was **measured false**. A session launched with `$FRAMEWORK_ROOT` as
its project directory carries no `sandbox` block, reaches the keyring, and `gh auth status` reports
authenticated with `repo` and `workflow` scopes — so GraphQL is reachable there and the stated ground
evaporates exactly where the guard is most needed. Credential state is a property of *which directory
the session started in*, not of the platform, and could never have carried this rule. It was
additionally a regression against the corpus's own record: `seed-auto-memory-store` had already
written that `gh pr *` is denied *"precisely for"* the silent no-op. Corrected here to describe
reality rather than deleted, per the ADR-0042 precedent.

**This strengthens the decision rather than weakening it.** The G4.2 live proof was performed in a
session holding `repo` and `workflow` scopes: the guard refused a channel that genuinely worked, with
real mutation capability behind it, rather than one already broken by a missing credential.

That finding has been recorded three times as prose — a memory entry, an index-line caveat, and a
runbook note — and by the memory file's own account it **misled the agent twice anyway**.

Measured 2026-08-20, in the same session, the contrast is exact:

- the memory line, loaded in context, did not prevent the wrong form;
- the outbound-publish guard, a PreToolUse hook returning `permissionDecision: deny`, refused twice
  and was obeyed both times.

The operator's diagnosis is the one this ADR adopts: **a rule which cannot refuse does not bind.**
The remedy is not a better sentence; it is moving `gh` from the *informs* column to the *refuses*
column.

An enumerated harness deny list was applied to the live vault the same day and verified red-then-green
(`gh pr list` refused by the permission layer; `gh api …/pulls` still exit 0). It works, and it also
demonstrated its own insufficiency within minutes: `vault-template/.claude/settings.json` — the seed
for every deployed vault — does not carry the new entries, and `value-memory-mining/.claude/settings.json`
has no `permissions` block at all.

## Options considered

1. **Restate the rule more prominently in memory / CLAUDE.md.** Rejected. This is the option that has
   already failed three times. Restating a failed rule is not a remediation, and recording it as one
   would be the estate's own documented anti-pattern.
2. **Keep the enumerated deny list as the end state.** Rejected as insufficient, retained as a
   backstop. It lists the forms already known to have failed; `gh run`, `gh workflow`, `gh search`
   and every subcommand GitHub ships next are permitted by omission. This is enumeration drift — the
   defect class the constitutional diff gate exists to catch — so curing it with a longer enumeration
   reproduces the disease.
3. **Invert the rule inside the existing `outbound-publish-guard.py`.** This was the initially
   preferred option and it is **reversed here**; see *Decision*.
4. **Invert the rule in a new, dedicated PreToolUse hook.** Chosen.
5. **Wrap `gh` in a shim on `PATH` that refuses non-REST forms.** Rejected. It binds any caller
   including the fleet's own scripts, which legitimately invoke `gh` internally; it is invisible to
   the harness, so a refusal would be indistinguishable from a tool error; and it adds a global
   `PATH` artifact of exactly the kind ADR-0044 spent a whole change removing.

## Decision

Govern `gh` invocation form with an **allowlist** — `gh api` and `gh auth status` permitted,
`gh api graphql` explicitly excepted back into deny, every other form refused — implemented as a
**new** PreToolUse Bash hook carried as its own literate meta-script note (INV-3), registered in all
three `settings.json` files, and seeded through `vault-template/`.

The enumerated Layer-1 deny entries are **retained alongside it**, deliberately.

### Why a new hook, reversing option 3

The extension case was reuse: the outbound guard already parses raw command text and already emits
deny decisions. Reading the file rather than recalling it reversed the judgement.

- Its docstring declares **"Two jobs"**, and its comments name it *"one of the two most
  security-relevant scripts in the fleet"*; `inv6-offline-check` AST-analyses it specifically to
  prove it spawns no subprocess.
- It rests on a stated invariant — *"This function cannot cause a refusal … the record may only ever
  DOWNGRADE a confirmation to an allowance"* — that a new refusal class would sit directly beside.
- Consequently every future edit to `gh`-form ergonomics would be an edit to the file whose
  correctness is load-bearing for INV-14, and every regression in the former would be a regression
  in the latter.

Both hooks are pure `stdin`→`stdout` JSON contracts, so separation costs one note, one render target
and one test module, and buys a policy that can be changed or reverted without touching the exfil
path.

### Why both layers are kept

Their failure directions are opposite, and this is the load-bearing reason:

| Layer | Coverage | Failure direction |
|---|---|---|
| the hook | general — any `gh` form | **fails OPEN** (a hook that crashes exits 0, and exit 0 means defer) |
| `permissions.deny` | enumerated — five known offenders | **fails CLOSED** (harness-enforced; needs no process to start) |

A crashed interpreter, a malformed payload, or a fresh clone whose hooks are unrendered all resolve
to *permit* under the hook alone. Five lines of enumeration cover the general control's own outage.
This redundancy is recorded so a later simplification does not remove it as duplication.

## Consequence

- New GitHub subcommands are refused by default rather than permitted by omission.
- New vaults inherit the control from the template; the framework repo gains a `permissions` block
  for the first time.
- Refusals teach: the deny message carries the REST mapping, so a refusal produces a correction
  rather than a retry.
- Two hook processes run per Bash tool call instead of one.
- **The design has an unmeasured dependency.** It assumes a second hook's `deny` can override another
  hook's `allow`. Multi-hook `PreToolUse` decision precedence in Claude Code has **not** been
  measured, and task G1.1 blocks all other work until it is. If an earlier `allow` pre-empts a later
  `deny`, this ADR is superseded and the fallback is option 3.

## Sacrifice

**What is given up, stated plainly:**

- **Ergonomic reach.** Legitimate `gh` uses that are neither `api` nor `auth status` — `gh run watch`
  during CI, `gh release view` — become refused for the agent even where they would have worked. The
  allowlist is deliberately narrower than the set of commands that function; being refused a working
  command is the price of not re-deriving the broken ones.
- **Single-guard simplicity.** The estate now has two Bash PreToolUse hooks with overlapping input
  and different mandates. A reader must consult both to know what will be refused.
- **A control that will be credited with more than it does.** It binds the agent's own channel, not
  subprocesses the fleet spawns; it is a text matcher, so composition and indirection defeat it. It
  is a **tripwire for a cooperating agent** — the threat model is the agent *forgetting*, not
  *evading*. The spec states this rather than leaving it to be discovered, because a control whose
  limits are undocumented gets trusted past them.
- **It does not touch prose.** The agent can still propose a denied command to the operator in
  writing. Execution is governed; suggestion is not.
