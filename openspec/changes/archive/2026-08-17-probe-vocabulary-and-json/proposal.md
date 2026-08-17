<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: probe-vocabulary-and-json

## Why

The capability probe is the instrument the session prime instructs every cold start to **trust before
making any capability claim**. Its report is more precise-looking than it is precise, in four ways
measured over 2026-08-16/17 (hardening-queue item 29).

**1. A row is named for what it infers, not what it measures.** `pr-flow.py:1204-1207` runs
`gh auth status` and checks the exit code and output — that measures **a credential**. The row prints
`gh mutations`. The runbook already has the right name: `session-bootstrap-loader` step 3 lists the
layer as *"**`gh` credential** — an operator keyring is unreadable from a confined session; a tool
reporting its own token 'invalid' is describing *that process*, not the operator's account."* **The
spec is correct and the instrument drifted from it.**

**2. Three conditions, two tokens.** `gh` present + authenticated → `OK`; `gh` present + no usable
credential → `UNAVAILABLE`; `gh` **absent** → `UNAVAILABLE (gh not installed)`. Two genuinely
different facts with different remedies, separated only by a parenthetical.

**3. The state column has no controlled vocabulary at all.** `AGENT` and `OPERATOR` are module
constants (`:61-62`). Every *state* is a bare literal inlined at its print site, so there is no
discoverable legal set and **a new state can be created by typo**. Measured 2026-08-17, the printed
literals are:

```
grep -oE "'(OK|FAILED|UNAVAILABLE|UNDECLARED|UNRESOLVED|PROTECTED|UNPROTECTED|SKIPPED|UNMEASURED)[^']*'|\"INV-14 HOLDING\"" tools/pr-flow.py | sort -u
```

| Today | Verdict |
|---|---|
| `FAILED` `PROTECTED` `UNPROTECTED` `SKIPPED` `UNAVAILABLE` `UNDECLARED` `UNRESOLVED` | single-word — keep |
| `UNPROTECTED+RESIDUE` | single token, no space — **parses fine, keep** |
| `INV-14 HOLDING` | space |
| `OK (dry-run)` | space + parenthetical, and it smuggles **evidence** into the state |
| `UNMEASURED (channel unreachable)` | space + parenthetical, smuggles a **reason** |
| `OK via <channel>` (built dynamically) | space, smuggles the **channel** |

**4. The report mixes two epistemic kinds under look-alike tokens.** `git push … OK (dry-run)` was
**attempted**; `gh mutations … UNAVAILABLE` was **never attempted** — a precondition was inspected. A
reader cannot tell which they hold. That confusion is the direct cause of F40: the agent read an
inspected precondition as an attempted channel, generalised one denial into a capability class, and
spent a session handing the operator commands that were the agent's to run.

## What Changes

- **ADDED requirement** (`maintenance`): *A Capability State Is A Single Word Naming What Was Found*
  — the controlled vocabulary, the naming rule, and the constant-declaration requirement. 5 scenarios.
- **ADDED requirement** (`maintenance`): *A Capability Report Distinguishes Inspection From Attempt*
  — the evidence field and the channel it names. 3 scenarios.
- **MODIFIED** `tools/pr-flow.py` — row rename, the three-token credential vocabulary, states as
  module constants, multi-word states split into state + fields, and `--capabilities --json`.

## The vocabulary — operator decision, 2026-08-16

| Condition | Token |
|---|---|
| `gh` present, credential usable | **`AUTHENTICATED`** |
| `gh` present, no usable credential | **`UNAUTHENTICATED`** |
| `gh` not on PATH | **`ABSENT`** |

Rejected, with reasons kept because the reasoning is the reusable part: **`UNAUTHENTICATABLE`** claims
it *cannot* be authenticated — false, the operator's shell authenticates fine, and it is the exact
overclaim F40 records. **`NOAUTH`** is mashed and ambiguous between *not attempted* / *not configured*
/ *not possible*. **`IMPOSSIBLE`** for the absent case is a claim about the world that `apt install gh`
falsifies. **`UNAVAILABLE`** is **retired rather than narrowed** — reusing a token with a tighter
meaning makes every past transcript ambiguous.

