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
      **Landing the allowlist breaks no live caller** — because every call site above is a Python
      subprocess the hook cannot see. That conclusion stands; the reasoning first written under it
      did not, and is corrected here rather than deleted.

      ⚠ **CORRECTED 2026-08-26.** This read: *"`pr-state.py:83` is GraphQL, already 401s in a
      confined session, and line 86 sets `graphql=False` and degrades to anonymous REST; the
      `gh run list` path at 168 is gated on `graphql` and is unreachable in that state."* Measured
      false. A session started in `$FRAMEWORK_ROOT` has no `sandbox` block, reaches the keyring, and
      `gh` authenticates with `repo` + `workflow` scopes — GraphQL then **succeeds**, `graphql` stays
      `True`, and line 168's `gh run list` **is reachable**. The safety of landing this change never
      rested on that degradation; it rests on subprocess invisibility, which holds in both states.
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
- [x] G1.2 Confirm the outbound guard's ASK and this guard's DENY raised by the *same* command
      resolve to DENY. A refusal that an ASK can override is not a refusal.
      **CONFOUND CLOSED — interactive session, real guards, no probes.**
      EVIDENCE: local · command TYPED into an interactive session at `6fe549d` (not a subprocess,
      not `claude -p`) · 2026-08-26T01:2x+08:00

      Command typed: `gh release create --help` — inert if it executes, covered by NO Layer-1
      `permissions.deny` entry (the five are `gh pr`, `gh issue`, `gh project`, `gh repo view`,
      `gh api graphql`), and trips BOTH guards. Verbatim result — **refused with NO permission
      prompt**, reason string is the gh-invocation guard's:

      ```
      `gh release` is refused: the `gh` invocation-form allowlist permits only `gh api` with a
      REST path and `gh auth status`; every other form is refused by default rather than permitted
      by omission (ADR-0045). Use `gh api` with an explicit REST path instead — e.g.
      `gh api repos/{owner}/{repo}/pulls`. Permitted forms: `gh api <REST path>`, `gh auth status`.
      ```

      The other half of the pair, proving an ASK was genuinely raised on the SAME command and did
      not merely fail to fire — the REAL `outbound-publish-guard.py`, not a probe:

      ```
      $ echo '{"tool_name":"Bash","tool_input":{"command":"gh release create --help"}}' \
          | python3 .claude/hooks/outbound-publish-guard.py
      {"hookSpecificOutput": {"hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "... OUTBOUND — CODE / DATA LEAVING THIS MACHINE — HARD STOP ...
        command: gh release create --help ..."}}
      EXIT=0
      ```

      Both confounds the `[~]` recorded are now excluded: the session was **interactive**, so `ask`
      *could* have prompted and did not; and the ASK came from the **real** outbound guard rather
      than a probe. `deny` beats `ask` on the same command. A refusal an ASK could override would
      have surfaced a prompt; none appeared.

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

### Per-row attribution of the 17 — added 2026-08-26

The tally above is an aggregate, and an aggregate does not show that **each** row was exercised.
Traceability was structural but unrecorded: every test function is named for the row it discharges.
Stated here so the mapping is in the record rather than only in the test file.

```
$ python3 -m pytest tests/test_gh_invocation_guard.py -v
test_g2_3_gh_api_graphql_is_the_one_api_form_that_must_not_pass                PASSED
test_g2_4_unlisted_subcommands_are_refused_by_default[gh pr list]              PASSED
test_g2_4_unlisted_subcommands_are_refused_by_default[gh issue list]           PASSED
test_g2_4_unlisted_subcommands_are_refused_by_default[gh run list]             PASSED
test_g2_4_unlisted_subcommands_are_refused_by_default[gh workflow view ci.yml] PASSED
test_g2_5_absolute_path_invocation_is_refused                                  PASSED
test_g2_6_leading_env_assignment_is_refused                                    PASSED
test_g2_7_compound_command_is_refused                                          PASSED
test_g2_1_gh_api_rest_path_is_allowed                                          PASSED
test_g2_2_gh_auth_status_is_allowed                                            PASSED
test_g2_8_the_token_as_data_is_not_a_command                                   PASSED
test_g2_9_unrelated_commands_fall_through_untouched                            PASSED
test_g2_10_malformed_input_fails_open_and_says_so[]                            PASSED
test_g2_10_malformed_input_fails_open_and_says_so[not json]                    PASSED
test_g2_10_malformed_input_fails_open_and_says_so[{}]                          PASSED
test_g2_10_malformed_input_fails_open_and_says_so[{"tool_input":{}}]           PASSED
test_g2_11_uncaught_evasions_are_recorded_not_claimed                          PASSED
============================== 17 passed in 1.33s ==============================
```

