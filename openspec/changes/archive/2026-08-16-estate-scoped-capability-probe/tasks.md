<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [x] 1.1 `maintenance` ADDED: *The Capability Probe Measures A Declared Estate* (5 scenarios)
- [x] 1.2 `maintenance` ADDED: *A Probe Reports Diagnoses, Not Internal Errors* (3 scenarios)
- [x] 1.3 Confirm nature is ordinary, not override — ADD-only; *Platform Capability Is Probed, Not
      Recalled* left **verbatim**. Derived from `constitution.md` §3, not from a green CI check
      (`constitution-lint` does no diff analysis — open finding in the hardening queue)

## 2. Estate declaration (the bridge that does not exist today)

- [x] 2.1 `vault-template/99-Operations/config.defaults.env` — add `FRAMEWORK_ROOT` to the existing
      *path placeholder* block beside `VAULT_ROOT`, carrying the same "MUST be overridden in
      config.env with your absolute path" warning: `export FRAMEWORK_ROOT="${HOME}/value-memory-mining"`
- [x] 2.2 `vault-template/99-Operations/config.env.example` — add the personal-override line beside the
      `VAULT_ROOT` one: `export FRAMEWORK_ROOT=…  # set your absolute framework-repo path`
- [x] 2.3 `vault-template/.claude/commands/vmm-session-rebooted.md:11` — resolve the
      `<framework-repo>` placeholder to `"$FRAMEWORK_ROOT"`. **This unfilled placeholder is what the
      agent improvised around on 2026-08-11**; it is the proximate cause, not a cosmetic edit

## 3. Instrument — `tools/pr-flow.py --capabilities`

- [x] 3.1 Take subjects from `VAULT_ROOT` / `FRAMEWORK_ROOT`; **remove cwd derivation for this mode
      only**. Leave `route` / `ready` / `assert-preconditions` on cwd — correct for them
- [x] 3.2 Print the roots actually measured, so output cannot be read as describing another subject
- [x] 3.3 Vault member: report remotelessness as **INV-14 holding**; report a pushable vault remote as
      a **violation** naming the remote
- [x] 3.4 `FRAMEWORK_ROOT` unset → framework layers `UNDECLARED`, never `FAILED` (closes the residual
      named by `2026-08-06-bootstrap-capability-probe`)
- [x] 3.5 Write-scope layer — the layer the runbook has claimed since 2026-08-06 and the instrument has
      never reported. Measure the permitted areas by attempted write. **Highest-priority item in
      section 3** (raised 2026-08-13): 3.6/3.7 are ugly but self-announcing; this gap is silent, and it
      has now produced a hand-rolled substitute twice — see the proposal's reproduction log.
      **Built + tested 2026-08-13** (`write_scope()` / `probe_protected_subtree()`); 7 tests, each
      observed FAILING against the unchanged instrument before the change went in. Subject is
      `$VAULT_ROOT` — the function takes **no** `repo_root` parameter, so cwd derivation cannot leak
      in by way of an argument. Scoped to the live vault: a `vault-template/` path component skips
- [x] 3.5a **Protection self-test** — attempt a real write into `40-Treasury/`, `96-Runbooks/`, and
      `99-Operations/`; refused = protection holding, succeeded = protection failure (operator
      instruction 2026-08-11; supersedes the withdrawn "cite, don't write" draft). ⚠ The subtree list
      is the *operator's*, not the prober's: the 2026-08-13 hand-roll silently dropped `96-Runbooks/`
      and substituted the two subtrees it wanted to write to. The instrument's list is fixed and MUST
      NOT be derived from the caller's interest. **Done:** `PROTECTED_SUBTREES` is a module constant,
      not a parameter and not a discovery; `test_write_scope_probes_every_governed_subtree_not_the_
      probers_choice` asserts all three are probed and that `30-Sites` is not
- [x] 3.5b Probe artifact is zero-byte, dot-prefixed, uniquely suffixed, written at the subtree root —
      unmistakably a probe artifact, never mistaken for content. **Done:** `O_CREAT|O_EXCL|O_WRONLY`
      then immediate close, named `.capability-probe-<pid>-<uuid8>` at the subtree root
