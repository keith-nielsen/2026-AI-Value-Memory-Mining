<!-- SPDX-License-Identifier: Apache-2.0 -->
# Phase 0 brief: freeze the framework before the split

> *Drafted 2026-10-23 (SGT) in a session started in this repo, on the local branch
> `docs/phase-0-freeze-brief`. It hasn't been pushed. It plans Phase 0 of the split of Value Memory
> Mining (VMM) into VMM and the governance hub RatchetHub (RH). It only plans: no release, tag, issue
> or constitutional change was made. The inputs are the vault Site `vmm-claudehub-split-rebuild`
> (strategy note §5–§7, the rulings note, and `phase-zero-route-findings`). Every repo fact below was
> re-read at `main` = `87ee947` (v0.1.56 plus Dependabot PR #122).*

## 1. What Phase 0 is for

Phase 0 freezes the current repo as the **quarry**: a public, citable record that both new repos
cite. It also tells readers that a split is coming. The operator leans towards a ground-up rebuild
(strategy §7.1, option c). Under that option the frozen repo is the only guard against losing
something by accident, so **completeness matters more than ceremony.**

**Exit test (simplified, see §5):** a GitHub Release for the freeze version exists and declares the
freeze; the README carries the notice; the three memory stores that git doesn't track are
snapshotted privately. Stopping here is the null option for the whole split, and it leaves a coherent state.

## 2. The three route findings, re-checked

### Finding 1: the freeze is the next normal release. **Confirmed, and ruled (operator, 2026-10-23).**

- The only tag route is `tools/ship-release.py vX.Y.Z` (`CONTRIBUTING.md` §"Shipping a version").
  Its first guard requires the CHANGELOG entry to be on `main` already. So step 0 is a
  CHANGELOG-only `release/vX.Y.Z` pull request (PR), as in PR #140 (`release/v0.1.56`, one commit,
  `CHANGELOG.md` only, read end to end).
- The Release body is the CHANGELOG section itself: `ship-release.py` writes
  `changelog_section()` to the notes file (`tools/ship-release.py:299`, `:361`). **So the freeze
  declaration goes in the `## [0.1.57]` CHANGELOG section, and it publishes as the Release notes with
  no extra step.**
