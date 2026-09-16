# Make three local controls report on what they actually check

## Why

Three defects, one root cause: **a control reporting on something other than what it claims to
check.** Each was found by inspection during one session, none by an instrument, and each produced a
confident, well-formed output that was wrong.

**1. The driver measures the working directory, not the estate.** `capabilities()` resolves its
subject from the declared `VAULT_ROOT` / `FRAMEWORK_ROOT`; `main()` resolved it from
`git rev-parse --show-toplevel`. The fix landed for the probe half and stopped there, in the same
file, under a docstring explaining why the working directory was wrong. This is reached by
*following* the documented procedure: `session-bootstrap-loader` step 4 instructs a session to run
`--plan`, and every cold session is vault-rooted, where the vault has no remotes by INV-14.
Measured, identical arguments, only the working directory differing:

| working directory | result |
| --- | --- |
| the vault | `BLOCKED at 'base'` — 1 of 14 steps measured |
| the repository | steps 1–4 MEASURED, `base` = `contains origin/main` |

It does not crash. It prints a plausible blocked route, and it **concealed a real finding**: against
the correct subject, step 1 reports `Gate 4 UNSIGNED`.

**2. The driver's declared-scope step checks presence, not coverage.** `scope_block_in` imports the
CI gate's fence regex — then asks only whether a non-empty block exists. The gate asks a second,
harder question: does the declared set *cover* the diff? On PR #117 a stale-but-present block passed
step 7 and was rejected by CI, because archiving had added four paths after the block was written.
The file's own docstring already states the principle it failed to apply: *"A check that
green-lights what the real gate will fail is worse than no check, because it is relied upon."*

**3. `preflight.py` excused `md-lint` with a hardcoded string whose claims went stale.** It read
*"markdownlint-cli is not installed locally; the CI job is also advisory"*. Both halves are now
false: the binary is installed, and the advisory construct was removed — the job ends in an explicit
`exit 0` and **does** fail on a tool failure or unreadable config. Preflight's `CLEAR` verdict had
therefore never once linted markdown. The asymmetry that makes it diagnosable: `openspec-validate`
is detected dynamically and moved itself from "could not run" to "reproduced" when the binary
returned; a constant cannot.

## What Changes

1. **`tools/pr-flow.py` — subject resolution.** A stated total order: `--repo` flag, then the
   declared framework root, then the working-directory toplevel. The resolved subject and its source
   are printed on **every** invocation, and a fallback is named as `DISCOVERED`. A subject that is
   not a repository is refused with the blocked exit code, naming the path.
2. **`tools/pr-flow.py` — `--repo PATH`.** Without it a declared framework root would hijack a
   deliberate invocation against another repository: one silent wrong subject traded for another.
3. **`tools/pr-flow.py` — `scope_covers_diff`.** The body step now runs the two **shipped** gate
   scripts against the real merge-base diff. They are invoked, not reimplemented, so they cannot
   drift. An unreachable gate passes rather than inventing a refusal.
4. **`tools/preflight.py` — `md-lint` moves from `NOT_LOCAL` into `LOCAL_JOBS`**, mirroring the CI
   job's exact ignore set and config. Availability is now measured per run; an absent binary reports
   `SKIP` with the real cause, exactly as `openspec-validate` already did. The stale string is
   deleted rather than reworded.
5. **Spec delta** — three ADDED requirements in `maintenance`.

## Impact

- **Behaviour narrows; nothing gains reach.** The driver acts on the declared repository instead of
  whichever tree the shell stood in. No step is skipped, no guard relaxed, no authority granted.
- **`--repo` is new surface**, which is why this takes a proposal. Its three design questions:
  *state lifetime* — none, per-invocation, never persisted; *reachability* — it can only name a path
  the caller could already reach by changing directory; *exhaustiveness* — three sources, one stated
  total order, no silent fourth.
- **One behaviour change is a new refusal.** The body step can now refuse where it previously
  passed. That is the intent — the refusal moves from CI to before the push — but it is a real
  change in when the driver stops.
- ⚠ **Preflight will now report failures it used to hide.** It did so immediately: on this branch it
  flagged 25 markdownlint findings in this change's own `proposal.md`, which the old exclusion would
  have passed through to a red CI run.
- **Scope note.** Three defects are fixed in one change deliberately. They share one root cause, and
  splitting them would put three unarchived deltas against the same `maintenance` spec — the
  merge-order hazard `CONTRIBUTING.md` warns about, where a later archive overwrites an earlier
  one's requirements *without a conflict*.

## Constitutional impact

Archiving syncs this delta into `openspec/specs/maintenance/spec.md`, `protects: [INV-2, INV-3,
INV-6]` — all **Tier 0 (Inviolable)** per `constitution.md` §2. Checked against each rather than
asserted:

- **INV-2** (*one automated change, exactly one commit*) — untouched; no commit ceremony is altered.
- **INV-3** (*operational scripts are literate meta-script notes, rendered to the host, drift
  detected never auto-fixed*) — **not engaged**: `tools/` holds repo-owned maintainer tools, not
  `99-Operations/scripts/` meta-script notes, and nothing here is deployed into a vault by `render`.
  Detection-only is preserved anyway: every control changed here reports and refuses; none writes.
- **INV-6** (*deterministic scripts: no network, no LLM*) — upheld. No network call is added. The new
  code paths are a path resolution and two local subprocess invocations of scripts already in the
  repository.

**The change is additive and narrowing.** It adds three requirements and one flag, removes one stale
string, relaxes no guarantee, and grants no caller new reach.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: three ADDED requirements plus defect fixes in two repo-owned tools; INV-3 not engaged (repo tools, not rendered meta-script notes) with detection-only preserved, INV-6 unchanged (no network added), INV-2 untouched; the driver's subject narrows to the declared estate and no authority is granted
```

## Verification

**Every test was observed to FAIL before the fix.** Ten new tests, written first:

| fix | tests | red proof |
| --- | --- | --- |
| subject resolution | 4 | all 4 failed against the old code |
| scope coverage | 3 | all 3 failed — `scope_covers_diff` did not exist |
| preflight accounting | 3 | all 3 failed — `md-lint` was in `NOT_LOCAL` |

⚠ **One test passed vacuously and was tightened.** `test_repo_flag_overrides_the_declared_estate`
asserted the repository path appeared in the output — which argparse's *"unrecognized arguments"*
error also satisfies, since it echoes the path. It was passing *because* the flag did not exist. It
now asserts that error is absent, and fails correctly against the old code.

**One existing test broke and was re-pointed, not weakened.**
`test_coverage_partitions_every_declared_job` used `md-lint` as its example of a job accounted for
via `NOT_LOCAL`. That premise is what this change removes. It now uses `secret-scan`, which remains
structurally excluded; the invariant under test — every declared job lands in exactly one category —
is unchanged.

**End-to-end against the real defect.** Run from the vault, the exact scenario that produced the
original false blocker, the driver now names its subject as the declared estate, measures the
correct repository, and surfaces `Gate 4 UNSIGNED` — the finding the old behaviour concealed.

**Preflight, end-to-end:** `md-lint` moved from the not-reproduced list into reproduced —
**13/16 jobs**, up from 12 — and immediately failed on real findings in this change's own proposal,
which have since been fixed.

Suite: **417 passed** (407 baseline + 10).