- [x] 3.5c Removal attempted in a `finally` **and its result checked** — an unchecked `rm` is exactly
      how the write-succeeded/delete-failed case becomes silent. **Field instance 2026-08-13:** the
      hand-rolled substitute used `rm -f` with the result discarded *and* errors suppressed by `-f`;
      had a governed subtree been writable, it would have reported `WRITABLE` and left residue unnamed.
      **Done:** removal is in a `finally`, its `OSError` escalates the verdict to
      `UNPROTECTED+RESIDUE` and carries the path out
- [x] 3.5d Each failing outcome prints its operator action: protection-gone → the harness
      `denyWithinAllow` list to check and "stop governed work"; residue-left → the **absolute path**,
      the exact `rm`, and the `git status` check proving it was never staged. **Done, and the tests
      assert the guidance text itself**, not merely the verdict — 3.5d makes the guidance part of the
      requirement, so a test that checks only the verdict would pass a probe that strands its reader
- [x] 3.6 Fix `:385-386` — the `else (None, None)` guard falls into the **success** print, so `{ch:<9}`
      formats `None` and the `TypeError` surfaces as a channel FAILED. Unresolved slug becomes a named
      precondition failure that skips the dependent channel
- [x] 3.7 Fix `:399` — quote the stderr line naming the **cause**, not `splitlines()[-1]`, and attribute
      it. Today it prints the orphan fragment `and the repository exists.`

## 4. Runbook / instrument reconciliation

- [x] 4.1 `vault-template/96-Runbooks/session-bootstrap-loader.md` step 3 — reconcile the four claimed
      layers with what the instrument reports once 3.5 lands
- [x] 4.2 Add the inversion to Pitfalls: **a remoteless vault is INV-14 holding, not a broken channel**;
      a red remote row in the vault is the instrument mis-scoped, not an environment fault
- [x] 4.3 Bump `last-validated`; keep the runbook **referencing** the meta-script — no inlined
      `gh`/`curl`, no harness-specific path as SSOT (the constraint the predecessor change nearly broke)

## 5. Tests — must exercise the states the mechanism itself creates

- [x] 5.1 Probe run from a remoteless vault → INV-14 holding, zero FAILED rows. **Observe this test
      failing against today's code first** — it currently produces 3 FAILED rows
- [x] 5.2 `FRAMEWORK_ROOT` unset → all framework layers `UNDECLARED`, exit `0`
- [x] 5.3 Vault with a pushable remote → reported as a violation. This is the adversarial case; write
      it **before** the confirming one
- [x] 5.4 Unresolved slug → named precondition failure, no `NoneType.__format__` text anywhere in output
- [x] 5.5 Exit code remains `0` on every failing channel — the predecessor's scenario must not regress
- [x] 5.6 **Protection self-test, all three rows.** Row 1 (refused) passes today, so a test covering
      only it is the vacuous pass the Definition of Done names. Rows 2 and 3 must be built: a writable
      governed subtree, and a write that succeeds while removal fails. Assert the *guidance text* is
      present, not just the verdict — the guidance is the requirement. **Row 3's geometry is no longer
      hypothetical** — the 2026-08-13 hand-roll is a working instance of the silent-residue path
      (proposal, reproduction log); model the test on it.
      **Done, with one disclosure that must not be glossed:** rows 1 and 2 are fully real — a real
      vault tree, real mode bits (`chmod 0o500`), a real accepted write. **Row 3 injects the errno**
      at the `os.unlink` seam, because the only unprivileged filesystem that produces
      write-succeeds/removal-fails naturally is a sticky directory owned by a *second user*, which a
      test cannot create. The `finally`, the checked result, the verdict escalation, the residue path
      and the guidance text are all real code paths; only the `OSError` is injected — and the test
      asserts the artifact is genuinely still on disk and that the reported path is that artifact.
      Row 1 is skipped when `geteuid()==0`, since root bypasses mode bits and would pass vacuously