**11 rows, 17 tests, every row represented** — `G2.4` and `G2.10` are parametrised ×4 each
(4 + 4 + 9 singles = 17), which is where the count exceeds the row total. G2.4's four parameters are
exactly the four forms its row names.

⚠ The `-v` listing is what makes the aggregate resolvable. A future re-run that reports only
`17 passed` re-opens this gap: the number is unchanged whether or not a row still has a test.

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
      EVIDENCE: local · `vault_naming.py --check-strict`, exit status · 2026-08-26T01:4x+08:00
      ⚠ **This row previously read `EVIDENCE: gh-invocation-guard-script — 4 hyphen-tokens,
      silo-section-descriptor (INV-11)`, which is a PROSE ASSERTION** — a restatement of the claim,
      forbidden by name in constitution §3 Gate 3 (*"never by a prose assertion"*). Replaced with an
      exit status from the governing instrument, rendered from
      `vault-template/99-Operations/scripts/naming-rules-script.md`.

      **Adversarial cases first**, so the exit-0 below is not vacuous — a checker that passes
      everything would pass this stem too:

      ```
      $ python3 vault_naming.py --check-strict "GH_Invocation Guard.md"
      INVALID 'GH_Invocation Guard.md': not a kebab slug (^[a-z0-9]+(?:-[a-z0-9]+)*$);
        fewer than 3 hyphen-tokens (INV-11 floor)
      EXIT=1

      $ python3 vault_naming.py --check-strict "gh-guard.md"
      INVALID 'gh-guard.md': fewer than 3 hyphen-tokens (INV-11 floor)
      EXIT=1

      $ python3 vault_naming.py --check-strict "gh-invocation-guard-script.md"
      EXIT=0
      ```

      ⚠ **`--check` is the WRONG mode and was measured to be so.** It validates cross-platform
      safety only and its contract is deliberately unchanged for existing callers; run against it,
      `GH_Invocation Guard.md` exits **0**. The INV-11 content rule this row claims lives behind
      `--check-strict` (ADR-0030). Recording a `--check` exit-0 here would have looked like evidence
      and proved nothing.

      ⚠ **DEFECT FOUND, recorded not fixed — `validate-scripts.sh` cannot evidence this row.**
      Line 47 runs `python3 "$BIN/vault_naming.py" >/dev/null` with **no `|| exit`**, and the script
      sets `set -uo pipefail` with **no `-e`** (line 8). The validator's exit code is therefore
      discarded and line 48's `ok "render + naming-rules.json"` prints unconditionally — a
      shell-printed verdict string, which §3 Gate 3 names explicitly as not-evidence. Same vacuity
      class as the known `md-lint || true`. The CI job `naming-validator` inlines its own copy of the
      logic and is unaffected; `validate-scripts.sh` is the surface that lies. Out of scope here —
      belongs to the GitHub platform hardening queue.
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
- [x] G3.5b **(found during G4 prep, not in the original task text)** Render the guard to
      `$FRAMEWORK_ROOT/.claude/hooks/gh-invocation-guard.py`.
      EVIDENCE: local · byte-identical to the note's `## Implementation` block, sha `6fed3595d3fce101`
      · smoke-tested on the harness payload shape: `gh pr list` -> deny with the REST mapping,
      `gh api repos/o/r/pulls` -> no output (defer) · 2026-08-26T00:1x+08:00
      **Why this was nearly missed:** G3.5 registered the hook in the framework settings, but the
      framework repo carries its own **tracked, byte-identical** copy of each hook (verified:
      `outbound-publish-guard.py` sha matches its note exactly). Without this render the registration
      pointed at a nonexistent file — the hook would fail to start, the harness would defer, and
      **G4.2 would have measured nothing while appearing to pass.** A registered hook pointing at a
      missing file is not a loaded hook.
      ⚠ **F29 was OWED here and is now CLOSED by G3.5c below** — it bit a second time on
      2026-08-26 (a note edit left the rendered copy stale, full suite green throughout), and a
      deferral that has drawn blood twice in one day is not a deferral.

