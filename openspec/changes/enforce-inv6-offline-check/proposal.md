<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: enforce-inv6-offline-check

**Change type:** `constitution-override`, **conforming**
**Principle(s) affected:** `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) — **ADDs** a Requirement. **No Tier-0/Tier-1 element is overridden or weakened**; INV-6 gains a runner for a scenario it already had.
**Tier:** 0 (INV-6)
**Proposer:** Keith Nielsen
**Date:** 2026-07-28

---

## Purpose (one sentence)

Give INV-6 — *"`[script]` operations make no network calls and no LLM calls"* — a firing mechanism,
so that it stops being the last Tier-0 invariant enforced by nothing.

## Why

INV-6 was, as of v0.1.35, **the only live Tier-0 invariant with no mechanism at all**. The
2026-07-28 enforcement audit measured it: of nine live Tier-0 invariants, four now fire without
agent cooperation (INV-4, INV-5 at the kernel; INV-11 and INV-7 at the commit gate). INV-6 had
nothing — no test, no lint, no CI job. A `grep` across `tests/` and all fifteen CI jobs for
`socket|network|offline|urllib|requests|unshare` returned exactly one hit, and it was **prose in a
docstring**.

**INV-6's defect is a different shape from INV-7's, and the difference is worth recording.** INV-7's
Requirement carried a *wrong* scenario — it inspected two config files, a Factor-A check standing in
for a Factor-B property. INV-6's scenario has always been **correct and behavioural**:

> **WHEN** any `[script]` operation runs · **THEN** it issues no network request and invokes no model

The rule was right. **Nothing ran it.** Same outcome — documented, unenforced — reached by the
opposite route. A well-formed test with no runner is its own failure mode, and it is harder to spot
than a wrong one precisely because reading the spec is reassuring.

## What Changes

Two complementary halves, plus the honest statement that neither is sufficient alone.

- **Static — `tools/inv6-offline-check.py`.** Analyses each fleet note's code fence. Python by
  **AST**; bash by a conservative command-position scan.
- **Dynamic — `.github/scripts/inv6-offline-dynamic.sh`.** Runs the fleet suite inside an
  unprivileged **network namespace**, having first proven the isolation is real.

**The design problem that dictates the AST approach.** A grep-based checker flags exactly the two
scripts it must not. `outbound-publish-guard` and `push-guard` are the INV-14 rail; their entire job
is to *name* outward verbs inside regex literals. Measured on the shipped files:

| Note | naive grep hits | AST / command-position violations |
|---|---|---|
| `outbound-publish-guard-script.md` | **6** | **0** |
| `push-guard-script.md` | **2** | **0** |

Naming is not calling. An `import socket` is an `Import` node; `"git push"` in a pattern is a
`Constant`. A checker that confuses them would fail the two most security-relevant scripts in the
fleet on every run, and would be switched off rather than obeyed — RC-E, *over-denial is camouflage*.
This is the second application of a lesson learned earlier the same day, when the INV-7 scanner's own
private-key fixture matched its own pattern table.

**Scope boundary, explicit.** The Layer-0 fleet only (`vault-template/99-Operations/scripts/*.md`).
Repo-side maintainer tools are **not** fleet scripts: `ship-release.py` legitimately performs
authenticated reads, and the maintenance spec already records that INV-6 is not engaged for it.
Checking `tools/` would manufacture violations out of correct behaviour.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle being strengthened (restated):**

> INV-6 says the deterministic layer never reaches the network or a model. It is what makes `[script]`
> operations reproducible and model-agnostic — the same inputs give the same outputs on any machine,
> in any year, with any AI tooling installed or absent. A script that quietly acquired a network
> dependency would still *look* deterministic in review, and would fail only in the environment least
> able to diagnose it.

**Enumeration transcripts (mandatory — Gate 4 re-runs these):**

```transcript
$ grep -rilE 'socket|network|offline|urllib|requests|no-net|unshare' tests/ .github/workflows/ .github/scripts/
tests/test_ceremony_tools.py
$ grep -nE 'socket|network|offline|urllib|requests|unshare' tests/test_ceremony_tools.py | head -5
4:git layer (fetch, ls-remote, tags, push) is exercised for real and offline. Only `gh` is
```
→ The single hit is **prose in a module docstring**, not an assertion. Nothing checked INV-6.

```transcript
$ for f in vault-template/99-Operations/scripts/*.md; do
    hits=$(grep -cE '\b(socket|urllib|http\.client|requests|curl|wget|ssh|git (push|fetch|clone|ls-remote)|gh )' "$f")
    [ "$hits" -gt 0 ] && printf '%-42s %s\n' "$(basename "$f")" "$hits"; done
outbound-publish-guard-script.md           6
push-guard-script.md                       2
```

```transcript
$ grep -rnoE '[0-9]+ (repo-only |maintainer )?(tools|CI jobs|jobs)\b' README.md AGENTS.md CONTRIBUTING.md docs/*.md openspec/specs/*/spec.md
(no output)
```
→ **No hardcoded tool or CI-job counts exist**, so no count edits are owed. Checked, not assumed —
the INV-7 change owed three such edits and they were found only by sweeping.

**Checklist:**

- [ ] `openspec/specs/maintenance/spec.md` — **ADDED** Requirement: *INV-6 Is Enforced by Static and Dynamic Checks*. The existing `Deterministic Scripts Are Offline (INV-6)` Requirement is **left intact** (ADR-0030 pattern)
- [ ] `tools/inv6-offline-check.py` — new repo-only static checker
- [ ] `.github/scripts/inv6-offline-dynamic.sh` — new netns runner with fail-closed controls
- [ ] `.github/workflows/ci.yml` — two new jobs (`inv6-offline-static`, `inv6-offline-dynamic`)
- [ ] `tests/test_inv6_offline.py` — 28 cases, weighted to the false-positive direction
- [ ] `openspec/adr/0037-enforce-inv6-offline-check.md` — new ADR
- [ ] `README.md` — ADR count 36 → 37 + reference `0037` (**CI-guarded** by `adr-count-lint`)
- [ ] `CHANGELOG.md` — v0.1.36 entry
- [ ] `openspec/constitution.md` — **no change**
- [ ] `tools/template-sync-manifest.json` — **no change** (no fleet member added; nothing to mirror)
- [ ] `vault-template/` — **no change**; the fleet is unmodified, so **no `render`, no mirror, no operator deploy step**
- [ ] `SECURITY.md` — **no change**; its table lists INV-4/5/7/11 and INV-6 is not a reportable-bypass row

**Explicitly NOT changed:** the INV-6 Requirement text; the fleet (still 14 scripts); the Script
Inventory Requirement; `docs/`.

**Deliberately excluded, queued separately** (F29 — one change, one purpose):

- **The two INV-14 guards have no tests**, so the dynamic half cannot cover them. That is a real
  coverage hole and it is stated in the tool's own output rather than hidden. Giving those guards
  tests is its own change.
- The stale `access-control` 68/73 claims, the `SECURITY.md` deferred-work entries, and
  `validate-scripts.sh`'s hardcoded `/tmp` paths all remain queued.

---

## Gate 2 — PLAN (Migration + Regression)

1. Land both checkers and their tests (done — see Gate 3).
2. Add the two CI jobs.
3. Author the ADDED Requirement in the change's `specs/maintenance/` delta.
4. Write ADR-0037; bump README ADR count to 37.
5. CHANGELOG v0.1.36.
6. Ship via `tools/ship-release.py v0.1.36` **after merge**; archive on the branch before merging.
7. **No deploy step.** Nothing under `vault-template/` changes, so there is no mirror and no
   operator `render` — unlike v0.1.35. The check is repo-side because the fleet is authored
   upstream and deployed down; a deployed vault cannot author a script.

**Regression tests that MUST pass before Gate 3:**

- [ ] `openspec validate --all`
- [ ] `constitution-lint`, `vocabulary-lint`, `adr-count-lint` (37)
- [ ] `pytest tests/` fully green including the 28 new cases
- [ ] `inv6-offline-check --selftest` and a clean fleet analysis
- [ ] `inv6-offline-dynamic.sh` green **with both controls proven**
- [ ] the fail-closed path demonstrably refuses when isolation cannot be established

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑
**All regression tests green:** ☑ (locally)
**CI green on this PR:** ☐ — no PR opened yet

**Verification transcripts attached for every named test:** ☑

```transcript
$ python3 tools/inv6-offline-check.py --selftest
selftest: fires on calls, silent on names
rc=0

