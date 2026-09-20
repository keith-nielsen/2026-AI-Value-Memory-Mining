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
4. **Three instruments, distinct jobs, none substituting for another:**
   - the **invocation guard** governs what *executes* on the agent's channel, at runtime;
   - the **detector** governs what the repo *ships* — emitted commands and documented instructions a
     human will copy. ⚠ It is also the only one that reaches the **Actions runner**, where no hook
     runs and the `gh` binary is not ours.
   - the **outbound guard** (INV-14) governs what *leaves the machine*, and is a **different axis
     from both**: it does not care whether a form is permitted, only whether it publishes.
5. **Every emitted mutation carries a server-side precondition** where the API offers one. A
   precondition enforced at GitHub is the only control that survives being pasted into a shell we do
   not control.
6. **The change reaches all three roots by the estate's normal path** — the guard is a literate note
   under `vault-template/`, so render + mirror deploy it, and `template-parity` proves it.
   ⚠ **The vault has no CI**: vault-side conformance rests on the deployed hook and parity, never on
   the detector.
7. **No conversion in §4 silently lowers an INV-14 ask.** Every form that raises the outbound banner
   today raises it in its REST shape too. **MEASURED 2026-09-19, and this is why the item exists:**
   `gh release create v1.2.3 --verify-tag --notes-file n.md` → `ask` (the full banner);
   `gh api -X POST repos/o/r/releases -f tag_name=v1.2.3` → **silence, exit 0**. `OUTWARD` and
   `PUBLISH` key on the literal token `gh release (create|edit|upload)`
   (`outbound-publish-guard.py:32,39`), so §4.4 *as first written* deleted the ask on the one path
   that publishes artifacts to the world. The vault battery predicted this as **B8/B9** before it was
   measured; the plan had lost it. Folded into this change by operator decision, 2026-09-19.

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

## 1. The detector — DONE, observed red, NOW GREEN

**GREEN 2026-09-20, when §4 landed and not before.** `tests/test_gh_form_conformance.py` 10 passed;
full suite **486 passed, 0 failed**. The detector was never edited to pass: the conversions moved
under it. Two refinements were made while converting, each measured and each in the conservative
direction — f-string FRAGMENTS are not commands (three conforming emissions were being reported as
violations), and a WHOLE-LINE shell comment is prose (the comment explaining what replaced
`gh label create` was reported as shipping it). Both are pinned by tests asserting the opposite
direction too, so neither became a way to hide a real command.


**BUILT AND OBSERVED RED — `tests/test_gh_form_conformance.py`, 2026-09-18.** 4 checks, 1 failing by
design, 32 files scanned, 0 parse failures. It named **exactly the seven predicted sites**:

```text
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

**BUILT AND TESTED 2026-09-19 — red observed first.** With the block written and neither guard
carrying a constant, `tests/test_write_endpoint_set_parity.py` failed on exactly the two equality
checks (*"carries no `SANCTIONED_WRITES` constant"*, *"carries no `OUTBOUND_ENDPOINTS` constant"*)
while its three structural checks passed; after 2.2 it went **5 passed**. Full suite **432 passed, 1
failed** — the failure being the §1 detector, still red by design. ⚠ Rendering the notes was **not**
optional: `test_each_repo_hook_is_byte_identical_to_its_note` (F29) compares each repo hook to its
note, so the deploy targets moved in the same commit, the way `6fe549d` did it.

- [x] 2.1 Add a machine-readable fenced block to `docs/version-control-legal-moves.md` §2, listing
      each sanctioned write: method · endpoint template · runs · authority · precondition. Use a
      fenced typed block, consistent with the estate's existing `scope` and `constitutional-impact`
      convention — one file that both a human and a tool read. Fields: **method · endpoint template ·
      runs · authority · precondition · outbound** (2.5).
- [x] 2.2 Carry the same set inside `vault-template/99-Operations/scripts/gh-invocation-guard-script.md`,
      and the **outbound subset** (the rows marked outbound in 2.5) inside
      `vault-template/99-Operations/scripts/outbound-publish-guard-script.md`.
      ⚠ **Both guards must stay self-contained and stdlib-only** (INV-6, and they render into roots
      with no `docs/`), so neither can read the doc at runtime.
      ⚠ **The notes are the source of truth, not the hooks.** Verified 2026-09-19: each note's
      ` ```python ` block is **byte-identical** to its rendered `.claude/hooks/*.py` copy. Edit the
      note; render and mirror deploy it (§8.9).