- [x] G3.5c **(added 2026-08-26, operator-approved: close F29 rather than ship it owed)**
      Verify every `$FRAMEWORK_ROOT/.claude/hooks/*.py` against the note that governs it.
      EVIDENCE: local · red observed twice, then green · 2026-08-26T02:4x+08:00

      Added to `tests/test_inventory_conformance.py` — the module that exists to close exactly this
      class of seam, and whose docstring already diagrammed three of them. The fourth is now in that
      diagram rather than in a parallel file:

      ```
      render / reconcile  ->  note -> deployed vault
      template-parity     ->  template -> live vault
      (nothing)           ->  SPEC -> NOTE
      (nothing)           ->  NOTE -> THIS REPO'S OWN .claude/hooks/ COPY   <- F29, closed
      ```

      **RED 1 — the drift that actually occurred**, reproduced against the live repo by restoring
      the pre-`0b07ddc` hook while the note carried the corrected message:

      ```
      $ git show 21b1925:.claude/hooks/gh-invocation-guard.py > .claude/hooks/gh-invocation-guard.py
      $ python3 -m pytest tests/test_inventory_conformance.py -k byte_identical
      E  AssertionError: 1 hook file(s) have DRIFTED from their note. The harness loads the file,
      E    not the note, so this drift is live:
      E      .claude/hooks/gh-invocation-guard.py differs from
      E      vault-template/99-Operations/scripts/gh-invocation-guard-script.md
      $ git checkout .claude/hooks/gh-invocation-guard.py     # 1 passed
      ```

      **RED 2 — the detector itself**, sabotaged to always report clean, proving the branch tests
      are not vacuous:

      ```
      $ # parity_report() stubbed to `return [], []`
      $ python3 -m pytest tests/test_inventory_conformance.py -k parity
      3 failed, 1 passed
      ```

      The partition is the point: the three *detection* tests go red, while the confirming case
      stays green — a blind-clean detector still reports clean on a matching pair. A suite where all
      four flipped would mean the fixtures, not the detector, were doing the work.

      **Design note — why `parity_report()` is a pure function.** The first draft asserted directly
      against the live `.claude/`, which made its failure branches reachable only by mutating the
      real repository. One such probe was refused by a permission control mid-task; rather than
      compose a variant to get around it (standing rule: a control's denial is handed over, never
      routed around), the check was refactored to take its subjects as arguments. Both failure
      branches are now exercised against `tmp_path` fixtures. An assertion nobody has watched fail
      is an assumption wearing a test's clothes, and one that *cannot* be watched fail is worse.

      **Fails closed in both directions**: a hook with no note, and a note with no `python` block,
      are both refused — INV-3 forbids a shipped control with no literate source. Ground truth is
      the hook set on disk, never a literal list in the test.

      ⚠ **Bound, stated so it is not over-read.** This governs THIS repository's copies only. The
      deployed vault's `.claude/hooks/` remains `render`/`reconcile`'s subject, and template → live
      vault remains `template-parity`'s. The seam closed is the third arrow, not all three.

