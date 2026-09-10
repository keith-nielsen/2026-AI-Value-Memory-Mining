## 1. Red proof first — the failing test before the fix

- [ ] 1.1 Add the discriminating case to `tests/test_pr_flow.py`: two real git trees, subject declared
      as A while the process runs with cwd in B, asserting the driver reports on A.
      *Done when:* it **FAILS against the current code**, naming tree B. A pass here means the test is
      not discriminating and the task is not done.
- [ ] 1.2 Add the fallback case: no declared subject, cwd in B — the driver measures B **and states
      that the subject was discovered rather than declared**.
      *Done when:* it fails today on the missing announcement, not on the subject.
- [ ] 1.3 If any non-discriminating test is kept for coverage, label it as such in its own docstring.
      *Done when:* no test counts as coverage without stating whether it can distinguish fixed from
      broken. (The render change's third test is the precedent.)

## 2. The fix

- [ ] 2.1 `tools/pr-flow.py` — resolve the lifecycle subject in a stated total order: `--repo` flag,
      then declared `FRAMEWORK_ROOT`, then working-directory toplevel. Import the resolution the
      probe already uses rather than restating it — one system owns the criterion (class 9).
      *Done when:* 1.1 and 1.2 go green and no other test regresses.
- [ ] 2.2 Add `--repo PATH` to the argument parser, with help text saying it overrides the declared
      estate.
      *Done when:* `--help` names it and an explicit `--repo` beats a conflicting `FRAMEWORK_ROOT`.
- [ ] 2.3 Announce a discovered subject in the route output, not in a comment. When a declared subject
      and the cwd toplevel are both repositories and differ, state which was taken and why.
      *Done when:* the vault-rooted invocation from the proposal prints the framework repo as its
      subject, and a subject-less invocation says it discovered one.
- [ ] 2.4 Refuse legibly when the resolved subject is not a git repository, inside the declared exit
      vocabulary — never a traceback (F33's contract).
      *Done when:* a `--repo /tmp/not-a-repo` run exits `EXIT_BLOCKED` with a named reason.

## 3. The blind spot, stated rather than discovered later

- [ ] 3.1 Record what this fix does **not** cover: it corrects the subject the driver measures; it does
      not verify that an emitted command's effective target matches that subject.
      *Done when:* written into the spec delta, not only into this file.
- [ ] 3.2 Determine whether the unproven escalation in the proposal is real — with `root` resolved to
      the vault, would a composed push have carried `git -C <vault>`? Reachable only by constructing a
      branch state that passes `base` with a vault subject.
      *Done when:* either reproduced and recorded, or recorded as unreachable with the reason. **Do not
      mark this done by reasoning about it.**

## 4. Regression — the checks this repo already ships

- [ ] 4.1 `openspec validate --all --strict` → specs + this change, 0 failed.
      ⚠ Check `openspec --version` against the `package.json` pin before calling any failure a corpus
      defect.
- [ ] 4.2 `python3 -m pytest tests/ -q` → green. Baseline before this change is 386 on `main`.
- [ ] 4.3 `tools/preflight.py . --body-file <PATH>` → CLEAR. ⚠ `--body-file` is not optional: without
      it step 7 prints `SKIP`, and a SKIP reads exactly like a PASS.

## 5. Gate 4 — operator authorization (Tier-0 touch)

Archiving syncs this change's delta into `openspec/specs/maintenance/spec.md`, whose frontmatter
carries `protects: [INV-2, INV-3, INV-6]` — all **Tier 0 (Inviolable)** per `constitution.md` §2. The
`AGENTS.md` hard stop requires the principle, its rationale and its "what breaks" consequence to be
surfaced, and explicit human confirmation received, before the change goes outward.

To be surfaced to the operator, with the sacrifice stated plainly: **the driver stops obeying the
directory you stand in.** An operator who today `cd`s into a repository and expects the driver to act
on it will, once `FRAMEWORK_ROOT` is declared, have it act on the declared estate instead. `--repo` is
the deliberate escape hatch; the loss is that the implicit, familiar gesture no longer governs.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

- [ ] 5.1 Tier-0 touch surfaced with its consequence; **Approved** — operator, <date>
      *Agents may not sign this. Leave unticked until the operator records it.*

## 6. Land it

- [ ] 6.1 Archive this change on this feature branch, before the PR opens (ADR-0040).
- [ ] 6.2 Re-read the branch name against what the branch delivers; rename while still unpushed if it
      drifted. The merged name is permanent in the merge commit subject.
- [ ] 6.3 Walk `tools/pr-flow.py` to `LIFECYCLE COMPLETE`. Never hand-compose the sequence.
      ⚠ **This change edits the driver that walks it.** Use the version on `main` to land this branch,
      or the instrument and the subject share an author and a blind spot — the exact mechanism this
      estate has already measured six times.

## 7. Sequencing decision — operator's, recorded here

- [ ] 7.1 Decide the landing order against `fix/render-root-resolution`, which is in flight at step
      `pushed` and blocked on its own unsigned Gate 4. The branches are independent (this one is cut
      from `main`), but this one changes the instrument the other is landed with.
      *Done when:* the chosen order is written here with its reason, before either is pushed.
