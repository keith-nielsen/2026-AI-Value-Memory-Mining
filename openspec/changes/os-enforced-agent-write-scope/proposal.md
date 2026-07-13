<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: os-enforced-agent-write-scope

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `access-control` spec (`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`) — **ADDs** a Requirement ("OS/Harness-Enforced Agent Write Scope"). **No principle is overridden or weakened; no new invariant is added.** This change delivers the *structural* enforcement the spec already mandates ("Enforcement is structural (code + hooks + CI), never trust-based") for the Area Access Matrix's Agent column — the enforcement the spec itself records as deferred ("OS-level enforcement is deferred per §14.1"). It un-defers it.
**Tier:** 0-adjacent (extends the enforcement of Tier-0 INV-4/INV-5; §5 AI hard-stop honored — surfaced to the operator with explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at Keith's explicit direction, 2026-07-04 — "begin putting in the essential tools/utilities and do all that is needed to start the burn-in stage")
**Date:** 2026-07-04

---

## Why

The live-vault failure record (`determinism-failure-modes-claude`, F1–F14) establishes one empirical
result: **across the whole operation, only externally-enforced guards held** (the INV-14 PreToolUse
guard; the strict-order refusal inside `vault-close-day.py`). Every breach — hand-authoring
script-owned artifacts (F13), commit bundling (F3/F4/F5), gate-acknowledged-then-abandoned (F1) —
lived where compliance rested on the agent honoring in-context text. The access-control spec already
asserts structural enforcement and already anticipates OS-level enforcement (deferred per §14.1).
Today, nothing OS-level or harness-level blocks an agent write to `99-Operations/`, `40-Treasury/`,
or a script-owned Logbook artifact before it happens; the commit-gate catches some of it after the
fact, and the rest is trust.

Claude Code now provides the two native mechanisms that close this without bespoke machinery
(researched 2026-07-04; see the live-vault Site `protocol-harness-framework`,
`harness-remediation-executive-summary`):

1. **OS sandbox** (bubblewrap/Seatbelt) — kernel-enforced `denyWrite` on every Bash child process,
   including arbitrary interpreters (`python3 -c "open(…,'w')"`) that no command-text scanner can see.
2. **Permission deny rules** — declarative, gitignore-style `Edit(...)` denies for the structured file
   tools (Edit/Write/MultiEdit/NotebookEdit), which the sandbox does not cover.

## What Changes

- **`access-control` spec:** ADD Requirement "OS/Harness-Enforced Agent Write Scope" — the Agent
  column of the Area Access Matrix SHALL be enforced pre-action at two layers (OS sandbox for shell;
  harness permission rules for structured tools), with a **two-stage adoption**: *burn-in* (sandbox on,
  escape-hatch fallback allowed, observations collected) then *strict* (`failIfUnavailable` +
  `allowUnsandboxedCommands: false`), the strict flip being a separate operator action.
- **`vault-template/.claude/settings.json`:** ships the burn-in configuration — `sandbox.enabled`,
  `filesystem.denyWrite` on `40-Treasury/ 99-Operations/ .claude/ 96-Runbooks/ 97-Molds/ 10-Logbook/`,
  `excludedCommands` for the rendered vault scripts the agent legitimately drives (exact invocations
  only), and `permissions.deny` Edit-rules mirroring the same scope plus the script-owned Logbook
  artifacts (`Daily/*.md`, `kanban.md`). The one agent-writable close artifact
  (`Daily/*.resolutions.json`) stays writable **by pattern disjointness** (deny rules cannot carry
  carve-outs) and is written via the Write tool only.
- **Docs:** `AGENTS.md` (agent-facing contract: drive scripts by bare exact invocation; sandbox is a
  fence, not a promise) and `docs/USING-THIS-TEMPLATE.md` (Linux deps; burn-in → strict adoption path).
- **New ADR-0022** (drafted as Proposed; Accepted at Gate 4).
- **CHANGELOG** `[Unreleased]` entry (drafted now, not after the fact — F10 lesson #3).

**Explicitly NOT in this change:** `failIfUnavailable` / `allowUnsandboxedCommands: false` (the strict
flip is Stage B, a later, separate operator action after clean burn-in); the runbook driver
(`vault-close-cycle`, Phase 2); GitHub rulesets (Phase 3); soft hooks (Phase 4); any live-vault file
(the live `.claude/settings.json` is operator-applied from the Site-authored merged file — the agent
cannot and does not touch it).

## Capabilities

### New Capabilities
- _(none — lands in the existing `access-control` capability)_

### Modified Capabilities
- `access-control`: ADD Requirement "OS/Harness-Enforced Agent Write Scope (INV-4/INV-5 enforcement)".

## Impact

- **Spec delta (synced at archive):** `access-control` (ADDED Requirement + scenarios). `protects:`
  frontmatter unchanged (no new invariant).
- **Implementation (vault-template):** `.claude/settings.json` burn-in configuration.
- **Docs:** `AGENTS.md`, `docs/USING-THIS-TEMPLATE.md`.
- **New ADR-0022.**
- **Live vault (operator-applied, out of band of this repo):** merged `settings.json` authored in the
  Site (`30-Sites/protocol-harness-framework/proposed-install/settings-live-burn-in.json`) with the
  vault's instance specifics (WebFetch/network medical-domain allowlist preserved; `allowWrite` for the
  framework repo working copy and the harness scratchpad); Phase-1a acceptance probes
  (`phase-1a-acceptance-probes.md`) run by the agent in-session after apply.
- **Honest residuals (recorded in ADR-0022):** structured-tool coverage is enumerated-deny (native
  permission rules have no default-deny mode), so unlisted paths remain tool-editable — every
  script-owned artifact class is enumerated; Bash-side coverage IS default-deny outside CWD and
  deny-listed inside it. `excludedCommands` matching is prefix/pattern-based: a driver invoked any
  other way runs sandboxed and its writes fail closed (safe, but the bare-exact-invocation contract
  must be documented). Burn-in stage retains the sandbox escape hatch (fallback commands still face
  the regular permission prompt — protection is reduced, not absent, and every fallback is a signal).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** Nothing constitutional is being overridden. INV-4 (bounded
agent write scope) and INV-5 (actor ≠ owner for Operations) currently bind the agent by convention,
commit-gate, and trust; this change makes them bind **before the write happens**, at the kernel for
shell and at the harness permission layer for structured tools. The access matrix is unchanged — what
changes is that its Agent column stops being advisory. The two-stage adoption exists because strict
mode flipped on day one converts every unforeseen-but-legitimate write into a hard failure on a
machine whose write inventory has never been observed under a sandbox (Sharp-edge SE-3), and because
`failIfUnavailable` set before dependencies are verified locks Claude Code out entirely (SE-2).

**Blast radius:**

- [x] `openspec/specs/access-control/spec.md` — ADDED Requirement (delta now; canonical sync at archive)
- [x] `vault-template/.claude/settings.json` — burn-in sandbox + permissions.deny (hooks preserved)
- [x] `AGENTS.md` — drive-contract + fence-not-promise guidance
- [x] `docs/USING-THIS-TEMPLATE.md` — deps + burn-in → strict adoption
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [x] ADR-0022 (new, Proposed → Accepted at Gate 4)
- [x] `vocabulary-lint` — no off-metaphor terms introduced
- [x] No script inventory change (no new literate scripts in this change — drivers come later)
- [x] `constitution.md` / `project.md` — untouched (no new INV; frozen-ID rule ADR-0008 not implicated)

**Discrepancies surfaced for Gate 4 (decide, don't bury):**

1. **`20-Claims/` direct capture.** The Area Access Matrix (footnote ²) grants the agent no general
   `20-Claims/` write — only `_refine-proposals/`. Live practice has the agent capturing Claims at
   operator direction routinely (e.g. the F3 recovery Claim). This change **does not deny** `20-Claims/`
   (matching practice and the v0.1 draft ACL), which means burn-in enforcement is *looser than the
   matrix* there. Operator to choose: (a) amend footnote ² to permit direct capture, or (b) add the
   deny and route capture through proposals. Until decided, the looseness is documented, not silent. **DECIDED at Gate 4 (2026-07-13):** operator chose (a) -- the agent is explicitly permitted direct 20-Claims/ capture (essential efficiency + comfort-of-ride requirement). Verified the shipped config already matches: 20-Claims is in neither the shell denyWrite nor permissions.deny. Access Matrix footnote to be amended to permit direct capture (documentation follow-up, folded with the README count fix).
2. **`70-Tailings/` / `71-Spoil/` (matrix: agent R / —).** Not in this deny set (v0.1 ACL seed did not
   cover them either; slag/dump script flows need design for the drive path). Follow-up change. **DECIDED at Gate 4 (2026-07-13):** operator permits agent interaction with 70-Tailings/ / 71-Spoil/ for now (no concerns); formal scoping TBD in a follow-up.
3. **README counts are stale** (still "18 ADRs" from v0.1.13 era; 21 exist pre-this-change). Not
   bundled here (F3/F4/F5 lesson: no unrelated sweeps) — flagged for a housekeeping commit.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan:**

1. Spec delta: `access-control` ADDED Requirement (this change's `specs/access-control/spec.md`).
2. `vault-template/.claude/settings.json`: merge burn-in config, preserving the existing PreToolUse /
   SessionStart hooks verbatim.
3. Docs: `AGENTS.md` §"Agent access rules" + §"Operating notes"; `USING-THIS-TEMPLATE.md` adoption
   section. CHANGELOG `[Unreleased]`. ADR-0022 (Proposed).
4. Live vault (operator): install `socat` (bubblewrap already present, AppArmor sysctl already 0);
   review + `cp` the Site-authored merged settings into `.claude/settings.json`; delete the
   superseded v0.1 trial `settings.local.json` hook; restart Claude Code; run `/sandbox` panel check.
5. Agent (post-restart, in-session): execute `phase-1a-acceptance-probes.md`; any SE-4 probe failure
   (a denied write succeeding) → **stop and escalate, never adapt around**.
6. Burn-in: N sessions of normal operation; every sandbox fallback prompt is captured as an
   observation; Stage-B strict flip is a **separate future change** (one ceremony step).
7. Forks: template ships burn-in defaults; `USING-THIS-TEMPLATE.md` documents deps and the strict flip.

**Regression tests that MUST pass before Gate 3 completes:**

- [ ] `openspec validate os-enforced-agent-write-scope --strict`
- [ ] `openspec validate --all --strict`
- [ ] Both `settings.json` files parse as strict JSON (`python3 -m json.tool`)
- [ ] `constitution-lint` preconditions (ceremony artifacts present: this proposal + ADR-0022)
- [ ] `vocabulary-lint` (no off-metaphor terms)
- [ ] Grep: no `failIfUnavailable` / `allowUnsandboxedCommands` anywhere in this change (burn-in only)

**Live acceptance (after operator apply — Phase-1a probes, agent-executed in-session):**

- [ ] Bash `echo x > 40-Treasury/…` → kernel deny (SE-4 precedence proof)
- [ ] Bash `python3 -c "open('10-Logbook/Daily/…','w')"` → kernel deny (the v0.1 known_gap, closed)
- [ ] Write tool → `10-Logbook/Daily/<date>.md` → deny; → `…resolutions.json` → allow (SE-8)
- [ ] `~/bin/vault-kanban-render.py` bare → succeeds; `python3 ~/bin/vault-kanban-render.py` → denied (SE-5)
- [ ] Repo working copy + scratchpad writes → allowed (`allowWrite`)
- [ ] Vault `git add`/`commit` of Site files → works

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — spec delta; vault-template settings; AGENTS.md; USING-THIS-TEMPLATE;
CHANGELOG `[Unreleased]`; ADR-0022 (Proposed)
**All repo-side regression tests green (local):** ☑ — `openspec validate` (change + `--all --strict`) ·
JSON parse both settings files · burn-in-only grep clean · vocabulary/constitution lint preconditions
**CI green on this PR:** ☑ (PR #20, 24/24 green on 7296db9, 2026-07-13)
**Live acceptance probes:** ☐ (run in-session after the operator applies the live settings — see
`phase-1a-acceptance-probes.md` in the Site)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> Sacrifice (proposed wording for sign-off): the agent permanently loses the ability to write —
> by any shell means, at the kernel — to `40-Treasury/`, `99-Operations/`, `.claude/`, `96-Runbooks/`,
> `97-Molds/`, and `10-Logbook/`, and loses structured-tool writes to the same scope plus the
> script-owned Logbook artifacts. Where the agent used to be *trusted* it is now *fenced*; legitimate
> new write needs must be added deliberately by the operator (allowWrite / excludedCommands / rule
> edits), which is friction accepted in exchange for pre-action enforcement of INV-4/5. During burn-in
> the sandbox escape hatch remains (fallback = regular permission prompt), so enforcement is
> "default-deny with operator-visible exceptions," not yet absolute; the strict flip is a separate,
> later decision. Enumerated-deny residual for structured tools and the `20-Claims` matrix
> discrepancy are accepted as documented open items, not silent gaps.

**ADR created:** `openspec/adr/0022-os-enforced-agent-write-scope.md` (Proposed) ☑ — flips to
Accepted at sign-off
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen (operator)
Date: 2026-07-13
Authorization: Gate-4 approved by the operator in session ("Approved", 2026-07-13), with explicit decisions on discrepancies 1 and 2 recorded above. Recorded by the agent at the operator's standing direction -- the human decided; the agent transcribed.
