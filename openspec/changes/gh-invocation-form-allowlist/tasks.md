<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks — gh-invocation-form-allowlist

**Marker contract:** `[ ]` not started · `[~]` **built, untested** · `[x]` **tested — the check was
observed to FAIL without the change, and its evidence is cited.**

**Evidence rule (constitution §3 Gate 3):** every result is evidenced by **its command and output** —
a tally with its denominator, a diff, or an exit status. Never a prose assertion, never a
shell-printed verdict string.

| Constitution §3 | Phase here |
|---|---|
| Gate 1 — CHECK (impact analysis) | G0 + G1 |
| Gate 2 — PLAN (migration + regression) | this file |
| Gate 3 — EXECUTE + REGRESSION-TEST | G2 – G4 |
| Gate 4 — RE-CHECK + HUMAN SIGN-OFF | G5 |

## Who performs what

| Surface | Scope | Who |
|---|---|---|
| `openspec/` · `vault-template/**` · `tools/` · `tests/` · framework `.claude/settings.json` | **WRITABLE** | agent |
| live vault `99-Operations/**` · live vault `.claude/**` | **PROTECTED** | operator |
| `git push` · PR · merge · release | INV-14 authority / keyring | operator |
| vault `render` | writes protected paths | **operator only** |

---

## G0 — Blast radius *(Gate 1)*

- [x] G0.1 Sweep every `gh ` invocation across `tools/ tests/ .github/ docs/ openspec/
      vault-template/ README.md AGENTS.md CONTRIBUTING.md`; partition live surface vs frozen record.
      Paste commands **and full output** into `blast-radius-transcript.md`. Never a composed table.
      EVIDENCE: local · recursive grep, command + full output pasted · 2026-08-25T21:0x+08:00
      LIVE (executes gh): `gh_read.py`, `pr-state.py`, `pr-flow.py`, `ship-release.py`,
      `openspec-canary.yml`. FROZEN (record only): all of `changes/archive/`, the ADRs, the
      capability specs, AGENTS/CONTRIBUTING/docs. TEST (asserts on strings, never executes):
      five `tests/test_*.py`. Transcript: `blast-radius-transcript.md`.
- [x] G0.2 Enumerate every fleet consumer of `gh`. **`ship-release.py` is already recorded as using
      raw `gh` for reads** and `pr-flow.py` invokes `gh`. For each: does it run as a subprocess of a
      Bash tool call (hook sees only the launching command) or is it typed by the agent (hook sees
      it)? Record the partition — this is the asymmetry the spec must state.
      EVIDENCE: local · argv call-site grep across the four tools · 2026-08-25T21:0x+08:00
      **EVERY fleet call site is a Python subprocess — the hook sees NONE of them.**
        `gh_read.py:112`   `["gh","api",path]`                    permitted anyway
        `pr-flow.py:1419`  `["gh","auth","status"]`               permitted anyway
        `pr-state.py:83`   `["gh","pr","view",…]`                 WOULD be refused if typed
        `pr-state.py:168`  `["gh","run","list",…]`                WOULD be refused if typed
      `ship-release.py` no longer shells out (item 21 moved it onto `gh_read`).
      **Landing the allowlist breaks no live caller**: `pr-state.py:83` is GraphQL, already 401s in a
      confined session, and line 86 sets `graphql=False` and degrades to anonymous REST; the
      `gh run list` path at 168 is gated on `graphql` and is unreachable in that state.
      ⚠ Third surface neither layer reaches: `openspec-canary.yml` runs `gh label create`,
      `gh issue list`, `gh issue create` on GitHub runners, where no harness — and therefore no hook
      and no `permissions` block — exists at all.
- [x] G0.3 Record the three `settings.json` files' current `PreToolUse` registrations and
      `permissions` blocks verbatim as the pre-change baseline.
      EVIDENCE: local · keys + block counts for all three roots · 2026-08-25T21:0x+08:00
        `$HOME/.claude/settings.json`            PreToolUse=0  deny=0
        `$VAULT_ROOT/.claude/settings.json`      PreToolUse=1  deny=10
        `$FRAMEWORK_ROOT/.claude/settings.json`  PreToolUse=1  deny=0, keys=['hooks'] only
      **RED confirmed for G3.5**: the framework repo has no `permissions` block at all. USER
      carrying no hooks and no deny entries is also what made the G1.1 lab uncontaminated.

## G1 — The precedence question, answered before anything is built

