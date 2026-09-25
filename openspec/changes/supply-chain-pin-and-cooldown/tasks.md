# Tasks — supply-chain-pin-and-cooldown

> **Durable plan.** Origin: Tier 1 of the 2026-09-25 remediation order — the OpenSpec bump review
> asked what prevents a bad release reaching us; the answer was "a default we do not own" plus
> tag-referenced actions. Operator decisions (2026-09-25): npm cooldown 14 days, the rest 7; include
> SHA-pinning in the same change. Recommended defaults taken (vetoable at Gate 4): pytest enforcement
> rather than zizmor; one grouped PR for Actions updates.

## 0. END STATE

All 25 `uses:` lines SHA-pinned with `# vX.Y.Z`; `dependabot.yml` declares cooldowns (npm 14, others 7),
npm monthly, Actions grouped; `tests/test_supply_chain_pins.py` enforces both; the `maintenance` spec
records the requirement.

## 1. Implementation

- [x] 1.1 Resolve each `@v7` tag to its commit (`git ls-remote`, 2026-09-25): checkout v7.0.1
      `3d3c42e5aac5ba805825da76410c181273ba90b1`, setup-node v7.0.0
      `820762786026740c76f36085b0efc47a31fe5020`, setup-python v7.0.0
      `5fda3b95a4ea91299a34e894583c3862153e4b97`. Lightweight tags — the SHA is the commit.
- [x] 1.2 Pin all 25 `uses:` lines in `ci.yml` (24) and `openspec-canary.yml` (1); 0 tag refs remain.
- [x] 1.3 `dependabot.yml`: `cooldown.default-days` github-actions 7, pip 7, npm 14; npm weekly →
      monthly; `groups.actions` for github-actions; policy header comment.

## 2. Tests (red-first)

- [x] 2.1 `tests/test_supply_chain_pins.py` observed to FAIL on the unpinned tree (25 tag refs; all three
      cooldowns `None`), green after.
- [x] 2.2 Mutations: drop one version comment → version-comment test fails; revert one pin to `@v7` →
      pin test fails. Restored.
- [x] 2.3 Vacuity guard (≥ 20 `uses:` found) and the per-block cooldown parser test.

## 3. Spec

- [x] 3.1 `maintenance` ADDED "Supply-Chain Inputs Are Pinned Immutably And Adopted After A Cooldown".

## 4. Regression

- [x] 4.1 Full suite green — 545 passed.
- [x] 4.2 `openspec validate --all --strict` — 7 passed, 0 failed.
- [x] 4.3 markdownlint — 0 findings (preflight md-lint PASS).
- [x] 4.4 `tools/preflight.py .` → CLEAR (the body-file run is 6.3, after the archive).

## 5. Gate 4 — protected-spec change (maintenance: INV-2, INV-3, INV-6)

The delta ADDs one requirement; it modifies none. It tightens CI inputs and changes no script and no
vault content. Decisions surfaced for sign-off:

- **Pin first-party `actions/*` too** (14 of 17 surveyed pinners do). Cost: a Dependabot PR per action
  release instead of silent tag drift — which is the point.
- **Cooldown values:** npm 14, github-actions and pip 7. Security updates are not delayed.
- **npm monthly**, **Actions grouped** into one PR (one failing bump holds the group).
- **Enforcement by stdlib pytest, not zizmor** (trust-ring minimisation); server-side "require SHA
  pinning" policy left to the operator.
- **PR #122** (OpenSpec 1.13.1) falls inside the new 14-day npm window until 2026-10-01.

- [x] 5.1 Protected-spec (maintenance) change surfaced; **Approved** — Keith Nielsen, 2026-09-26

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff (generated after the archive commit).
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.
- [ ] 6.5 After merge: confirm Dependabot parses the new config (no config error on the repo's
      Dependabot page) and note what happens to PR #122.
