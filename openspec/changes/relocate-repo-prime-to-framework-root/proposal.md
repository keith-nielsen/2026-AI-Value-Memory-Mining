<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: relocate-repo-prime-to-framework-root

## Why

PR #115 (2026-09-08) added the repo-work prime `/vmm-repo-github` under
`vault-template/.claude/commands/`. That prefix is LOCKSTEP, so `template-mirror.py` deploys the prime
into **every** vault. It was built for one situation — framework work done from a vault-rooted
session — and three decisions made since then contradict where it lives:

- **A deployed vault is standalone** (conduct rule 26, `agent-conduct-standing-rules`): no in-vault
  artifact may depend on the framework repo. The prime pointed at `$FRAMEWORK_ROOT/tools/pr-flow.py`
  and at a `30-Sites/` card that exists in one vault only; any other vault receives a command that
  can only fail.
- **Development knowledge loads only in framework-rooted sessions** (memory partition, 2026-09-16).
  A session rooted here loads `CLAUDE.md` → `AGENTS.md` by itself, so repo work belongs here.
- **The framework root has no repo-contribution prime of its own.** The vault Site
  `repo-work-bootstrap-enforcement` recorded this gap on 2026-09-07 and rated closing it *"worth doing
  regardless"*.

A 2026-09-26 audit also measured the card the prime loads: four stale items, and no test comparing it
to `AGENTS.md` / `CONTRIBUTING.md`, though the card's own hardening note calls that test mandatory.
The two facts the card carried that no source of record did — Dependabot bodies need a scope block,
and `npm ci` after a dependency bump — would be lost with the card.

**Operator decision, 2026-09-26:** move the prime into this repository, with the stated future intent
of a full split in which the framework repo's GitHub work is independent of the vault. The split
itself is a later, separate project; this change only stops shipping repo-work context into vaults.

## What Changes

- **Removed:** `vault-template/.claude/commands/vmm-repo-github.md`. Vaults stop receiving the prime.
- **Added:** `.claude/commands/vmm-repo-github.md` — the prime for sessions rooted in this repo. It
  carries the one irreducible instruction (`tools/pr-flow.py --plan`, never hand-compose) and points
  at `AGENTS.md`, `CONTRIBUTING.md` and `docs/version-control-legal-moves.md`, **restating none of
  them** (failure class 9). It references no vault-side name and needs no card.
- **`AGENTS.md` operating notes:** the card's two facts no source of record carried — Dependabot
  bodies need a scope block (and a `dep:` line); run `npm ci` after a dependency bump merges. Wording
  taken from the card, not re-composed.
- **`tests/test_repo_prime_framework_standalone.py`:** the prime is in the framework root, is absent
  from `vault-template/`, names no vault-side identifier, and names the route and its sources.
- **No spec change** (`skip_specs: true`). No capability spec names the prime; the `.claude/commands/`
  LOCKSTEP prefix stays declared, because `vmm-session-rebooted.md` still ships under it.

### Deliberately NOT in this change

- The framework root's own `.claude/commands/vmm-session-rebooted.md` is stale (unchanged since
  2026-06-29: four gates, no probe, no route state). Separate decision.
- `agent-conduct-standing-rules` §Verification calls the SessionStart check "operator-observed"; it is
  agent-measured. Separate fix.
- The full framework/vault split.

## Impact

- **Deploy-down owes a manual removal.** `template-mirror.py` never deletes, and parity compares every
  file under a lockstep prefix in **either** tree — so after the mirror, parity reports
  `MISSING-IN-TEMPLATE: .claude/commands/vmm-repo-github.md` until the operator removes
  `$VAULT_ROOT/.claude/commands/vmm-repo-github.md` (the agent's sandbox does not write `.claude/`
  there). Parity then returns to 0 drift, one file fewer.
- **The vault card is orphaned** once the vault copy is gone, and the Site
  `repo-work-bootstrap-enforcement` is no longer coupled to a deployed control, so it may be closed
  through the vault pipeline. Vault-side, not part of this pull request.
- **Workflow:** framework work starts from a session rooted in this repository. A vault session no
  longer has `/vmm-repo-github`.
- Not constitutional: no file touched carries a `protects:` key.

## Verification

- The new test **fails 4 of 4** before the change and passes after. Adversarially, its coupling check
  catches all three vault references in the removed prime's real text (`VAULT_ROOT`, `FRAMEWORK_ROOT`,
  `30-Sites`), and its route check fails when the `--plan` line is absent.
- Full suite: 553 on `main` → 557 passed. `openspec validate --all --strict`: 7 passed, 0 failed.
  Preflight CLEAR (13/16 CI jobs reproduced locally; scope-review re-run once the body exists).
- After merge: mirror; remove the vault copy; parity 0 drift.
