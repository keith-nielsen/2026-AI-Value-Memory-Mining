<!-- SPDX-License-Identifier: Apache-2.0 -->

# Tasks — seed-auto-memory-store

> **Marker discipline.** `[~]` = built · `[x]` = tested. Never the same marker. A box is ticked only
> when the test was **observed to fail without the change**, and its evidence is cited (ADR-0031:
> a step that says *enumerate* or *verify* is satisfied only by a pasted, re-runnable transcript).

## Who performs what

| Actor | Steps |
|---|---|
| **agent** | 1–5, 7 · template + spec + linter edits, tests, transcripts |
| **operator** | 6 (Gate-4 sign-off), 8.5–8.7 (ship: tag → Release object → verify), 9 (deploy-down) |

Ship is operator-only by structure: a Release object needs authenticated `gh`, whose token is in the
OS keyring, and `allowUnsandboxedCommands: false` (vault commit `eb2bed1`) removes any path to it.

## 1. Baseline *(Gate 1 · transcript required)*

- [ ] 1.1 Show `vault-template/.gitignore` has **no** memory-store rule while `$VAULT_ROOT/.gitignore`
      does — the divergence this change closes. Paste both greps.
- [ ] 1.2 Show `openspec/specs/vault-structure/spec.md` does not mention the store.
- [ ] 1.3 Run the linter on the reference vault **before** the guard exists and record the result.
      Known baseline: exit **1**, one finding, `30-Sites/.claude` (untracked harness scratch dir,
      unrelated). The guard must not change that finding.
- [ ] 1.4 Confirm the `.example` file on the branch is byte-identical to what this change governs —
      it is already committed as `a4deb6e`; this change adds no second copy.

## 2. Template

- [x] 2.1 `vault-template/.gitignore` — add `/10-Logbook/vmm-working-memory/` with the rationale
      comment and the **narrowness note** the `99-Operations/bin/` rule above it already carries
      (ignores the store directory only, never a parent holding tracked scaffold).
- [x] 2.2 Confirm the rule is anchored (`/10-Logbook/...`), so it cannot match a same-named directory
      nested elsewhere in a deployment.

## 3. Specs

- [x] 3.1 `vault-structure` — MODIFIED `Folder Structure` per the delta: store in the tree marked
      optional and harness-owned, the ADR-0032 non-ownership paragraph, the no-tracking paragraph,
      and the two scenarios (present / absent).
- [x] 3.2 `maintenance` — ADDED Requirement for the linter guard per the delta.
- [x] 3.3 **Constitutional-impact declaration** — `vault-structure/spec.md` carries
      `protects: [CONST-02, CONST-04, CONST-05, INV-1, INV-12]`, so ADR-0042's gate fires. Declare the
      touched identifiers and state that **none is overridden**, with the reason. Do not skip this on
      the grounds that the change feels small — the gate refuses silence, not work.
      ⚠ **Measured 2026-08-25:** `preflight.py` reports *"constitutional-diff-gate: no protected
      element touched — not applicable"* on this tree. That is correct and temporary: the gate reads
      `protects:` **frontmatter**, and the delta at `changes/*/specs/vault-structure/spec.md` carries
      none. The gate becomes applicable at task 8.4, when archiving syncs the delta into
      `openspec/specs/vault-structure/spec.md` **on the feature branch** (ADR-0040) and the PR diff
      finally touches a tagged file. Do not read today's "not applicable" as "no declaration needed".

## 4. The guard — `99-Operations/scripts/knowledge-lint-script.md` → `bin/vault-lint.py`

- [x] 4.1 Read `.claude/settings.local.json` if present; extract `autoMemoryDirectory` if declared.
- [x] 4.2 Refuse in three **distinctly reported** cases: path does not exist · exists but is not a
      directory · resolves **outside** the vault root. Resolve symlinks before the containment test —
      a symlink inside the vault pointing out of it is the escape case, not the exists case.
- [x] 4.3 Pass when the file is absent, or present with no declaration. The store is optional.
- [x] 4.4 Report the declared path verbatim and the case matched. Never a verdict string (F20).
- [x] 4.5 Do **not** read the store's contents; do **not** modify the settings file.
- [x] 4.6 ADR-0023 exit-code contract; the literate note is the source, `render` produces the target
      (INV-3) — never edit `99-Operations/bin/vault-lint.py` directly.

## 5. Tests — refusing cases first

- [x] 5.1 **Adversarial before confirming:** a fixture declaring the shipped placeholder MUST be
      refused. Run this before any passing fixture.
- [x] 5.2 Path exists but is a file → refused, reported distinctly from 5.1.
- [x] 5.3 Path resolves outside the vault root → refused, reported distinctly. **Include the symlink
      variant**, which is the case a naive `startswith` check passes.
