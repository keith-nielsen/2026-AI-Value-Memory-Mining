# Tasks — seed-github-read-hosts

> **Durable plan.** Origin: GitHub platform hardening queue item 38. Seed the GitHub read-hosts into
> the template so a deployed vault does not start one denied prompt away from losing GitHub reads.
> SEED not lockstep, so the guard is a test (assertion), not a parity comparison.

## 0. END STATE

`vault-template/.claude/settings.json` carries `api.github.com`/`github.com` in
`sandbox.network.allowedDomains` and `WebFetch(domain:github.com)` in `permissions.allow`; it seeds no
`allowWrite`. A test asserts the seed default. The maintenance spec records the requirement.

## 1. The seed

- [x] 1.1 Add `sandbox.network.allowedDomains = [api.github.com, github.com]` and
      `permissions.allow += WebFetch(domain:github.com)` to `vault-template/.claude/settings.json`.
      Do NOT seed the vault-specific research domains, and do NOT seed `allowWrite` (the deliberate
      decision: each instance grants its own).

## 2. The assertion (SEED cannot be compared)

- [x] 2.1 `tests/test_settings_paths.py`: assert the template carries the two hosts + the WebFetch
      entry, and asserts it seeds no `allowWrite`. Red-first against the pre-change template.

## 3. Spec

- [x] 3.1 `maintenance` ADDED "The Seed Template Carries The GitHub Read-Hosts" — the seed defaults,
      the session-scoped-deny rationale, the not-a-relaxation note (prompting not routing, INV-14
      untouched), and the no-allowWrite decision.

## 4. Regression

- [x] 4.1 Full suite green.
- [ ] 4.2 `openspec validate --all --strict` — 0 failed.
- [ ] 4.3 markdownlint (CI's four `--ignore` paths) — 0 findings.
- [ ] 4.4 `tools/preflight.py . --body-file <path>` → CLEAR.

## 5. Gate 4 — maintenance touch

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md` (`protects: [INV-2, INV-3,
INV-6]`). No new control surface, no new refusal, and INV-14 is explicitly untouched (host allowlisting
governs prompting; the guard governs commands).

- **What this touches** — a seed default + its test + a maintenance requirement documenting it.
- **What breaks if wrong:** a seed that lacks the hosts leaves a deployed vault one prompt from losing
  GitHub reads (the test is the guard); over-seeding `allowWrite` would grant a deployed vault write to
  sibling repos (the no-allowWrite test is the guard).

- [x] 5.1 Tier-0 (maintenance touch) surfaced; **Approved** — Keith Nielsen, 2026-09-22

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff.
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; merge; cleanup.
- [ ] 6.5 No deploy-down owed for THIS vault (it already has the hosts). Future deployments inherit the
      seed. The framework repo and development store manage their own settings — unaffected.