- Since v0.1.56, `main` has one merge (#122, an OpenSpec 1.12.0 → 1.13.1 bump). `[Unreleased]` is
  empty. v0.1.57 would cover #122 plus the README-notice PR (§4 step 2).
- The `core-freeze-v0.1.56` tag in the strategy note is dropped. No ceremony exists for it.

### Finding 2: the `ACMR` scanner fix. **Partly corrected: the full override protocol is not required.**

The problem stands. `access-control/spec.md:373` says the secret scan covers
`git diff --cached --diff-filter=ACM`. A file renamed **and** edited in one commit is never
secret-scanned. That's a gap in INV-7, which is Tier 0. The same `ACM` is in
`vault-template/99-Operations/scripts/secret-scan-script.md:116` (the code),
`commit-gate-script.md:28` (the rationale), ADR-0036 line 90, and the comment at
`tests/test_secret_scan.py:74`.

**What changes:** the finding said any change to a `protects:` file needs the Informed-Upheaval
Protocol (IUP). The governing text says otherwise:

- `openspec/constitution.md` §3: the IUP applies to an **override** of a Tier-0 or Tier-1 element.
  Widening `ACM` to `ACMR` overrides nothing. It makes the scan cover more, which is what INV-7 asks.
- `CONTRIBUTING.md` §"Declaring constitutional impact": a change to a `protects:` spec carries a
  `constitutional-impact` block, and **`overrides: none` passes**. A `constitution-override`
  directory is needed only when that block names an overridden element.
- `CONTRIBUTING.md` §"Touching a constitutional element?" says the opposite: "any" modification
  takes the IUP, and "CI will fail" without it. Constitution §3–§4 says no continuous-integration
  (CI) check refuses such a change. The constitution governs. **This is a documentation defect**
  (see §6).
- The **agent hard stop** (constitution §5, `AGENTS.md`) applies either way. An agent touching a
  `protects:` file must first show the operator the principle and its trade-off, and must get
  explicit confirmation.

**So the light route is:** an ordinary OpenSpec change. It adds `R` to the filter in the spec, the
literate note and the rationale. It adds a test that is **seen to fail first** (a staged rename plus
edit that carries a HIGH-tier token). It declares `overrides: none`, with the basis "widens INV-7's
enforcement; nothing is narrowed". It goes ahead only after the §5 hard-stop confirmation.

**The operator's choice. Risk if left alone: INV-7 has a known gap on renamed-and-edited files until
it's fixed.**

| Option | Cost | Risk |
| --- | --- | --- |
| **(a) Fix now, light route** (recommended) | one OpenSpec change and one PR, inside the freeze's "fixes only" rule | low; it widens a scan. A false-positive surge is unlikely, since the HIGH tier is anchored vendor formats |
| (b) Fix now, full IUP | four gates, an ADR, human sign-off | the same fix, with ceremony the constitution doesn't require |
| (c) Defer to the rebuild | none now; PPE's Stage 1 contract already requires `ACMR` | the gap stays open in the frozen v0.1.x line, which keeps running the live vault through Phase 4 |
| (d) Null | none | as (c), with no record that the gap was accepted |

**Why (a):** the live vault runs v0.1.x for the whole rebuild (strategy §5). A Tier-0 gap left open
for months is a fix, and "fixes only" allows it. If (c) is chosen, the stop-gap is not automatic:
`scan_history` must actually be run against the vault, and someone must own that.

### Finding 3: the planned-split issue. **Confirmed: the agent and the operator have no route.**

- `POST /repos/{slug}/issues` is in the sanctioned write set (`docs/version-control-legal-moves.md`
  §2b) with `runs: ci | authority: ci | issue-absent`. Its only consumer is
  `.github/workflows/openspec-canary.yml:74`. `gh issue …` is denied (§1).
- The `gh` invocation guard's `SANCTIONED_WRITES` (`.claude/hooks/gh-invocation-guard.py:55`) holds
  the endpoint **without** its `runs:` column. **Measured 2026-10-23:** the guard was given three
  hook payloads, and no command was run. It **allowed** `gh api -X POST /repos/<slug>/issues`. It
  denied `POST …/forks` (the adversarial control) and `gh issue create`. So the guard would let the
  agent type the POST that the table assigns to CI. The table, not the guard, is what forbids it:
  the guard matches the form, not the actor.
- **No REST endpoint for pinning was found.** GitHub documents pinning only as a web-UI action. The
  GraphQL `pinIssue` mutation is reachable only through `gh api graphql`, which is denied.

**Recommendation: drop the issue from Phase 0.** The Release notes and the README note carry the
notice through channels that already have routes. If the operator still wants an issue, the
operator can open it and pin it in the GitHub web UI. That's outside the agent's typed channel, which
is all the legal-moves set governs. The alternative, adding an operator row to §2b, costs a change
to a control for a single use. Phase 0 exists to stop that kind of machinery growth.

## 3. Freeze practice (external review, condensed)

- **Don't archive the repo during the freeze.** Archiving makes issues, PRs, code and releases
  read-only for everyone, owners included. Nothing can be created through the API until the repo is
  unarchived ([GitHub: archiving repositories](https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories);
  [2017 API change note](https://developer.github.com/changes/2017-11-08-archiving-repositories)).
  That would block the fixes the freeze allows, and the v0.1.x line that runs the live vault.
  **Archive only after Phase 4**, once the README points to both successors. GitHub and Google both
  order it this way: update the README, then archive
  ([Google OSS repository management](https://opensource.google/documentation/reference/github/management)).
- **Say what is still accepted.** A freeze notice should state its scope (fixes only), whether issues
  and security reports are still reviewed, and where the successors will be
  ([FOSSHub: archiving a project](https://www.fosshub.com/resources/development/archive-project/)).
  The 2026-10-18 draft notice covers the scope. It doesn't cover security reports.
- **Splitting into an archived core and an active successor** is a recognised pattern (same
  source). It needs successor guidance in the README once the successors exist, not before.
- **Pinned issues:** up to three, through the web UI only
  ([GitHub: pinning an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/administering-issues/pinning-an-issue-to-your-repository)).

## 4. The Phase 0 route

Each step is a normal ceremony that `tools/pr-flow.py` and `tools/ship-release.py` already drive.
**Nothing here is a new route.**

| # | Step | Route | Waits on |
| --- | --- | --- | --- |
| 1 | *(Only if the notice names RH)* reserve the `ratchethub` GitHub organization **before** the name is public, as the 2026-10-23 rulings require | operator, web UI | operator decision §7 Q2 |
| 2 | README notice PR (`docs/` prefix): the note under the badge row, from the 2026-10-18 draft, updated (§4.1) | `pr-flow.py` | after Q2 |
| 3 | *(If option (a))* the `ACMR` fix as an OpenSpec change | `/opsx:propose` then `pr-flow.py` | after Q1 |
| 4 | `release/v0.1.57`: cut `## [0.1.57]` from `[Unreleased]` with the freeze declaration (§4.2), as a CHANGELOG-only PR | `pr-flow.py` | after 2 (and 3) merge |
| 5 | Tag and Release `v0.1.57` | `tools/ship-release.py v0.1.57` | after 4 merges |
| 6 | Mirror to the live vault and prove parity | `tools/template-mirror.py <VAULT_ROOT>` (`CONTRIBUTING.md` step 5) | after 5 |
| 7 | Snapshot the three memory stores privately (§4.3) | a **vault** session; never this repo | operator decision §7 Q3 |

### 4.1 The README note (updated from the 2026-10-18 draft)

Changes to the draft:

- It names the hub **RatchetHub** only if step 1 is done. Otherwise it says "a separate governance
  project".
- It drops the issue link (finding 3).
- It adds one line on security reports (§3).
- It points to the v0.1.57 Release as the frozen reference.

Drafting the exact text is step 2's PR, not this brief.

### 4.2 The freeze declaration (CHANGELOG `[0.1.57]`)

It covers: what is frozen (the protocol and the harness, fixes only), what is still accepted
(security and correctness fixes, Dependabot **security** updates), and that v0.1.57 is the reference
both successors cite. **Dependabot version updates** keep opening PRs during the freeze
(`.github/dependabot.yml`). Merging them is a fix-only judgement each time. Pausing them would be a
supply-chain policy change (the `maintenance` spec), and isn't needed.

### 4.3 Completeness: what the tag doesn't hold

The strategy (§7.1) requires "the tag, full history, archived changes, ADRs and the dev store all
retained untouched". The tag holds the first four. **Measured 2026-10-23, it holds none of the
memory stores:**

| Store | Files | In git? |
| --- | --- | --- |
| `~/.claude/projects/-home-administrator-Documents-Vault/memory/` (holds `github-platform-hardening-queue.md`, 1,250 lines) | 29 | no |
| `$VAULT_ROOT/10-Logbook/vmm-working-memory/` | 32 | no (`.gitignore:70`) |
| `~/.claude/projects/-home-administrator-Documents-repo-value-memory-mining/memory/` | 2 | no |

These are private (INV-14), so they must **not** go into this public repo. The simplest safe
snapshot is a dated copy committed into the private vault. That's vault work, for a vault session.

## 5. Simplicity pass: what was cut from the strategy's Phase 0

- **Cut: the custom freeze tag.** It's now the next normal release (finding 1).
- **Cut: the issue.** The Release notes and README carry the notice (finding 3).
- **Moved to Phase 1: triaging the hardening queue.** Under option (c), no old code is ported, so
  "hub v1 or stays frozen" becomes "which lessons become RH v1 requirements". That is Phase 1's
  scope list. Doing it in Phase 0 would mean triaging twice. The queue is kept whole by §4.3.
- **Kept:** completeness (§4.3), because under option (c) it's the whole point of the freeze.

Phase 0 becomes **two or three PRs and one ship**, all on existing routes.

## 6. Found on the way (filed here, not fixed)

1. **`CONTRIBUTING.md` contradicts the constitution** on when the IUP applies, and repeats the
   "CI will fail" claim that constitution §3–§4 retracted on 2026-08-16. A docs fix is needed; it
   could ride on step 2's PR.
2. **The vault's protected paths are writable from a session started in this repo.** On 2026-10-23,
   `pr-flow.py --capabilities` reported `UNPROTECTED` for `40-Treasury`, `96-Runbooks` and
   `99-Operations`. The probe wrote a file into each and then removed it. The cause: the repo's
   `.claude/settings.json` and `~/.claude/settings.json` declare no `sandbox`. The vault's denies are
   in `$VAULT_ROOT/.claude/settings.json` (`denyWrite: ["./40-Treasury", …]`, relative paths). They
   load only when a session starts in the vault. This session made no vault
   writes. It matters for step 6, the mirror, which writes to the live vault by design, and for RH's
   settings generator (strategy §4).
3. **Lint over the Site** (`vault-lint.py`, read-only, run 2026-10-23): one violation in the whole
   vault, `30-Sites/.claude`. That's an empty harness scratch directory (`.cc-writes/`), not this
   Site's content. The Site holds a similar empty `.claude/`, which the linter doesn't flag. All 20
   distinct wikilinks in the Site resolve.

## 7. Decisions for the operator

1. **`ACMR`:** (a) fix now, light route (recommended) · (b) fix now, full IUP · (c) defer to the
   rebuild · (d) null.
2. **The name in the notice:** (a) reserve `ratchethub` first, then name RH · (b) say "a separate
   governance project" and don't name it yet (no outward action needed) · (c) null: no README note.
3. **The memory-store snapshot:** (a) copy into a vault Site in a vault session (recommended) · (b)
   leave the stores as they are (null; risk: the quarry is incomplete under option c).
4. **The issue:** (a) drop it (recommended) · (b) the operator opens and pins it in the web UI.
