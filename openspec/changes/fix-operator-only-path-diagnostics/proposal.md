<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: fix-operator-only-path-diagnostics

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** one Requirement ("Operator-Only Paths Fail Legibly"). **No principle is overridden or
weakened**; it is a conforming diagnostic amendment that makes an *existing, deliberate* denial
self-explaining. Ships **without a new ADR** per the `fix-append-idempotent-catalog-link` /
`add-template-parity-check` precedent for conforming amendments.
**Tier:** 0-adjacent (a legibility change to the INV-3 fleet; no behavioural change to any
*successful* path)
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-20)
**Date:** 2026-07-20

---

## Why

The live-vault exclusion-list inventory (**P17**, Site `protocol-harness-framework`, vault commits
`6c2f9c2`/`f6d823d`) exercised every fleet write path with a real write from inside the OS sandbox and
found two scripts whose targets are **entirely** in denied areas:

| Script | Denied target(s) | Observed |
|---|---|---|
| `vault-render.py render` | **all 13** `deploy_target`s — `~/bin/` (out-of-vault default-deny), `99-Operations/hooks/`, `.claude/hooks/` | `OSError errno=30` on the first target; renders nothing |
| `vault_naming.py` (emit) | `99-Operations/schemas/naming-rules.json` | `OSError errno=30` |

The operator chose **branch 3**: add no `excludedCommands` entries, and treat both as **operator-only
paths** — the only branch that *reduces* the trusted surface, and consistent with the Area Access
Matrix, which already withholds `99-Operations/` (`A: —`) and `.claude/` from the agent. **The denial
is correct. Its presentation is not.**

Today both scripts die with a bare Python traceback. Nothing in that traceback says the failure is
*intentional*, so the reader's first hypothesis is a broken deploy, a missing dependency, or a
misconfigured sandbox — and they debug a fault that does not exist. **This gets strictly worse after the
Stage-B strict flip** (`allowUnsandboxedCommands: false`), which removes the burn-in escape hatch: these
stop prompting and start simply failing.

