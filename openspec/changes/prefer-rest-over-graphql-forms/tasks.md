# Tasks — prefer-rest-over-graphql-forms

## 1. The detector, red before anything else

**BUILT AND OBSERVED RED — `tests/test_gh_form_conformance.py`, 2026-09-18.** 4 checks, 1 failing by
design, 32 files scanned, 0 parse failures. The failing check names **exactly the seven predicted
sites, no more and no fewer**:

```
7 shipped `gh` form(s) are refused by the estate's own guard:
  tools/pr-flow.py:1919                       gh pr create      (emitted)
  tools/pr-state.py:112                       gh pr view        (executed)
  tools/pr-state.py:181                       gh run list       (executed)
  tools/ship-release.py:343                   gh release create (emitted)
  .github/workflows/openspec-canary.yml:49    gh label create   (CI)
  .github/workflows/openspec-canary.yml:51    gh issue list     (CI)
  .github/workflows/openspec-canary.yml:55    gh issue create   (CI)
```

⚠ **Canary `:51` is in that list only because the detector unwraps command substitution.** It is
`open=$(gh issue list …)`, the shape the guard itself is blind to, and the 2026-09-18 dry run missed
it. The blind spot was designed out rather than inherited — see 1.5.

**Three sources of noise were removed after the first red run**, each a real lesson:
- sink calls now examine **only the first positional argument** — `emit(route, "pr", cmd, why=…)`
  carries prose in keyword arguments that names refused forms *on purpose*, and walking the whole
  call reported the driver's own explanation of why it avoids `gh pr merge` as an emission;
- the notes' python fences are **parsed as code**, not scanned as lines — scanning reported the
  guard note's own comments and refusal messages, i.e. the one file whose job is to name refused
  forms;
