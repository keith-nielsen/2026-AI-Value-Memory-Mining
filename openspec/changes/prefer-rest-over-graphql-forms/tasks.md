# Tasks — prefer-rest-over-graphql-forms

> **This file is the durable plan.** It is written to survive a session restart: anyone picking this
> up should be able to finish the change from here plus the artifacts it names, with no recollection
> of the conversation that produced it.

## 0. END STATE — what the estate looks like when this lands

1. **Every `gh` invocation in the tree is `gh api <REST path>` or `gh auth status`.** No subcommand
   form survives in executed code, emitted commands, or CI workflows.
2. **`gh api` is no longer a blanket permit.** `GET` is unconstrained; `-X POST|PATCH|PUT|DELETE`
   reaches only an enumerated endpoint set. This is the answer to the fact that `gh api` is a *wider*
   permission than the seven subcommands it replaces —
   `gh api -X DELETE /repos/{owner}/{repo}` is otherwise permitted by form.
3. **One source of truth for that set**, carried inside the guard note (which must work in roots that
   have no `docs/`) and pinned to `docs/version-control-legal-moves.md` by an equality test. Drift
   fails CI.
4. **Two instruments, distinct jobs, neither substituting for the other:**
   - the **guard** governs what *executes* on the agent's channel, at runtime;
   - the **detector** governs what the repo *ships* — emitted commands and documented instructions a
     human will copy. ⚠ It is also the only one that reaches the **Actions runner**, where no hook
     runs and the `gh` binary is not ours.
5. **Every emitted mutation carries a server-side precondition** where the API offers one. A
   precondition enforced at GitHub is the only control that survives being pasted into a shell we do
   not control.
6. **The change reaches all three roots by the estate's normal path** — the guard is a literate note
   under `vault-template/`, so render + mirror deploy it, and `template-parity` proves it.
   ⚠ **The vault has no CI**: vault-side conformance rests on the deployed hook and parity, never on
   the detector.

### Explicitly NOT in the end state — decided, do not re-litigate

- ❌ **A thirty-three-entry `permissions.deny` expansion.** A blocklist cannot cover a `gh`
  subcommand family that does not exist yet, and it would be enforcement machinery for a boundary the
  credential layer already holds.
