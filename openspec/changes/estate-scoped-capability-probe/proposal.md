<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: estate-scoped-capability-probe

## Why

`2026-08-06-bootstrap-capability-probe` shipped the cold-start capability probe and **named its own
residual** rather than papering over it:

> **Named residual:** the capability reporter is `tools/pr-flow.py --capabilities`, a **framework-repo**
> tool. A vault deployed without the repo alongside it has no reporter […] it is **not solved here** and
> is recorded rather than papered over.

That residual came due on **2026-08-11**, the first live cold start after it shipped. The runbook says
*run the probe*; the probe is a repo tool; the session begins in the **vault**; nothing declares where
the repo is. The adapter still carries an unfilled placeholder —
`vault-template/.claude/commands/vmm-session-rebooted.md:11` reads
`python3 <framework-repo>/tools/pr-flow.py --capabilities`. The agent bridged the gap the only way an
unaided agent can: it ran the tool from the current directory. `main()` derives its subject from
`git rev-parse --show-toplevel` (`tools/pr-flow.py:1061`), so the probe measured the **vault** and
reported this:

```
  repo slug (from remote, not folder name): UNRESOLVED
  READ  github state ....... FAILED (unsupported format string passed to NoneType.__format__)
  READ  git ls-remote ...... FAILED        AGENT / AGENT
  WRITE git push ........... FAILED        OPERATOR / OPERATOR via the INV-14 ask
        and the repository exists.
  WRITE gh mutations ....... UNAVAILABLE   OPERATOR / OPERATOR
```

Every remote row is red. **Not one of them is a defect in the environment.** The vault has no remotes
*because INV-14 requires it to have none* — it is private by default and deliberately has nowhere to
push. The instrument rendered a **governance guarantee holding** as a **capability failure**.

That inversion is the actual danger, and it is precisely the F30/F35 class the probe was built to
kill: an agent reading that output can bank *"GitHub is unreachable this session"* — the exact false
belief `--capabilities` exists to prevent. A second agent could equally well read `git push FAILED` as
something to fix. **If `git push` ever succeeds from the vault, that is an alarm, not a pass** — and
the current instrument has no way to say so.

## The structural error — subject, not syntax

The two crashes below are real but secondary. The root defect is that `--capabilities` answers the
wrong question.

| | Question | Correct subject |
|---|---|---|
| `route` / `ready` / `assert-preconditions` | "what may I do to **this repo**?" | cwd's git root — **correct today** |
| `--capabilities` | "what can **this session** do?" | the **estate** — not cwd |

A session-scoped question was implemented with a repo-scoped subject and then pointed at whatever
directory the shell happened to be in. Discovery was never appropriate here: **the estate has exactly
two members and both locations are known in advance.**

- **The vault** — where the session starts; `$VAULT_ROOT`, already authoritative in `config.env`.
  Expected state: **remoteless, by INV-14.** Absence of a remote is a **PASS**.
- **The framework repo** — where the GitHub channels live and where `OK`/`FAILED` is meaningful.
  Expected state: has `origin`. **Its location is declared nowhere machine-readable today.**

So the fix is not to make the probe fail more gracefully when it is lost. It is to stop it from being
lost: **declare the estate, probe each member against the state that member is supposed to be in.**

## What Changes

- **ADDED requirement** (`maintenance`): *The Capability Probe Measures A Declared Estate* — the probe
  SHALL take its subjects from declared roots, never from the working directory; SHALL evaluate each
  member against that member's expected state; SHALL report a remoteless vault as INV-14 holding, and
  a **writable** vault remote as a violation. 5 scenarios.
- **ADDED requirement** (`maintenance`): *A Probe Reports Diagnoses, Not Internal Errors* — no
  language-runtime exception text in a state column; a precondition failure named as a precondition
  failure; a quoted subprocess error attributed and selected for cause, not by position. 3 scenarios.
- **ADDED config** `FRAMEWORK_ROOT` — declared **exactly the way `VAULT_ROOT` already is**, in both
  template env files (see *Where `FRAMEWORK_ROOT` goes*). Not a new mechanism.
- **MODIFIED** `tools/pr-flow.py` — `--capabilities` becomes estate-shaped; the three reporting
  defects fixed. **`route` / `ready` / `assert-preconditions` keep cwd derivation, deliberately.**