$ python3 tools/inv6-offline-check.py
inv6-offline-check: 14 fleet notes analysed - 0 violation(s), 0 unresolved
NOTE: a clean static result does not prove offline behaviour; the netns run
      (inv6-offline-dynamic) is the behavioural half.
rc=0
```

**The first behavioural evidence INV-6 has ever had**, with controls discriminating in both
directions in the same run:

```transcript
$ bash .github/scripts/inv6-offline-dynamic.sh
== control 1: the network must be reachable OUTSIDE the namespace ==
  ok: reachable outside
== namespace mode: map-current-user ==
== control 2: the network must be UNREACHABLE inside the namespace ==
  ok: blocked inside
== fleet suite, offline ==
......................................                                   [100%]
38 passed in 7.31s

INV-6 dynamic: fleet suite completed with NO network available (mode: map-current-user).
rc=0
```

**The fail-closed path fires** — a control that cannot refuse is decoration, so it was made to
refuse and then observed refusing:

```transcript
$ unshare --map-current-user -n bash .github/scripts/inv6-offline-dynamic.sh
== control 1: the network must be reachable OUTSIDE the namespace ==
curl: (7) Failed to connect to localhost port 3128
BLOCKED: no network on this runner, so 'blocked inside' would be meaningless.
  This is an INVALID instrument, not a passing test.