- [x] 5.7 Assert the residue path reaches the report even when the probe is exiting
- [x] 5.8 End-to-end on the real estate at least once: run from the live vault, cold, and paste the
      output into the change. A stubbed estate passes vacuously while reading as coverage.
      **Done — and it earned its keep on the first run: it caught a defect all 6 unit tests missed.**
      Output pasted in the proposal (*End-to-end run E1*); the defect and its fix are recorded there

## 6. Regression

- [x] 6.1 `openspec validate --all --strict` (CLI `1.6.0` == `package.json` pin — verified 2026-08-11)
- [x] 6.2 `runbook-lint` (CI job reproduced locally)
- [x] 6.3 `validate-scripts.sh` — `.py` touched, so this must run. ⚠ known `/tmp` defect in the
      hardening queue may block it in a write-scoped sandbox; if so, say so and defer to CI rather
      than ticking it. **Ran clean 2026-08-13: `VALIDATION OK`**, the `/tmp` defect did not bite this
      time. Note the real path is `.github/scripts/validate-scripts.sh`, not `scripts/` as CI's job
      name suggests — shellcheck was skipped (not installed locally), so that half defers to CI
- [x] 6.4 `pytest` — existing `pr-flow` coverage, confirming `route` / `ready` / `assert-preconditions`
      still derive from cwd (3.1 must not leak into them). **183 passed** 2026-08-13 (176 + 7 new);
      no existing test modified. ⚠ Re-run when 3.1 lands — this run only proves 3.5 did not leak,
      since 3.5 is not yet built on top of estate scoping

## 7. ✅ DISCHARGED ELSEWHERE — not work in this change (verified 2026-08-16)

The owed follow-on named below **has shipped**: ADR-0040 exists, and `maintenance` carries the
requirement *A Change Is Archived On Its Own Branch*. Nothing is owed here. Retained for provenance.

## 7-OLD. Document the archive rule (operator decision 2026-08-11)

🚫 **NOT IN THIS CHANGE — moved out on governance grounds, 2026-08-11.**

An earlier draft put a `CONTRIBUTING.md` edit here. That is wrong twice over:

- **Mechanically:** `scope-review` is Phase-B blocking and diffs the PR against the scope declared in
  its body. This change's proposal declares a capability-probe reshape; a `CONTRIBUTING.md` edit and a
  CI guard are outside it, and the gate would fail the PR. (Not in `required_status_checks` yet, so
  the binding is `pr-flow.py` step 8 refusing to emit a merge on a failing check.)
- **Substantively:** grep of all six specs for "archive" returns **zero** — no requirement states the
  convention. A guard enforcing an unstated rule is the inverse of the `constitution.md` §4 class-9
  defect (documented enforcement that does not exist). The requirement and its guard must ship
  together, in a change that proposes both.