- **MODIFIED adapter** `vault-template/.claude/commands/vmm-session-rebooted.md` — the
  `<framework-repo>` placeholder resolved to `"$FRAMEWORK_ROOT"`.
- **MODIFIED runbook** `vault-template/96-Runbooks/session-bootstrap-loader.md` — step 3's four layers
  reconciled with what the instrument actually reports (see *Instrument/runbook divergence*).

### Nature of the change — ordinary, not a constitution-override

Derived from `constitution.md` §3, `CONTRIBUTING.md:89-98`, and the **precedent set by PR #53**, not
from my own reading alone:

- `CONTRIBUTING.md:91` says the Informed-Upheaval Protocol applies if a change "modifies anything
  tagged `protects:` in the spec files"; `constitution.md` §3 scopes the protocol to an **override** of
  a Tier-0/Tier-1 element, and adds that "doc-only edits to `protects:`-tagged elements are rejected by
  CI without the ceremony." Read literally these two do not agree on ADD-only edits.
- **The precedent resolves it, and I follow it rather than re-deriving:** PR #53
  (`2026-08-06-bootstrap-capability-probe`) added a requirement to this same `protects:`-tagged
  `maintenance` spec, classified itself ordinary on ADD-only grounds, and merged. This change is the
  same shape, so it takes the same classification.
- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the test matters.
- This change is **ADD-only**. *Platform Capability Is Probed, Not Recalled* is **left verbatim** — it
  is correct, and it makes no claim about the probe's subject, so the new requirements sit orthogonal
  to it rather than amending it. Nothing is modified, weakened, or narrowed; no sacrifice to accept.
- Therefore: **ordinary OpenSpec change.**

⚠ Per the finding raised in the predecessor change and still open in the hardening queue,
`constitution-lint` performs **no diff analysis** — so CI passing is *not* evidence that this
classification is right. The classification above stands on the reasoning, not on a green check.

## Where `FRAMEWORK_ROOT` goes

`VAULT_ROOT` already established the pattern for a machine-specific absolute path, and this follows it
rather than inventing a second mechanism:

| File | Tracked? | Carries | `VAULT_ROOT` today | `FRAMEWORK_ROOT` added |
|---|---|---|---|---|
| `99-Operations/config.defaults.env` | public, tracked, sourced **first** | framework defaults + **path placeholders** | `export VAULT_ROOT="${HOME}/Vault"` under *"MUST be overridden in config.env with your absolute path"* | `export FRAMEWORK_ROOT="${HOME}/value-memory-mining"`, same placeholder block, same warning |
| `99-Operations/config.env.example` | tracked, copied to `config.env` | the personal-override worked example | `export VAULT_ROOT="${HOME}/Vault"  # set your absolute vault path` | `export FRAMEWORK_ROOT=…  # set your absolute framework-repo path` |
| `99-Operations/config.env` | **gitignored, live, personal** | the real machine values | the operator's real path | operator adds their real path (deploy-down, task 7.1) |

**How `/vmm-session-rebooted` picks it up, with no new plumbing:** step 1 of the runbook already runs
`source 99-Operations/config.env`, which sources `config.defaults.env` first and then applies the
personal overrides. So by the time step 3 runs, `$FRAMEWORK_ROOT` is exported in the same shell that
exports `$VAULT_ROOT`. The adapter's unfilled `<framework-repo>` placeholder becomes
`python3 "$FRAMEWORK_ROOT/tools/pr-flow.py" --capabilities --estate`, and the prime can no longer get
lost, because it stops looking for the repo and is *told* where it is.

Placeholder-not-blank is deliberate and matches `VAULT_ROOT`: a wrong-but-present default fails loudly
on the next line (`no such file`), where a blank silently degrades to the `UNDECLARED` path and looks
like a supported configuration when it is actually an unfinished setup.

## Design decision worth your dissent

**An undeclared `FRAMEWORK_ROOT` is a valid estate, not an error.**

A vault deployed without the repo alongside it is the exact case the predecessor change named. So an
unset `FRAMEWORK_ROOT` yields an estate of one member: vault layers reported normally, repo layers
reported `UNDECLARED (FRAMEWORK_ROOT not set)` — never `FAILED`. This closes the named residual by
making the degradation *legible* rather than by pretending the repo is always present.

