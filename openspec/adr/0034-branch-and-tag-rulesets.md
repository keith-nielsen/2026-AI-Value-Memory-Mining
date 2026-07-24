<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0034 — Server-side branch & tag rulesets: the first guard that binds the operator, not just the agent

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-07-24)
**Date:** 2026-07-24
**Change:** `record-github-rulesets` (recording change, **no spec delta**). Repository configuration
only (two GitHub rulesets, provisioned by `gh api`). **No `vault-template/` delta, no `protects:`-tagged
element touched, not a `constitution-override`.** A recording ADR: its purpose is that a deliberate
departure from GitHub defaults is discoverable and attributable, never mistaken later for a platform bug.
**Relates / extends:** ADR-0022 (OS-enforced agent write scope — the *agent-side* runtime rail this
complements); ADR-0027 (release-object-per-tag + INV-14 guard conformance — the *local* ship-ceremony
guard this backstops server-side). **Answers, at the strongest layer:** the F10 (tag-before-merge / tag
on the wrong commit), F21 (GitHub-as-one-oracle), and F26/RC-7 (denial displaces execution to the one
unguarded actor) records in the live vault's `determinism-failure-modes-claude` Site.

## Context

Every runtime guard the operation has built to date is **agent-side and local**: the OS write-scope
sandbox (ADR-0022) binds the agent's shell; the INV-14 PreToolUse guard text-matches the agent's
outward commands; `ship-release.py` proves merge-ancestor before it emits a tag command. Each protects
the repository **from the agent**.

**None of them binds the operator.** F10 is the proof: the agent handed over a bundled command block
and the *operator* ran it, landing `v0.1.15` on the wrong commit on local **and** remote. F26 is the
same shape one level up — a hand-composed `cp` handed to the operator wrapped in the terminal and
clobbered a repo file. The synthesis named this RC-7: **every increment of agent-side denial displaces
the operation onto the one actor the sandbox does not bind — the operator — through channels
(terminal width, keyring, network) that no local guard can observe.** The trusted surface shrinks; the
emitted-command surface grows; only the first was ever costed.

The operation has also concluded, from the F27 recurrence (a verbatim repeat of F25 whose corrective
was already binned `ENFORCE` as prose), that **the problem is not knowledge, it is runtime enforcement**:
a rule that depends on any actor — agent or human — electing to remember it has the reliability of
memory, which is the thing this program exists to distrust.