- [x] 2.3 **Equality test**, observed failing first on a deliberately divergent table: the doc's block
      and **each** guard's list are the same set — the full set for the invocation guard, the outbound
      subset for the outbound guard. **This test is what makes 2.2 an import rather than a
      restatement** — restating a rule with no equality test is the class-9 defect.
- [x] 2.4 The initial set, to be confirmed against the doc rather than from this list:
      `POST /repos/{slug}/pulls` · `PATCH /repos/{slug}/pulls/{n}` ·
      `PUT /repos/{slug}/pulls/{n}/merge` (precondition `sha`) · `POST /repos/{slug}/releases`
      (precondition: tag read) · `POST /repos/{slug}/labels` · `POST /repos/{slug}/issues` ·
      `DELETE /repos/{slug}/releases/{id}` (the UAT revert path).
      ⚠ **`PUT /repos/{slug}/rulesets/{id}` — DECIDED 2026-09-19: EXCLUDED, not admitted.**
      Operator decision, taken on a written comparison rather than a default. `PUT`, `PATCH` and
      `DELETE` on that endpoint are now listed in a ` ```gh-write-endpoints-excluded ` block in
      `docs/version-control-legal-moves.md` §2b carrying six numbered grounds, and
      `openspec/adr/0038-…` is amended to rest on **authority rather than capability**.
      The short form: the endpoint edits the **control plane**, not content; a `PUT` replaces the
      entire `rules` array, so a hand-written payload silently drops `pull_request` / `deletion` /
      `non_fast_forward`; `bypass_actors` is empty so nobody can *evade* the ruleset, but an admin
      token can *rewrite* it, which makes its integrity procedural; admitting it would let the
      agent-channel allowlist authorize edits to the only server-side layer (ADR-0034), which
      backstops every other layer; and excluding it costs nothing that exists — the guard binds the
      agent's typed channel, the operator's terminal runs no hook, ADR-0038 carries a verified
      recipe, and there have been **two** ruleset writes in the estate's entire record.
      ⚠ The old ground *"the agent cannot authenticate"* was measured FALSE on 2026-08-26 (`0b07ddc`).
      A boundary resting on assumed incapacity is not a boundary.
      ⚠ **This does not close the gap it sits next to.** Nothing observes the live rulesets, and
      GitHub can change ruleset parameters **without bumping `updated_at`** (ADR-0038, Residual), so a
      web-UI edit or an out-of-estate token is still undetected. That is **`github-state-reconcile`'s**
      to build, and it is the one plausible reason these rows would ever be admitted — as its own
      change, with its own Gate 4.
      ⚠ The detector cannot help here either: its scan scope is `tools/`, `.claude/hooks/`,
      `.github/scripts/`, `.github/workflows/` and the `vault-template/…/scripts/` python fences —
      **never `docs/` or ADR prose**. The exclusion is held by
      `tests/test_write_endpoint_set_parity.py` instead, which fails if a ruleset row is admitted to
      the sanctioned set or leaks into either guard. **Observed failing 2026-09-19** on a deliberate
      widening: 3 failed, 4 passed, naming the ruleset row.
- [x] 2.5 **Each row carries whether the endpoint is OUTWARD** — i.e. whether reaching it must raise
      the INV-14 ask. This is the field §0.7 exists to protect, and it is what makes the block
      readable by **two** guards rather than one.

## 3. The method split in the guard

**BUILT AND TESTED 2026-09-19 — red observed first, 10 failures.** Tests written before the split:
5 unsanctioned-write cases, 4 graphql-behind-a-method-flag cases, 3 excluded-endpoint cases, plus 14
permitted forms asserted to survive. Then green, 43 passed. Full suite **466 passed, 1 failed** — the
§1 detector, still red on exactly the seven sites.

⚠ **A HOLE WAS MEASURED IN THE SHIPPED GUARD while writing 3.2, and is now closed.** `positional`
was built as *"every token not starting with `-`"*, so a flag's VALUE occupied a positional slot:
`gh api graphql` was refused, **`gh api -X POST graphql` DEFERRED**. A GraphQL mutation is always a
POST, so the one shape capable of the silent no-op the rule exists to stop was the shape that got
through — and Layer 1's `Bash(gh api graphql:*)` prefix rule does not cover it either. Closed by
`non_flag_tokens()`, which drops a flag's value with the flag. ⚠ Only the **space-separated** forms
were holes; `-XPOST` and `--method=POST` were already refused. Measured, not assumed.

⚠ **The detector needed a fix in the same change, and it is not cosmetic.** Walking a sink argument
yielded the flattened f-string **and** each constant piece of it, so the driver's own conforming
emissions were submitted twice — once whole, once as the fragment `" && gh api -X PATCH /repos/"`,
whose endpoint reads as `/repos/`. Invisible while `gh api` was a blanket permit; the moment writes
were judged by endpoint it reported **three conforming emissions as violations** (pr-flow.py:1953,
1972, 2088). `_fstring_fragments()` skips the pieces; the whole is still submitted, and two new
tests assert both directions rather than asserting it in a comment.

⚠ **`{slug}` matches one OR two segments by design.** The detector flattens an f-string's
interpolations to a single token, so a guard demanding `owner/repo` would refuse the estate's own
emissions. It loosens nothing — the collection path after the slug must still match exactly.

- [x] 3.1 Extend `verdict()` so `gh api` is evaluated by method: no `-X`, or `-X GET`, is permitted
      unchanged; a write method is permitted only against an endpoint in the set from §2.
- [x] 3.2 Red first — a test that `gh api -X DELETE repos/o/r` is refused **before** the change, and
      the existing permitted forms still pass after it.
- [x] 3.3 Keep the refusal teaching: the message names the sanctioned endpoint set, the way the
      current message carries the REST mapping. *"Refusals teach"* (ADR-0045 §Consequence).
      ⚠ For an endpoint in the **excluded** block (2.4), the message must say it is excluded **by
      decision** and point at §2b — a bare "not permitted" invites the next reader to add the row.
- [x] 3.4 Extend `tests/test_gh_form_conformance.py` to fail on a shipped write to an unsanctioned
      endpoint. ⚠ This matters **more** than 3.1: it covers emitted commands and the Actions runner,
      where no hook runs.

### 3a. The outbound guard learns the REST forms (B8/B9 — folded in 2026-09-19)

**BUILT AND TESTED 2026-09-19 — `tests/test_outbound_rest_coverage.py`, 17 passed.** Red first: 7
failures before 3a.1 (five B9 spellings, the upload host, and the mutation). Full suite **480
passed, 1 failed** — the §1 detector, unchanged.

⚠ **The rail's REST half is DERIVED from `OUTBOUND_ENDPOINTS`, not hand-written.** A second copy
here would drift from docs §2b exactly when it mattered; deriving it means adding an
`outbound: yes` row to the doc extends this rail automatically, and the parity test already holds
the constant equal to the doc.

⚠ **A CRASH was found and fixed in the same work, and it is worth keeping.** The first cut used
`re.sub(..., r"[^/\s]+", ...)`, where `\s` in a **replacement** is a template escape: the guard
raised `bad escape \s` and exited **1 at import**. That is NOT the documented fail-open behaviour —
fail-open covers a malformed payload at runtime, not a module that will not load. The test harness
caught it only because it asserts the hook's exit code rather than just its decision; a suite
checking decisions alone would have read the crash as fourteen ordinary failures.

- [x] 3a.1 Extend `OUTWARD` / `PUBLISH` in
      `vault-template/99-Operations/scripts/outbound-publish-guard-script.md` so a REST write to an
      outbound-marked endpoint (2.5) raises the same ask the subcommand form raises today.
      Minimum coverage: `POST /repos/{slug}/releases`, `PATCH|DELETE /repos/{slug}/releases/{id}`,
      and the release **asset upload** host, which is `uploads.github.com`, not the API host.
- [x] 3a.2 **B9 red→green** — a test that `gh api -X POST repos/o/r/releases -f tag_name=v1.2.3` is
      **NOT** asked before the change and **is** asked after. ⚠ *"A B9 that is green on both sides
      proves nothing"* — observe the red first, per the battery.
- [x] 3a.3 **B8 — by MUTATION, not by before/after.** Operator decision 2026-09-19, replacing the
      weaker "green→green" wording this item shipped with. A test that only ever sees the
      post-change world cannot show the original clause survived the rewrite, and widening a regex
      is exactly how an alternation gets lost — so *"it was green, it is still green"* asserts
      history, not discrimination.
      **Method** (the extract-and-run pattern `test_gh_form_conformance.py` already uses):
      1. extract the implementation block from `outbound-publish-guard-script.md`;
      2. remove **only** the `\bgh\s+release\s+(create|edit|upload)\b` alternation, and **assert the
         replacement count is exactly 1** — a clause that was renamed or reflowed means the mutant is
         unmutated, and the test silently reverts to theatre;
      3. write the mutant to `tmp_path` and run both payloads through it as a subprocess;
      4. assert the mutant **no longer asks** on `gh release create …` — this is the demonstration
         that the B8 assertion can fail, and therefore that its green carries information;
      5. assert the mutant **still asks** on the REST form — proving the two clauses are
         **independently** covered and neither leans on the other.
      ⚠ **Nothing is deleted from the shipped guard at any point.** The mutation lives in the test,
      on a throwaway copy in `tmp_path`; the note, the rendered hooks and the live rail are untouched.
      ⚠ Land it **in the same commit as 3a.1** — a mutation test written after the widening has the
      same provenance problem as any other after-the-fact test.
- [x] 3a.4 **Check what the HARD DENY does to the REST form — it TIGHTENS, and that needs a decision.**
      Read 2026-09-19, `_targets_vault()` in order: the literal `VAULT` path in the command → true;
      an explicit **`-R owner/repo` → false** ("names a GitHub repo, not the local vault working
      tree"); then `git -C` / a leading `cd`; otherwise **fall back to the reported `cwd`**.
      `gh api` carries the slug **inline in the path** and has no `-R`, so it never reaches that
      early-out and lands on the cwd fallback. Consequence once 3a.1 makes `OUTWARD` match it: a REST
      release write issued from a vault cwd is **hard-denied even when the slug is another repo**,
      where `gh release create -R other/repo` today only **asks**. *Done when:* both shapes are
      pinned by tests and the asymmetry is either accepted deliberately or closed by teaching
      `_targets_vault()` to read the inline slug.
- [x] 3a.5 Keep the banner's teaching intact — it is read at the moment of approval, and the command
      it prints must be the command that runs.

## 4. Convert the seven, each with its measured trap

**4.1 + 4.2 + 5.2 DONE 2026-09-19.** The detector now names **five** sites, not seven.
`tools/pr-state.py` carries no `gh` subcommand at all and ran END TO END against the live
repository (PR #120): every layer answered `via anon-rest`, 36/36 checks, two workflow runs with
`name` populated.

⚠ **4.2's pre-registered trap does NOT apply — measured, and the plan was wrong.** A single
`/actions/runs?head_sha=` call was expected to drop workflow names. Against the live repository all
four consumed fields (`name`, `status`, `conclusion`, `event`) are present, `name` = `"CI"`. The
second request `gh run list` makes serves its own workflow-to-name mapping, not a field REST lacks.
A pre-registered trap that turns out not to exist is a finding too.

⚠ **4.1 was a REMOVAL, not a conversion.** Converting `gh pr view` to `gh api repos/{slug}/pulls/{n}`
would have duplicated `gh_read.pull_request`, which already tries anonymous REST and then `gh api`.
Its only unique value was the two GraphQL-only fields: `mergeStateStatus` now comes from REST
`mergeable_state` (5.2) and the rollup already had a labelled REST substitute. **What genuinely
goes:** the case where `slug_from_remote` cannot parse `origin` but `gh` could resolve the repo
itself — that degrades to BLOCKED with the reason named, per this reporter's own rule that a
degraded layer is reported, never synthesised.

⚠ **The run layer STOPPED needing `gh` installed.** It used to print UNAVAILABLE without it; it now
reads anonymously first, so a channel that was dark on a confined session answers.

⚠ **The ceremony fixtures were GraphQL-shaped and had to move** (5.1's class): `pr-state` reads
REST, so a stub answering camelCase would prove the tool works against a payload GitHub never
sends. The stub's `pr view` and `run list` branches are now **deliberately unhandled** — a stub that
still answered them would let a reversion to the subcommand form pass green.

- [x] 4.1 `pr-state.py:112` — `gh pr view --json` → `gh api repos/{slug}/pulls/{n}`.
- [x] 4.2 `pr-state.py:181` — `gh run list --commit` → `gh api`.
      ⚠ **Measure first what the caller consumes.** `gh run list` issues TWO requests
      (`/actions/runs` **and** `/actions/workflows?per_page=100`); a single `/actions/runs?head_sha=`
      call drops workflow names. *Done when:* the fields used downstream are enumerated and shown
      present in the replacement's response.
- [x] 4.3 `pr-flow.py:1919` — emitted `gh pr create` → `gh api -X POST repos/{slug}/pulls`
      with `-f title=` `-f head=` `-f base=` `-F body=@<file>`.
- [x] 4.4 `ship-release.py:343` — emitted `gh release create` → `gh api -X POST repos/{slug}/releases`.
      ⚠ **BLOCKED ON 3a.1 — do not land this conversion before the outbound guard covers the REST
      form.** Measured 2026-09-19: the subcommand raises the INV-14 ask, the REST equivalent passes in
      silence (§0.7). Landing 4.4 first leaves the publish path ungated for the length of that gap.
      ⚠ `--verify-tag` has no REST equivalent; its replacement is an explicit
      `GET repos/{slug}/git/ref/tags/{tag}` **before** the POST — the pattern
      `uat-release-roundtrip.sh` already proved at its step 1.
      ⚠ **That script is NOT in this repo.** It lives in the vault:
      `30-Sites/estate-gap-reconciliation/uat-release-roundtrip.sh`, with its evidence in
      `uat-evidence-20260909-095053/` and the coverage analysis in `rest-conversion-test-battery.md`
      (which is also where B8/B9 come from). Searching the tree for it finds nothing.
      ⚠ From that battery, two limits on what the round-trip proved: **`make_latest` is request-only
      and is not echoed in the response**, so a draft cannot confirm it was honoured; and
      `target_commitish` came back as `main` — the field that would have created a tag had one not
      existed. **The first real release is the first true test of the write**, which argues for
      converting on a patch release with no other content.
- [x] 4.5 canary `:49` `gh label create` → `GET …/labels/openspec-canary`, and on 404 `POST …/labels`.
      ⚠ Removes a `2>/dev/null || true` that makes an auth failure indistinguishable from "already
      exists" — the estate's catalogued `|| true` vacuity defect, in CI.
- [x] 4.6 canary `:51` `gh issue list` → `GET …/issues?labels=…&state=open&per_page=100`
      ⚠ **with `--jq '[.[] | select(.pull_request == null)] | length'`.** `/issues` returns pull
      requests; without the filter the dedupe silently stops opening issues it should open.
- [x] 4.7 canary `:55` `gh issue create` → `POST …/issues` with `-f 'labels[]=openspec-canary'`
      (`-f labels=` sends a string and is rejected).

## 5. Consequences, recorded rather than discovered later

- [x] 5.1 `tests/test_emitted_command_shape.py` — its `-R <slug>` assertion dies with 4.3/4.4 since
      `gh api` carries the slug inline. Change the premise **in the same commit**, and widen its
      scope: it reads only `ship-release.py`'s `_emit_next(…)` today and never sees `pr-flow.py`'s
      `emit(…)` sites, which is the second reason `gh pr create` stood unnoticed.
- [x] 5.2 `pr-state.py` — populate `mergeStateStatus` from REST `mergeable_state` (same enum,
      lowercased) instead of `UNAVAILABLE (GraphQL-only)`. ⚠ `mergeable_state` is thinly documented:
      **pin the observed values in a test**. `mergeable` is computed asynchronously, so `null` on a
      cold read is a real state — `--ready mergeable` already polls it.
- [x] 5.3 Document surfaces, same change: `docs/version-control-legal-moves.md` (rows *Open a PR*,
      *Create a Release*, plus the §2 block), `AGENTS.md`, `CONTRIBUTING.md`,
      `docs/USING-THIS-TEMPLATE.md`, and the vault's `vmm-repo-github-card.md` with `CARD-VERSION`
      bumped — nothing detects that card drifting.
- [x] 5.4 Update the vault ledger `gh-form-findings-ledger.md`: FIX rows absent, KEEP rows present
      and still denied.
- [x] 5.5 Import into ADR-0045's rationale the strongest argument found in the survey, which the ADR
      does not currently make: **hooks run outside the model as separate processes, so prompt
      injection cannot talk its way past them.**
- [ ] 5.6 **The outbound guard is now in this change's blast radius** (§3a). Its note, its rendered
      hook in all three roots, and `docs/version-control-legal-moves.md` §1.3 — which enumerates the
      ASK set as subcommand forms — all move together. ⚠ §1.3's list is the **documented** copy of
      what 3a.1 edits; leaving it describing only `gh release create|edit|upload` reproduces the
      class-9 defect on the surface a human reads.

## 6. Regression

**ALL GREEN 2026-09-20.** Suite **490 passed, 0 failed** (baseline was 424 on this branch; the
detector that was red by design is green because the call sites moved). `openspec validate --all
--strict` 7 passed 0 failed. markdownlint **0 findings** — the 13 that pre-existed were in this
change's own spec delta and tasks file, and the delta now matches the live spec's blank-line
convention. `preflight.py . --body-file .git/pr-flow/prefer-rest-body.md` → **CLEAR**, 13/16 CI jobs
reproduced, 0 unrunnable, 3 not reproduced by design.

⚠ **6.5's matrix caught a defect in ITSELF, which is the point of it.** The first cut mutated
`SANCTIONED_WRITES = {` into `SANCTIONED_WRITES = {} or {`, which evaluates to the ORIGINAL set — so
one row passed while mutating nothing. It was only noticed because a neighbouring row failed loudly
and forced a re-read. Mutations are now anchored at the USE SITE, and each asserts its anchor
appears exactly once.

⚠ **A second finding from the same matrix: the two controls OVERLAP for writes.** With the method
split in place, `gh api -X POST graphql` is refused as an unsanctioned write even with the graphql
clause deleted. A mutation row using a graphql WRITE would therefore have credited the wrong rule;
only a graphql READ isolates the clause, and the row uses one.


- [x] 6.1 Full suite. Baseline **424 passed** on this branch, rebased onto `a22c2ea`, 2026-09-18.
- [x] 6.2 `openspec validate --all --strict` — 7 items, 0 failed at last run.
- [x] 6.3 `node_modules/.bin/markdownlint` with the four `--ignore` paths `ci.yml` uses → 0 findings.
- [x] 6.4 `tools/preflight.py . --body-file <path>` → CLEAR. ⚠ `--body-file` is **not optional**:
      without it the body step prints `SKIP`, and a SKIP reads exactly like a PASS.
- [x] 6.5 A mutation matrix behind the detector and the method split — an instrument that cannot be
      shown to fail is not evidence, and this change's premise is that unexercised instruments rot.
- [ ] 6.6 **B8 and B9 run as a pair**, per `rest-conversion-test-battery.md`: B8 green→green (no
      regression on the subcommand form), B9 red→green (the new REST coverage). Record the red
      observation, not just the green one — a B9 green on both sides proves nothing.

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
- **The INV-14 outbound rail is edited, not merely relied upon** (§3a, folded in by operator decision
  2026-09-19). The conversion **removed an ask before it added one** — measured, §0.7 — so the rail's
  coverage now depends on a matcher this change writes. Two named consequences: the release publish
  is gated by a form the guard learned yesterday rather than one it has held since INV-14 was
  written; and the vault HARD DENY **tightens** for `gh api`, because the inline slug misses the
  `-R owner/repo` early-out and falls back to cwd (3a.4).
- **What breaks if this is wrong:** these are the controls other work is judged by. A defect here
  does not fail loudly — it produces a confident, well-formed, wrong answer.

⚠ **The ASK coverage this change adds is a NO-OP in auto mode — sign with this in front of you.**
Measured 2026-09-20 (adversarial probe, vault Site `harness-permission-control-deep-dive/
adversarial-probe-plan-and-recovery`; dev-store hardening item 37): the outbound guard's **ASK**
verdict silently proceeds in auto mode — it neither prompts nor blocks. §3a taught the rail to
recognise a REST publish and return ASK; in auto mode that ASK does nothing. Three consequences.

**(a)** §3a's REST-publish coverage **protects in interactive mode and is a no-op in auto mode**. It
is still correct and is the necessary foundation for the fix — the guard cannot be converted to
hard-stop a form it does not recognise, and §3a is what makes it recognisable.

**(b)** The rail's **DENY** verdict is NOT affected — the vault HARD DENY held under every probe.
Only ASK degrades.

**(c)** **Approving this gate does NOT close the auto-mode outbound gap.** A follow-on change (its
own Gate 4) re-buckets outbound by irreversibility — release publish, `v*` tag push, `remote add` /
`repo create` become DENY-and-hand-to-operator; feature-branch push stays ASK because its ref is
reversible. This change is a prerequisite for that one, not a substitute.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [x] 7.1 Tier-0 touch surfaced (item-37 auto-mode caveat incl.); **Approved** — Keith Nielsen, 2026-09-20

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
- [ ] 8.9 **Deploy-down is operator-run** and is NOT optional for this change: **both** guards live in
      literate notes, so until `template-mirror.py` and `vault-render.py render` run, **the live fleet
      still carries the old guards** — including the outbound rail that §3a widens.
      Then verify: `template-parity.py $VAULT_ROOT` → 0 drift, and
      `vault-render.py reconcile` → 15/15 ok.
      ⚠ Run render with the working directory **at the vault root** — see the render-root defect.