**G1.1 BLOCKS EVERY OTHER TASK.** The design assumes a second hook can refuse what the first allows.
That assumption is unmeasured.

- [x] G1.1 Measure Claude Code multi-hook `PreToolUse` decision precedence: register two Bash hooks
      where one returns `allow` and the other `deny` for the same command, and observe which wins.
      Evidence = the observed harness behaviour, not the documentation.
      **If an earlier `allow` can pre-empt a later `deny`, STOP** — record the reversal in ADR-0045
      and fall back to extending `outbound-publish-guard.py`. Do not proceed on hope.
      **MEASURED — the assumption HOLDS. `deny` wins unconditionally, in either registration order.**
      EVIDENCE: local · `claude -p` in `lab/`, probes A(first)/B(second) · 2026-08-25T20:53+08:00
        `PRECEDENCE_AD`  A=allow B=deny  -> REFUSED, `[probe hook B] DENY for PRECEDENCE_AD`
        `PRECEDENCE_DA`  A=deny  B=allow -> REFUSED, `[probe hook A] DENY for PRECEDENCE_DA`
      The second case closes a gap this task did not ask about: a `deny` is **not** reversible by a
      later `allow`, so the control cannot be undone by a hook registered after it. Procedure and
      full reasoning: `lab/hook-precedence-measurement-procedure.md`. The option-3 fallback is NOT
      needed and ADR-0045's Decision stands unamended.
- [~] G1.2 Confirm the outbound guard's ASK and this guard's DENY raised by the *same* command
      resolve to DENY. A refusal that an ASK can override is not a refusal.
      **MEASURED with probes, `[~]` not `[x]` — one confound remains.**
      EVIDENCE: local · `claude -p` in `lab/` · 2026-08-25T20:53+08:00
        `PRECEDENCE_ASKDENY`  A=ask B=deny -> REFUSED with no prompt,
        `[probe hook B] DENY for PRECEDENCE_ASKDENY`
      ⚠ Run non-interactively, where `ask` **cannot prompt** — so the refusal could in principle come
      from non-interactivity rather than from `deny` beating `ask`. The reason string names hook B's
      DENY specifically rather than a generic refusal, which argues against that reading but does not
      settle it. **Ticks to `[x]` only after one interactive-session confirmation**, and against the
      REAL outbound guard rather than a probe emitting `ask`.

## G2 — The matcher state space, written as failing tests FIRST

Each row states its intended disposition **before** implementation. Write the test, watch it fail
against an absent hook, then implement. A matcher that reports coverage it does not have is the
specific failure being defended against.

- [x] G2.1 `gh api repos/o/r/pulls` → **allow**
- [x] G2.2 `gh auth status` → **allow**
- [x] G2.3 `gh api graphql -f query=...` → **deny** (the one `gh api` form that must not pass)
- [x] G2.4 `gh pr list` / `gh issue list` / `gh run list` / `gh workflow view` → **deny**
      (`gh run` and `gh workflow` are unlisted in Layer 1 and run today — this is the red)
- [x] G2.5 `/usr/bin/gh pr list` (absolute path) → **deny**
- [x] G2.6 `GH_TOKEN=x gh pr list` (leading env assignment) → **deny**
- [x] G2.7 `cd /tmp && gh pr list` (compound) → **deny**
- [x] G2.8 `echo "run gh pr list"` (the token is data, not a command) → **allow**; a guard that
      refuses prose about itself is unusable
- [x] G2.9 `git push` → falls through untouched; **assert the outbound guard's behaviour is
      byte-identical to the pre-change baseline.** This change must not perturb INV-14 enforcement.
- [x] G2.10 Malformed / empty stdin → exit 0, no output. Document explicitly that this **fails open**
      and is the reason Layer 1 is retained.
- [x] G2.11 Record the cases the matcher provably does **not** catch (variable indirection, alias,
      base64/eval). Do not claim them. **Do not execute an evasion of a live control to test one** —
      any such measurement is operator-instructed, per the standing guard-denial rule.


### G2 evidence — RED observed 2026-08-25T21:1x+08:00

Tests written FIRST, in `tests/test_gh_invocation_guard.py`, and run against the absent note:

```
python3 -m pytest tests/test_gh_invocation_guard.py -q
1 failed, 16 errors in 0.08s          # 17/17 fail

E  AssertionError: vault-template/99-Operations/scripts/gh-invocation-guard-script.md
   does not exist — this is the RED state these tests were written in
   (task G2, before G3.1 builds the note).
```

The rest of the suite is unperturbed by the new module:

```
python3 -m pytest tests/ -q --ignore=tests/test_gh_invocation_guard.py
359 passed in 81.08s
```

**All G2 rows are now `[x]`.** Observed to FAIL without the guard (transcript above) and to PASS
with it: `17 passed in 1.43s`, first run after G3.1. Both halves of the red-first cycle are
recorded, which is what `[x]` requires.

Two implementation obligations the tests already bind, so G3 cannot quietly skip them:

- **G2.3 asserts the refusal names the REST replacement**, not merely that it refuses — G3.3's
  requirement, enforced by the suite rather than left to review.
- **G2.9 asserts `defer` (no output at all)** for `git push`, not `allow`. An `allow` is a
  decision; emitting one on the outbound guard's subject matter would perturb the exfil path this
  change must leave byte-identical.
- **G2.11 asserts on the NOTE's text**, requiring it to name the four evasions it cannot catch
  (indirection, alias, base64, subprocess). Written as a documentation assertion rather than an
  xfail behavioural test, because proving an evasion would mean executing one against a live
  control — operator-instructed only, per the standing guard-denial rule.

## G3 — Build

- [x] G3.1 Write `99-Operations/scripts/gh-invocation-guard-script.md` as a literate meta-script note
      EVIDENCE: local · `pytest tests/test_gh_invocation_guard.py` · **17 passed** · 2026-08-25T21:3x+08:00
      `vault-template/99-Operations/scripts/gh-invocation-guard-script.md` written. Deterministic
      (INV-6): `json`/`shlex`/`sys` only, no subprocess, no network. **Design decision beyond the
      task text: it emits `deny` or NOTHING, never `allow`** — an allow is a decision, and expressing
      one about `git push` would perturb the outbound guard's ASK; G1.1 already showed a deny wins
      regardless, so an allow would buy nothing.
      (INV-3). No subprocess invocation; no network (INV-6).
- [x] G3.2 Stem conforms to the naming ruleset — silo-section-descriptor, ≥3 hyphen-tokens (INV-11).
      EVIDENCE: `gh-invocation-guard-script` — 4 hyphen-tokens, silo-section-descriptor (INV-11).
- [x] G3.3 Deny message carries the REST mapping and states the reason once
      EVIDENCE: bound by test G2.3, which asserts the refusal string contains the REST mapping —
      enforced by the suite rather than left to review.
      (GraphQL requires auth unconditionally; REST does not).
- [x] G3.4 Register the hook in `vault-template/.claude/settings.json`; add the five Layer-1
      EVIDENCE: local · `vault-template/.claude/settings.json` Bash PreToolUse hooks **1 -> 2**;
      its five Layer-1 deny entries already landed in `33e9ba4`. JSON re-parsed clean.
      `Bash(gh …)` deny entries there. **Red first:** show the template lacks both today.
- [x] G3.5 Add a `permissions` block plus the hook registration to
      EVIDENCE: local · `$FRAMEWORK_ROOT/.claude/settings.json` — **`permissions.deny` 0 -> 5** and
      Bash hooks **1 -> 2**. RED confirmed at G0.3: its only top-level key had been `hooks`.
      `value-memory-mining/.claude/settings.json`. **Red first:** its top-level keys are `['hooks']`.
- [ ] G3.6 `render` → `reconcile` reports zero drift; `git status --porcelain` clean afterwards
      (proving generated output is ignored, not merely uncommitted).


### G3 — obligations discovered during execution, not in the task text

- **Script Inventory conformance.** `tests/test_inventory_conformance.py` verifies **in both
  directions** that the fleet, the `maintenance` Script Inventory and the README name the same set.
  Adding a note therefore obliged: a **second spec delta** (`specs/maintenance/spec.md`, MODIFIED —
  generated from the live text so nothing was transcribed: 14 -> 15 rows, **all 3 scenarios
  preserved verbatim**); a README row; the README count **14 -> 15**; and the prose "the harness
  guard" -> "two harness guards".
- **`constitutional-impact` widened.** The block declared only `access-control`. It now declares
  both specs and `protects` gains INV-2 — `maintenance/spec.md` carries
  `protects: [INV-2, INV-3, INV-6]`, and the diff gate refuses a declaration that does not match
  the diff.
- **F15 defect found and fixed in the shipped note.** The first draft cited `tools/pr-state.py` as
  the subprocess example. `vault-template/` ships to deployed vaults, which have no `tools/`, and
  the standalone-vault lint refused it. The measurement stays in this change's
  `blast-radius-transcript.md` (repo-only); the note now states the principle without naming a
  framework-repo path. **F15 findings: 0.**