**Owed as a separate ordinary OpenSpec change** (`CONTRIBUTING.md:6-8` — every change originates as a
proposal; ADR-0038's "no spec delta → docs PR" carve-out does not apply, because this one has a delta):
ADDED `maintenance` requirement + CI guard + `CONTRIBUTING.md` in lockstep + ADR-0040 naming the two
2026-08 deviations, and `enforce-inv7-secret-scan`'s unticked line, as **not precedent**. Ordinary, not
Informed-Upheaval: ADD-only, overrides nothing, and §2 puts conventions at Tier 2 ("no ceremony
required"). Closes the *"archive-order rule undocumented"* hardening-queue item.

## 8. Deploy-down (operator)

- [x] 8.1 **DONE — operator, 2026-08-16.** `FRAMEWORK_ROOT` added to the live gitignored
      `99-Operations/config.env`; verified to resolve to a directory.
- [ ] 8.2 Operator applies the three changed files into the live vault — **after this change merges**,
      so the vault never carries unmerged content. All three measured as differing 2026-08-16:
      `96-Runbooks/session-bootstrap-loader.md` (40 lines),
      `.claude/commands/vmm-session-rebooted.md` (13),
      `99-Operations/config.defaults.env` (19).
      Two sit in subtrees the agent is denied by INV-4/5 — confirmed `PROTECTED` by the probe's own
      write-scope layer in the same run. ⚠ `96-Runbooks/` is **not a lockstep prefix** (queue item
      11), so `template-mirror` will not carry it and no instrument detects the drift in between.
      (`denyWrite` paths — never edited in-vault)
- [x] 8.3 **VERIFIED ON THE REAL ESTATE, 2026-08-16** — run exactly as a cold session does, from the
      vault, sourcing only `config.env`:
      `source 99-Operations/config.env && python3 "$FRAMEWORK_ROOT/tools/pr-flow.py" --capabilities`
      → estate printed, `INV-14 HOLDING`, framework channels measured against the correct subject,
      all three protected subtrees `PROTECTED`, exit `0`.
      **Same session, four hours earlier, same directory, before the fix:** `slug UNRESOLVED`,
      `github state FAILED (unsupported format string passed to NoneType.__format__)`,
      `ls-remote FAILED`, `push FAILED` — the third recorded occurrence of the inversion.
      ⚠ Scope of this verification: it exercises the **probe** against the real estate. The full cold
      prime reading the **deployed runbook** is only possible after 8.2.

## 9. Evidence

- **Rebased onto current `main` first.** The branch was 66 commits behind and `tools/pr-flow.py` had
  moved 710 insertions / 35 deletions underneath it. Clean, and the already-built write-scope layer
  survived — verified by running it, not by the rebase exiting 0.
- **All four estate states exercised on the real estate**: declared (correct), `FRAMEWORK_ROOT` empty
  (UNDECLARED + suggestion, exit 0), **run from the vault (byte-identical to run from the repo — the
  thesis)**, and the violation path.
- **255 passed**; `openspec validate --all --strict` 7/7 (CLI `1.6.0` == the `package.json` pin);
  pre-flight `CLEAR`, 12/15, 0 unaccounted.

### Two spec/code mismatches found by reading the delta against the implementation

1. **The spec asked for something unsafe.** *"A remote that accepts a push"* can only be established
   by attempting a push **from the vault** — the act INV-14 forbids, and which the outbound guard
   refuses. A probe may not commit the breach it checks for. Trigger changed to **presence**, which is
   also the earlier signal: a remote lacking credentials today is one credential away from pushable.
2. **The code missed a clause.** The second requirement says a quoted subprocess line SHALL be
   *attributed*; it was printed bare. Now `git push says: …`, with a test pinning both the attribution
   and the cause-selection over positional selection.

### Caught by the tooling, not by me

- **`standalone-vault lint` failed the pre-flight**: the `config.env.example` comment leaked this
  operator's actual framework path into the vault template, which a standalone vault must not
  reference. Genericised. **Caught before the push** — the first time the pre-flight has paid for
  itself on work it did not itself introduce.
- The **INV-14 outbound guard refused** the command that would have created a real remote for the
  violation test. Not routed around: the test stubs the `git remote` seam, which never performs the
  forbidden act.
- The first HOLDING test used the `work` fixture, which is **cloned from a bare origin and therefore
  has a remote** — it asserted the opposite of a vault's real geometry. Caught on first run.

### Design call not in the proposal

Task 3.1 says *remove cwd derivation*, and it is removed — but the `UNDECLARED` report **suggests**
the export and labels the candidate `NOT used`. A silent cwd fallback would reintroduce the original
bug exactly: run from the vault, measure the vault. **Suggesting is not substituting**, and a test
pins the difference.

## 10. Gate 4 — human sign-off (not agent-delegatable)

- [x] 10.1 **Approved** — Keith Nielsen, 2026-08-16. Reviewed the proposal and this task file,
      including the two departures from the proposal as originally written, both argued in §9:
      the **presence-not-pushability** trigger (a probe may not commit the breach it checks for), and
      **suggest-don't-substitute** for an undeclared `FRAMEWORK_ROOT` (a silent cwd fallback would
      reintroduce the original defect exactly). Gate 3 complete: 255 passed, `openspec validate
      --all --strict` 7/7, pre-flight `CLEAR`, and 8.1/8.3 verified on the real estate.
