<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Ship-Release Driver (Guarded, Re-Entrant, Never Outbound Itself)

The framework repo SHALL provide a ship-release driver (`tools/ship-release.py`) that mechanizes
the "Shipping a version" ceremony as a guarded, re-entrant state machine, so the ceremony's
documented hazards are guard clauses at their point of action instead of per-session
recollections. Each invocation re-derives the ship's state from the world (git refs, the remote,
the Release object) — the driver holds no state file and is safe to re-run at any point.

- **Merge-ancestor proof before any tag exists.** The driver SHALL refuse (exit `1`) to create or
  accept a tag whose target commit is not an ancestor of `origin/<base>` — never tag before merge.
- **CHANGELOG proof.** The driver SHALL refuse when `CHANGELOG.md` carries no `## [X.Y.Z]` section
  for the version being shipped; that section is the source of the emitted release notes.
- **Stale tags are refused with the true cause named.** A local or remote tag for the version that
  points at a different commit than the target is a refusal that prints BOTH commits and names the
  actual cause (a stale tag), never a mis-report of a different failure (e.g. "not merged").
  Resolving a stale tag — especially a published one — is a deliberate human action the driver
  SHALL NOT perform.
- **The driver SHALL NOT execute outward mutations.** `git push` and `gh release create` are
  ASK-gated by the INV-14 outbound guard, which text-matches the command being run; a wrapper that
  ran them internally would bypass that rail. The driver performs exactly one mutation itself — the
  local annotated tag, created only after both guards pass and verified by re-read — and otherwise
  EMITS the next single outward command verbatim, exiting `2` (needs-input). The caller runs that
  one command through the normal gated channel and re-invokes the driver.
- **Post-mutation verification, per layer.** On re-invocation the driver SHALL verify the previous
  step actually landed (the remote tag peels to the target; the Release object exists and is not a
  draft) before emitting the next step — a silent success is never trusted. Layer reads are printed
  one per line with the layer named (`local-tag` / `remote-tag` / `release-object`).
- **Tag↔Release parity tally closes the ship.** Once the Release exists, the driver SHALL tally all
  `vX.Y.Z` tags on origin against all Release objects and print the counts with their denominators
  (`N version tags / M releases — K tags without a release, J releases without a tag`), naming each
  parity miss. Exit `0` only on a clean tally; any miss (or a draft / a newest-version Release not
  marked Latest) exits `1`.
- **Network posture.** This is a ceremony tool, not a deterministic fleet script: it legitimately
  performs authenticated reads (`git fetch`/`ls-remote`, `gh release view/list`) per the
  "GitHub Release Object Per Version Tag" requirement, so INV-6 is not engaged. It is repo-only —
  not part of the deployed vault, not a CI gate. Exit contract: `0` ship complete · `1` refused ·
  `2` next gated command emitted · `3` blocked.

#### Scenario: An unmerged target is refused before any tag exists

- **WHEN** the driver runs for `vX.Y.Z` with a target commit that is not an ancestor of
  `origin/main`
- **THEN** it refuses with the ancestor proof named and exits `1`, and no tag for `vX.Y.Z` exists
  anywhere afterwards

#### Scenario: The driver walks the ceremony one gated command at a time

- **WHEN** the driver runs with both guards passing and no tag or Release yet
- **THEN** it creates the local annotated tag, verifies it by re-read, emits exactly
  `git push origin refs/tags/vX.Y.Z` as the next command, and exits `2`
- **WHEN** the caller has run that command and re-invokes the driver
- **THEN** the driver verifies the remote tag peels to the target, emits the
  `gh release create vX.Y.Z --verify-tag --latest …` command with notes derived from the CHANGELOG
  section, and exits `2`
- **WHEN** the Release exists and every version tag has its Release
- **THEN** the driver prints the parity tally with its denominators and exits `0`

#### Scenario: A stale tag is named as the true cause

- **WHEN** a tag for the version already exists (locally or on origin) pointing at a commit other
  than the target
- **THEN** the driver refuses, printing both commits and naming the stale tag as the cause — it
  does not report a merge problem, and it does not delete the tag itself

#### Scenario: A tag without a Release fails the closing tally

- **WHEN** the parity tally finds a version tag on origin with no corresponding Release object
- **THEN** the driver prints the miss (`parity-miss … tag vA.B.C has no Release`) and the tally
  with denominators, and exits `1` — an incomplete ship is never reported as complete

### Requirement: PR State Is Reported Per Layer

The framework repo SHALL provide a read-only PR-state reporter (`tools/pr-state.py <PR#>`) that
prints a pull request's state with the answering layer named on every line, because GitHub is a
stack of layers — event payload · workflow run · check aggregation · REST · GraphQL · branch/PR
state machine — that answer different questions and can disagree while all being correct.
Collapsing them into one oracle is the documented failure mode; the reporter keeps them apart.

- **Layers reported:** the PR state machine (state, draft, mergeable, `mergeStateStatus`); the
  branch layer read from origin refs (base and head existence and SHAs, diffed against the PR's
  recorded head oid); check-level aggregation (per-check verdicts with a tally and its
  denominator); run-level aggregation (per-run conclusions for the head commit); and the event
  payload as a standing advisory — it is not re-readable, a rerun replays the snapshot from the
  triggering event, and an amended PR body is seen only by a new push or an API read at job time.
- **Disagreement is a named signal, not an error.** When the run layer and the check layer
  disagree (e.g. a `continue-on-error` job), the reporter SHALL print a `LAYERS-DISAGREE:` line
  naming both layers and both tallies. The reporter exits `0` — the finding is the deliverable.
- **Known irreversible hazards are printed at the point of observation:** a deleted base branch
  (a closed stacked PR can be neither reopened nor retargeted — retarget the child before merging
  its parent) and a stale head oid (two layers out of sync) are flagged as `HAZARD [branch]:`
  lines.
- **Post-mutation verifier.** The reporter is the designated re-read after any `gh`/GraphQL
  mutation (a mutation can fail silently where REST succeeds); its output, not a silent success,
  is the evidence the state changed.
- **Read-only and repo-only.** Every call it makes is a read; it emits no outward command, so it
  sits below the INV-14 rail. Exit contract: `0` report delivered · `3` blocked.

#### Scenario: Every layer is named in the report

- **WHEN** the reporter runs against an open PR with checks and workflow runs
- **THEN** its output carries one or more lines for each of `pr-state-machine`, `branch`,
  `check-aggregation`, `workflow-run`, and `event-payload`, each prefixed with the layer name, and
  the check tally shows its denominator

#### Scenario: Disagreeing aggregation layers are surfaced as a signal

- **WHEN** the check layer reports a failing check while every workflow run for the same head
  commit concluded success (or vice versa)
- **THEN** the reporter prints a `LAYERS-DISAGREE:` line naming both layers and both tallies, and
  still exits `0`

#### Scenario: A deleted base branch is a printed hazard

- **WHEN** the PR's base branch no longer exists on origin
- **THEN** the reporter prints a `HAZARD [branch]:` line stating the retarget-before-merge rule
  for stacked PRs