⚠ **Axis note the parser must know:** `AUTHENTICATED`/`UNAUTHENTICATED` are one axis (the credential);
`ABSENT` is another (the tool). **`ABSENT` means the credential state is UNKNOWN**, not
"unauthenticated". Stated in the spec, not left to inference.

## The naming rule this settles

> **A state token names what was FOUND IN THIS PROCESS. It never names what is possible in the world.**
> Test: could this token be falsified by something outside this process? If yes, it is the wrong word.

`AUTHENTICATED` ✓ · `UNAUTHENTICATED` ✓ · `ABSENT` ✓ · `IMPOSSIBLE` ✗ · `UNAVAILABLE` ✗ (*unavailable
to whom?*). This is F35 and F40 compressed into a naming convention, which is where it will actually
get applied.

## Design decisions worth your dissent

**1. `OK` is kept where it honestly means "the operation succeeded".** Rule D argues for naming the
finding, which would give `REACHABLE`, `ACCEPTED` and so on per row. **Recommendation: don't.** That
forks vocabulary across rows for little gain, and what `OK` was actually smuggling — the channel, the
dry-run-ness, the reason — moves into its own fields where a parser can read it. The tokens that get
better names are the ones where a better word genuinely exists: `HOLDING`, `AUTHENTICATED`, `ABSENT`.

**2. The evidence field carries the channel it exercised, not just the kind.** `attempted` alone would
not have prevented F40; `attempted:python-subprocess` would, because the mismatch with the Bash channel
becomes visible **in the output** instead of only in the source. That is item 29-A, which was
downgraded from defect to **latent divergence** on 2026-08-17 (the probe's `AGENT` verdict was
correct — the agent can push) but remains real: the probe cannot see the guard, so the two could
diverge with no warning.

**3. A test asserts every emitted state is in the declared set.** Without it, the constants are
documentation and a typo still invents a state. This is the difference between writing the vocabulary
down and enforcing it.

## Answered on paper, not built — item 29-A2

A saved plan is written only for `runs == OPERATOR` steps, so the AGENT-run outward steps carry no
expiry, branch pin or precondition re-assertion. **This was originally filed as a defect on the premise
that push is the operator's step; that premise was wrong** (F40's correction — push is the agent's
step). The remaining question is whether an agent re-running a stale outward command needs the
protection a human gets. **Not answered here, and deliberately not built:** ADR-0043's emission record
now covers the specific hazard (a command that does not match what the driver emitted no longer passes
silently), which weakens the case for a second mechanism. Recorded so it stays owed rather than
forgotten.

## Nature of this change — ordinary, not a constitution-override

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the test matters.
- **ADD-only** against that spec. No existing requirement modified, weakened or narrowed.
- It changes an instrument's *reporting*, not any invariant's meaning. No sacrifice to accept.
- Precedent: PR #53 / #80 / #87 / #91.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only; two new requirements; no existing requirement modified, weakened or narrowed
```

## Blast radius (swept 2026-08-17, re-runnable)

```
grep -rn "capabilities\|gh mutations\|INV-14 HOLDING\|UNMEASURED" --include=*.py --include=*.md \
  . | grep -v node_modules | grep -v changes/archive
```

| Reference | Action |
|---|---|
| `tools/pr-flow.py` capabilities block | **UPDATE** — the whole of this change |
| `vault-template/96-Runbooks/session-bootstrap-loader.md` | **UPDATE** — step 3 already says `gh credential`; add the token set so the runbook and the instrument agree |
| `vault-template/.claude/commands/vmm-session-rebooted.md` | **no change** — it names layers, not tokens |
| `tests/test_pr_flow.py` | **UPDATE** — any assertion on the old tokens |
| `openspec/specs/maintenance/spec.md` | **ADD** two requirements |

## Regression evidence

Nothing is built; every task is `[ ]`. Per the Definition of Done, `[x]` requires a test **observed to
fail without the change**. The test that matters most is the vocabulary-closure one — it is the only
thing that stops the next state being invented by typo, and it must be shown to fail against a
deliberately-introduced stray token.

## Impact

No behaviour change to `route` / `ready` / `assert-preconditions`. `--json` is additive; the human
table remains the default. Two tokens are **retired** (`UNAVAILABLE`, and `OK` in the credential row),
which is a reporting change only — no caller of this repository parses that column today, and the
`--json` mode exists so none ever has to parse the table again.
