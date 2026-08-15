<!-- SPDX-License-Identifier: Apache-2.0 -->
# Changelog

This changelog is generated from completed OpenSpec changes in
`openspec/changes/archive/`. Each entry corresponds to an archived change.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

<!-- New entries are added here as changes land. -->

## [0.1.42] - 2026-08-15

### Fixed

- **Read-after-write observations now partition** (`fix/lag-report-partition`, defect fix,
  **no change directory**, PR #74). The observation log recorded two independent facts in one place:
  `step` carried the sentinel `"(not-a-verify)"`, and `outcome` could itself **be** `"not-a-verify"`,
  entangling *was this a post-mutation verify?* with *was the value visible?*

  Measured on the real log, this was not a formatting problem. **26 series were printed under a footer
  claiming 22, and only 6 of the 26 were verifies** — so the summary folded twenty ordinary driver
  runs, which had never been waiting for anything, into a *"became visible"* tally. Anyone sizing the
  retry ladder from that number would have been averaging unrelated runs: the defect was corrupting
  the dataset the ladder is meant to be derived from, not merely mis-rendering it. The footer
  disagreeing with its own table was the second, lesser symptom of the same cause.

  `is_verify` is now its own field, `step` is `None` when a run is not a verify, and outcomes
  partition — `visible`, `not-visible`, `censored-ladder-exhausted`, `abandoned-low-budget`. A
  non-verify that saw nothing is `not-visible` and explicitly **not** censored: nothing was being
  waited for, so it is a lower bound on nothing and must never reach a lag summary. The report
  separates verify series from ordinary runs, counts exactly the rows it prints, and raises an
  explicit alarm if the tally ever stops partitioning.

  **Records written before the split are upgraded on read, never rewritten.** That file holds the only
  real measurements this operation has of GitHub's read-after-write behaviour, so "cleaning" it would
  destroy the evidence it exists to collect. Verified in production against a mixed log — 40
  pre-partition records and 6 post-partition records read together without loss.

  With the record legible, a shape appears that the conflated report had hidden: **merge visibility
  clusters at ~11.2s across six observations spanning 0.19s**, against a retry ladder that waits about
  7s. That is consistent with every merge on record — one exceeded the ladder, the rest cleared on its
  final rung. **No constant is changed here.** Eleven verify series is not a distribution, the report
  still declines to recommend a ladder, and choosing a better-looking number from eleven points is
  precisely the defect that made the ladder worth measuring in the first place.

## [0.1.41] - 2026-08-15

Two changes, both aimed at the same thing from opposite ends: the release ceremony stops being
operator-only by defect, and the contribution rules stop being silently approximate.

### Fixed

- **Release reads degrade to the anonymous channel** (`fix/ship-release-anon-reads`, defect fix,
  **no change directory**, PR #72). `ship-release.py` called `gh release view` / `gh release list`
  directly. Both need the operating-system keyring, so from a confined session `gh` returns a
  misleading 401 and the driver exited **`3 BLOCKED` on a read** — *after both of its real guards had
  already passed*. Measured twice mid-ceremony during this repository's own v0.1.40 ship: the tag
  could be pushed on the git channel, but the driver could not be re-run to advance or verify its own
  success. This violated a shipped requirement (`maintenance` — *GitHub Reads Degrade To An
  Unauthenticated Channel*), and the sibling `pr-flow.py` already complied, so the fix reuses that
  layer rather than inventing one.

  Three decisions came out of the design pass rather than out of a failure. Release **existence is
  read from the list**, never a per-tag endpoint: `gh_read.get()` raises on a failed read and does not
  distinguish 404, so `/releases/tags/<tag>` would turn *"this release does not exist"* — an ordinary,
  expected answer — into an error. **`isLatest` is asked, never recomputed**: REST carries no
  per-release `isLatest`, and *"newest non-draft, non-prerelease by date"* is GitHub's rule, so
  restating it locally would fork an acceptance criterion across two systems with no merge.
  And **draft releases are invisible to unauthenticated callers**, so on that channel a missing
  release means *absent or draft*; the ambiguity is printed rather than assumed away, and stays
  silent on the authenticated channel where drafts are visible and a warning would be over-denial.

  Release **mutations remain operator-owned** — credential absence is the real INV-14 barrier. Only
  the reads changed.

### Changed

- **The no-proposal exception is written down and bounded** (`docs/proposal-threshold-rule`,
  docs-only, no spec delta, PR #71). `CONTRIBUTING.md` states that *every* change originates as an
  OpenSpec proposal, while practice has exempted defect fixes to maintainer tools since PR #35 — an
  exception that was real, load-bearing, and recorded nowhere. A documented absolute that practice
  quietly contradicts teaches its readers that the document is approximate.

  The exception is now stated **with edges**, because an unwritten one has none: it had been stretched
  to cover a 204-line change that added a command-line flag, module-level state, a refusing guard and
  new exit semantics, which then shipped three defects. A change may ship without a proposal only if
  it is a defect fix to a maintainer tool **and** it adds no caller-visible surface, introduces no
  persistent state, and changes no exit semantics. Recorded alongside are the three questions a design
  pass exists to force — **state lifetime** (what is the exit condition?), **reachability** (which real
  invocation reaches this line?) and **exhaustiveness** (do the categories partition?) — each mapped to
  a defect that shipped for want of asking it.

  The rule is **prose and unenforced**, and says so: nothing in continuous integration checks it, and
  a requirement and its guard ship together or not at all. The candidate enforcement point is named
  instead. Its first application was PR #72, where it changed the design — a module-level cache was
  replaced by explicit data flow.

## [0.1.40] - 2026-08-14

Four defect fixes to `tools/pr-flow.py`, none carrying an OpenSpec change directory (maintainer-tool
fixes, per the precedent of PRs #35, #39 and #49). Every one was found by **running the driver**, not
by the tests written for it, and three of the four surfaced in production on the driver's own pull
requests — recorded here because the pattern is more useful than the individual defects.

### Fixed

- **A saved plan can no longer replay the previous step's mutation** (`fix/pr-flow-saved-plan-pinning`,
  defect fix, **no change directory**, PR #66). `next.sh` is written only for operator-owned steps, so
  it survived untouched across agent-owned steps while still holding the last operator mutation:
  running it at the wrong moment re-issued a merge for the previous pull request. Measured 2026-08-12,
  when it replayed PR #64's merge. The mutation was baked in as literal text at write time while the
  branch it verified resolved at run time, so a plan could **mutate one pull request and verify
  another** — producing `"merged": true` immediately followed by `REFUSED: no open PR`, two lines
  describing different objects. The plan now pins its verification target and arguments at write time,
  records the branch it was written for and refuses to run from anywhere else, and deletes itself once
  its step completes.

- **A post-mutation verify tolerates read-after-write lag instead of refusing**
  (`fix/pr-flow-post-mutation-lag`, defect fix, **no change directory**, PR #67). The verify tail
  re-derived the route immediately after the mutation and treated *"GitHub's read view has not caught
  up"* as *"the mutation did not happen"*. Two sites, one cause: `post_merge()` printed
  `REFUSED: PR #64 is not merged (state=open)` at exit 1 directly beneath the mutation's own
  `"merged": true`; and the `pr` step read 0 pull requests seconds after `gh pr create` succeeded and
  **re-emitted that same command**, an instruction that opens a duplicate pull request if followed. The
  driver already owned the right vocabulary — `not_ready()` and exit 2 mean *"the platform has not
  answered yet"* everywhere else in the file — so an unconfirmed read is now `WAITING`, quoting the
  mutation's own response, and no outward mutation may be emitted while a verify is unconfirmed.
  **Both halves confirmed in production**: duplicate suppression on PR #69's creation, false-refusal
  prevention on #67's own merge.

- **Post-mutation suppression is scoped to the unconfirmed step** (`fix/pr-flow-suppression-scope`,
  defect fix, **no change directory**, PR #68). The guard above shipped over-denying: it suppressed
  **every** later step, not only the one it was verifying. Measured on PR #67's own merge — the driver
  printed `merged: PR #67 at 2026-08-14T10:13:11Z` and then refused the branch deletion with *"the read
  view does not yet show the merge mutation"*, a diagnosis the line directly above it had already
  disproven, blocking work that genuinely needed doing. Suppression was scoped to *"this run carried
  the flag"* and is now scoped to *"the verified mutation is still unconfirmed"*, keyed to the specific
  step because `post_merge()` pre-marks earlier steps `ok` before verifying anything. Over-denial is
  its own failure mode: a guard that blocks correct work teaches its reader to ignore it.

- **The lag retry is reachable** (`fix/pr-flow-lag-observations`, defect fix, **no change directory**,
  PR #69). The retry added in PR #67 was **dead code on every real invocation**: `prefetched` is a
  two-tuple, so `if prefetched:` was truthy even when the list was empty — and empty is precisely the
  lag symptom — leaving the lag-tolerant read in an unreachable `else`. Measured on PR #68's own
  creation, where the suppression guard fired correctly but the read happened exactly once. The
  prefetch is now passed into the retry as its first attempt, so one path serves both cases, every
  outcome is observed, and the prefetch read is never wasted.

### Added

- **Read-after-write observations are recorded** (same pull request). The retry ladder was chosen from
  taste rather than measurement, and the live record refuted the comment justifying it: PR #67 cleared
  on the last rung, #68 exceeded the ladder entirely, #69 cleared on the last rung again. Nothing in
  this repository recorded what GitHub's read view actually does, so every future adjustment would have
  been another guess wearing a number. `.git/pr-flow/lag-observations.jsonl` now holds one raw record
  per read attempt, and `--lag-report` prints them. Three properties decide whether that data can be
  trusted: **every** attempt is logged, including immediately-visible ones, because a record of only
  the lagging cases makes the ladder look more necessary than it is; an exhausted ladder is marked
  **censored**, because that series is a lower bound and averaging only the visible ones is how a
  too-short ladder justifies itself with the data its own shortness produced; and the report
  **refuses to propose a delay**, asserted by test, because a tool that hands back a number is one the
  number gets adopted from. The ladder constants are marked provisional in-source until the log holds
  enough observations to size them from evidence.

## [0.1.39] - 2026-08-12

### Added
- **Every ADR citation must resolve** (`enforce-adr-reference-integrity`, ADR-0039, PR #62).
  `spec-lint` gains two checks. **Contiguity** is now derived from the records present, replacing a
  `range(1, 9)` hardcode that validated **8 of 38** ADRs while passing regardless — measured: with
  ADR-0037 *and* ADR-0039 both absent and ADR-0039 cited in `ci.yml`, the old check returned PASS.
  **Reference integrity** requires every `ADR-NNNN` cited anywhere to resolve, reporting `file:line`;
  unresolved citations are permitted **only** inside a live change directory, because a proposal is
  forward-looking while specs, workflows, README and the archive are records.
- **ADR-0039 written.** `.github/workflows/ci.yml` had cited ADR-0039 for the declared-scope gate's
  Phase-B flip across nine merged pull requests while **no such record existed**; the originating change
  never planned one. The ADR consolidates the decision from the workflow comment and that change's
  proposal, including why the check context stays *unrequired* (whether a `skipped` conclusion satisfies
  a required context cannot be dry-run on this plan — ADR-0034) and why the job name dropped ", burn-in"
  while the context was still unrequired: the name **is** the check-context identity, and renaming a
  required context deadlocks merges.
- **The archive convention is written down** (`document-archive-convention`, ADR-0040). A change is
  archived **on its own feature branch, in the pull request that merges it** — moving
  `openspec/changes/<slug>/` into `archive/<date>-<slug>/`, applying the delta into `openspec/specs/`,
  and stamping the CHANGELOG. The one exception: a concurrent change carrying a delta against the
  **same** capability spec defers and applies in merge order, naming the change it defers to, because
  two deltas to one spec file can overwrite each other without ever conflicting.
  Measured over `main`'s merge graph: **12 of 14** pull-request-era changes archived in one PR, and both
  deviations (#40→#41, #58→#59) are that exception firing. The rule previously existed in no spec, ADR,
  or runbook — only in per-change `tasks.md` files — and was confidently re-derived **wrong twice in one
  day**; ADR-0040 records the three flawed measurement methods by name so the next derivation
  recognises them. Enforcement is **owed, not shipped**, and says so: the naive guard would have failed
  PR #58's legitimate deferral.

## [0.1.38] - 2026-08-06

### Changed
- **The declared-scope gate is now BLOCKING** (`flip-scope-review-blocking`, conforming amendment,
  **no Architecture Decision Record (ADR)**, `maintenance` ~1 Requirement). `scope-review` loses
  `continue-on-error` after a burn-in measured across the 14 most recent merged pull requests
  (#41–#57), every one `success`. A pull request whose diff touches a path outside its declared
  ```scope block now **fails** rather than reporting quietly. The job was renamed
  `Scope review (declared-scope gate, burn-in)` → `Scope review (declared-scope gate)` deliberately
  **while the context was still unrequired**, because the job name is the check-context identity and
  renaming a required context deadlocks merges. **Where the block binds is stated, not assumed:** the
  gate is *not* in the branch ruleset's required contexts, because the job reports `skipped` on the
  `push` trigger and on Dependabot pull requests, and whether a `skipped` conclusion satisfies a
  required context cannot be dry-run on this plan (ADR-0034 — `evaluate` enforcement is
  Enterprise-only). Until that is resolved the gate binds through `tools/pr-flow.py` step 8, which
  refuses to emit a merge command while any check is failing. Approval was **conditional on an
  escape-hatch regression**, discharged by three independent measurements: the ruleset cannot refuse
  a merge on this context, `ship-release.py` has no dependency on checks so releases are unaffected,
  and a revert of the change passes the blocking gate itself.

### Fixed
- **`validate-scripts.sh` no longer reports failures for checks it never ran**
  (`fix/validate-scripts-tmp-capture`, defect fix, **no change directory**). The script created its
  work directory with `mktemp -d` but hardcoded bare `/tmp/pc.txt`, `/tmp/bn.txt` and `/tmp/sc.txt`
  for stderr capture. Under a write-scoped sandbox `/tmp` is read-only, so each redirect failed and
  the enclosing `if` fell to its `else` branch — **12 false `FAIL` lines and exit 1**, while every
  file compiled clean. It passed in continuous integration, where `/tmp` is writable, so the defect
  was invisible exactly where the corpus is normally validated and present exactly where an agent
  would run it. All three captures now route through `$WORK`.

### Added
- **ADR-0038 — the required check contexts are complete** (`record-required-check-contexts`,
  recording ADR, **no spec delta**). Discharges ADR-0034's Follow-on §2. The `main` ruleset's
  `required_status_checks` rule was neither absent nor complete: **13** contexts required against
  **17** that run, and the four unrequired ones included **all three Tier-0 runners** — `Secret scan
  (INV-7)`, `INV-6 static` and `INV-6 dynamic` — so the invariants with the highest blast radius had
  runners that could not block a merge. Extended to **16**.

## [0.1.37] - 2026-08-06

### Added
- **The session prime now measures its own capability instead of recalling it**
  (`bootstrap-capability-probe`, conforming amendment, **no Architecture Decision Record (ADR)**,
  `maintenance` +1 Requirement). The cold-start prime gains a fifth gate — *measure, don't infer* —
  and a capability-probe step that runs before any claim about what the session can read, write, or
  reach. Write scope, `gh` credential, `git` credential, and network reachability are reported as
  four **independent** layers, none inferred from another; and capability is distinguished from
  authority, since a channel the agent can execute may still require operator consent (INV-14). The
  step **references** the existing capability reporter rather than restating its checks, so one
  system owns the criterion. Both gate-enumerating adapters (`vault-template/CLAUDE.md`,
  `vmm-session-rebooted.md`) were updated in lockstep. Attested by failure mode F35: an agent
  asserted "no network" from a single credential-lock error that was in fact a *write* failure,
  while a purpose-built probe answering the question in one call sat unrun in the open repository.
- **The pull request lifecycle is now driven, not composed — `tools/pr-flow.py`**
  (`add-pr-flow-driver`, conforming amendment, **no Architecture Decision Record (ADR)**,
  `maintenance` +11 Requirements). The sibling of
  `ship-release.py`: a guarded, re-entrant state machine for branch → push → PR → checks → merge →
  branch deletion, holding no state file and re-deriving everything from the world each run. Same
  load-bearing contract — it **never executes an outward mutation**, because the INV-14 guard
  text-matches the command the *caller* runs and a wrapper would silently bypass the rail. It proves
  each guard, emits the next single command **with its owner named**, exits `2`, and on re-invocation
  verifies the mutation actually landed.
- **Why:** F30 (live vault `determinism-failure-modes-claude`, class 8) recorded a single session in
  which a child PR was opened before its parent merged, a mandatory body-PATCH step was named then
  dropped, `gh pr merge --delete-branch` half-failed while printing `✓ Merged`, a rebase was reported
  complete with `.git/rebase-merge` still active, and three emitted commands were not executable as
  written. All ordering, syntax, or postcondition defects — precisely what `ship-release.py` already
  solves for the *other* half of the ceremony. This extends the proven contract rather than inventing
  a second pattern. **A table of command templates was considered and rejected:** this repo's own
  record is that a prose ENFORCE has the reliability of recall, and a list an agent is meant to
  consult is a list it can skip.
- **Ownership is probed, never recalled — `--capabilities`.** The one defect class a driver cannot
  fix by ordering is *"the operator must run this"* when the agent can. The agent asserted "no GitHub
  egress this session" and it was false: plain `git` and the anonymous REST API both worked, and only
  `gh` was unavailable (a sandboxed `gh` cannot reach the OS keyring and reports a bogus 401). A
  static table would have preserved that wrong answer; a probe re-measures. It reports the mechanism,
  not just the verdict.
- **`tools/gh_read.py`** — shared read layer, anonymous REST first with `gh` as fallback, returning
  the answering **channel** with every payload. Stdlib only; no new dependency.
- **The whole route is shown before the next step — `--plan`.** The driver was a *step* oracle, not
  a *route* oracle: it could say what to do next but not what the journey was, so planning fell back
  to recall. One ordered step table now drives both the emitter and the planner, every invocation
  prints a route header, and `--plan` reports each step's executor, authority and guard, marked
  **measured** or **projected**. No command text is composed for a projected step, because an
  unreached step's command is a prediction.
- **Authority is distinguished from execution (RACI; four-eyes).** A single `owner` field conflated
  *who runs it* with *whose authority is required* — reproducing the very defect F30 names. Emissions
  now carry `runs:` / `authority:` / `consent:`, and the consent class is **measured** by evaluating
  the outbound guard against the exact command. Consequently `git push` and the post-merge branch
  deletion move **off the operator's keyboard**: the agent runs them under the INV-14 ask. Human
  decision points went *down*, not up.
- **Preconditions are re-asserted at the moment of mutation.** An operator-executed command may run
  long after the state that justified it was measured — an unbounded time-of-check-to-time-of-use
  (TOCTOU) window. Operator steps are written to `.git/pr-flow/next.sh` with the approved predicates
  asserted ahead of the mutation and a 24-hour expiry, so a short line is what gets pasted (the
  interactive paste channel had already corrupted two hand-offs and clobbered a repo file).
- **Asynchronous state is awaited, never assumed.** Zero check runs and uncomputed mergeability now
  report NOT READY rather than reading as "green" and "not false". `--ready` answers one condition in
  one request with a meaningful exit code, so a wait is testable instead of described, and the driver
  never blocks or sleeps. The anonymous read budget is surfaced: **60/hour, and `304 Not Modified`
  still decrements it** — measured, refuting the usual "conditional requests are free" claim, which
  holds only for authenticated requests.

### Fixed
- **The driver's route markers now carry their own legend, and the pass mark no longer inverts**
  (`fix/pr-flow-marker-legend`, defect fix to maintainer tooling, **no change directory**, by the
  precedent of #35/#39/#49). Six status glyphs shipped with no key anywhere, so a reader had to infer
  all of them. The legend now renders **from the marker table** — a glyph cannot exist without a
  definition — and lists only the markers actually on screen. The pass mark was `x`, copied from the
  markdown-checkbox habit, and `x` **inverts**: "an X in the box" reads as *selected* in the US and
  UK, while *batsu* means *wrong* across Japan and much of East Asia, against *maru* for correct. The
  isolated glyph was survivable; the **pair** was not — `[x]=passed` sat beside `[!]=failed`, and
  under the batsu reading both scan negative, collapsing the route's most important distinction. A
  legend only rescues that if it is read, and a status line's whole value is being scannable
  *without* reading prose. Now `P`=passed and `F`=failed: language-bound but never inverted, and
  ASCII so no terminal font can render a box. `!` is dropped too — in most interfaces it means
  *warning*, which understates a hard failure. Task files keep `[x]` because the GitHub renderer
  accepts only `[ ]` and `[x]`; that split is renderer-forced, and both legends state their own set.
  Also fixes an off-by-one that reported the completed route as `step 15/14`.
- **`gh pr merge --delete-branch` is never emitted again.** It is defective on three independent
  counts: it cannot express a head precondition (`cli/cli#5686`); it bypasses GitHub's own
  retargeting of stacked children, which are **closed** instead (`cli/cli#1168`) — this, not platform
  inscrutability, is how PR #29 died; and its branch deletion is non-atomic and prints a success tick
  when it did not happen. The merge now goes through the REST endpoint carrying `sha`, so a raced
  head is refused **by the server** with 409, and deletion is a separate, verified step.
- Retargeting a stacked child is prescribed via `gh api -X PATCH` with a re-read, not
  `gh pr edit --base`, which can fail **silently** behind a deprecated GraphQL layer.
- A failing body-derived check now prescribes a **push, not a re-run**: the gate reads the body from
  the event payload, which is a snapshot as of push time, so a re-run replays the stale one.
- Zero check runs no longer read as "all 0 checks green"; `mergeable` is now read at all (from the
  single-pull-request endpoint, the only one that carries it); a failed `git fetch` no longer lets
  base-currency be measured against a stale ref; and the declared-scope block is verified rather than
  requested in a prose string.
- **Gate-4 approval is measured on a ticked checkbox.** Caught by dogfooding: an earlier cut matched
  the word "Approved" anywhere, so the *unticked* task describing the sign-off read as the sign-off
  itself — a declared end-state reported as reached, inside the driver built to prevent that.
- **Extended against all 49 PRs in this repo's history before shipping**, so the driver covers the
  flows we are *allowed* to run and not merely the ones we happened to run last. Five attested
  shapes were unhandled or mishandled, and the two most serious were live defects: **a Dependabot
  branch read as local** (a bare revision parse resolves a remote-tracking ref by DWIM) so the
  driver proposed **rebasing a branch we do not own**, which detaches it from Dependabot's
  automation; and **a bare `git rebase` emitted while a different branch was checked out**, which
  acts on `HEAD` and would have rebased the wrong branch. Also now handled: **stacked PRs** — open
  children are detected and the merge refused until they are retargeted, because merging a parent
  with `--delete-branch` closes them irrecoverably (PR #29 died exactly that way, F21); **closed-
  unmerged PRs** (#18, #29), previously invisible to an open-only query so a duplicate would have
  been proposed; **draft PRs** and **multiple open PRs sharing a head**, both now refused rather
  than guessed; and **re-running a completed lifecycle**, which used to refuse and now reports
  LIFECYCLE COMPLETE, restoring the re-entrancy the driver claims. Release PRs, feature+archive
  two-PR ceremonies, docs-only recording ADRs and the non-vault repos need no special case; fork
  PRs are out of scope and stated as such.

- **Two non-default GitHub rulesets on the repo, recorded by ADR-0034** (`record-github-rulesets`,
  recording change, **no spec delta**). Server-side, empty-bypass (binds even admin): `v*` tags are
  immutable (can't be moved/deleted/force-pushed; creation still allowed) and `main` requires a PR +
  merge-commit-only (no direct push, no squash/rebase). The first guard in the stack that binds the
  operator, not just the agent — closing the F10/RC-7 class server-side. Provisioned `active`
  (`evaluate` dry-run is Enterprise-only); `required_status_checks` added via a follow-on once a live
  PR confirms the exact check-context names. Repo-config only — no `vault-template/` delta.

### Changed
- **`tools/pr-state.py` no longer dies when `gh` is unavailable.** The standing rule *"run
  `pr-state.py` first on any confusing PR state"* was unrunnable by a sandboxed agent, which is why
  hand-rolled `curl` replaced it at the exact moment of confusion. Reads now degrade to the anonymous
  channel; GraphQL-only layers (`mergeStateStatus`, the check rollup, run-level aggregation) report
  **UNAVAILABLE and are never synthesised**, and the layer-disagreement comparison is skipped rather
  than computed from one side. **Dogfooding caught a real defect pre-ship** — the state-machine line
  was labelled `· GraphQL` while sourced from REST, which is the channel-stripping error the reporter
  exists to prevent.
- **Reference deployment adopted the strict write-scope sandbox (Stage-B), recorded by ADR-0035**
  (`adopt-strict-write-scope-sandbox`, recording ADR, **no spec delta, no `vault-template/` change**).
  The live instance's `.claude/settings.json` moves from burn-in to strict — `failIfUnavailable: true`
  + `allowUnsandboxedCommands: false` — completing ADR-0022's two-stage rollout for this deployment and
  closing the P15 residual (*the write-scope guarantee held only while the sandbox was on*). **Instance-
  only:** `settings.json` is SEED (instance-owned); the template default stays in burn-in so forks
  adopt strict only after their own clean burn-in (SE-3), per `docs/USING-THIS-TEMPLATE.md` Step 4c.
  Evidence: P6/SE-4 (re-run 2026-07-27, EROFS + path-specific control), P16/SE-5, P15 substrate, and
  SE-2 deps (`bwrap`/`socat`) verified present.
- **CI validates with `--strict`, matching the weekly canary and the ceremony docs** (editorial, **no
  spec delta, no ADR**). `.github/workflows/ci.yml` ran `openspec validate --all`; the
  `openspec-canary.yml` workflow already ran `openspec validate --all --strict` against `@latest`, and
  `AGENTS.md` and the ceremony docs mandate the strict form. The PR/push job now agrees with both.
  Verified green under the pinned 1.6.0: `OpenSpec validate` passed on this branch with `--strict` in
  place.
- **`maintenance` requirement *Operator-Only Paths Fail Legibly* reflowed** so `SHALL` sits on the
  first physical line rather than the second. Semantics unchanged — same EROFS trigger, same exit
  status **4**, same message obligations, same re-raise rule. This is defensive, not corrective: under
  the pinned OpenSpec **1.6.0 the original wrap validates cleanly**. It fails only under **1.4.1**,
  which parses just the first physical line as `requirement.text`. Keeping the modal verb on line 1
  costs nothing and removes a parser-version dependency.

### Notes
- **A false alarm is recorded here deliberately, because the corrective is a rule and not an
  apology.** This change was first written up as *"the `openspec-validate` job has been RED on `main`
  since v0.1.33 (2026-07-20) and nothing surfaced it"*, with two consequences drawn from it: that the
  weekly canary had been filing false upstream-incompatibility issues, and that the Dependabot OpenSpec
  bump PR — the compatibility gate — had been reporting against a red baseline and was therefore
  uninterpretable. **All three claims were false.**
- **The cause was a stale local CLI, not the corpus.** `~/.local/bin/openspec` on the maintainer
  machine is **1.4.1**; the repo pins **1.6.0** and CI installs the pin via `npm ci`. Every local
  `validate` run was executing a two-minor-versions-old parser against a corpus written for the pin.
- **What refuted it, and what should have been checked first:** the GitHub API. `OpenSpec validate` is
  `success` on `main` head `405dee3` (2026-07-28); both open PRs report **34/34 green**; the repository
  has **zero open issues**, so no canary issue was ever filed. Anonymous `api.github.com` needs no
  token and answers in one call — *the check history is observable, and a claim about CI's state that
  is never checked against it is a guess wearing evidence's clothes.*
- **Rule going forward:** compare `openspec --version` against `package.json` before treating any local
  validation failure as a defect. A local tool disagreeing with the pinned tool is the first hypothesis,
  not the last.
- **One true finding survives, and it is unrelated:** per ADR-0034 the `main` ruleset carries **no
  `required_status_checks`** (follow-on *pending*), so a PR is required to merge but no check must
  pass. That gap is real and still queued — **it simply was not masking anything here**, and the
  retracted red-CI story must not be cited as its evidence.

### Removed
- **`add-telemetry-segment` RETRACTED** — the osquery file-integrity/egress detection change, authored
  in the initial commit (`82fa68a`, 2026-06-14) and untouched since, is withdrawn unshipped. **No spec
  delta was ever applied; none is applied now** — retraction is a deletion, not an archive. It was the
  only entry in `openspec/changes/` and stood at `0/17` tasks for seven weeks.
- **Its deferral condition had been met, and that is why it needed deciding rather than ignoring.**
  Task 1.1 gated it on *"OS-level write-protection of `99-Operations/`"*, which shipped as ADR-0022
  (v0.1.19) and the Stage-B strict flip (ADR-0035); `access-control` already records §14.1 as
  *"hereby un-deferred"*. A change whose only blocker is gone is not dormant, it is pending.
- **Retracted rather than activated, because three of its four premises were overtaken by
  measurement.** (1) Its egress rule flags *"connections to anything other than `localhost`"* — but the
  INV-14 investigation measured **all sandboxed egress traversing the auth proxy at `localhost:3128`**,
  so as written the rule flags nothing and misses the only real path. (2) Its FIM half is now largely
  served by the kernel-level write scope it was designed to backstop. (3) osquery is a third-party
  runtime dependency, against the trust-ring-minimization posture adopted later (precedent N2/v0.1.22).
  (4) Its log targets sat under `99-Operations/`, an autonomy-banned area under the current matrix.
- **It was also imposing a running tax.** Because it MODIFIED `maintenance`, every later
  `maintenance`-touching change had to write a coexistence paragraph and an archive-ordering note
  against it — found in `add-template-parity-check`, `add-ship-ceremony-tools`, `add-template-mirror-driver`,
  and `fix-append-idempotent-catalog-link`. Retraction ends that.
- **The standing hazard it carried:** `openspec archive` applies deltas at archive time by header match,
  last-writer-wins. Archiving it — by name or in a batch — would have injected two ADDED Requirements
  describing machinery that does not exist, re-opening the ADR-0037 *rule-with-no-runner* class from the
  other end. Closes the `add-telemetry-segment` re-scope item queued in v0.1.36's §6.
- **Not lost:** the design intent is preserved in git history at `82fa68a`, and runtime detection may be
  re-proposed on measured premises. This retracts a June design, not the idea.

## [0.1.36] - 2026-07-28

### Added
- **INV-6 gains a runner — static AST analysis plus a network-namespace behavioural check**
  (`enforce-inv6-offline-check`, `constitution-override` **conforming**, **ADR-0037**). INV-6 —
  *"`[script]` operations make no network calls and no LLM calls"* — was, after v0.1.35, **the last
  live Tier-0 invariant with no mechanism at all**. Measured: a grep across `tests/` and all fifteen
  CI jobs for `socket|network|offline|urllib|requests|unshare` returned one hit, and it was **prose in
  a docstring**.
- **The defect was the opposite shape to INV-7's**, and both are now on record. INV-7's Requirement
  carried a *wrong* scenario (it inspected two config files). INV-6's scenario was already **correct
  and behavioural** — *"THEN it issues no network request and invokes no model"* — and **nothing ran
  it.** A well-formed rule with no runner is the harder of the two to notice, because reading the spec
  is reassuring.
- **`tools/inv6-offline-check.py`** (repo-only, stdlib-only) analyses each fleet note's fence: Python
  by **AST**, bash by a conservative command-position scan. The AST requirement is not fastidiousness —
  the `outbound-publish-guard` and `push-guard` notes implement the INV-14 rail and exist to *name*
  outward verbs in regex literals. Measured on the shipped files: naive grep **6** and **2** hits,
  AST violations **0** and **0**. A checker that failed the two most security-relevant scripts on every
  run would be disabled, not obeyed (RC-E, *over-denial is camouflage*). Indirection — computed dynamic
  imports, non-literal argv — is reported **UNRESOLVED** and fails, never passed silently.
- **`.github/scripts/inv6-offline-dynamic.sh`** runs the fleet suite inside an unprivileged **network
  namespace**, proving the isolation first: the network must be reachable *outside* and unreachable
  *inside* in the same run, or the job **fails closed**. A confound was found and eliminated rather
  than worked around — `unshare -r` maps the caller to root, which ignores permission bits and broke
  one test asserting `EACCES`; `--map-current-user` preserves uid and the suite passes 38/38 with the
  control still blocking.
- Two CI jobs (`inv6-offline-static`, `inv6-offline-dynamic`) and `tests/test_inv6_offline.py`
  (28 cases, weighted toward the false-positive direction). `maintenance` gains an ADDED Requirement;
  the existing INV-6 Requirement is left intact, per ADR-0030's pattern.

### Notes
- **All nine live Tier-0 invariants now have a mechanism.** The condition RC-B identified — an
  invariant asserted as enforced with no behavioural evidence — no longer holds anywhere in the set.
- **Honest bound, carried in the spec, the tool's help, and its output:** a pass means *no statically
  visible network call, and none on the paths the suite exercises*. It does **not** mean the fleet is
  offline. Static analysis is blind to `__import__`/`eval`/C extensions; the dynamic half is bounded by
  test coverage — and coverage is thinnest where the verbs live, since **the two INV-14 guards have no
  tests**. Queued separately.
- **Repo-side only — no `render`, no mirror, no operator deploy step.** No fleet member is added; the
  fleet is authored upstream and deployed down.

## [0.1.35] - 2026-07-28

### Added
- **INV-7 acquires a mechanism — credential scanning at the commit boundary** (`enforce-inv7-secret-scan`,
  `constitution-override` **conforming**, **ADR-0036**). A new Layer-0 literate meta-script,
  `secret-scan-script.md` → `~/bin/vault_secrets.py` (fleet 13 → 14), is called by the existing commit
  gate on staged **content**, and a new `secret-scan` CI job sweeps the repository's full object
  database. **Why:** INV-7 — *"no secrets in any vault file"* — is Tier-0, sits in the Safety band, and
  was enforced by **nothing**: no hook, no linter, no CI job, no test. A credential pasted into any note
  committed cleanly. The spec meanwhile already *stated* the rule, and its sole scenario inspected the
  contents of two config files — a Factor-A check standing in for a Factor-B property, in the corpus
  that defines the invariant. Same defect class as ADR-0030's, one step worse: INV-11's floor at least
  existed as dead code; INV-7 had no artifact at all.
- **Two-tier detection, only one of which gates.** `HIGH` patterns are anchored vendor token formats
  (`ghp_` + 36, `AKIA` + 16, …) with a near-zero false-positive rate. `ADVISORY` patterns
  (`password = "…"`) are reported by the standalone tool and **never consulted by the hook** — a
  deliberate application of the barium-lunch investigation's RC-E (*over-denial is camouflage*): this
  corpus discusses credentials constantly, and a gate that fires on its own audit notes teaches its
  operator to bypass it.
- **Three properties that make the gate falsifiable rather than decorative.** Findings are **redacted**
  to a four-character prefix and a length (a scanner that echoes what it found violates INV-7 while
  enforcing it). The scanner **selftests before every scan** and refuses to report clean if its patterns
  cannot be shown to fire — the exit-3 control-gate pattern, reused. And the historical scan walks
  `cat-file --batch-all-objects`, so **unreachable** blobs from discarded commits and dropped rebases
  are in scope, where `git rev-list` cannot see them and a committed-then-"removed" credential survives.
- **Scoping asymmetries with the gate's INV-11 half, stated in the spec:** every file type (not just
  `.md`), modified files too (`--diff-filter=ACM`, not `AR`), and **never grandfathered** — a
  pre-existing non-conforming *name* is cosmetic debt, a pre-existing *credential* is an active
  compromise.
- `openspec/specs/access-control/spec.md` — **ADDED** Requirement *Secrets Prohibition Is Enforced at
  the Boundary* (5 scenarios). The existing prohibition Requirement is left intact, per ADR-0030's
  pattern. `tests/test_secret_scan.py` adds 13 cases weighted toward negative controls.

### Notes
- **Prophylactic, not remedial.** A Phase-0 sweep of both repositories' full object databases — 610 +
  889 blobs plus 548 working-tree files — found **zero** matches at either tier, with the instrument
  validated first against a control fixture carrying planted secrets in live, deleted, and unreachable
  states. Nothing has leaked.
- **Honest bound, carried in the spec so it cannot be dropped:** this detects *known formats*. A
  shapeless password, a split or encoded secret, or a novel vendor prefix passes. **A clean scan is not
  proof of absence** — custody discipline is the other half of INV-7 and is not delivered here.
- **A deployed vault gains nothing until the operator runs `render`** (operator-only by design,
  ADR-0022). The repo half is live at merge; the vault half is a deliberate human act.
- **INV-6 is now the only live Tier-0 invariant with no mechanism at all.**

## [0.1.34] - 2026-07-24

### Added
- **`tools/template-mirror.py` — a guarded repo→live mirror driver** (`add-template-mirror-driver`,
  conforming amendment, **no ADR**). The write-capable counterpart to `template-parity.py`: where
  parity DETECTS drift between the repo's `vault-template/` LOCKSTEP scaffold and a deployed vault,
  the driver FIXES it in the one direction governance allows — repo → live, one way, never the
  reverse, never a delete. It reuses the existing `template-sync-manifest.json` unmodified, computes
  its own diff (never an enumeration typed from memory), copies `MISSING-IN-LIVE`, overwrites
  `DIFFERS`, and REPORTS `MISSING-IN-TEMPLATE` without resolving it (a human decides). It ends by
  re-deriving parity and printing the same denominator'd tally, never a bare success word, and never
  `git add`/commits (that stays the operator's INV-2 step). The shared tree-walk/compare/tally logic
  is factored into `tools/template_sync.py`, which both tools import (one source of truth for "in
  sync"; `template-parity.py`'s output is byte-identical to before). Stdlib-only, offline, no LLM
  (INV-6). **Why:** CONTRIBUTING step 5 was prose — *"Mirror … (operator action)"* — with no vehicle,
  the exact gap F26 fell through when a hand-composed multi-arg `cp` wrapped in the operator's terminal
  and overwrote a repo file. A reviewed script invoked by one short line cannot wrap into a different,
  destructive command. INV-4/5 are unchanged — the operator still runs the mirror; only *how* changes.

## [0.1.33] - 2026-07-20

### Changed
- **The two operator-only fleet paths now fail legibly instead of with a bare traceback**
  (`fix-operator-only-path-diagnostics`, conforming amendment, **no ADR**). `vault-render.py render`
  and `vault_naming.py` (emit mode) write *only* into areas the Area Access Matrix withholds from the
  agent — all 13 `deploy_target`s (`~/bin/` out-of-vault, `99-Operations/hooks/`, `.claude/hooks/`) and
  `99-Operations/schemas/naming-rules.json` respectively. Both now catch `OSError` with
  `errno == EROFS`, print a message naming the path, stating the denial is **by design**, and directing
  the reader to run the step as the operator, then exit **4** (a new code reserved for "denied by
  design", distinguishable from a genuine fault at exit 1). **Any other `OSError` re-raises unchanged**
  — a dedicated test guards this with a real `EACCES`, because widening the catch would report a full
  disk or a permission fault as a governance decision. `reconcile` and `--check`/`--check-strict` exit
  above the amended blocks and are untouched, so drift detection and **the commit gate keep working**.
  **Why:** the live-vault exclusion inventory (P17) confirmed both denials are correct and deliberate —
  the operator chose to add *no* `excludedCommands` entries, keeping the trusted surface minimal — but a
  bare traceback carries no signal that a failure is intentional, so the reader debugs a deploy fault
  that does not exist. This gets strictly worse after the Stage-B strict flip, which removes the burn-in
  fallback. A self-explaining failure is the only documentation channel guaranteed to be open at the
  moment of confusion.
  **Deployment note:** the fix ships *inside the script that deploys it*, so it cannot self-deploy —
  the **operator** must run `render` after this mirrors to a live vault.

## [0.1.32] - 2026-07-19

### Changed
- **`10-Logbook/` is now agent-writable at both enforcement layers** (`open-logbook-write-scope`,
  **ADR-0033**): `./10-Logbook` leaves `sandbox.filesystem.denyWrite`, and no tool-layer `Edit(...)`
  rule replaces the one ADR-0032 removed. This is the **second deliberate widening of agent write
  scope** in the project's history, after ADR-0025 opened `20-Claims/` — recorded as a governed
  decision precisely because a withdrawn safety rail must never be inferable from a config diff.
  **Why:** after ADR-0032 the framework owns no artifact in the silo, and the rail was demonstrably
  what emptied it — agents were denied at both layers, leaving a human in Obsidian as the only
  possible author, and exactly **one** `daily:` commit exists in the project's history as a result.
  The silo becomes the working area for whatever external harness drives the effort cadence.
  **What survives, confirmed by the Gate-1 sweep rather than assumed:** INV-11 naming is still
  enforced twice (the commit-gate *and* `vault-lint.py`, which walks `10-Logbook/` directly), and
  `publish-manifest.json` still lists `10-Logbook/**` under `never_publish_examples` — **opening write
  scope does not open publication**. What is withdrawn is pre-action write prevention and content
  validation; no frontmatter schema governs the silo. `access-control` spec: 2 Requirements modified,
  +2 scenarios. All other protected areas unchanged.

## [0.1.31] - 2026-07-19

### Removed
- **The daily note and its close cycle** (`retire-daily-close-cycle`, **ADR-0032**): the
  `daily-note` / `daily-close` script pair and their deploy targets, the `Daily Close Lifecycle`
  Requirement, `vault_lib.is_closed()`, the `DISPOSITIONS` vocabulary, `daily-mold-blank.md`,
  `daily-close-runbook.md`, the `daily` note type, and four dead `.claude/settings.json` references.
  ADR-0028 retired the cadence but kept the daily; an audit found the surface in the kanban's
  condition by a wider margin — **12 dailies in 32 days then 0 in 13** (a span covering 70 commits,
  v0.1.24→v0.1.30 and five ADRs), the last two empty, **zero inbound content citations**, and
  `2026-06-29.md` stating it was *"reconstructed from git"*: git was already the real log. Nothing
  automated could ever fill it — the harness denied agents the path at both the tool and kernel
  layers, leaving one `daily:` commit in the project's entire history. The framework is a refinery
  with a defined intake, not an end-to-end operating system; `10-Logbook/` is retained as a working
  area. **Fleet 15 → 13 scripts; molds 4 → 3.** Existing dailies and their `## Close` manifests are
  untouched provenance. The retired cycle's one durable asset — the typed-slot enforcement pattern,
  the project's only working instance of control-flow inversion — was extracted to the
  `determinism-failure-modes-claude` Site before deletion.
  Specs: `maintenance` (1 removed, 3 modified), `access-control` (1 modified), `vault-structure`
  (2 modified — CONST-04's ordering **retained**, its daily-based rationale restated as a
  reservation). **Not done here:** `./10-Logbook` remains in the sandbox `denyWrite` list; opening it
  is a write-scope widening and its own governed decision.

### Added
- **Standalone-vault lint** (F15): a CI job failing the build if `vault-template/` references a
  framework-repo-only *path* (`openspec/`, `tools/ship-release|pr-state|template-parity`, or an
  absolute `Documents/repo/` path). Naming the origin repo in prose stays legal; depending on its
  paths does not. Caught and fixed three live leaks on introduction — two in
  `session-bootstrap-loader.md`, one in `00-Docs/README.md`.

## [0.1.30] - 2026-07-18

### Added
- **GitHub ceremony tools** (`add-ship-ceremony-tools`): two repo-owned, stdlib-only tools that move
  the documented F10/F21 GitHub hazards out of agent recall and into guard clauses at the point of
  action (failure-modes fix program, item 3). `tools/ship-release.py` walks the tag→Release ceremony
  as a guarded, re-entrant state machine — merge-ancestor proof before any tag exists, CHANGELOG-entry
  proof, stale-tag refusals that name the true cause with both commits, per-layer post-mutation
  verification, and a closing tag↔Release parity tally with denominators — and **never executes an
  outward mutation itself**: it emits each `git push` / `gh release create` for a visible run through
  the INV-14 ASK guard. `tools/pr-state.py` reports PR state with the answering layer named on every
  line (pr-state-machine / branch / check-aggregation / workflow-run / event-payload), prints
  `LAYERS-DISAGREE:` as a signal instead of confusion, and flags the deleted-base stacked-PR hazard.
  `maintenance` spec: +2 Requirements. Conforming amendment, no ADR (template-parity precedent).

### Fixed
- **`ship-release.py` reads `isLatest` from the only surface that carries it** (pre-tag fix, same
  version): live `gh release view --json` rejects `isLatest` (it exists on `release list` only) —
  found by dogfooding the driver on this very release, where it BLOCKED cleanly before any
  mutation. The test stub now mirrors the live field split so the regression stays covered.

## [0.1.29] - 2026-07-18

### Changed
- **Ceremony enumeration and verification deliverables are now command transcripts**
  (`require-transcript-verification`, ADR-0031): Gate 1's blast radius must be a pasted,
  re-runnable command transcript with full untruncated output and per-hit disposition; Gate 3
  results are evidenced by tally/diff/exit status — shell-printed verdict strings (`echo "ok"`)
  no longer count; Gate 4's second review re-runs the transcript and diffs. The
  `constitution-override` template gains a mandatory transcript block + two checkboxes;
  `AGENTS.md` generalizes the rule to all governed work and adds the delivery-channel rule
  (commands name actor + channel; long content travels as a file, never an interactive paste).
  `agent-integration` spec: +1 Requirement ("Verification Deliverables Are Transcripts").

## [0.1.28] - 2026-07-18

### Fixed
- **Refine executor catalog linking is now idempotent** (`fix-append-idempotent-catalog-link`):
  `bank-execute` appended `- [[<stem>]]` to every `index_links` target unconditionally, so an
  `append` to an already-catalogued note duplicated its Catalog bullet (and an empty `index_links`
  defaulted to the absent `pending-catalog` index and hard-rejected) — there was no clean way to
  append to an existing note. The bank-loop now links only if the index does not already carry the
  bullet: `append` extends a note without polluting its index, a genuinely new index is still linked,
  and `create` is unchanged. `maintenance` spec: +1 Requirement ("Catalog Linking Is Idempotent").

## [0.1.27] - 2026-07-18

### Added
- **Template–live parity check** (`add-template-parity-check`): a repo-owned, stdlib-only,
  detection-only tool (`tools/template-parity.py` + `tools/template-sync-manifest.json`) that verifies
  a deployed vault's LOCKSTEP scaffold (`99-Operations/scripts/`, `99-Operations/schemas/`) is
  byte-identical to what `vault-template/` ships — the mirror-completeness axis `reconcile` never
  covered (`reconcile` is note → `~/bin`; this is template → live). Byte-exact and bidirectional per
  lockstep prefix, with a manifest `exclude` for vault-generated artifacts (`naming-rules.json`); it
  prints the count of files checked and never auto-fixes (INV-3 posture). Motivated by three unfinished
  applies caught by hand on 2026-07-17. Repo-only (the deployed vault stays standalone, F15); not a CI
  gate (CI has no live vault). `maintenance` spec: +1 Requirement.

## [0.1.26] - 2026-07-17

### Changed
- **The ≥3-token naming floor is now enforced, not merely documented** (`enforce-naming-token-floor`,
  ADR-0030, completing **ADR-0015**): `vault_naming.py` gains `--check-strict FILENAME` (exemption-aware:
  `is_exempt` → `validate_name` → `slug_pattern` → `has_min_hyphen_tokens`); the commit gate calls it on
  the basename; the refine executor pre-flights the floor **before any write**; the linter's staged
  `elif` is switched on and the floor extends to Treasury stems and effort folder slugs. `--check STEM`
  keeps its contract, so no existing caller moves implicitly. `min_hyphen_tokens: 3` and `slug_pattern`
  are **unchanged** — this adds no rule, it switches on ADR-0015's.

  ADR-0015 deferred enforcement in June "gated on full conformance" and named it *"a separate later
  change"* — **which was never written**. Until now the whole pending item was one ADR sentence and three
  commented-out lines; **`has_min_hyphen_tokens` had no production caller at all**, so the rule was
  enforced nowhere. The precondition is met: **118 live `.md`, 15 exempt, 103 subject, 0 failing**. Every
  family conformed by hand exactly as ADR-0015 predicted, and nobody flipped the switch, because the
  thing that would have noticed was a comment.

  **Live constraint:** newly *created* content names must carry ≥3 kebab tokens. No existing artifact is
  affected — 0 offenders, and the gate is `--diff-filter=AR` regardless.

### Fixed
- **Refine executor could be stranded half-applied** (ADR-0030, found by two *pre-existing* tests failing
  once the gate went live): the executor writes `40-Treasury/<stem>.md` and *then* commits, so a sub-3
  stem passing pre-flight would be written and then blocked at commit. Its pre-flight now rejects the
  floor violation at the boundary, keeping *"reject at the boundary, no Treasury write"* true.

## [0.1.25] - 2026-07-17

### Added
- **`PILLARS` tokens are validated as kebab slugs** (`enforce-pillar-slug-tokens`, ADR-0029): the linter
  validates the vocabulary at the point it resolves, before the frontmatter loop, using the existing
  `is_valid_slug()`. A malformed vocabulary exits immediately rather than cascading into a per-note
  pile-up. The ≥3-token floor is deliberately **not** applied — it governs `.md` stems, not name
  fragments, so `mental` stays valid.

### Changed
- **Pillar naming rule stated and demonstrated** (ADR-0029): each pillar is **one** lowercase kebab slug;
  whitespace separates. A multi-word pillar is one hyphenated token (`mental-health`), never two words.
  `config.defaults.env`, `config.env.example`, and `docs/USING-THIS-TEMPLATE.md` now show the
  two-words-vs-one-token contrast explicitly, label the example default as **six** pillars, and tell
  adopters to **pin `PILLARS` in their private `config.env`** — unpinned, they inherit the framework's
  *example* default and a public-repo edit would silently re-pillar their vault. **The pillar set did not
  change** (value verified byte-identical).

  Origin: an agent read the whitespace-delimited value during session bootstrap and reported six pillars
  as five, welding `mental` and `health` into one. `vocab()` was never wrong — the format let a *reader*
  invent a boundary the format forbids, and the prohibition lived in a comment enforced by nothing. The
  `;`-delimiter fix was rejected: a pillar is interpolated into `<pillar>-domain-index.md`, so literal
  spaces would need a slug transform in every consumer plus a permanent display/slug identity split.
  Demarcation comes from making the **token** self-delimiting instead.

  **Sacrifice:** literal spaces in pillar names are permanently unavailable. Display forms alias at the
  link — `[[mental-health-domain-index|Mental Health]]`, the pattern `home-master-index.md` already uses.

## [0.1.24] - 2026-07-17

### Removed
- **Effort projections retired** (`retire-effort-projections`, ADR-0028): `kanban-render-script`
  (`~/bin/vault-kanban-render.py`, `10-Logbook/kanban.md`) and `dig-rollover-script`
  (`~/bin/vault-rollover.py`, daily `## Carry-over`) leave the fleet — 17 scripts → 15. Neither had a
  consumer: the board was rendered 4 times in 32 days and read 0 (not Obsidian-Kanban format, no
  plugins installed); the carry-over wrote 12 unchanging links a day until it read as noise. The vault
  does not project effort state — that lens is delegated to the harness.

### Changed
- **Cadence retracted from the framework** (ADR-0028): no script declares `runtime: cron` or a
  `schedule:`; `cron`/`schedule` leave `note-frontmatter-schema.md`; `docs/USING-THIS-TEMPLATE.md`
  Step 5 no longer instructs installing a crontab. The vault is a **self-priming pump, not a driven
  one** — `render` deploys code and never installed schedules, so the declared cadence was a
  decoration nothing honoured. Scripts run bare, on demand, by an actor who chose to run them.
- `maintenance` spec: MODIFIED *Script Inventory* (+ a scenario recording that a retirement must
  delete its deploy target explicitly — `reconcile` iterates notes, so an orphaned `~/bin` artifact is
  invisible to drift detection), *One Mutation One Commit*, *Daily Close Lifecycle*, *Shared Fleet
  Plumbing* — re-exemplified with surviving fleet members; no rule weakened.
- `access-control` spec: MODIFIED *OS/Harness-Enforced Agent Write Scope* — `10-Logbook/kanban.md`
  drops from the structured-tool deny enumeration (the whole of `10-Logbook/` remains denied).

## [0.1.23] - 2026-07-14

### Added
- **GitHub Release object per version tag** (change `release-object-per-tag`; conforming override,
  additive — Gate-4 sign-off recorded in the proposal). The ship ceremony now documents and mandates
  tag → `gh release create --verify-tag --latest` → `gh release view` parity check → mirror, so a tag
  can never again strand without its Release (the drift that pinned the Releases page at v0.1.13 while
  tags ran to v0.1.22). Documented in `CONTRIBUTING.md` and `AGENTS.md`.

### Changed
- **INV-14 outbound guard made target-aware and gap-closed** (ADR-0027; conforming — the Safety band is
  tightened, nothing relaxed). `outbound-publish-guard.py` now judges "targets the vault" by the
  command's *effective target* (`cd` / `git -C` / `gh -R`), not the shell's reported cwd — removing the
  false HARD-DENY that blocked every legitimate publish to the sibling framework repo from a
  vault-rooted session. It also raises the ASK **hard stop** on **any** non-denied outward op (now
  including a plain `git push`, and `git -C <path> push`), closing a gap where a push could defer
  unprompted. Vault-outward commands are still hard-denied. Mirrored byte-identically across the hook's
  three homes (repo, vault-template, literate meta-script note).

## [0.1.22] - 2026-07-14

### Added
- **Scope-review CI gate** (change `add-overreach-scope-review`; conforming override, additive —
  Gate-4 sign-off recorded in the proposal). Every PR now declares its authorized surface as a
  fenced ```scope block (for ceremony changes: the Gate-1 blast radius, machine-checked); a new
  `scope-review` CI job compares the diff against the declaration deterministically — offline, no
  LLM in the decision path — and fails on any undeclared file (medium), workflow env var, or
  manifest dependency (high). Phase-A burn-in (report-only); the blocking flip follows as its own
  change. The gate is **self-contained**: two stdlib-only Python scripts, zero runtime
  dependencies (a supply-chain audit rejected the initial `npx` form — a 113-package floating
  transitive tree resolved per run).
  *Concept credit:* the declared-scope gate pattern, scope-JSON schema, and severity taxonomy
  were learned from **OverReach** ([Naveja00/OverReach](https://github.com/Naveja00/OverReach),
  MIT) — reimplemented clean-room with stricter matching; no code copied.
  *Provenance hat-tip:* from the 2026-07-14 competitive landscape analysis, which also evaluated
  (with thanks): BRACE (CC BY 4.0 — its self-assessment checklist was run against the live
  deployment), statewright, microsoft/agent-governance-toolkit, eqtylab/cupcake,
  falcosecurity/prempti, ThumbGate, mori, elephantasm-core, traceguard, Terminalcontrol
  (FleetView), and nousresearch/hermes-agent.

## [0.1.21] - 2026-07-13

### Changed
- **Relocated the constitution-override ceremony template out of the OpenSpec change tree and adopted
  OpenSpec 1.6.0** (change `relocate-override-template-openspec-16`; ADR-0026; `constitution-override`,
  procedural — touches the `protects:`-tagged `maintenance` spec and pointer text in `constitution.md`,
  no Tier-0/1 element overridden). OpenSpec 1.6.0's stricter default discovery enumerated the blank
  template at `openspec/changes/templates/constitution-override/proposal.md` as a delta-less change and
  failed it; the template now lives at `openspec/templates/constitution-override/proposal.md` (outside
  the scanned `changes/`/`specs/` tree), with all 7 references and the CI `test -f` guard repointed in
  lockstep. The `@fission-ai/openspec` pin advances `1.4.1 → 1.6.0` (supersedes Dependabot #18). A new
  `maintenance` requirement codifies that governance tooling is version-pinned and ceremony templates
  live outside the change tree, so this cannot recur. The ceremony and every constitutional principle are
  unchanged.

## [0.1.20] - 2026-07-13

### Changed
- **Agent may capture directly into `20-Claims/`** (change `permit-agent-claims-capture`; ADR-0025;
  `constitution-override` touching `access-control`). The Area Access Matrix Agent cell for `20-Claims/`
  moves from `—` to `RW` and footnote 2 is reworded: the agent may create Claim notes directly (operator
  efficiency / comfort-of-ride decision from the ADR-0022 Gate 4). The `_refine-approved/` Treasury gate
  is untouched (Agent `—`), so promotion into `40-Treasury/` stays human-gated (INV-4). `20-Claims/` is
  Layer-2 Workings (CONST-02); no Tier-0 invariant is weakened. Also: README ADR count corrected
  (18 -> 25) and a CI guard added so the README ADR count must equal the actual `openspec/adr/` file count.

## [0.1.19] - 2026-07-13

### Added
- **OS/harness-enforced agent write scope — burn-in stage** (change: `os-enforced-agent-write-scope` —
  ADR-0022; enforcement for INV-4/INV-5, no new invariant). `vault-template/.claude/settings.json` now
  ships pre-action enforcement of the Area Access Matrix's Agent column: an OS sandbox
  (bubblewrap/Seatbelt) denies agent shell writes — all child processes, all interpreters — to
  `40-Treasury/ 99-Operations/ .claude/ 96-Runbooks/ 97-Molds/ 10-Logbook/`, and `permissions.deny`
  Edit-rules block structured-tool writes to the same scope plus script-owned Logbook artifacts
  (`Daily/*.md`, `kanban.md`); the disposition sidecar (`Daily/*.resolutions.json`) stays writable by
  pattern disjointness. Rendered scripts remain drivable via bare exact invocations
  (`sandbox.excludedCommands`). Ships burn-in only — the strict flip (`failIfUnavailable`,
  `allowUnsandboxedCommands: false`) is a deliberate later stage. `access-control` ADDED Requirement;
  AGENTS.md drive contract; USING-THIS-TEMPLATE Step 4c.

## [0.1.18] - 2026-07-13

### Added
- **Refine executor: empty `index_links` defaults to a pending-catalog holding index** (change
  `bank-execute-pending-catalog`; ADR-0024; `constitution-override` touching `maintenance`). An
  explicit empty `index_links` is no longer a silent orphan nor a hard block — the executor links the
  banked note into `40-Treasury/Catalog/pending-catalog-index.md` (a new template Catalog index), so
  every banked note stays reachable via ≥1 Catalog index (INV-12) and un-cataloged notes form a
  visible "awaiting-catalog" queue. Missing / non-list `index_links` remains a schema rejection.
  Surfaced by the Crucible prove-out dig (Qwen dry-run #10). `maintenance`: MODIFIED pre-flight requirement.

## [0.1.17] - 2026-07-06

### Added
- **Runbooks + declared floors** (change `runbooks-and-floors`; fleet-review B6/B7).
  New `render-reconcile-runbook` (the INV-3 deploy/drift loop) and `refine-pipeline-runbook`
  (detect → propose → human gate → atomic bank, with B4 reject semantics). `maintenance` gains
  "Platform and Dependency Floors": Python ≥ 3.12, `python-frontmatter` as the sole third-party
  dependency (hook paths stdlib-only), Linux/POSIX floor — new dependencies become governed
  decisions. `USING-THIS-TEMPLATE` documents the floors.
- **Render fence lint + publish-guard inventory** (change `reconcile-fence-lint-guard-inventory`;
  fleet-review B5/R8). `vault-render.py` refuses a note with ≠1 `python|bash` fence (VIOLATION,
  exit 1 — the extractor no longer silently takes the first); `outbound-publish-guard.py` (the
  INV-14 PreToolUse rail) gains a literate source note (`runtime: harness hook`, enum extended)
  so `reconcile` finally guards it against drift.

### Changed
- **Shell pair conformance** (change `shell-pair-conformance`). `vault-slag.sh`/`vault-dump.sh`
  join the fleet contract: env-free root resolution (inline bash copy), INV-11 slug validation
  via `vault_naming.py --check`, usage/source/destination gates (exit 1/3), and pathspec-scoped
  commits of exactly the moved effort — the last `add -A` sweeps in the fleet are gone.

### Fixed
- **Fleet hygiene bundle** (change `fleet-hygiene-bundle`). `runtime:` enum gains `git hook`
  (commit-gate note aligned; rendered hook unchanged); close-lint `--check` now validates every
  manifest disposition against `DISPOSITIONS` (typos FAIL — the old guard was near-tautological,
  R7); bootstrap-runbook clean-ops line updated for the env-free hook/fleet reality (template;
  live copy operator-applied).

### Added
- **Refine executor pre-flight + batch isolation** (change `bank-execute-pre-flight`; fleet-review
  B4). The sole automated Treasury writer now validates every proposal whole before any write:
  schema, path containment (target in `40-Treasury/`, links in `40-Treasury/Catalog/`), INV-11
  stem, **create never overwrites (INV-9)**, append-target existence, `GRADES`/`PILLARS` vocab,
  link-target existence. Rejections print all reasons, write nothing, and don't stop the batch;
  any reject exits 1. `maintenance`: ADDED Requirement.

### Changed
- **Commit ownership + close de-sweep** (change `commit-ownership-de-sweep`; operator decision
  B3-(a)). Every mutation now owns its scoped commit: daily-note commits the note it creates
  (`daily: opened <date>`); the refine executor banks each proposal atomically (`bank: <stem>` —
  note + Catalog links + consumed proposal); close-day replaces its load-bearing `git add -A`
  sweep with a scoped seal (daily + consumed sidecar) — the last Python sweep is gone, and a
  close never captures unrelated working-tree content. `commit_paths` tolerates consumed
  (deleted, never-tracked) paths. INV-2 requirement gains the ownership clause + scenarios.
- **Wave-2 `vault_lib` adoption + `commit_paths` hardening** (change `wave-2-vault-lib-adoption`;
  extends ADR-0023). `commit_paths` now no-ops cleanly on unchanged state (fixes the kanban
  same-day empty-index crash fleet-wide) and commits with an explicit pathspec so unrelated
  pre-staged content stays staged (closes the F3/F4/F5 sweep class structurally). Adopted in
  `knowledge-lint`, `treasury-orphan`, `tailings-reprospect`, `ore-detect`, and the
  `naming-rules` mirror-writer (lazy, `__main__`-only; `--check`/hook path dependency-free) —
  the full Python fleet now runs bare with no pre-sourced environment. Shell pair
  (`site-slag`/`spoil-dump`) deferred to the B3-era change.

### Fixed
- **Commit-gate hook is now environment-free** (change `fix-commit-gate-env-guard`). Deleted the
  vestigial `VAULT_ROOT` guard (set but never used) that broke bare-exact drive-path commits at
  their final step — the last blocker found by the Phase-1a live acceptance. INV-11 enforcement
  unchanged. `push-guard` audited: already self-locates, no change.

---

## [0.1.16] - 2026-07-05

Shared fleet plumbing `vault_lib` + drive-path adoption. (change: `add-shared-vault-lib` — ADR-0023)

### Added
- **Shared fleet plumbing `vault_lib`** (ADR-0023 Accepted; change `add-shared-vault-lib` —
  Gate 4 signed 2026-07-05).
  New `vault-lib-script.md` → `~/bin/vault_lib.py`: vault-root resolution (env-first, config-marker
  walk — makes the ADR-0022 bare-exact drive invocations work with no pre-sourced environment,
  closing burn-in probe P5), config vocabulary precedence (process env > `config.env` >
  `config.defaults.env` > code default), YAML-typed `is_closed`, scoped `commit_paths` (INV-2
  shape), fleet exit-code contract (`0` ok · `1` violation · `2` needs-input · `3` gate-blocked).
  `maintenance` spec: ADDED Requirement + Script Inventory row.

### Changed
- Drive-path scripts adopt `vault_lib` (`daily-close`, `daily-note`, `dig-rollover`,
  `kanban-render`, `bank-execute`; `render-reconcile` carries an inline bootstrap copy).
  Behavioral deltas (enumerated in ADR-0023): rollover and close-day gate refusals now exit 3
  (were 0 / 1); `closed: false` uniformly reads as open; kanban grades/statuses come from the
  config SSOT; `DISPOSITIONS` gains a config-file source below the environment.

---

## [0.1.15] - 2026-07-02

Publication boundary (path-level default-deny manifest) + special-file naming exemptions. (changes: `publication-boundary-manifest` — ADR-0020; `naming-special-file-exemptions` — ADR-0021)

### Added
- **Publication boundary — path-level default-deny manifest** (ADR-0020; extends ADR-0018/INV-14). `99-Operations/schemas/publish-manifest.json` is a default-deny allowlist of publishable framework paths; `push-guard-script` refuses a push to a `PUBLIC_REMOTE_ALLOWLIST` remote whose diff touches any non-allowlisted (private) path, path-by-path. Layers on the existing remote-level INV-14 gate; both allowlists empty by default. `access-control` (ADDED Requirement) + `maintenance` (MODIFIED Script Inventory) specs.
- **Special-file naming exemptions** (ADR-0021; extends ADR-0015/INV-11). `naming-rules` gains `exempt_names` / `exempt_globs` (basename-matched) so tool-mandated / convention filenames (`README.md`, `CLAUDE.md`, dailies, `*.example`, …) are skipped by the kebab / ≥3-token rules; `is_exempt` is honored by the linter now (mechanical rejection still deferred per ADR-0015). `docs/naming-exemptions-rationale.md` documents each by dependency class.
- **Framework/instance config split** — `99-Operations/config.defaults.env` (public defaults, sourced first) + `config.env.example` (stub); the live `config.env` is now a gitignored private instance. New `PUBLIC_REMOTE_ALLOWLIST` guard key.

### Changed
- `docs/obsidian.md` — prominent "turn OFF *Automatically update internal links*" warning (governed renames conflict with auto-relinking; INV-3).
- `docs/USING-THIS-TEMPLATE.md` — config defaults/instance setup (`cp config.env.example config.env`) + `PUBLIC_REMOTE_ALLOWLIST` / publish-manifest.
- `vault-template/` mirror of the push-guard path-gate, the two naming meta-scripts, `publish-manifest.json`, and the config split.

### Fixed
- Config-split blast radius: `.github/scripts/validate-scripts.sh` (sandbox now instantiates `config.env` from `config.env.example`) and `.github/workflows/ci.yml` `vocabulary-lint` (reads `config.defaults.env`) — both would otherwise break on the removed `config.env`.

---

## [0.1.14] - 2026-06-30

`98-Warehouse` re-chartered as the **reference stockroom**. (change: `warehouse-reference-stockroom`; ADR-0019)

### Added
- **`98-Warehouse/` reference stockroom** — retained source/reference material the operation draws on repeatedly (binaries *and* digitized references), organized into media shelves `Books/`, `Music/`, `Art/`, `Pictures/`, `Audio/`. Re-classified from generic "binary attachments / infrastructure" in `vault-structure` (*Three-Layer Model* + *Folder Structure*) and `access-control` (*Area Access Matrix*); both retain `protects:`.
- **Shelf-naming scope scenario** — Warehouse shelf *folders* take human-friendly names under the universal path-component rule only; the kebab-case / ≥3-token convention is scoped to `.md` stems and `30-Sites/`/`70-Tailings/` effort folders + `40-Treasury/` stems, so it does not reach them.
- `vault-template/98-Warehouse/{Books,Music,Art,Pictures,Audio}/.gitkeep`.

### Changed
- `vault-template/00-Docs/README.md` — `98-Warehouse/` charter line.

### Fixed
- Completed ADR-0016 propagation: `vault-structure` spec + `vault-template/99-Operations/schemas/refine-prompt-contract.md` `index_links` example `<pillar>-index.md` → `<pillar>-domain-index.md` (the pre-v0.1.9 straggler; `agent-integration` was already correct).

---

## [0.1.13] - 2026-06-29

Private by default — **INV-14** (Tier-0) + the outbound publish guard. (change: `private-by-default-publish-guard`; ADR-0018)

### Added
- **`INV-14` — private by default; no unbid publication** (Tier-0, Safety band; appended per ADR-0008, INV-1–13 unchanged). A deployed vault never publishes outward: no automated actor may push/mirror vault content except to an operator-allowlisted remote, and public publication requires deliberate human confirmation — never an agent's unprompted suggestion. Carried by the `access-control` spec; defined in `project.md`; listed Tier-0 in `constitution.md`.
- **`push-guard-script`** → `99-Operations/hooks/pre-push`: deny-by-default, `PUSH_ALLOWLIST`-gated (deterministic, INV-6).
- **Portable Claude Code `PreToolUse` guard** (`.claude/`, repo + vault-template): hard-denies vault-outward commands; loud ASK before any public repo creation / distribution-hub publish.
- **`config.env`** keys `VAULT_PUBLISH_GUARD`, `PUSH_ALLOWLIST` (empty = deny all pushes).

### Changed
- Docs: README ("Private by default" + counts → 18 ADRs / 14 invariants), `AGENTS.md`, `docs/USING-THIS-TEMPLATE.md` (Step 4b).

### Fixed
- `config.env` comment `close-daily` → `daily-close` (v0.1.12 straggler; non-`.md`, missed by the earlier `.md`-scoped grep).

**Honest limit (ADR-0018):** Tier-0 guarantees *safe-by-default + governed + loud-to-remove*, not a physical impossibility — git hooks don't clone, `--no-verify` bypasses, an owner can opt out. OS-level egress control is deferred.

---

## [0.1.12] - 2026-06-29

Runbook naming brought to the ≥3-token convention; the daily-close / provenance-seal vocabulary
unified. Plus a moc→index residual sweep. (change: `runbook-naming-3token`; ADR-0017)

### Changed
- **Runbooks → ≥3-token `silo-section-descriptor`** (constitution-override, conforming amendment;
  ADR-0017): `close-daily.md` → `daily-close-runbook.md`, `seal-provenance.md` →
  `provenance-seal-runbook.md` (last grandfathered system-artifact family). The ritual vocabulary is
  unified on one stem family per ritual: `close-daily` → `daily-close`, `seal-provenance` →
  `provenance-seal` — coherent with the already-renamed `daily-close-script`. `session-bootstrap-loader`
  unchanged (already conforms). Spec deltas: `maintenance` (Daily Close Lifecycle), `vault-structure`
  (Folder Structure + Frontmatter Schemas). References repointed across AGENTS.md, CLAUDE.md, scripts,
  and schema. No principle weakened; INV-11 reinforced.
- **Upgrade (forks/vaults):** `git mv` the 2 runbook files + repoint references; no re-render
  (runbooks have no deploy target).

### Fixed
- **moc→index residual cleanup** — purged stale "MOC" wording left over from the `moc → index`
  rename (v0.1.6 / ADR-0013) in four non-protected vault-template files: `bank-execute-script`
  prose, `treasury-orphan-script` (`moc_text` → `index_text`), `home-master-index` heading
  ("Pillar MOCs" → "Pillar indexes"), and `config.env` comment. Terminology-only; no behavior change.

---

## [0.1.11] - 2026-06-29

`/vmm-session-rebooted` slash command — explicit cold-start prime trigger.

### Added
- **`/vmm-session-rebooted`** Claude Code command (`.claude/commands/`, repo + vault-template) — a thin
  adapter that invokes the `session-bootstrap-loader` runbook (env + the four gates + JIT pointers).
  The most reliable prime trigger (it makes *engaging* the bootstrap the agent's explicit task). No
  spec change; points at the runbook SSOT (no duplication).

---

## [0.1.10] - 2026-06-29

Session bootstrap loader — the cold-start prime mechanism (minimum bootstrap, maximum confidence).

### Added
- **`96-Runbooks/session-bootstrap-loader`** runbook (harness-agnostic SSOT): at session start, source
  env, engage the four gates (governance-first · re-read-before-acting · autonomy-bans · clean-ops),
  and know the just-in-time pointers (the `llm-context-reboot` load-list, the deferred-not-built list,
  other runbooks, the memories). A Claude Code **SessionStart hook** (`.claude/settings.json`, in-repo)
  surfaces it automatically; `AGENTS.md` + `CLAUDE.md` point at it. No spec change (conforms to the
  existing Runbook-Format).

---

## [0.1.9] - 2026-06-29

System-artifact naming (Informed-Upheaval Protocol, conforming amendment) — scripts, schemas, and Catalog indexes brought to the `silo-section-descriptor` convention.

### Changed
- **Scripts** → `<domain>-<action>-script` (`.md` notes only; deploy targets unchanged — `.py` rename deferred; canonical mining verbs): e.g. `close-daily`→`daily-close-script`, `dump`→`spoil-dump-script`, `refine-execute`→`bank-execute-script`, `pre-commit`→`commit-gate-script` (deployed hook stays `pre-commit`).
- **Schemas** → `note-frontmatter-schema`, `runbook-format-schema`, `refine-prompt-contract`.
- **Catalog indexes** → `<pillar>-domain-index` + `home-master-index` (the scope token anticipates future sub-sector indexes).
- Specs synced: `maintenance`, `vault-structure`, `agent-integration`. See ADR-0016.

---

## [0.1.8] - 2026-06-28

Token-minimum naming (Informed-Upheaval Protocol, conforming amendment) — the ≥3-token naming rule, codified as convention.

### Added
- **Token-Minimum Naming requirement** in `naming-rules`: every `.md` stem carries **≥3 hyphen-tokens
  — the floor, not the ceiling** (use *more* where the extra tokens add human-meaningful specificity).
  System-artifact families use `silo-section-descriptor` (silo first); content stems are ≥3-token
  slugs; dailies exempt. Existing sub-3 names grandfathered; **mechanical enforcement is deferred** to
  a later change (after the families conform). Agent guidance noted in `AGENTS.md`. See ADR-0015.

---

## [0.1.7] - 2026-06-27

Mold naming (Informed-Upheaval Protocol, conforming amendment) — self-identifying molds.

### Changed
- **Molds → `<note-type>-mold-blank.md`** — the four `97-Molds/` templates (`daily`, `effort`,
  `index`, `knowledge`) are renamed on the `silo-section-descriptor` convention so each mold is
  self-identifying in any flat / search / migrated view, and `index` no longer collides with the
  Catalog `<pillar>-index.md` notes. The `daily-note` script's mold path and the docs are repointed;
  the `vault-structure` Folder Structure listing is updated. No principle weakened (CONST-01 /
  INV-11 reinforced). See ADR-0014.

---

## [0.1.6] - 2026-06-19

Naming & identity (Informed-Upheaval Protocol, conforming amendment) — intuitive names + self-identifying artifacts.

### Changed
- **`moc → index`** — Catalog overview notes are now `<pillar>-index.md` (`type: index`); the mold,
  the `index_links` proposal field, and CONST-05's label "(MOCs)" → "(indexes)" follow. "MOC" (Map
  of Content) was opaque PKM jargon; "index" is self-teaching. The *principle* (domain via metadata
  + Catalog, never folders) is unchanged.
- **`_effort → <slug>/<slug>.md`** — a Site/Tailings/Spoil effort note is now the **folder-note**
  (stem == folder), self-identifying in any flat view (graph/search/migration) instead of an
  anonymous `_effort.md`. Maintenance scripts locate it as "the file whose stem equals its folder."
  See ADR-0013.

### Migration (existing forks/vaults)
- `git mv 40-Treasury/Catalog/<pillar>-moc.md → -index.md` (+ `home`); `git mv 30-Sites/<slug>/_effort.md → <slug>/<slug>.md`
  (and Tailings/Spoil); repoint wikilinks (`/_effort|` → `/<slug>|`, `-moc` → `-index`); re-render scripts.

### Process
- Constitution-override `naming-and-identity` (CONST-05 label, Tier 1), **authorized** by Keith Nielsen; ADR-0013.

---

## [0.1.5] - 2026-06-17

Spec-as-code runbooks + the daily close lifecycle (Informed-Upheaval Protocol, conforming amendment).

### Added
- **`96-Runbooks/` band** — operational procedures as harness-agnostic *spec-as-code* (schema:
  `99-Operations/schemas/runbook.md`; CI `runbook-lint`). Two charter runbooks: **`seal-provenance`**
  (forensic sealing) and **`close-daily`** (daily disposition sweep).
- **Daily close lifecycle** — `vault-close-day.py` assigns every daily item a disposition from a
  controlled vocabulary (`DISPOSITIONS`), writes an **append-only `## Close` manifest**, and sets
  `closed:`. Invariants: append-only, total-disposition, strict-order close, gated advance (capture
  is never gated). Deterministic (INV-6); AI invoked only at `unknown/other`. See ADR-0011, ADR-0012.
- Daily mold `closed:` field; `rollover` gated on the prior close; `daily-note` capture-home
  `⚠ BLOCKED` banner.
- `AGENTS.md` runbook pointer + agent operating notes; `CLAUDE.md` adapter.

### Changed
- `vault-structure` Folder Structure adds `96-Runbooks/` (reserved band `90–96 → 90–95`); CONST-04/02 upheld.
- `maintenance` spec: **Runbook Format** + **Daily Close Lifecycle** requirements.

### Process
- Constitution-override `spec-as-code-runbooks` (conforming amendment, Tier 1), **authorized** by
  Keith Nielsen; ADR-0011, ADR-0012.

---

## [0.1.4] - 2026-06-15

Lifecycle vocabulary refinement (Informed-Upheaval Protocol, CONST-01) + the project rename.

### Changed
- **Retired `prospect` as a Site status.** Prospecting is the *upstream, human* act that
  discovers Claims from the world — it is not a Site state. Sites are born at `dig`; the
  effort status set is now `dig | ore | slagged`. Updated `EFFORT_STATUSES`, the effort
  mold default, the kanban columns, the frontmatter schema, and the `value-pipeline` spec.
- **Locked the transition verbs:** `dig` (Claim→Site), `slag` (Site→Tailings),
  **`dump`** (Site→Spoil, renamed from `dispose` → `vault-dump.sh`), `redig`
  (Tailings→Site), `refine` (ore→bullion), **`bank`** (the human gate that authorizes
  bullion into the Treasury; state `authorized`). `reprospect` reclassified as the lone
  automatable read-only survey.
- New **Lifecycle Vocabulary** table in `docs/glossary.md`; CONST-01 chain updated to
  `Claim → Dig → Ore → Sort → Refine → Bank → Treasury → Polish`. See ADR-0010.
- **Renamed:** GitHub repo `memory-mining` → **`2026-AI-Value-Memory-Mining`** (year-prefixed
  Title-Kebab); internal project identity **`value-memory-mining`** (lower-kebab).

### Migration (existing forks/vaults)
- Drop `prospect` from `EFFORT_STATUSES` and set the effort mold default to `dig`;
  `git mv ~/bin/vault-dispose.sh` usage → `vault-dump.sh` (re-`render`).

### Process
- Constitution-override change `lifecycle-vocabulary` (CONST-01, Tier 1), **authorized**
  by Keith Nielsen; ADR-0010. CONST-01's principle is sharpened, not sacrificed.

---

## [0.1.3] - 2026-06-15

Constitutional correction (Informed-Upheaval Protocol) — Layer-2 folder ordering.

### Changed
- **Swapped `10-Claims` ↔ `20-Logbook`** so the daily logs sort to the top of the
  file explorer, conforming to CONST-04 ("daily logs at top"). The layout previously
  contradicted its own numbering principle. Result: `10-Logbook/` (the daily cockpit)
  now precedes `20-Claims/` (the capture inbox). The refine gate travels with Claims:
  `20-Claims/_refine-proposals/`, `20-Claims/_refine-approved/`, `20-Claims/_refine-queue.json`.
- Updated every path reference in lockstep — scripts, specs, the access-control matrix,
  schemas, molds paths, diagrams (Folder Stack), and the layout trees.

### Migration (for existing forks/vaults)
- `git mv 20-Logbook 10-Logbook` and `git mv 10-Claims 20-Claims`, then re-`render` the
  scripts. Anything pinned to the old paths (cron lines, external tooling) must update.

### Process
- Recorded as constitution-override change `swap-logbook-claims-order` (CONST-04, Tier 1)
  with human sign-off; see `openspec/adr/0009-layer2-ordering-correction.md`. CONST-04's
  principle text is unchanged — this is a corrective amendment, not an override.

---

## [0.1.2] - 2026-06-15

Documentation fills from dogfooding the live vault — Obsidian setup and the
Claim→Site promotion workflow.

### Added
- `docs/obsidian.md` — recommended Obsidian setup: core plugins; the
  **default-new-note-location → `10-Claims`** setting that keeps accidental/dangling-link
  notes out of the vault root; native Templates / Daily Notes for note creation; the
  Shell Commands + `flatpak-spawn --host` recipe for running maintenance scripts from
  the sandbox; and the Flatpak install + NVIDIA GL-extension matching note.
- `docs/method.md` → **"Promoting a Claim to a Site"** — the manual Claim→Site
  procedure, the single-source-of-truth cleanup discipline, and the three
  "where's my work?" indices (`30-Sites/`, the kanban board, the daily carry-over).

### Changed
- `vault-template/00-Docs/README.md` — clarified the two in-vault READMEs and noted that
  the full fork guide (`docs/USING-THIS-TEMPLATE.md`) and Obsidian guide (`docs/obsidian.md`)
  live in the template repo and do not copy into a forked vault; added pointers.
- `README.md` and `docs/USING-THIS-TEMPLATE.md` link the new Obsidian guide.

### Deferred (captured in docs, not built)
- A `vault-promote.sh` + an Obsidian "promote-from-inbox" punch-list button, a
  stray-fragment lint, and a `99-Operations` index MOC.

---

## [0.1.1] - 2026-06-15

Adopter-friction fixes found by performing a real install of the template into a
live Obsidian vault.

### Added
- `vault-template/.gitignore` — a forked vault now ignores `.venv/`, `__pycache__`,
  the generated `10-Claims/_refine-queue.json`, and Obsidian per-machine UI state
  (`.obsidian/workspace*`, `.obsidian/cache`) out of the box. The template previously
  shipped without a vault-level `.gitignore`.

### Changed
- Setup now installs `python-frontmatter` into a **vault-local venv** at
  `$VAULT_ROOT/.venv` rather than the system Python, which modern distros block under
  PEP 668. `config.env` (and `config.env.example`) prepend `$VAULT_ROOT/.venv/bin` to
  `PATH`, so `source 99-Operations/config.env` activates the right interpreter for both
  manual ops and cron. Updated `README.md`, `docs/USING-THIS-TEMPLATE.md`, and
  `vault-template/00-Docs/README.md` accordingly.

---

## [0.1.0] - 2026-06-15

First validated release. The deterministic engine (Phases 0–2) is proven against
the full PRD acceptance suite; Phase 3 (agent operations) remains spec-only/deferred.

### Added
- Initial repository structure: OpenSpec SDD scaffold, vault-template skeleton,
  constitution, 6 capability specs, 8 ADRs, 2 archived teaching changes,
  1 live change stub (add-telemetry-segment), CI pipeline, docs layer.
- Worked end-to-end example in `vault-template/00-Docs/examples/` (Claim → Treasury).
- `.github/scripts/validate-scripts.sh` — renders all 13 meta-scripts and runs
  `py_compile` + `shellcheck` + a fresh-vault pipeline smoke + the INV-11 executor
  boundary test. Wired as a CI matrix job (Python 3.12, 3.13).

### Fixed
- `config.env` used an HTML comment (`<!-- SPDX -->`) on line 1, which broke
  `source 99-Operations/config.env`. Changed to a shell comment (`# SPDX`).
- The literate-script render extractor used a non-line-anchored regex that
  truncated any script whose body contains a triple-backtick (notably
  `render-reconcile` itself). Anchored the closing fence to line start
  (`^``` ` with `re.MULTILINE`) in the script and both documented bootstrap
  snippets (`README.md`, `docs/USING-THIS-TEMPLATE.md`).
- The in-vault bootstrap (`00-Docs/README.md`) instructed running a `.md`
  meta-script note directly as Python; replaced with the code-block extraction step.
- Cron and ongoing-ops invocations set only `VAULT_ROOT`, so `vault-refine-detect.py`
  (needs `REFINE_GATE_GRADES`) and `vault-lint.py` (needs `PILLARS`/`GRADES`/
  `KNOWLEDGE_STAGES`) would `KeyError`. All documented invocations now source
  `config.env`.

### Changed
- Aligned proposal-schema MOC path examples with the kebab-case filenames
  (`<pillar>-moc.md`) used by the actual template (INV-11).
- Supported Python floor set to **3.12+** (was advertised as 3.10+, which the
  version matrix showed was not actually met).

### Validated
- Full PRD Phase 0→2 acceptance suite (A0.1–A2.6, plus orphan detector) against a
  sandboxed vault: 19/19 checks pass. All 13 operational scripts deploy via
  `render`, `reconcile` reports zero drift, and the refine pipeline
  (detect → propose → gate → execute), dispose, slag, rollover, kanban, linter,
  naming validator, and commit-gate hook all behave per spec.
- The documented onboarding was dogfooded literally end-to-end on a fresh vault.

[0.1.6]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.6
[0.1.5]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.5
[0.1.4]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.4
[0.1.3]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.3
[0.1.2]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.2
[0.1.1]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.1
[0.1.0]: https://github.com/keith-nielsen/2026-AI-Value-Memory-Mining/releases/tag/v0.1.0
