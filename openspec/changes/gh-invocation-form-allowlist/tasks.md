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

- [~] G2.1 `gh api repos/o/r/pulls` → **allow**
- [~] G2.2 `gh auth status` → **allow**
- [~] G2.3 `gh api graphql -f query=...` → **deny** (the one `gh api` form that must not pass)
- [~] G2.4 `gh pr list` / `gh issue list` / `gh run list` / `gh workflow view` → **deny**
      (`gh run` and `gh workflow` are unlisted in Layer 1 and run today — this is the red)
- [~] G2.5 `/usr/bin/gh pr list` (absolute path) → **deny**
- [~] G2.6 `GH_TOKEN=x gh pr list` (leading env assignment) → **deny**
- [~] G2.7 `cd /tmp && gh pr list` (compound) → **deny**
- [~] G2.8 `echo "run gh pr list"` (the token is data, not a command) → **allow**; a guard that
      refuses prose about itself is unusable
- [~] G2.9 `git push` → falls through untouched; **assert the outbound guard's behaviour is
      byte-identical to the pre-change baseline.** This change must not perturb INV-14 enforcement.
- [~] G2.10 Malformed / empty stdin → exit 0, no output. Document explicitly that this **fails open**
      and is the reason Layer 1 is retained.
- [~] G2.11 Record the cases the matcher provably does **not** catch (variable indirection, alias,
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

**All G2 rows are `[~]`, not `[x]`.** They are written and observed to fail without the guard;
they tick to `[x]` only when they pass WITH it, after G3.1. Marker discipline: `[~]` built,
`[x]` tested.

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

- [ ] G3.1 Write `99-Operations/scripts/gh-invocation-guard-script.md` as a literate meta-script note
      (INV-3). No subprocess invocation; no network (INV-6).
- [ ] G3.2 Stem conforms to the naming ruleset — silo-section-descriptor, ≥3 hyphen-tokens (INV-11).
- [ ] G3.3 Deny message carries the REST mapping and states the reason once
      (GraphQL requires auth unconditionally; REST does not).
- [ ] G3.4 Register the hook in `vault-template/.claude/settings.json`; add the five Layer-1
      `Bash(gh …)` deny entries there. **Red first:** show the template lacks both today.
- [ ] G3.5 Add a `permissions` block plus the hook registration to
      `value-memory-mining/.claude/settings.json`. **Red first:** its top-level keys are `['hooks']`.
- [ ] G3.6 `render` → `reconcile` reports zero drift; `git status --porcelain` clean afterwards
      (proving generated output is ignored, not merely uncommitted).

## G4 — Regression, by instruments that did not perform the work

- [ ] G4.1 Full `pytest` green. `inv6-offline-check` green — including on the **unmodified**
      outbound guard, proving this change did not touch it.
- [ ] G4.2 **Operator step, through the real harness:** invoke a denied form and an allowed form in a
      live session. No unit test traverses hook registration; a passing test suite is not evidence
      that the hook is loaded. Record both outcomes.
- [ ] G4.3 `template-parity` still reports 0 drift. `preflight.py` CLEAR — noting its recorded hard
      bound: it runs the shipped check, so it moves findings earlier and adds no coverage.
- [ ] G4.4 Constitutional diff gate green on the `constitutional-impact` block.

## G5 — Gate 4

- [ ] G5.1 Re-run the G0 sweeps; diff output against `blast-radius-transcript.md`.
- [ ] G5.2 ADR-0045 header flipped from Proposed to Accepted **on merge** — the three stale ADR
      headers (0032, 0033, 0042) are the recorded reason this is a task and not an intention.
- [ ] G5.3 Human sign-off (§3 Gate 4, human-only). Full absolute `view <path>` + explicit
      "reply Approved".
- [ ] G5.4 Operator re-runs `render` in the live vault after deploy-down.
