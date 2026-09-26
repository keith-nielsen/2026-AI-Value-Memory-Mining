<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: eliminate-repo-prime-command

## Why

PR #115 (2026-09-08) added `/vmm-repo-github`: a stub under `vault-template/.claude/commands/`
(LOCKSTEP, so every vault receives it) that loads a card from one vault's `30-Sites/`. It existed
because a vault-rooted session doing framework work loads **none** of the repo's governance.

A 2026-09-26 audit of the stub and card against `main` (`28c94ba`) found:

- **Almost everything it carries is already held elsewhere.** Of 17 content items, 12 are in a
  source of record (`CONTRIBUTING.md`, `AGENTS.md`, `session-bootstrap-loader`,
  `agent-conduct-standing-rules`) and 2 are enforced by controls (`permissions.deny` and
  `gh-invocation-guard` refuse `gh pr *` and unsanctioned `gh api` writes; the outbound guard gates
  publishing endpoints). The card restates them without the drift test its own hardening note calls
  mandatory — failure class 9 — and four of its items were already stale.
- **Three items are held nowhere else:** the pointer a vault-rooted session needs to reach the repo's
  sources of record, and two facts (Dependabot bodies need a scope block; `npm ci` after a
  dependency bump).
- **Its value is low for its cost:** ~10 KB per invocation, some of it wrong; its instruction is
  duplicated by bootstrap step 4 and conduct rule 2; and it ships a `30-Sites/` dependency to every
  vault, where it can only fail.

A relocation to the framework root was drafted first and withdrawn: a compatibility sweep showed a
framework-rooted session is not yet fit for repo work (the outbound guard falls back to
`CLAUDE_PROJECT_DIR` and denies the repo's own push when `VAULT_ROOT` is absent; that root has no
sandbox; the development memory store is not wired to it).

**Operator decision, 2026-09-26:** repo work stays in vault-rooted sessions. Eliminate the command
completely, moving whatever is not redundant into existing guidance.

## What Changes

- **Removed:** `vault-template/.claude/commands/vmm-repo-github.md`. No copy is added anywhere.
- **`session-bootstrap-loader` step 5** (just-in-time pointers) gains one entry: for repo work, and
  only when `FRAMEWORK_ROOT` is declared, read `$FRAMEWORK_ROOT/AGENTS.md`,
  `$FRAMEWORK_ROOT/CONTRIBUTING.md` and `$FRAMEWORK_ROOT/docs/version-control-legal-moves.md` before
  planning; the route is step 4's driver. Pointer only — it restates none of them. Gated on the
  declared variable, so a standalone vault is unaffected (and it passes `standalone-vault-lint`,
  whose patterns are path-shaped).
- **`AGENTS.md` operating notes:** the two facts only the card held, wording taken from the card.
- **`tests/test_repo_prime_command_eliminated.py`:** the command exists in neither commands directory;
  bootstrap step 5 names the three sources; `AGENTS.md` carries the two facts.
- **No spec change** (`skip_specs: true`). No capability spec names the command; the
  `.claude/commands/` LOCKSTEP prefix stays declared (`vmm-session-rebooted.md` still ships there).

### Redundancy map (measured against `main`)

| Card / stub item | Held by |
| --- | --- |
| Driver owns the route; `--plan` first; never hand-compose | `CONTRIBUTING.md` §Landing; bootstrap step 4; conduct rule 2 |
| Nothing in flight ⇒ run nothing | bootstrap step 4 |
| One `next.sh`; stop touching the driver after an emission | bootstrap step 4; `CONTRIBUTING.md` §Landing step 2 |
| Constitutional hard stop | `AGENTS.md` (top); preflight STEP 7b; CI `constitution-lint` |
| Lifecycle, incl. the `--body-file` SKIP footgun | `CONTRIBUTING.md` §Landing step 0 |
| `gh` mutations are the operator's | `CONTRIBUTING.md` "Authority is not the same as typing" |
| A probe answers CAN, not HOW | conduct rule 5 |
| Green checks ≠ route clear | conduct rule 5; `CONTRIBUTING.md`; the driver's `body` step refuses |
| Rename the branch before the first push | `AGENTS.md`; `CONTRIBUTING.md` §Before the first push |
| Archive on the feature branch | `CONTRIBUTING.md`; ADR-0040; driver step 11 |
| Never `gh pr *` | `permissions.deny`; `gh-invocation-guard` |
| `gh api` write set; rulesets excluded; REST publish gated | `gh-invocation-guard`; outbound guard; legal-moves §2b |
| Drivers emit `gh api`; release tag-existence read | `CONTRIBUTING.md` §Shipping step 2 |
| Relay a driver line verbatim | conduct rule 16; `relay-conformance-guard` |
| **Read AGENTS / CONTRIBUTING / legal-moves before planning** | **moved → bootstrap step 5** |
| **Dependabot bodies need a scope block + `dep:`** | **moved → `AGENTS.md`** |
| **`npm ci` after a dependency bump** | **moved → `AGENTS.md`** |

### Deliberately NOT in this change

- Making framework-rooted sessions fit for repo work (guard fallback, sandbox, memory wiring).
- The framework root's stale `.claude/commands/vmm-session-rebooted.md` (June: four gates, no probe).
- `agent-conduct-standing-rules` §Verification calling the SessionStart check "operator-observed".

## Impact

- **Vault sessions lose `/vmm-repo-github`** and its skill-listing trigger. What replaces the trigger:
  the step-5 pointer at session start, and the driver and guards at the point of action — the
  controls that already refuse the failures the card warned about.
- **Deploy-down owes a manual removal.** `template-mirror.py` never deletes, and parity compares every
  file under a lockstep prefix in either tree, so it reports
  `MISSING-IN-TEMPLATE: .claude/commands/vmm-repo-github.md` until the operator removes
  `$VAULT_ROOT/.claude/commands/vmm-repo-github.md`. The mirror also carries the bootstrap edit.
- **The vault card is orphaned** and the Site `repo-work-bootstrap-enforcement` is no longer coupled
  to a deployed control, so it may be closed through the vault pipeline (vault-side, not this PR).
- Not constitutional: no file touched carries a `protects:` key.

## Verification

- The new test, run on a clean checkout of `main`, **fails 3 of 3**; on this branch it passes 3 of 3.
- Full suite, `openspec validate --all --strict`, and preflight — recorded in `tasks.md` §4.
- After merge: mirror; remove the vault copy; parity 0 drift.
