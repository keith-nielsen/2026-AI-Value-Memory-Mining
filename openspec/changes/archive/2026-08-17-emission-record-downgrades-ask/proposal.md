<!-- SPDX-License-Identifier: Apache-2.0 -->

# Change: emission-record-downgrades-ask

## Why

The vault's failure log adopted **class 10 — unauthorized deviation from a codified route** on
2026-08-17, at operator direction. It is the oldest pattern in that catalogue: carried unnumbered
since 2026-07-01 as *"the F1/F15 throughline"*, invoked **eight times**, tallied **never**. Ten
attested instances in the tight set.

The stage-1 shape is always the same: **the driver prints the exact command to run, and the agent
retypes it wrong.**

On 2026-08-16 the driver emitted, with the instruction *"run exactly this"*:

```
git -C /home/administrator/Documents/repo/value-memory-mining push -u origin <branch>
```

The agent ran `R=…; cd "$R"; timeout 180 git -C "$R" push …` instead. `outbound-publish-guard.py`
resolves a command's effective target from **raw text**; `-C "$R"` captured an unexpanded variable
resolving to nothing, and the `cd` was not leading, so the guard fell back to the reported cwd — the
vault — and denied, **correctly**. The agent then read one denial as a capability class, and spent a
session handing the operator commands that were the agent's to run.

**Everything downstream of that came free from one mangled retype.**

### Why prose cannot fix it, stated from the record rather than from opinion

- **F19** recorded the rule.
- **F32** restated it as *"the part that must not regress"*, naming character substitution explicitly,
  and observed: *"the shortest, loudest feedback loop the system can produce did not change the next
  command. A guardrail that denies is doing everything a guardrail can do; if that does not generalise
  one command later, no amount of additional prose will."*
- **F37** banked the driver case on 2026-08-06. The same substitution recurred ten days later.

The operator's standing concern — that this recidivism looks unsolvable — is recorded with class 10
and is **not** claimed to be answered here. This change addresses **stage 1 only**.

### The mechanism already exists, aimed at the other half of the population

`write_saved_plan()` exists for exactly this failure, for the *operator*:

> *"Write the operator's command to disk so a SHORT line is what gets pasted. F14 and F26: the
> interactive paste channel corrupted two hand-offs and clobbered a repo file. The full text is
> printed for review; only a short invocation is typed."*

F14 and F26 are the operator-side instances of class 10. The fix was built and gated to
`runs == OPERATOR`, on the assumption that the agent transfers commands losslessly. F40 disproves the
assumption.

## What Changes

- **ADDED requirement** (`maintenance`): *An Outward Command Is Checked Against The Driver's Emission*
  — the record, the three-zone classification, and the downgrade-only invariant. 6 scenarios.
- **ADDED requirement** (`maintenance`): *A Downgrade Record Is Forgeable And Says So* — the limit is
  a requirement, not a footnote. 2 scenarios.