- workflow line continuations are **joined before lexing** — a `\`-split command was being reported
  as unlexable when the file is perfectly well formed.

- [x] 1.1 Enumerate every `gh` invocation in the tree **by mechanism, not by pattern**: AST over
      `tools/*.py`, `.claude/hooks/*.py` and `.github/scripts/*.py` for both executed argv lists and
      emitted command strings; `run:` blocks for `.github/workflows/*.yml`; code fences for
      `vault-template/99-Operations/scripts/*.md`.
      *Done when:* the enumeration's denominator is printed (files parsed, parse failures) so a
      silent miss is visible. A count with no denominator is the defect this file exists to stop.
- [x] 1.2 Submit each enumerated form to `gh-invocation-guard.py` — **import the guard, never restate
      its rule.** Restating is class 9, and the 2026-09-08 ledger sweep already proved the import
      approach works by using the guard as its oracle.
- [x] 1.3 **Observe it FAIL, and record what it names.** Expected: the seven non-conforming sites.
      *Done when:* the red run's output is pasted into this file. **If it names more than seven, the
      extra rows are the finding and this task's expectation was wrong — do not trim the output to
      match the prediction.**

      **DRY RUN ALREADY PERFORMED, 2026-09-18** (scratchpad prototype, not committed) — 32 files,
      0 parse failures, **13 refusals: 6 true · 6 false-positive · 1 missed.** The real detector must
      beat this, and the three lessons are requirements on it, not observations:
      - **False positives are strings that MENTION a command** (`"gh credential"`,
        `"gh not installed"`, `"gh run list failed:"`, and prose inside the guard note's own fence).
        Distinguish *is a command* from *names one*; the 2026-09-08 sweep hit this 43 times.
      - **The miss was canary `:51`**, `open=$(gh issue list …)` — see 1.5.
      - **Conformance of the targets is already confirmed:** all nine proposed `gh api` replacements
        pass the guard unchanged, so the conversion aims at known-good forms.
- [x] 1.5 **Extract invocations from inside command substitution** — `$( )`, backticks, and
      subshells — or the detector reproduces the guard's own blind spot. ⚠ Measured 2026-09-18: the
      guard PERMITS `open=$(gh pr list)`, ``open=`gh pr list` ``, `echo $(gh pr list)` and
      `( gh pr list )` while denying the plain form, because `open=$(gh` parses as an environment
      assignment. **The detector must NOT inherit this.** Hardening the guard itself is out of scope
      here — different control, its own spec delta and Gate 4 — and is recorded in
      `gh-form-findings-ledger.md`.
- [x] 1.6 **Unlexable input is a FINDING, never a skip.** `guard.segments()` raises on a trailing
      backslash or an unbalanced quote, and the hook's `main()` does `except Exception: return`,
      i.e. fail open. A detector that skipped unlexable lines would inherit exactly that.
- [x] 1.4 A test asserting coverage does not depend on registration: add a deliberately
      non-conforming emission in a fixture and confirm the detector catches it without being told.

⚠ **The 2026-09-08 ledger sweep — the one generated with the guard as oracle — captured canary lines
49 and 51 but NOT line 55.** A live `gh issue create` has no `GH-` id at all. Read that generator
before trusting any enumeration's completeness, including this one's.

## 2. Convert the seven, each with its own trap checked

- [ ] 2.1 `pr-state.py:83` — `gh pr view --json` → `gh api repos/{slug}/pulls/{n}`.
      The REST-first read is already built on this branch; this removes the GraphQL first attempt.
- [ ] 2.2 `pr-state.py:168` — `gh run list --commit` → `gh api`.
      ⚠ **Measure first what the caller actually consumes.** `gh run list` issues TWO requests
      (`/actions/runs` and `/actions/workflows?per_page=100`); a single `/actions/runs?head_sha=`
      call drops workflow names. *Done when:* the fields used downstream are enumerated and shown
      present in the replacement's response.
- [ ] 2.3 `pr-flow.py:1919` — emitted `gh pr create` → `gh api -X POST repos/{slug}/pulls`
      with `-f title=` `-f head=` `-f base=` `-F body=@<file>`.
- [ ] 2.4 `ship-release.py:343` — emitted `gh release create` → `gh api -X POST repos/{slug}/releases`
      with `-f tag_name=` `-F body=@<file>` `-f make_latest=true`.
      ⚠ `--verify-tag` has no REST equivalent; its replacement is an explicit
      `GET repos/{slug}/git/ref/tags/{tag}` precondition **before** the POST — the pattern
      `uat-release-roundtrip.sh` already proved at step 1.
- [ ] 2.5 canary `:49` `gh label create` → `GET repos/$GITHUB_REPOSITORY/labels/openspec-canary`,
      and on 404 `POST .../labels`. ⚠ This removes a `2>/dev/null || true` that currently makes an
      auth failure indistinguishable from "already exists".
- [ ] 2.6 canary `:51` `gh issue list` → `GET .../issues?labels=…&state=open&per_page=100`
      ⚠ **with `--jq '[.[] | select(.pull_request == null)] | length'`.** `/issues` returns pull
      requests; without the filter the dedupe silently stops opening issues it should open.
- [ ] 2.7 canary `:55` `gh issue create` → `POST .../issues` with `-f 'labels[]=openspec-canary'`
      (the bracket form is the `gh api` array syntax; `-f labels=` sends a string and is rejected).

## 3. Consequences, recorded rather than discovered later

- [ ] 3.1 `tests/test_emitted_command_shape.py` — its `-R <slug>` assertion dies with 2.3/2.4, since
      `gh api` carries the slug inline. Change the premise **in the same commit**, and widen its
      scope: it reads only `ship-release.py`'s `_emit_next(…)` today and never sees `pr-flow.py`'s
      `emit(…)` sites, which is the second reason `gh pr create` stood unnoticed.
- [ ] 3.2 `pr-state.py` — populate `mergeStateStatus` from REST `mergeable_state` (same enum,
      lowercased) instead of reporting `UNAVAILABLE (GraphQL-only)`. ⚠ `mergeable_state` is thinly
      documented: **pin the observed values in a test** rather than assuming the enum. `mergeable` is
      computed asynchronously, so `null` on a cold read is a real state — `--ready mergeable` already
      polls it.
- [ ] 3.3 Document surfaces, same change: `docs/version-control-legal-moves.md` rows *Open a PR* and
      *Create a Release*; `AGENTS.md`; `CONTRIBUTING.md`; `docs/USING-THIS-TEMPLATE.md`; and the
      vault's `30-Sites/repo-work-bootstrap-enforcement/vmm-repo-github-card.md` with `CARD-VERSION`
      bumped — nothing detects that card drifting.
- [ ] 3.4 Update `gh-form-findings-ledger.md`: FIX rows now absent, KEEP rows still present and still
      denied.

## 4. Regression

- [ ] 4.1 Full suite. Baseline measured 2026-09-18: **424 passed**, on this branch rebased onto
      `a22c2ea` with the REST-first refactor already applied.
- [ ] 4.2 `openspec validate --all --strict`.
- [ ] 4.3 `tools/preflight.py . --body-file <path>` → CLEAR. ⚠ `--body-file` is **not optional**:
      without it the body step prints `SKIP`, and a SKIP reads exactly like a PASS.
- [ ] 4.4 A mutation matrix behind the detector — a detector that cannot be shown to fail is not
      evidence, and this change's whole premise is that unexercised instruments rot.

## 5. Gate 4 — operator authorization (Tier-0 touch)

Archiving syncs this delta into `openspec/specs/access-control/spec.md`, `protects: [CONST-02, INV-4,
INV-5, INV-6, INV-7, INV-8, INV-14]`. The `AGENTS.md` hard stop requires the principle, its rationale
and its "what breaks" consequence surfaced, and explicit human confirmation received.

To be surfaced, with the sacrifices stated rather than minimised — **drafted by the agent; the
sign-off is human-only and is NOT recorded here until given:**

- **A new refusal exists.** The detector can fail CI on a form that previously shipped. If its
  enumeration is wrong in the strict direction, it blocks work that was fine.
- **The operator's pasted command changes shape.** `next.sh` will carry
  `gh api -X POST repos/{slug}/pulls …` rather than `gh pr create …`.
- **`--verify-tag` becomes an explicit precondition read** rather than a flag. If 2.4 gets that
  wrong, the rail that stops a typo'd version silently tagging a branch head is the thing that
  weakens.
- **What breaks if this is wrong:** these are the controls other work is judged by. A defect here
  does not fail loudly — it produces a confident, well-formed, wrong answer.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [ ] 5.1 Tier-0 touch surfaced with its consequence; **Approved** — <operator>, <ISO date>

## 6. Land it

- [ ] 6.1 Archive the change on this feature branch, in the same PR (ADR-0040).
- [ ] 6.2 Walk `tools/pr-flow.py`; do not hand-compose the sequence.