## The write-scope layer is a protection self-test, and it writes

Operator instruction (2026-08-11): the prime SHALL verify that `VAULT_ROOT` is correctly configured
**and protected**, by attempting a real write into `40-Treasury/`, `96-Runbooks/`, and
`99-Operations/`. An earlier draft of this proposal declined to write into governed subtrees on INV-4
grounds; that reasoning is withdrawn. INV-4 forbids writing to Treasury **autonomously** — an
operator-specified startup self-test is not autonomous, and authorising it is exactly the operator
authority INV-4 reserves. The probe is not storing value in Treasury; it is testing the lock.

Because this check *does* write, its failure modes leave real artifacts, so each outcome carries its
own guidance. Reporting only pass/fail would hand the operator a red line with no next action:

| Write | Delete | Verdict | Guidance the probe must print |
|---|---|---|---|
| DENIED | — | ✅ protection holding | none needed; this is the expected result |
| SUCCEEDED | SUCCEEDED | ⛔ **protection is gone** | the subtree is writable and INV-4/5 rest on nothing this session. Stop governed work; the guard is harness-level, so check the sandbox `denyWithinAllow` list; re-probe before trusting any write |
| SUCCEEDED | **FAILED** | ⛔⛔ **protection gone + residue left** | worst case: a stray file now sits in a protected subtree. Print the **absolute path**, the exact `rm` the operator should run, and the `git status` check confirming it was never staged. Do not proceed and do not commit |

Design constraints that follow:

- The probe file is zero-byte, dot-prefixed, uniquely suffixed, and written at the subtree root, so a
  residue is unmistakably a probe artifact and not mistaken for content.
- Deletion is attempted in a `finally`, and its **result is checked** — an unchecked `rm` is how the
  third row becomes silent.
- The residue path must survive into the report even when the process is about to exit.
- Task 5.3/5.7 must exercise rows two and three by construction. Row one passes today, so a test that
  only covers it is the vacuous-pass failure the Definition of Done names.

**Scope: the live vault only.** `vault-template/` in this repo carries the same folder names
(`40-Treasury/`, `96-Runbooks/`, `99-Operations/`), but it is template source, not a live vault, and
the repo is writable by design. Probing it would report a protection failure on every run and train
the reader to ignore the check.

## Instrument/runbook divergence (found by this sweep)

The runbook's step 3 enumerates **four** layers and names write scope first. The instrument reports
**zero** of it — the write-scope layer was specified and never built. On 2026-08-11 the agent supplied
it by hand-rolling `touch` probes, which is exactly the "four worse probes were hand-rolled instead"
failure the predecessor change catalogued. Either the instrument gains the layer or the runbook stops
claiming it; this change chooses the former (task 3). **Recurred 2026-08-13 — see the reproduction log
below; it is a reflex the gap produces, not a one-off.**

## Reproduction log

The defects above were observed on 2026-08-11 during the sweep that opened this change. They are
re-observed here because a defect seen once in the session that found it is weaker evidence than one
that recurs, unprompted, in a session that was not looking for it.

### R2 — 2026-08-13, cold start, independent of this change

A `/vmm-session-rebooted` prime ran the runbook's step 3 from the vault, with no knowledge of this
branch. Every symptom reproduced verbatim:

```
CAPABILITY PROBE (measured now, not recalled)
  repo slug (from remote, not folder name): UNRESOLVED
  channel .................. state ......... runs / authority
  READ  github state ....... FAILED (unsupported format string passed to NoneType.__format__)
  READ  git ls-remote ...... FAILED        AGENT / AGENT
  WRITE git push ........... FAILED        OPERATOR / OPERATOR via the INV-14 ask
        and the repository exists.
  WRITE gh mutations ....... UNAVAILABLE   OPERATOR / OPERATOR
  READ  budget ............. 39/60 reads remaining, resets in ~32 min
```

Confirmed still-live at `tools/pr-flow.py:385-386` (the `else (None, None)` guard falling into the
success print) and `:399` (`splitlines()[-1]`, yielding the orphan `and the repository exists.`).
Line numbers in tasks 3.6 / 3.7 are **unchanged** and need no re-anchoring.

