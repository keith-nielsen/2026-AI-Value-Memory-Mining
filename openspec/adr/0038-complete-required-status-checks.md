<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0038 — Complete the required check contexts: the Tier-0 runners can now block a merge

**Status:** **Accepted** (human sign-off: Keith Nielsen, 2026-08-06)
**Date:** 2026-08-06
**Change:** `record-required-check-contexts` (recording ADR, **no spec delta, no `vault-template/`
change**). Records a **platform-side** completion: the `main` ruleset's `required_status_checks` rule
goes from **13 contexts to 16**. It discharges an anticipated follow-on; it does not change the
enforcement model, so it touches no `openspec/specs/` and no `vault-template/`. Not an OpenSpec change
(OpenSpec requires a spec delta this completion has none of) — a docs PR plus an operator-applied
ruleset `PUT`.
**Relates / completes:** **ADR-0034** (server-side branch & tag rulesets — established these rulesets
and recorded this exact work as Follow-on §2, *"capture the exact check-context names and `PATCH` the
`required_status_checks` rule into the `main` ruleset (id `19666243`)"*); **ADR-0036** (INV-7 secret
scan) and **ADR-0037** (INV-6 offline check), whose runners this makes binding.

## Context

ADR-0034 provisioned the `main` ruleset **without** `required_status_checks`, deliberately: `evaluate`
(dry-run) enforcement is Enterprise-only on this plan, and a wrong required context deadlocks every
merge with no way to test it first. The rule was to be added by a later `PATCH` once a live pull
request revealed the exact context names. The ruleset was even **named for it** —
`vmm-main-pr-and-checks-ADR-0034`.

**Measured 2026-08-06, the state was neither "absent" nor "done".** The rule existed with **13**
contexts against **17** that actually run. The four unrequired ones were:

| Context | Required? | Assessment |
|---|---|---|
| `Secret scan (INV-7)` | no | **Tier-0 invariant, runner could not block a merge** |
| `INV-6 static (no fleet script calls the network)` | no | **Tier-0 invariant, same** |
| `INV-6 dynamic (fleet suite in a network namespace)` | no | **Tier-0 invariant, same** |
| `Scope review (declared-scope gate, burn-in)` | no | correct — `continue-on-error`, cannot fail |

So the thirteen enforced contexts were substantially lint and format, while the runners for the two
highest-blast-radius invariants — **INV-6** (*deterministic layer is offline*) and **INV-7** (*no
secrets in the vault*) — were advisory. ADR-0036 and ADR-0037 each closed a *"rule with no runner"*;
this closes **runner with no teeth**, the same gap one layer out.

The project's own tracking said the rule was **absent**, which is a class-8 instance in miniature: a
declared platform state that drifted, with no instrument watching. Nothing in the stack observes
GitHub — the standing `github-state-reconcile` gap.

## Decision

`PUT` the `main` ruleset (id `19666243`) with `required_status_checks` extended from 13 to **16**,
adding `Secret scan (INV-7)`, `INV-6 static (…)` and `INV-6 dynamic (…)`.

**Two deliberate exclusions, each with a stated trigger rather than an open end:**

- **`Scope review` stays unrequired** until its Phase-B blocking flip. While it is
  `continue-on-error: true` it cannot fail, so requiring it would assert protection that does not
  exist — the class-9 shape. **Add it in the same change as the flip.**
- **`strict_required_status_checks_policy` stays `false`.** Setting it true forces every branch
  up to date before merging, which without a merge queue converts one rebase into serialized thrash.
  Sequence remains **required checks → merge queue → the driver's base-current guard becomes largely
  redundant.**

## Options considered

- **(a) Add the three Tier-0 contexts only (chosen).** Closes the real gap, changes nothing whose
  behaviour is not already understood, and leaves both exclusions triggered rather than forgotten.
- **(b) Require all 17.** Rejected: `Scope review` cannot fail, so requiring it manufactures false
  assurance, and it would have to be un-required if the Phase-B flip is ever reverted.
- **(c) Also set `strict`.** Rejected for now — correct destination, wrong order. It is the merge
  queue that makes it cheap, and the queue is the next item.
- **(d) Leave it.** Rejected: two Tier-0 runners that cannot block a merge are decorative, and both
  were built specifically to bind (ADR-0036, ADR-0037).

## Consequence / sacrifice

**Gained:** a red INV-6 or INV-7 check now refuses a merge server-side, after the ref leaves the
machine — the layer no local hook or driver can be talked out of. `bypass_actors` remains **empty**,
so this binds the admin too.

**Sacrificed:** three more contexts that must stay green, so a flaky INV-6 dynamic run (it builds a
network namespace) now blocks rather than warns. That is the intended trade, but it is a real cost on
a bad day, and the break-glass is an attributable ruleset `PATCH`, per ADR-0034.

**Residual, stated not hidden:** `Scope review` and the `strict` policy remain unrequired by design,
each with its trigger above. **Nothing yet observes the ruleset**, so this ADR is a point-in-time
record, not a guarantee of continuing state — precisely what `github-state-reconcile` is owed for.
GitHub ruleset parameters can also change **without bumping `updated_at`**, so any future check must
compare content, never timestamps.

## Application (operator — the agent cannot authenticate to perform this)

A ruleset `PUT` **replaces the entire `rules` array**, so a hand-written payload silently drops
`pull_request`, `deletion` or `non_fast_forward`. The applied method was: fetch the live ruleset,
mutate only the `required_status_checks` context list, send it back —

```
gh api -X PUT /repos/keith-nielsen/2026-AI-Value-Memory-Mining/rulesets/19666243 --input <payload>
```

**Verified after application** by re-reading the ruleset: four rules preserved, `bypass_actors` still
empty, `enforcement: active`, `created_at` unchanged, 16 contexts, and `Scope review` the only
unrequired context. A **dependabot** pull request (#48) was checked first and emits all 17 contexts,
so none of the three additions can deadlock dependabot merges — the failure mode ADR-0034 warned of
and could not dry-run.
