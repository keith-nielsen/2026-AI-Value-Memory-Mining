<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `access-control` — ADDED Requirement "OS/Harness-Enforced Agent Write Scope
      (INV-4/INV-5 enforcement)" + scenarios (shell kernel-deny, structured-tool deny + sidecar
      allowance, exact-invocation drive contract, ordered strict flip)

## 2. Enforcement configuration (vault-template)

- [x] 2.1 `.claude/settings.json` — `sandbox.enabled` + `filesystem.denyWrite` (six protected areas)
      + `excludedCommands` (rendered-script drive list, bare + `*` forms) + `permissions.deny`
      Edit-rules (protected areas + `Daily/*.md` + `kanban.md`); existing PreToolUse / SessionStart
      hooks preserved verbatim; **no strict keys** (burn-in only)

## 3. Docs

- [x] 3.1 `AGENTS.md` — write-scope fence + bare-exact-invocation drive contract
- [x] 3.2 `docs/USING-THIS-TEMPLATE.md` — Linux deps (bubblewrap, socat, AppArmor sysctl note);
      burn-in → strict adoption path
- [x] 3.3 `CHANGELOG.md` — `[Unreleased]` entry (drafted with the change, not after — F10 lesson)
- [x] 3.4 ADR-0022 (Proposed; flips to Accepted at Gate 4)

## 4. Regression (repo-side, before Gate 3 closes)

- [x] 4.1 `openspec validate os-enforced-agent-write-scope --strict` + `openspec validate --all --strict`
- [x] 4.2 Both settings.json files parse as strict JSON
- [x] 4.3 Grep clean: no `failIfUnavailable` / `allowUnsandboxedCommands` in this change
- [x] 4.4 vocabulary/constitution lint preconditions (ceremony artifacts present; no off-metaphor terms)

## 5. Live vault (operator + agent, out of band of this repo)

- [ ] 5.1 [human] `sudo apt-get install socat` (bubblewrap present; AppArmor sysctl already 0)
- [ ] 5.2 [human] Review + apply Site-authored `settings-live-burn-in.json` → `.claude/settings.json`;
      delete superseded v0.1 trial hook from `settings.local.json`; restart Claude Code; `/sandbox`
      Dependencies + Config tabs verified
- [ ] 5.3 [agent] Execute `phase-1a-acceptance-probes.md` in-session; SE-4 failure ⇒ stop-and-escalate
- [ ] 5.4 [both] Burn-in observation: capture every sandbox fallback as an observation for Stage B

## 6. Gate 4 + release (human-gated)

- [ ] 6.1 Gate-4 sign-off recorded in `proposal.md`; ADR-0022 → Accepted
- [ ] 6.2 PR from `harness/os-enforced-agent-write-scope`; CI green; human merge (INV-14: agent cannot)
- [ ] 6.3 Archive (sync `access-control` spec) + CHANGELOG release heading + tag (human, post-merge,
      merge-ancestor guard)