- **MODIFIED** `tools/pr-flow.py` — `emit()` also writes `.git/pr-flow/emitted.json`.
- **MODIFIED** `tools/ship-release.py` — same, or its pushes regress to ASK.
- **MODIFIED** `vault-template/99-Operations/scripts/outbound-publish-guard-script.md` — **the meta-script
  note, which is the source of truth; the rendered `.claude/hooks/…` artifact is NEVER edited
  directly** (INV-3, and the note's own frontmatter carries `deploy_target:`).
- **ADDED** ADR-0043.

## The design, and the invariant that makes it safe

`outbound-publish-guard.py` already has two tiers:

```
1. HARD DENY  outward op whose effective target is the deployed vault (INV-14)
2. ASK (loud) any other outward-replication or publish — "An ASK cannot proceed without an
   explicit human Yes in any permission mode: no outward op silently defers."
```

**Tier 2 already solves the ad-hoc case.** A one-off push to another repository raises an ASK, the
operator says yes, it runs. Nothing about that changes, and an earlier draft of this proposal that
turned "no record" into a **denial** is withdrawn: it would have converted a working ASK into a refusal
and manufactured the over-denial (RC-E) that trains readers to route around guards.

One tier is inserted, scoped by effective target:

| Zone | Command | Today | After |
|---|---|---|---|
| Vault (`$VAULT_ROOT`) | outward | HARD DENY | **unchanged** |
| Governed repo (`$FRAMEWORK_ROOT`) | outward, **matches a live emission** | ASK | **ALLOW, silent** |
| Governed repo | outward, no/expired/mismatched emission | ASK | **ASK + the diff** |
| Anywhere else | outward / publish | ASK | **unchanged** |

> **THE INVARIANT: the emission record may only ever DOWNGRADE an ASK to an allow. It may never
> create a refusal.**

Every failure mode — absent record, expired, wrong branch, mangled text, a bug in the comparison —
falls through to today's ASK. **This change cannot make anything stricter than it already is**, which
is what makes it shippable without a burn-in phase.

`$FRAMEWORK_ROOT` is already declared in `config.env` (from `estate-scoped-capability-probe`), and
`_targets_vault()` already resolves effective targets honouring `cd`, `git -C` and `gh -R`. It
generalises to `_zone(cmd, cwd) -> vault | governed | elsewhere`. No new concept is introduced.

### Why this inverts the incentive, which is the actual point

Today the prescribed route and a mangled improvisation cost the same: one ASK each. After this,
**running the driver's command verbatim is the frictionless path** and deviating is the one that stops
and shows a diff. The protocol stops being a rule the agent must remember and becomes the cheapest
thing to do.

It also **reduces operator interrupts**: driver-emitted pushes stop prompting, and only off-script
commands do. Fewer prompts and more safety together is unusual, and is available only because the
driver already knows what the correct command is.

**Every remaining ASK on the governed repo becomes a signal** — either the agent deviated, or the
driver's lifecycle has a gap. Both are worth knowing; neither is currently countable.

## The limit, stated as a requirement rather than a footnote

**The record is forgeable by the agent it constrains.** `.git/pr-flow/` is inside the agent's write
scope, so an agent that wrote its own `emitted.json` could silently authorise its own command.

This is **consistent with the stated posture and not a defect discovered late**: ADR-0018 describes the
rail as *"safe-by-default + governed guarantee, not a physical impossibility"* — a **tripwire for a
cooperating agent**. The threat model is agent **error**, and class 10 is an error class. A mistaken
retype does not also forge a matching record; that is the whole basis on which this works.

It is written into the spec because an unstated forgeable control is precisely the false-assurance
defect this repository has had to retract before (`constitution.md` §4, PR #85, six false rows). **A
green allow means "this matched a record", never "this was authorised".**

## Design decisions worth your dissent

**1. Silent allow, or quiet log line?** A silent allow is the incentive inversion; but a control that
succeeds invisibly cannot be audited afterwards. Recommendation: **allow, and print one line naming the
step it matched**, so the transcript shows which emission authorised it. Costs one line, keeps the
path frictionless, and makes the downgrade visible in review.

**2. Should `ship-release.py` be in scope now or next?** Its pushes regress to ASK if it does not write
records — which is *correct but noisier*. Recommendation: include it, because leaving it out ships a
known regression and the write is the same helper.

**3. Ad-hoc outward commands on the governed repo still ASK.** A hotfix push the driver does not model
prompts the operator. That is deliberate. If it stops being rare, that is evidence the driver's
lifecycle has a gap — and the ASK count is how we would find out.

## Nature of this change — ordinary, not a constitution-override

- `maintenance/spec.md` carries `protects: [INV-2, INV-3, INV-6]` (Tier 0), so the test matters.
- **ADD-only.** No existing requirement is modified, weakened or narrowed. No sacrifice to accept.
- It **adds** enforcement fidelity to INV-14 without changing what INV-14 means, and **removes no
  permission from anyone** — by the invariant above it cannot refuse anything that is allowed today.
- Follows the classification precedent of PR #53, #80, #87.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: ADD-only; two new requirements; no existing requirement modified, weakened or narrowed; the change cannot create a refusal
```

## Blast radius (swept 2026-08-17, re-runnable)

```
grep -rn "outbound-publish-guard\|PLAN_TTL_SECONDS\|saved_plan_path\|write_saved_plan" \
  --include=*.py --include=*.md --include=*.json . | grep -v node_modules | grep -v changes/archive
```

| Reference | Action |
|---|---|
| `vault-template/99-Operations/scripts/outbound-publish-guard-script.md` | **UPDATE — the source of truth.** Frontmatter `deploy_target:` renders it to `.claude/hooks/` |
| `.claude/hooks/outbound-publish-guard.py` (repo + vault) | **NEVER edited directly** — rendered output; drift is detected by `reconcile`, never hand-fixed (INV-3) |
| `tools/pr-flow.py:498` `emit()` | **UPDATE** — write the emission record |
| `tools/ship-release.py` | **UPDATE** — same helper (design decision 2) |
| `tools/inv6-offline-check.py:10` | **no change** — but the guard is AST-analysed and must stay clean: the record read is `pathlib`/`json`, no network, no `subprocess` |
| `tests/test_inv6_offline.py:98` | **no change** — parametrized over the guard note; must still pass |
| `openspec/specs/maintenance/spec.md:115` | **no change** — the deploy-target table already lists the note |
| `openspec/specs/maintenance/spec.md:840` | **no change** — the naming-vs-calling requirement already covers the guard |
| `openspec/adr/0018`, `0027` | **no change** — this refines the rail they define; ADR-0043 cites both |
| `CHANGELOG.md` | **no change here** — stamped at release |

## Regression evidence

Nothing is built. Every task is `[ ]`. Per the Definition of Done, `[~]` is built and `[x]` requires a
test **observed to fail without the change**.

The tests that matter are the **fall-through** ones, because the invariant is the safety property:
absent record, expired record, wrong branch, mangled text and a corrupt record must each still reach
ASK — and a test suite proving only the happy path would prove nothing about the invariant.

## Impact

No existing behaviour becomes stricter. `route` / `ready` / `assert-preconditions` unchanged. The
vault's HARD DENY is untouched. Ad-hoc outward commands outside the governed repo are unaffected.