rc=1
```

**A confound found and eliminated rather than worked around.** The first netns attempt used
`unshare -rn` and one test failed — `test_non_erofs_oserror_is_not_swallowed`, which does
`chmod(0o444)` and asserts `Errno 13`. `-r` maps the caller to **root inside the namespace**, and
root ignores permission bits, so the failure was a permissions artifact, **not** a network call.
Re-run with `--map-current-user` (uid preserved, network still isolated): **38 passed**, and the
control still returned `000` inside. The runner script prefers `--map-current-user` and, when it
must fall back to `-r`, deselects that one test *and prints which mode ran*.

```transcript
$ python3 -m pytest tests/ -q
104 passed in 11.51s          # 76 prior + 28 new, no regressions
```

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [ ] Blast radius re-checked against the final diff
- [ ] Gate-1 transcripts re-run and diffed clean

**Consequences explicitly accepted:**

> **Neither half is complete, and the spec says so.** Static analysis is complete over *text* and
> blind to *semantics* — `__import__` with a computed name, `eval`, or a network call inside a C
> extension is undecidable, and is reported **UNRESOLVED** rather than clean. The dynamic half is
> complete over *semantics* but bounded by **test coverage** — and coverage is thinnest exactly
> where the network verbs live, since the two INV-14 guards have no tests at all.
>
> **The bash half is the weaker one** and is not claimed to be complete: it is a command-position
> scan facing the same unbounded-language problem that leaves the INV-14 guard's regex with known
> holes.
>
> **A green result therefore means "no statically visible network call, and none on the paths the
> suite exercises" — not "the fleet is offline."** Citing it as the latter would be the Factor-A
> substitution this change exists to end.
>
> CI gains two jobs and roughly a minute. A future fleet script that legitimately needs the network
> would have to become an `[agent]` operation instead — which is what INV-6 already requires.

- [ ] **ADR created:** `openspec/adr/0037-enforce-inv6-offline-check.md`
- [ ] **Human sign-off recorded:** _pending_ — constitution §5, human-only.

**SIGN-OFF** (human only — agents may not sign):
Name: ___________________________
Date: ___________________________