- ❌ **A `gh` PATH shim.** Surveyed prior art is unanimous that it is *"a soft barrier … not a hard
  boundary"* (`navikt/cplt`, filed against their own code), bypassable by absolute path, PATH edit,
  or raw API call (`VibeCoder` #1371, High severity, against their own code).
- ❌ **Hardening the guard's lexer against command substitution.** Real, measured, recorded in the
  vault Site — but a **different control** with its own spec delta and Gate 4. The detector already
  designs the blind spot out on the shipping side.

**The reasoning for all three is in `30-Sites/harness-permission-control-deep-dive/` in the vault**,
particularly `shim-approach-prior-art-survey`. Read it before reopening any of them.

## 1. The detector — DONE, observed red

**BUILT AND OBSERVED RED — `tests/test_gh_form_conformance.py`, 2026-09-18.** 4 checks, 1 failing by
design, 32 files scanned, 0 parse failures. It named **exactly the seven predicted sites**:

```
tools/pr-flow.py:1919                       gh pr create      (emitted)
tools/pr-state.py:112                       gh pr view        (executed)
tools/pr-state.py:181                       gh run list       (executed)
tools/ship-release.py:343                   gh release create (emitted)
.github/workflows/openspec-canary.yml:49    gh label create   (CI)
.github/workflows/openspec-canary.yml:51    gh issue list     (CI)
.github/workflows/openspec-canary.yml:55    gh issue create   (CI)
```

- [x] 1.1 Enumerate by mechanism — AST for Python, `run:` blocks for workflows, code fences for the
      literate notes — with the denominator printed so a silent miss is visible.
- [x] 1.2 Submit each form to the shipped guard, **imported by execution, never restated**.
- [x] 1.3 Observe it FAIL and record what it names (above).
- [x] 1.4 Prove coverage needs no registration: a fixture emission is caught without being listed.
- [x] 1.5 Unwrap command substitution — canary `:51` is `open=$(gh issue list …)` and appears **only**
      because of this; the guard itself cannot see that shape.
- [x] 1.6 Treat unlexable input as a finding, never a skip — the guard fails open on it.

⚠ **Three sources of the detector's own noise were removed**, each a lesson worth keeping: sink calls
examine only the **first positional argument** (`emit(route, "pr", cmd, why=…)` carries prose in
keyword arguments that names refused forms on purpose); the notes' python fences are **parsed as
code** (scanning them as lines reported the guard note's own refusal messages); and workflow line
continuations are **joined before lexing**.

⚠ **The 2026-09-08 ledger sweep captured canary lines 49 and 51 but NOT 55.** A live `gh issue
create` has no `GH-` id. Read that generator before trusting any enumeration's completeness,
including this one's.

## 2. Single source of truth for the write-side endpoint set

- [ ] 2.1 Add a machine-readable fenced block to `docs/version-control-legal-moves.md` §2, listing
      each sanctioned write: method · endpoint template · runs · authority · precondition. Use a
      fenced typed block, consistent with the estate's existing ```scope and ```constitutional-impact
      convention — one file that both a human and a tool read.
- [ ] 2.2 Carry the same set inside `vault-template/99-Operations/scripts/gh-invocation-guard-script.md`.
      ⚠ **The guard must stay self-contained and stdlib-only** (INV-6, and it renders into roots with
      no `docs/`), so it cannot read the doc at runtime.
- [ ] 2.3 **Equality test**, observed failing first on a deliberately divergent table: the doc's block
      and the guard's list are the same set. **This test is what makes 2.2 an import rather than a
      restatement** — restating a rule with no equality test is the class-9 defect.
- [ ] 2.4 The initial set, to be confirmed against the doc rather than from this list:
      `POST /repos/{slug}/pulls` · `PATCH /repos/{slug}/pulls/{n}` ·
      `PUT /repos/{slug}/pulls/{n}/merge` (precondition `sha`) · `POST /repos/{slug}/releases`
      (precondition: tag read) · `POST /repos/{slug}/labels` · `POST /repos/{slug}/issues` ·
      `DELETE /repos/{slug}/releases/{id}` (the UAT revert path).

## 3. The method split in the guard

- [ ] 3.1 Extend `verdict()` so `gh api` is evaluated by method: no `-X`, or `-X GET`, is permitted
      unchanged; a write method is permitted only against an endpoint in the set from §2.
- [ ] 3.2 Red first — a test that `gh api -X DELETE repos/o/r` is refused **before** the change, and
      the existing permitted forms still pass after it.
- [ ] 3.3 Keep the refusal teaching: the message names the sanctioned endpoint set, the way the
      current message carries the REST mapping. *"Refusals teach"* (ADR-0045 §Consequence).
- [ ] 3.4 Extend `tests/test_gh_form_conformance.py` to fail on a shipped write to an unsanctioned
      endpoint. ⚠ This matters **more** than 3.1: it covers emitted commands and the Actions runner,
      where no hook runs.

## 4. Convert the seven, each with its measured trap

- [ ] 4.1 `pr-state.py:112` — `gh pr view --json` → `gh api repos/{slug}/pulls/{n}`.
- [ ] 4.2 `pr-state.py:181` — `gh run list --commit` → `gh api`.
      ⚠ **Measure first what the caller consumes.** `gh run list` issues TWO requests
      (`/actions/runs` **and** `/actions/workflows?per_page=100`); a single `/actions/runs?head_sha=`
      call drops workflow names. *Done when:* the fields used downstream are enumerated and shown
      present in the replacement's response.
- [ ] 4.3 `pr-flow.py:1919` — emitted `gh pr create` → `gh api -X POST repos/{slug}/pulls`
      with `-f title=` `-f head=` `-f base=` `-F body=@<file>`.
- [ ] 4.4 `ship-release.py:343` — emitted `gh release create` → `gh api -X POST repos/{slug}/releases`.
      ⚠ `--verify-tag` has no REST equivalent; its replacement is an explicit
      `GET repos/{slug}/git/ref/tags/{tag}` **before** the POST — the pattern
      `uat-release-roundtrip.sh` already proved at its step 1.
- [ ] 4.5 canary `:49` `gh label create` → `GET …/labels/openspec-canary`, and on 404 `POST …/labels`.
      ⚠ Removes a `2>/dev/null || true` that makes an auth failure indistinguishable from "already
      exists" — the estate's catalogued `|| true` vacuity defect, in CI.
- [ ] 4.6 canary `:51` `gh issue list` → `GET …/issues?labels=…&state=open&per_page=100`
      ⚠ **with `--jq '[.[] | select(.pull_request == null)] | length'`.** `/issues` returns pull
      requests; without the filter the dedupe silently stops opening issues it should open.
- [ ] 4.7 canary `:55` `gh issue create` → `POST …/issues` with `-f 'labels[]=openspec-canary'`
      (`-f labels=` sends a string and is rejected).

## 5. Consequences, recorded rather than discovered later

- [ ] 5.1 `tests/test_emitted_command_shape.py` — its `-R <slug>` assertion dies with 4.3/4.4 since
      `gh api` carries the slug inline. Change the premise **in the same commit**, and widen its
      scope: it reads only `ship-release.py`'s `_emit_next(…)` today and never sees `pr-flow.py`'s
      `emit(…)` sites, which is the second reason `gh pr create` stood unnoticed.
- [ ] 5.2 `pr-state.py` — populate `mergeStateStatus` from REST `mergeable_state` (same enum,
      lowercased) instead of `UNAVAILABLE (GraphQL-only)`. ⚠ `mergeable_state` is thinly documented:
      **pin the observed values in a test**. `mergeable` is computed asynchronously, so `null` on a
      cold read is a real state — `--ready mergeable` already polls it.
- [ ] 5.3 Document surfaces, same change: `docs/version-control-legal-moves.md` (rows *Open a PR*,
      *Create a Release*, plus the §2 block), `AGENTS.md`, `CONTRIBUTING.md`,
      `docs/USING-THIS-TEMPLATE.md`, and the vault's `vmm-repo-github-card.md` with `CARD-VERSION`
      bumped — nothing detects that card drifting.
- [ ] 5.4 Update the vault ledger `gh-form-findings-ledger.md`: FIX rows absent, KEEP rows present
      and still denied.
- [ ] 5.5 Import into ADR-0045's rationale the strongest argument found in the survey, which the ADR
      does not currently make: **hooks run outside the model as separate processes, so prompt
      injection cannot talk its way past them.**

## 6. Regression

- [ ] 6.1 Full suite. Baseline **424 passed** on this branch, rebased onto `a22c2ea`, 2026-09-18.
- [ ] 6.2 `openspec validate --all --strict` — 7 items, 0 failed at last run.
- [ ] 6.3 `node_modules/.bin/markdownlint` with the four `--ignore` paths `ci.yml` uses → 0 findings.
- [ ] 6.4 `tools/preflight.py . --body-file <path>` → CLEAR. ⚠ `--body-file` is **not optional**:
      without it the body step prints `SKIP`, and a SKIP reads exactly like a PASS.
- [ ] 6.5 A mutation matrix behind the detector and the method split — an instrument that cannot be
      shown to fail is not evidence, and this change's premise is that unexercised instruments rot.

## 7. Gate 4 — operator authorization (Tier-0 touch)

Archiving syncs this delta into `openspec/specs/access-control/spec.md`, `protects: [CONST-02, INV-4,
INV-5, INV-6, INV-7, INV-8, INV-14]`. The `AGENTS.md` hard stop requires the principle, its rationale
and its "what breaks" consequence surfaced, and explicit human confirmation received.

To be surfaced — **drafted by the agent; the sign-off is human-only and is NOT recorded until given:**

- **A new refusal exists.** Both guard and detector can refuse a write to an unsanctioned endpoint.
  Wrong in the strict direction, it blocks work that was fine.
- **The operator's pasted command changes shape** to `gh api -X POST repos/{slug}/pulls …`.
- **`--verify-tag` becomes an explicit precondition read.** If 4.4 gets it wrong, the rail that stops
  a typo'd version silently tagging a branch head is what weakens.
- **The "no new ADR is owed" reading lowers this very gate**, and should be checked against ADR-0045
  §Decision before it is relied upon.
- **What breaks if this is wrong:** these are the controls other work is judged by. A defect here
  does not fail loudly — it produces a confident, well-formed, wrong answer.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [ ] 7.1 Tier-0 touch surfaced with its consequence; **Approved** — <operator>, <ISO date>

## 8. Land it — the PR command sequence, step by step

⚠ **Walk `tools/pr-flow.py`; do not hand-compose the sequence** (`CONTRIBUTING.md` §*Landing a
change*). Every command below is either emitted by the driver or verifies it. Run the driver **from
`$FRAMEWORK_ROOT`**.

- [ ] 8.1 **Archive on this feature branch, in the same PR** (ADR-0040) — the change directory moves
      to `openspec/changes/archive/<YYYY-MM-DD>-prefer-rest-over-graphql-forms/`.
- [ ] 8.2 **Write the PR body** to `$FRAMEWORK_ROOT/.git/pr-flow/prefer-rest-body.md`, carrying a
      fenced ` ```scope ` block that **covers every path in the diff** — presence is not coverage,
      and PR #114 was refused at step 7 with all 36 checks green for exactly this.
- [ ] 8.3 **Preflight, before the first push:**
      `python3 tools/preflight.py . --body-file .git/pr-flow/prefer-rest-body.md` → expect `CLEAR`.
- [ ] 8.4 **Route:** `python3 tools/pr-flow.py --plan --branch fix/prefer-rest-over-graphql-forms
      --base main` → read the CURRENT step, its `runs:` and `authority:`.
- [ ] 8.5 **Walk each emitted step, one at a time**, re-invoking the driver after each mutation to
      verify it landed before advancing. Agent-owned steps are run directly; the push is
      `runs: AGENT · authority: OPERATOR` under the INV-14 ask.
- [ ] 8.6 **Operator steps arrive as one invariant command** —
      `bash "$FRAMEWORK_ROOT/.git/pr-flow/next.sh"`, tagged. ⚠ **Once an operator step is emitted,
      stop touching the driver** until it is reported done: `next.sh` is a single mutable slot and
      re-running the driver overwrites a step they have not yet run.
      ⚠ **Never hand-compose a `gh` mutation**, and relay the driver's tagged line rather than the
      inner command.
- [ ] 8.7 **Merge** goes through `gh api -X PUT …/merge` carrying `sha=`, never `gh pr merge`.
- [ ] 8.8 **Cleanup** — `remote-gone` then `local-gone`, each verified by re-invoking the driver, then
      `LIFECYCLE COMPLETE`.
- [ ] 8.9 **Deploy-down is operator-run** and is NOT optional for this change: the guard lives in a
      literate note, so until `template-mirror.py` and `vault-render.py render` run, **the live fleet
      still carries the old guard**. Then verify: `template-parity.py $VAULT_ROOT` → 0 drift, and
      `vault-render.py reconcile` → 15/15 ok.
      ⚠ Run render with the working directory **at the vault root** — see the render-root defect.