Branch 3 traded a config entry for a **documentation duty**, and P17 recorded that duty as three layers:
the probe sheet (reaches only someone already reading it), agent memory (*passive load is not
consultation* — this project's own F21/F24 finding), and **the script's own failure message**. Only the
third fires at the moment of confusion, unavoidably, for every actor. This change builds the third.

**A self-explaining failure beats any amount of documentation**, because it is the one channel
guaranteed to be open exactly when someone is confused.

## What Changes

- **`maintenance` spec:** +1 ADDED Requirement ("Operator-Only Paths Fail Legibly", 3 scenarios).
- **`vault-template/99-Operations/scripts/render-reconcile-script.md`:** the `render` write is wrapped;
  `OSError` with `errno == EROFS` prints a four-line operator-only explanation and exits **4**. Any
  other `OSError` **re-raises unchanged** — this must not become a blanket error swallow. `reconcile`
  is untouched and stays read-only/available.
- **`vault-template/99-Operations/scripts/naming-rules-script.md`:** identical treatment for the
  emit-mode write. `--check` / `--check-strict` exit *above* this block and are unaffected — **the
  commit gate keeps working**.
- **`tests/test_fleet.py`:** **+4 cases** — EROFS → exit 4 + message + no traceback (render *and*
  naming); `--check-strict` still gates commits while the schema path is unwritable; and a **real
  `EACCES`** proving a non-EROFS `OSError` still propagates. Planned as +2; see the method note in
  `tasks.md` §3 for why the split was necessary and why the original test plan was wrong.
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Out of scope:** the Stage-B strict flip itself; any `excludedCommands` edit (branch 3 is *no entry* —
adding one would silently reverse the operator's decision); the `vault-lint.py` false positive on
harness-created dot-directories under `30-Sites/` (recorded in P17, unfixed).

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> The `maintenance` spec governs the deterministic fleet: INV-2 (one mutation, one commit), INV-3
> (literate source of truth, drift detected via render/reconcile), INV-6 (offline determinism). This
> change adds **no** capability and removes none: the set of paths each script can write is byte-for-byte
> unchanged, and every *successful* run behaves identically. It changes only what a **failing** run
> prints and returns. INV-5 is strengthened in presentation, not in force — the agent is denied
> `99-Operations/` before and after; it simply now learns *why*. Exit **4** is introduced as a distinct
> "denied by design" code so a caller can tell it from a genuine fault (exit 1) — the same
> discriminating-exit-code discipline P16's probe used.

**Blast radius — every artifact this change touches:**

- [x] `openspec/specs/maintenance/spec.md` — ADDED Requirement (spec delta in this change)
- [x] `vault-template/99-Operations/scripts/render-reconcile-script.md` — EROFS branch + Rationale
- [x] `vault-template/99-Operations/scripts/naming-rules-script.md` — EROFS branch + Rationale
- [x] `tests/test_fleet.py` — +4 behaviour cases (each with an unshimmed control)
- [x] `CHANGELOG.md` — `[Unreleased]` entry
- [x] **`vault-template/99-Operations/scripts/vault-lib-script.md`** — the canonical fleet exit-code
      contract + `EXIT_OPERATOR_ONLY = 4`. **Surface found late, by audit, not by the original blast
      radius:** the contract documented `0/1/2/3` and states *"drivers key on codes, not prose"*, so
      introducing a `4` in two scripts without amending it was real drift
- [x] **`vault-template/96-Runbooks/render-reconcile-runbook.md`** — step 2 already said "operator-run"
      (correct, and *not* rewritten), but named only `.claude/` and `99-Operations/hooks/`. P17 showed
      **every** target is denied — `~/bin/` is out-of-vault and fails *first* — so the runbook
      understated the scope. Corrected, and the new message + exit 4 documented
- [ ] `openspec/adr/` + README ADR count — **no change** (conforming amendment, no ADR)
- [ ] `.claude/settings.json` / `excludedCommands` — **no change, deliberately** (branch 3)
- [ ] Live vault — **no change in this PR**; the amended notes mirror post-merge, then the **operator**
      runs `render` (the agent cannot — that is the very condition this change documents), then
      `tools/template-parity.py` confirms the mirror

**External dependency being adopted: NONE.** `errno` is stdlib.

## Gate 2 — PLAN (Migration + Regression)

- Purely additive error handling; no migration, no data change, no change to any successful path.
- **Bootstrap constraint honored:** the message is **inlined** in `render-reconcile-script.md` rather
  than factored into `vault_lib` — ADR-0023's bootstrap exception forbids that script importing it.
  The duplication is deliberate and is documented in-line at both sites.
- **Deployment ordering is the one real hazard.** The fix lives in the very script that deploys it, so
  the agent cannot self-deploy it. Post-merge the **operator** must run `render`. Until then the live
  vault keeps the old traceback behaviour — annoying, not dangerous.
- Regression: full CI (`openspec validate --all --strict`, lints, `validate-scripts`, fleet-pytest incl.
  the 2 new cases). The exactly-one-fence rule and both code blocks' syntax were verified locally.
- Rollback: revert the two try/except blocks + requirement + tests + CHANGELOG line (single revert).

## Gate 3 — EXECUTE + REGRESSION-TEST

- Implementation in this PR. **Locally verified, 2026-07-20:**
  - `openspec validate --all --strict` → **8 passed, 0 failed**
  - both notes still carry **exactly one** code fence (B5) and both blocks `ast.parse` clean
  - `pytest tests/` → **56 passed** (4 new cases included)
- **Executed, not composed:** the four new cases were run and their output read; the original test plan
  in `tasks.md` §3.1 was found wrong during execution (`chmod` yields `EACCES`, not `EROFS`, so the
  planned test would have passed for the wrong reason) and the correction is recorded there rather than
  quietly re-specified.
- **END-TO-END AGAINST A REAL `EROFS`, 2026-07-20 — the evidence the test suite cannot provide.**
  The suite *injects* the errno; a real `EROFS` needs a read-only mount. The live vault has one, so both
  amended code blocks were extracted and run against the live read-only bind mounts as the sandboxed
  agent:
  - `render` → `BLOCKED: cannot write /home/administrator/bin/vault-refine-execute.py` + the
    operator-only lines, **exit 4, no traceback**
  - `vault_naming.py` (emit) → equivalent message on
    `99-Operations/schemas/naming-rules.json`, **exit 4**
  - **Regression, same real conditions:** `--check-strict` still exits **0** on a conforming name and
    **1** on `two-tokens.md` (commit gate intact); `reconcile` still exits **0** with `ok:` for all 13.
- **Mutation-tested.** With the shim's prefix broken so it cannot fire, both operator-only tests
  **FAIL** (`assert 0 == 4`). The tests can express failure; they are not vacuous.
- **Exit-code collision audit:** `4` is used nowhere else in `vault-template/`, `tools/`, `.github/`,
  or `tests/`. The one CI caller (`validate-scripts.sh:43`) treats any non-zero as failure, so a `4`
  there surfaces correctly rather than being swallowed.
- CI green on the PR = Gate 3 complete (recorded here when checks finish).

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [x] Blast radius re-checked against the final diff, 2026-07-20 — **9 files, all declared, nothing
      undeclared**: `CHANGELOG.md`, `tests/test_fleet.py`, the three amended script notes
      (`render-reconcile`, `naming-rules`, `vault-lib`), `96-Runbooks/render-reconcile-runbook.md`, and
      the change record itself (`proposal.md`, `tasks.md`, `specs/maintenance/spec.md`). Two of those
      surfaces (`vault-lib`, the runbook) were **absent from the first blast radius and found by
      audit** — recorded as such rather than folded in silently
- [ ] Consequences explicitly accepted (a new exit code **4**; two scripts gain a non-default failure
      path; **zero external runtime dependencies**; the live fix requires an **operator-run `render`**)
- [ ] Human sign-off recorded: **pending** — awaiting operator `Approved`