**New in R2 — the hand-roll recurred, and it was worse the second time.** The 2026-08-11 instance was
recorded above as a one-off. It is not: given a runbook that claims a write-scope layer and an
instrument that reports none, a second agent independently hand-rolled the same substitute —

```bash
for d in 40-Treasury 99-Operations 30-Sites 20-Claims; do p="$VAULT_ROOT/$d/.wprobe.$$"; \
  if (touch "$p" 2>/dev/null); then echo "$d: WRITABLE (OS)"; rm -f "$p"; \
  else echo "$d: DENIED (OS)"; fi; done
```

Two failures in that eleven-line substitute, both of which this change's tasks already predict, now
with a field instance behind them rather than a design argument:

| Predicted by | The hand-roll's actual behaviour |
|---|---|
| task 3.5c — *"an unchecked `rm` is exactly how the write-succeeded/delete-failed case becomes silent"* | `rm -f` — return value discarded, and `-f` suppresses the error besides. Had a governed subtree been writable **and** the removal failed, this probe would have printed `WRITABLE (OS)` and left residue in `40-Treasury/` with no mention of it. Row three of the write-scope table would have been silent, exactly as predicted |
| task 3.5a — the self-test names `40-Treasury/`, `96-Runbooks/`, `99-Operations/` | `96-Runbooks/` was **not probed**. The hand-roll substituted `30-Sites/` and `20-Claims/` — the agent measured where it wanted to write, not what the operator instruction says to verify |

The second row is the more instructive one. An improvised probe converges on the prober's own
interest, not on the specification, because the specification lives in a runbook the improviser is
mid-way through executing. This is the argument for 3.5 being *in the instrument*: a hand-roll cannot
under-cover a layer it does not choose the scope of.

**Bearing on the change:** no new requirement is owed — R2 lands inside the existing scope. It raises
the priority of task 3.5 relative to 3.6/3.7 (the crashes are cosmetic to a careful reader; the silent
residue is not), and it supplies task 5.6's adversarial rows with a real-world instance of the failure
they must construct. It also confirms 5.8's premise: the estate is reachable and the end-to-end run is
cheap, so there is no excuse for stubbing it.

## Blast radius (swept 2026-08-11, re-runnable)

```
grep -rn "pr-flow.py --capabilities\|--capabilities" --include=*.md --include=*.json \
  --include=*.env --include=*.yml . | grep -v node_modules | grep -v changes/archive
grep -rn "FRAMEWORK_ROOT\|framework-repo" vault-template/ docs/ AGENTS.md CLAUDE.md CONTRIBUTING.md
```

| Reference | Action |
|---|---|
| `vault-template/.claude/commands/vmm-session-rebooted.md:11` | **UPDATE** — `<framework-repo>` placeholder → `"$FRAMEWORK_ROOT"` |
| `vault-template/99-Operations/config.env.example` | **UPDATE** — `FRAMEWORK_ROOT` override line, beside `VAULT_ROOT` |
| `vault-template/99-Operations/config.defaults.env` | **UPDATE** — `FRAMEWORK_ROOT` placeholder in the path-placeholder block, beside `VAULT_ROOT` |
| `vault-template/96-Runbooks/session-bootstrap-loader.md` | **UPDATE** — step 3 layers reconciled |
| `CONTRIBUTING.md:31` | **no change** — run from the repo, where cwd derivation is correct |
| `openspec/specs/maintenance/spec.md:1076` | **no change** — left verbatim; ADD-only |
| `CHANGELOG.md:86`, archived changes | **no change** — historical records, correctly immutable |

## Procedure this change follows (read from history, not invented)

Reviewed newest-first: PR #60, #59, #58, #57, #56, plus #53 as the direct predecessor.