- **README ADR count 44 -> 45** in three places, plus the range `ADR-0001–0044` -> `–0045`.
  Pre-existing on this branch since `ac6db32` added ADR-0045 without updating the README.

⚠ **One test is expected-RED until landing:**
`test_maintenance_spec_inventory_names_exactly_the_note_set` reads the **main** spec, and the
Script Inventory row reaches it only when `openspec archive` syncs the delta. This repo archives on
the feature branch **before opening the PR**, so CI sees it green; it cannot be green before then
without bypassing the delta flow. `preflight.py`: 12/16 reproduced, this the only issue.

## G4 — Regression, by instruments that did not perform the work

- [~] G4.1 Full `pytest` green. `inv6-offline-check` green — including on the **unmodified**
      outbound guard, proving this change did not touch it.
      EVIDENCE: local · 2026-08-26T00:0x+08:00
      `inv6-offline-check` **GREEN — 15 fleet notes analysed, 0 violations, 0 unresolved** (14 before
      this change; the new note is included and passes).
      **The outbound guard is byte-identical to `main`**, proven by blob SHA rather than an empty
      diff: `44b66baf1132da21f3ab35c4ad1dfca9e3e79933` on both sides.
      `pytest tests/ -q` -> **1 failed, 375 passed**. `[~]` NOT `[x]` because "full pytest green" is
      not yet true: the single failure is
      `test_inventory_conformance::test_maintenance_spec_inventory_names_exactly_the_note_set`,
      which reads the **main** spec. The Script Inventory row reaches it only when `openspec archive`
      syncs the delta, which this repo does on the feature branch **before** opening the PR. Ticks to
      `[x]` after archive.
- [ ] G4.2 **Operator step, through the real harness:** invoke a denied form and an allowed form in a
      live session. No unit test traverses hook registration; a passing test suite is not evidence
      that the hook is loaded. Record both outcomes.
- [~] G4.3 `template-parity` still reports 0 drift. `preflight.py` CLEAR — noting its recorded hard
      bound: it runs the shipped check, so it moves findings earlier and adds no coverage.
      EVIDENCE: local · 2026-08-26T00:0x+08:00
      `template-parity` -> **19 lockstep files across 2 prefixes, 1 drift**, and the drift names
      itself: `MISSING-IN-LIVE: 99-Operations/scripts/gh-invocation-guard-script.md`. That is the new
      note present in the template and not yet mirrored to the live vault — it resolves at operator
      deploy-down, not on this branch. **No other drift exists** (enumerated: exactly 1 line).
      template-parity is **not a CI job** (it needs a live vault CI does not have), so this does not
      gate the PR.
      `preflight.py .` -> 12/16 CI jobs reproduced, **1 issue**, and that issue is G4.1's expected-red
      above. STEP 11 reports **CAN ARCHIVE gh-invocation-form-allowlist**.
      Recorded hard bound (unchanged): preflight runs the SHIPPED check, so it moves findings earlier
      and adds no coverage.
- [~] G4.4 Constitutional diff gate green on the `constitutional-impact` block.
      EVIDENCE: local · `preflight.py` STEP 7b, against the real merge-base diff ·
      2026-08-26T00:0x+08:00
      Result: **`constitutional-diff-gate: no protected element touched -- not applicable`.**
      That is a DEFERRAL, not a pass. The gate reads the diff, and this change's
      `specs/maintenance/spec.md` lives under `openspec/changes/`; the **main**
      `openspec/specs/maintenance/spec.md` is untouched until archive. The widened declaration
      (`touches:` both specs, `protects` gains INV-2) is therefore correct and necessary but **not yet
      exercised**. It ticks `[x]` when the archive commit makes the gate fire — the same sequence
      ADR-0042's own change recorded when it became its gate's first live subject.

## G5 — Gate 4

- [ ] G5.1 Re-run the G0 sweeps; diff output against `blast-radius-transcript.md`.
- [ ] G5.2 ADR-0045 header flipped from Proposed to Accepted **on merge** — the three stale ADR
      headers (0032, 0033, 0042) are the recorded reason this is a task and not an intention.
- [ ] G5.3 Human sign-off (§3 Gate 4, human-only). Full absolute `view <path>` + explicit
      "reply Approved".
- [ ] G5.4 Operator re-runs `render` in the live vault after deploy-down.