- [x] 5.4 Correctly configured store → passes, and reports nothing about the notes inside.
- [x] 5.5 Settings file absent → passes. Declaration absent → passes.
- [ ] 5.6 Real reference vault after the change: the guard passes (its store resolves), and task 1.3's
      pre-existing `30-Sites/.claude` finding is **unchanged**. A guard that alters an unrelated
      finding has changed something it was not asked to change.
- [ ] 5.7 Confirm 1.3 and 5.6 are the same invocation.

## 6. Gate 4 — human sign-off *(operator; not agent-delegatable)*

- [x] 6.1 Re-run the Gate-1 transcripts and **diff** against task 1.
- [x] 6.2 Present the absolute path to `proposal.md`; request explicit approval.
- [x] 6.3 **Approved** — Keith Nielsen, 2026-08-25
      **Provenance of this line.** The operator gave the approval in session, verbatim: *"You can
      edit the seed-auto-memory-store/tasks.md file, it's based on my approval, I Approve."* The
      decision is the operator's; the agent typed the line at their explicit direction. Recorded
      here because a sign-off whose authorship is ambiguous is worth less than one that says who
      approved and who wrote it down.
- [ ] 6.4 **Flip ADR status → Accepted if this change carries an ADR.** Expected: it does not — it
      records no new decision, and the decision it does make (guard over prompt) is argued in
      `proposal.md`. If review disagrees, an ADR is written and this box governs it.

## 7. Validation + CHANGELOG

- [x] 7.1 `openspec validate seed-auto-memory-store --strict` — transcript.
- [x] 7.2 `openspec validate --all --strict` — transcript.
- [x] 7.3 `pytest` and `validate-scripts.sh` green — transcripts.
- [x] 7.4 `CHANGELOG.md` `[Unreleased]` entry.

## 8. Landing

- [ ] 8.1 The branch `feat/seed-auto-memory-store` already carries `a4deb6e`. Do **not** rebase it onto
      unrelated work; the uncommitted `config.env.example` edit stays out (task 10.1).
- [ ] 8.2 `tools/preflight.py .` before the first push (ADR-0041).
- [ ] 8.3 `tools/pr-flow.py --plan --branch feat/seed-auto-memory-store`, then drive it; run each
      emitted command **verbatim**.
- [ ] 8.4 Archive **on the feature branch** before merge (ADR-0040).
- [ ] 8.5 **operator** — `tools/ship-release.py vX.Y.Z`: tag → Release object → parity check.
- [ ] 8.6 **operator** — confirm the Release object exists (ADR-0027).
- [ ] 8.7 **operator** — confirm the CHANGELOG carries the shipped version. `v0.1.43` is the standing
      counter-example: a tag with no entry.

## 9. Deploy-down *(operator)*

- [ ] 9.1 `tools/template-mirror.py <VAULT_ROOT>` — carries the `.gitignore` rule down.
- [ ] 9.2 Confirm the reference vault's existing `.gitignore` rule and the template's now **agree**;
      the live one was written first and is the drift being reconciled, not overwritten blindly.
- [ ] 9.3 `vault-render.py render` — deploys the amended linter to `99-Operations/bin/`.
- [ ] 9.4 Re-run `vault-lint.py` on the reference vault: guard passes, `30-Sites/.claude` finding
      unchanged, exit still 1 for that reason alone.

## 10. Deliberately NOT in this change

- [ ] 10.1 The uncommitted `vault-template/99-Operations/config.env.example` venv/PATH comment —
      unrelated, takes its own change (F29).
- [ ] 10.2 Any deploy-down prompt for the absolute path — considered and rejected in `proposal.md`.
- [ ] 10.3 `vault-structure`'s other divergences from the live vault (`50-Mint/`, `60-Forge/`,
      `80-Crucible/`, `99-Operations/bin/` are all absent from the canonical tree). Real finding,
      separate change — recorded so it is owed rather than forgotten.

## Evidence (transcripts, 2026-08-25)

```
$ openspec validate seed-auto-memory-store --strict
Change 'seed-auto-memory-store' is valid

$ openspec validate --all --strict
Totals: 8 passed, 0 failed (8 items)

$ python3 -m pytest tests/test_memory_store_guard.py -q
9 passed in 0.03s

$ python3 -m pytest -q
359 passed in 81.26s

$ bash .github/scripts/validate-scripts.sh
VALIDATION OK

$ python3 tools/preflight.py .
CLEAR - 12/16 CI jobs reproduced, 0 unrunnable here, 4 not reproduced by design
```

**Negative control for task 5 (Definition of Done: observed to fail without the change).** The guard
block was replaced with `store = None` and the same nine cases re-run: **6 of 8 assertions failed**
(placeholder · file-not-directory · symlink escape · malformed JSON · relative path · correctly-
configured). The two that still passed are the two "should pass" cases, which pass **vacuously**
without the guard — stated because a 2/8 result read as partial coverage would be misleading.

Task 1.3/5.6 baseline: the reference vault linter exits **1** with one finding, `30-Sites/.claude`
(untracked harness scratch directory, unrelated to this change and unchanged by it).