- **Branch + commit form** — `type/kebab-slug` branches (`feat/`, `fix/`, `docs/`, `ops/`, `chore/`,
  `release/`); commits `type(scope): imperative summary`. A change-opening commit uses
  `change(<slug>): …` (PR #53's `1ba6f08`).
- **Not every PR carries a change dir** — #56 (a script defect) and #57 (an ADR) carried none. This
  change alters `pr-flow.py` behaviour *and* adds requirements, so it needs one.
- **Live change dirs are undated** — PR #58 created `openspec/changes/flip-scope-review-blocking/`;
  the `2026-08-06-` prefix was applied by the archive PR. I had originally dated this directory, which
  is the archive-time name; **corrected to `estate-scoped-capability-probe/`**.
- **Landing is driven, never hand-composed** — `tools/pr-flow.py --plan --branch BR` first, then
  `--branch BR`, run exactly the emitted command, re-run to verify it landed (`CONTRIBUTING.md:21-41`).

### The one place precedent disagreed with itself — settled by the operator, 2026-08-11

The two most recent spec-bearing changes archived differently, and nothing documented which was right:

| | PR #53 (`ops/bootstrap-capability-probe`) | PR #58 + #59 (`feat/flip-scope-review-blocking`) |
|---|---|---|
| change dir created | already at `changes/archive/<date>-<slug>/` | at `changes/<slug>/`, undated |
| delta → `specs/maintenance/spec.md` | same PR (+36) | **separate** archive PR (+18) |
| CHANGELOG | same PR | backfilled in the archive PR |
| shape | propose + apply + archive **collapsed into one PR** | feature PR, then `chore/archive-*` PR |

**Operator decision (2026-08-11): this change ships in the #58 shape** — a feature PR carrying an
**undated** `openspec/changes/<slug>/` plus its implementation, with **no** sync into `openspec/specs/`
and **no** CHANGELOG entry; a following `chore/archive-<slug>` PR renames to `archive/<date>-<slug>/`,
syncs the delta, and backfills the CHANGELOG. This change is staged that way.

**This establishes no new precedent — it follows the existing one.** Measured across all 48 archived
changes: **40+ carry a dedicated `archive(<slug>): apply delta; stamp CHANGELOG` commit**, separate
from the change's own work. Exactly two archived inside the feature branch, both in early August —
`2026-08-04-add-pr-flow-driver` ("archive on the feature branch") and `2026-08-06-bootstrap-capability-probe`
("archive on the branch and apply the spec delta"). PR #53 is therefore the **deviation**, and per the
hardening queue it is the shape that exposed the Gate-4 approval-erasure defect (since fixed: the
driver now reads sign-off from the archived change by name).

A caution for anyone re-deriving this later: `enforce-inv7-secret-scan`'s tasks.md carries the line
"Archive **on the feature branch before merge** (else a second archive PR is owed)" — but its checkbox
is **`[ ]`, never ticked**, and that change's actual archiving commit is
`archive(enforce-inv7-secret-scan): apply access-control delta; v0.1.35 stamped`. It did not follow its
own line. Reading a repo-wide default out of that one unticked line is a mistake already made once in
this session.

The remaining nuance is **ordering, not location**: concurrent changes touching the same capability
spec archive in merge order (`add-template-mirror-driver`: "both touch `maintenance`") to avoid
batch-archive last-writer-wins. That is orthogonal to which PR does the archiving.

Documenting and enforcing that convention is **owed as a separate ordinary OpenSpec change** and is
deliberately **not** in this one — see task 7. Two reasons, both from the corpus rather than from
convenience: `scope-review` (Phase-B blocking) diffs a PR against the scope its body declares, and
this proposal declares a capability-probe reshape; and a grep of all six specs for "archive" returns
**zero**, so the convention is stated in no requirement — meaning a guard would enforce an unwritten
rule, the inverse of the `constitution.md` §4 class-9 defect. Requirement and guard ship together or
not at all.

## Regression evidence

Nothing is built yet — every task is `[ ]`. Per the standing Definition of Done, `[~]` is claimed only
when built and `[x]` only when a test was **observed to fail without the change**. The estate probe's
test must exercise the states the mechanism itself creates — remoteless vault, undeclared framework
root, vault-with-a-remote — not merely a happy path against a repo that already works.

## Impact

Behaviour of `route` / `ready` / `assert-preconditions` is unchanged. No schema changes. No existing
requirement modified.

**Deploy-down:** the live vault's `96-Runbooks/session-bootstrap-loader.md`, `CLAUDE.md`,
`.claude/commands/`, and `99-Operations/config.env` are deployed copies inside `denyWrite` —
operator-applied, never edited in-vault. The live `config.env` is gitignored and personal, so
`FRAMEWORK_ROOT` must be added there **by the operator**; the probe's `UNDECLARED` path is what keeps
a not-yet-updated vault honest rather than broken.