- [x] G3.6 `render` → `reconcile` reports zero drift; `git status --porcelain` clean afterwards
      (proving generated output is ignored, not merely uncommitted).
      EVIDENCE: OPERATOR ran `render` in `$VAULT_ROOT` (writes protected paths); agent ran the
      read-only halves · 2026-08-26T03:0x+08:00

      ```
      $ python3 99-Operations/bin/vault-render.py render
      rendered bank-execute-script.md -> 99-Operations/bin/vault-refine-execute.py
      … 14 targets …
      RENDER_EXIT=0

      $ python3 99-Operations/bin/vault-render.py reconcile
      ok: … 14 targets, every one ok …
      RECONCILE_EXIT=0

      $ git status --porcelain
      ?? 10-Logbook/vmm-working-memory-notes.md
      ?? 30-Sites/verification-provenance-audit/
      ```

      **14 targets rendered, 14 reconciled ok, zero drift, exit 0 both ways.** No render target
      appears in `git status`. The two untracked entries are pre-existing and unrelated to render
      (a memory-notes file and a parked Site); neither is a render target.

      ⚠ **The parenthetical in this task's own text is wrong for 3 of the 14, and the truth is
      stronger.** Render targets do not form one class — measured, by asking git rather than by
      reading `.gitignore`:

      | Class | Count | Why it is absent from `git status` |
      |---|---|---|
      | `99-Operations/bin/*` | **11** | **ignored** — `.gitignore:58` (`99-Operations/bin/`) |
      | `99-Operations/hooks/pre-commit`, `pre-push`, `.claude/hooks/outbound-publish-guard.py` | **3** | **TRACKED** — absent because render reproduced them **byte-identically** to the committed content |

      For the 11, a clean status proves the output is ignored. For the 3 it proves something the
      task did not think to claim: **`render` is idempotent against committed content**. Had render
      altered any of those three by even a byte, they would have shown as modified. Reading all 14
      as "ignored" would have discarded that, and would also have been a false statement about the
      three files most worth watching — two git hooks and the INV-14 outbound guard.

      ⚠ **Scope: 14 targets, not 15.** `gh-invocation-guard-script.md` is not in the live vault yet
      (`template-parity` MISSING-IN-LIVE, recorded at G4.3). It arrives at deploy-down, and
      re-rendering there is **G5.4**. This run therefore proves the change did not perturb the
      EXISTING fleet; it does not exercise the new note.

      **Pre-render baseline** (agent, before the operator's write): `reconcile` already reported
      14 ok / zero drift / exit 0, so this render was expected to be a no-op and was.


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
- [x] G4.2 **Operator step, through the real harness:** invoke a denied form and an allowed form in a
      live session. No unit test traverses hook registration; a passing test suite is not evidence
      that the hook is loaded. Record both outcomes.
      EVIDENCE: local · three commands TYPED, one per tool call, into an interactive session at
      `6fe549d` with both Bash `PreToolUse` hooks loaded from `$CLAUDE_PROJECT_DIR` · never wrapped
      in a script, because a subprocess is invisible to the hook (G0.2) · 2026-08-26T01:2x+08:00

      Every form below is covered by **no** Layer-1 `permissions.deny` entry, so only the hook can
      account for the outcomes — this measures hook *registration*, which is what no unit test can.

      **DENIED form — `gh run list`.** Refused, verbatim, and the reason names the REST replacement
      as G3.3 requires:

      ```
      `gh run` is refused: the `gh` invocation-form allowlist permits only `gh api` with a REST
      path and `gh auth status`; every other form is refused by default rather than permitted by
      omission (ADR-0045). Use `gh api` with an explicit REST path instead — e.g.
      `gh api repos/{owner}/{repo}/pulls`. Permitted forms: `gh api <REST path>`, `gh auth status`.
      ```

      **ALLOWED form — `gh auth status`.** Executed untouched, no prompt, real output:

      ```
      github.com
        ✓ Logged in to github.com account keith-nielsen (keyring)
        - Active account: true
        - Git operations protocol: https
        - Token: gho_************************************
        - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
      ```

      **ALLOWED form — `gh api repos/keith-nielsen/2026-AI-Value-Memory-Mining/pulls`.** Executed
      untouched; returned 102.7 KB of live PR JSON, first object
      `"number":101 … "state":"open" … "title":"deps(openspec): Bump @fission-ai/openspec from
      1.6.0 to 1.10.0"`.

      ⚠ **One recorded expectation was wrong, in the direction that strengthens the evidence:** the
      session was expected to be UNAUTHENTICATED, so an auth failure *after* execution would have
      counted as a pass (the hook having stood aside). `gh` is in fact authenticated via keyring, so
      both allowed forms returned real data. There is no auth-error ambiguity to interpret: the two
      allowed forms demonstrably reached GitHub and the denied form demonstrably never ran.

      This is also the first end-to-end proof that G3.5b's rendered
      `.claude/hooks/gh-invocation-guard.py` is *loaded*, not merely registered — the failure mode
      G3.5b warns of (a registration pointing at a missing file, deferring silently) would have
      shown `gh run list` executing.

      ⚠ **The credential state this proof ran under, recorded because it changes what it proves.**
      `gh auth status` in that same session returned **authenticated** — account `keith-nielsen`, via
      keyring, scopes `gist`, `read:org`, `repo`, `workflow`. The session was unsandboxed:
      `$FRAMEWORK_ROOT/.claude/settings.json` carries no `sandbox` key, while
      `$VAULT_ROOT/.claude/settings.json` sets `sandbox.enabled: true` with
      `allowUnsandboxedCommands: false`. Credential reach is therefore a property of the project
      directory the session started in.

      **This makes G4.2 a stronger result, not a weaker one.** The guard refused a channel that
      genuinely worked, with real mutation capability behind it — not one already broken by an
      unreadable credential. It also invalidated the auth-based rationale the change originally
      shipped with; see the ADR-0045 Context correction of the same date, and the corrected G0.2
      reasoning above.
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

- [x] G5.1 Re-run the G0 sweeps; diff output against `blast-radius-transcript.md`.
      EVIDENCE: local · all three sweeps re-run and diffed · 2026-08-26T03:2x+08:00

      | Sweep | Result |
      |---|---|
      | G0.1 | **DEFECT FOUND — the record was truncated.** Fixed; see below |
      | G0.2 | **IDENTICAL** — same four executing call sites, same line numbers (`gh_read.py:112`, `pr-flow.py:1419`, `pr-state.py:83`, `pr-state.py:168`); a widened sweep of all of `tools/` finds no fifth |
      | G0.3 | **IDENTICAL** — byte-for-byte against the post-change block, zero drift |

      **G0.1 — the recorded output stopped at 30 lines; the sweep returns 60.** The cut falls exactly
      where per-file counts drop to `2`, which is a `head`-shaped truncation, not a filter. Gate 1
      requires *full, untruncated* output for this precise reason: a truncated record cannot
      distinguish a NEW match from one that was always present and merely unrecorded, so the Gate 4
      diff it exists to support cannot be read.

      **This is Gate 4 working as designed.** The constitution defines it as re-running the Gate-1
      transcript and diffing, *"not by re-reading the composed sections"* — and re-reading would
      never have found this, because the composed partition below the block was correct.

      **No live caller was hidden — verified, not assumed.** Each of the ~27 newly-revealed files was
      checked against `git diff --name-only main...HEAD`: this branch touches none of them, so they
      matched at G0.1 time and were cut off. Each was then read directly:

      ```
      tools/inv6-offline-check.py:11    docstring naming outward verbs inside regex literals
      tests/test_secret_scan.py:64      an assertion's message string
      vault-template/.claude/hooks/outbound-publish-guard.py:9   comment
      vault-template/96-Runbooks/session-bootstrap-loader.md:113 runbook prose
      README.md:250                     the Script Inventory table row
      docs/USING-THIS-TEMPLATE.md:187   documentation prose
      ```

      **All prose, docstrings, test strings or doc tables. None executes `gh`.** The LIVE partition
      is unchanged at five surfaces, and G0.2's conclusion — that landing the allowlist breaks no
      live caller — is unaffected.

      The transcript now carries the full 60-line output plus a note recording what was truncated
      and how it was found.
- [ ] G5.2 ADR-0045 header flipped from Proposed to Accepted **on merge** — the three stale ADR
      headers (0032, 0033, 0042) are the recorded reason this is a task and not an intention.
- [x] G5.3 Human sign-off (§3 Gate 4, human-only) — **Approved** — Keith Nielsen, 2026-08-26
      Requested with full absolute `view <path>` paths + an explicit "reply Approved" prompt.
      ⚠ The operator's approval, the name and the ISO date sit on the TICKED LINE ITSELF, and
      `Approved` is exact-case. `pr-flow.py`'s `SIGNOFF_LINE` requires all three on one line and is
      case-sensitive — deliberately: its own comment records that an earlier cut matched "Approved"
      anywhere, so the UNTICKED task *describing* the sign-off read as the sign-off, and dogfooding
      caught it reporting Gate 4 signed while unsigned. A multi-line record is not machine-readable
      consent.
      Requested in the standing format: `Proposal to review/approve:` + full absolute `view` paths
      for `proposal.md`, `openspec/adr/0045-gh-invocation-form-allowlist.md` and `tasks.md`, with the
      consequences and the ADR's Sacrifice restated for explicit acceptance, and an explicit
      "reply `Approved`" prompt. Operator replied **`Approved`**.

      Recorded by the agent, attributed and dated. The human made the decision; the agent only
      transcribes it — §5 reserves the sign-off act to the human and it is not agent-delegatable.

      Consequences explicitly accepted at sign-off: refusal of working-but-unlisted `gh` forms
      (`gh run watch`, `gh release view`); two overlapping Bash `PreToolUse` guards rather than one;
      a control bounded to the agent's typed channel — every fleet `gh` call is a subprocess it
      cannot see — and defeated by composition or indirection, making it a **tripwire for a
      cooperating agent**, not an anti-evasion control; and no governance of prose, so a denied
      command may still be proposed to the operator in writing.
- [ ] G5.4 Operator re-runs `render` in the live vault after deploy-down.