**GitHub rulesets are the only control in the stack that runs server-side, after a ref leaves the
machine.** They evaluate at the repository before the ref lands, so they bind the agent, the operator,
a mistyped `git push`, and a confused `gh` call **identically** — and cannot be bypassed by any local
mistake (verified against `docs.github.com` 2026-07-24). This is the missing layer the failure corpus
has pointed at since F10 (RC-1b: "one operator hour, server-side, closes the F10 class at the strongest
layer").

## Decision

Provision **two rulesets** on `keith-nielsen/2026-AI-Value-Memory-Mining`. **Plan constraint found live
(2026-07-24): `evaluate` (dry-run) enforcement is Enterprise-only** (`HTTP 422` on this plan), so the
originally-intended evaluate→burn-in→active discipline is unavailable. Adapted: provision directly at
**`active`**, and provision the `main` ruleset **without `required_status_checks`**, adding that rule by
a later `PATCH` once a real PR confirms the exact check-context names — because a wrong required context
deadlocks all merges and cannot be dry-run here. `active`-without-checks is the burn-in equivalent this
plan allows (PR-required + merge-commit-only enforce immediately, all safe; checks added deliberately).
Both carry an **empty bypass list** (`current_user_can_bypass: never` — binds even the admin) and
**name ADR-0034 in the ruleset name itself**, so the enforcement announces its own rationale at the
moment of a block.

**Ruleset 1 — `vmm-tag-immutability-v-ADR-0034`** · target: tags matching `refs/tags/v*` · rules:
- **restrict updates** (`update`) — a published version tag is **frozen to its commit**; it cannot be
  moved. The categorical F10 close: the driver ensures the tag is *created* on the right commit, the
  ruleset ensures it can never be *moved* to a wrong one.
- **restrict deletions** (`deletion`) and **block force pushes** (`non_fast_forward`) — a published
  release tag cannot be deleted or force-rewritten.
- **`creation` is deliberately NOT restricted** — a normal first `git push refs/tags/vX.Y.Z` still
  works; only mutation of an existing tag is denied. (Immutable published tags are also a supply-chain
  integrity gain.)

**Ruleset 2 — `vmm-main-pr-and-checks-ADR-0034`** · target: `~DEFAULT_BRANCH` (`main`) · rules:
- **require a pull request before merging** (`pull_request`) with **`required_approving_review_count: 0`**
  (solo repo — no second human exists to approve; the teeth are "no direct push to `main`", not a review
  that cannot happen) and **`allowed_merge_methods: ["merge"]`** — pinning the standing merge-commit
  choice server-side, forbidding squash/rebase.
- **block force pushes** (`non_fast_forward`) and **restrict deletions** (`deletion`) on `main`.
- **`required_status_checks` — added AFTER provisioning** (§ Follow-on), once a live PR reveals the exact
  CI check-context names, because `evaluate` dry-run is unavailable here and a wrong required context
  would deadlock all merges. Intended set: the governance-critical jobs (`scope-review`,
  `openspec-validate`, `naming-validator`, `constitution-lint`, `standalone-vault-lint`).
- **`required_linear_history` is deliberately NOT set** — it would forbid the merge commits we use.

## Provisioned state (live, 2026-07-24)

Both created `active`, `bypass_actors: []`, `current_user_can_bypass: never`:
- **Tag ruleset** id **`19666225`** — rules `update`, `deletion`, `non_fast_forward`.
- **Main ruleset** id **`19666243`** — rules `deletion`, `non_fast_forward`, `pull_request` (0 reviews,
  merge-commit only); `required_status_checks` **pending** the Follow-on.

## Options considered

- **(a) Two rulesets, empty bypass, ADR in the name (chosen).** Strongest coverage of the failure
  classes, self-documenting at the point of block.
- **(b) Local guards only (status quo).** Rejected: proven insufficient by F10/F26 — the operator is
  unbound, and RC-7 shows more agent-denial makes that worse, not better.
- **(c) Admin bypass on both rulesets.** Rejected for the tag ruleset — "the mistake-proofing is real
  precisely because it resists the admin too." Admin bypass on `main` is a *defensible* convenience,
  left as an operator toggle (`pull_request` mode) added only if break-glass recurs; the default is empty.
- **(d) Require signed commits / linear history.** Rejected/deferred: signed commits would block
  unsigned agent commits (a separate decision; the operator's SSH key is theirs); linear history
  contradicts the merge-commit choice.
- **(e) Provision `active` with required checks immediately.** Rejected: a mis-named required status
  check deadlocks all merges, and `evaluate` dry-run (which would surface the real context names first)
  is Enterprise-only on this plan. Chosen instead: provision `active` **without** required checks, then
  add them from a real PR's confirmed names.
- **(f) `strict_required_status_checks_policy: true` (branch must be current before merge).** Rejected
  for now: forces update-branch churn on every stacked change; revisit if stale-merge problems appear.

## Consequence / sacrifice

- **Direct pushes to `main` end.** All changes route through a PR — the SDD ceremony becomes physically
  mandatory, not conventional. Accepted; it is the intended teeth.
- **Published `v*` tags become immutable — including to the operator.** With an empty bypass list, a
  genuinely-wrong published tag cannot be quietly moved; fixing it requires **deliberately editing the
  ruleset first** (or cutting a corrected new version). That friction is the point — it converts a
  silent clobber into a visible, deliberate act.
- **A wrong *required status check* context deadlocks merges.** The sharpest operational hazard. Since
  `evaluate` dry-run is Enterprise-only here, the mitigation is to provision `main` **without** required
  checks and add them only after a live PR confirms the exact context names (fragile across renames —
  `scope-review`'s job name still contains "burn-in"; matrix jobs emit per-Python contexts).
- **Reversal / break-glass is cheap, non-destructive, and deliberately attributable**: `PATCH` a ruleset
  to `enforcement=disabled`, do the fix, `PATCH` back to `active` — the two toggles are the audit trail.
  (`evaluate` is unavailable on this plan, so break-glass uses `disabled`.) A disable is itself a
  deliberate act — which is the whole design.
- **Discoverability is a first-class requirement of this decision** (operator instruction, 2026-07-24:
  *mark it prominently so we find it later when confused why something isn't behaving like a default —
  because we changed it*). Markers, in order of "reaches you at the moment of confusion":
  1. **The ruleset name carries `ADR-0034`** — GitHub prints the blocking ruleset's name in the refusal,
     with read-visibility, so a blocked push shows *why* and *where to read* without admin access.
  2. **`AGENTS.md` operating-notes + `README`** name the non-default rulesets.
  3. **The GitHub repo description / About** — an optional terse operator-run pointer.
  4. **This ADR** is the canonical record.
- **The G4 gap in the operation's guard stack closes** — F10-class protection moves from local-only to
  server-side enforced.
- **Standing policy — break-glass is a human-originated ritual; the agent never originates a
  protected-system escape.** Relaxing any protection (ruleset enforcement, a bypass, a hook, a
  write-scope denial) is the operator's act, entered from their own understanding of a genuine need in
  their own terminal — never a command the agent proposes, drafts, emits, or prepares (this extends
  INV-14's "never even *propose*" to all protected systems). **The agent's sole permitted action at a
  protected block is to surface it and stop.** This policy does **not** rely on agent restraint; it is
  enforced in depth by (L1) the sandbox physically denying the agent GitHub network + keyring, (L3) this
  policy, (L4) an execution-scoped guard tripwire that HARD-DENYs escape-shaped commands *if built* (its
  own change), and (L5) the operator's off-system veto card. The ritual is a forthcoming
  `96-Runbooks/break-glass-runbook`; it is safe to keep agent-readable because it is capability-gated
  (the agent cannot authenticate to perform any of it), whereas the veto *tells* are kept off-system
  because they are detection-gated.

## Follow-on (not part of the decision; recorded for execution)

1. Land this ADR + the `AGENTS.md`/`README` markers via this PR (the `main` ruleset now enforces
   PR-required on it — a live dogfood), with human Gate-4 sign-off.
2. From this PR's live CI, capture the exact check-context names (`gh pr checks`) and `PATCH` the
   `required_status_checks` rule into the `main` ruleset (id `19666243`). This is the burn-in this plan
   allows.
3. Land the `96-Runbooks/break-glass-runbook` as its own governed change once all details are final.
4. Build + live-test the L4 execution-scoped tripwire (its own change).
