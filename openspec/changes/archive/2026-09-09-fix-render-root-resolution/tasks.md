## 1. The fix, in the literate note

- [x] 1.1 Join a relative `deploy_target` to the resolved root in
      `vault-template/99-Operations/scripts/render-reconcile-script.md`; honour an absolute path as
      written. Edited in the NOTE (INV-3), never the rendered file.
      *Done when:* the shipped code block contains no bare
      `pathlib.Path(os.path.expanduser(str(post["deploy_target"])))`.

## 2. The gate that misdescribed it

- [x] 2.1 Correct the clean-ops gate in
      `vault-template/96-Runbooks/session-bootstrap-loader.md` — env-FIRST, not env-free — and
      instruct pinning `VAULT_ROOT` when the target is not the tree you stand in.
      *Done when:* the phrase "env-free" no longer appears as an assertion about the fleet.

## 3. Tests — each observed failing first

- [x] 3.1 `test_target_is_resolved_against_the_notes_root_not_the_cwd` — the discriminating case.
      *Done when:* observed **FAIL** against the pre-fix note and **PASS** after. ⚠ Its first cut
      passed against the defect; rebuilt so a spurious `DRIFT` about the other tree is the signature.
- [x] 3.2 `test_render_source_never_resolves_a_bare_relative_deploy_target` — structural guard.
      *Done when:* observed FAIL against the pre-fix note.
- [x] 3.3 `test_note_side_drift_is_detected` — baseline only, **labelled non-discriminating** in its
      own docstring. *Done when:* the label states it passes either way and is not counted as
      coverage of this defect.
- [x] 3.4 Red proof recorded: **2 of 3 fail** against the pre-fix note.

## 4. Regression

- [x] 4.1 `python3 -m pytest tests/ -q` → **389 passed** (386 baseline + 3).
- [x] 4.2 `openspec validate --all --strict` → specs + this change, 0 failed.
- [x] 4.3 `tools/preflight.py . --body-file <PATH>` → CLEAR.
- [x] 4.4 Add the `constitutional-impact` declaration — archiving syncs this delta into
      `openspec/specs/maintenance/spec.md`, which carries `protects:`.

## 5. Land it

- [x] 5.1 Archive on this feature branch, before the PR opens (ADR-0040).
- [ ] 5.2 Walk `tools/pr-flow.py` to `LIFECYCLE COMPLETE`. Never hand-compose the sequence.

## 6. Deploy-down — operator-run

- [ ] 6.1 `tools/template-mirror.py <VAULT_ROOT>` — carries the corrected note and runbook.
      ⚠ `99-Operations/` and `.claude/` are agent-write-denied; the mirror is the operator's step.
- [ ] 6.2 `vault-render.py render` as the operator, so the corrected note reaches
      `99-Operations/bin/vault-render.py`. **Until this runs, the live fleet still carries the
      defect** — the fix is in the note, and the note is not what executes.
- [ ] 6.3 `template-parity.py $VAULT_ROOT` → 0 drift, and `vault-render.py reconcile` → 15/15 ok.

## 7. Re-validate what the defect invalidated

- [ ] 7.1 Re-run the UAT harness fidelity checks (T0) with `VAULT_ROOT` pinned to the replica, and
      confirm F0.2 now fails when deliberately mis-pinned.
      *Done when:* the harness is demonstrated capable of catching its own misconfiguration — the
      property it lacked when it reported a clean pass against the wrong tree.

## 8. Gate 4 — operator authorization (Tier-0 touch)

Archiving synced this change's delta into `openspec/specs/maintenance/spec.md`, whose frontmatter
carries `protects: [INV-2, INV-3, INV-6]` — all **Tier 0 (Inviolable)** per `constitution.md` §2.
The `AGENTS.md` hard stop requires the principle, its rationale and its "what breaks" consequence to
be surfaced, and explicit human confirmation received, before the change goes outward.

Surfaced, with the sacrifices stated rather than minimised:

- **INV-3 is strengthened, not relaxed.** The fix is authored in the literate note, never in the
  rendered file, and `reconcile` stays detection-only. What changes is that it detects drift in the
  tree it was pointed at rather than sometimes reporting on another one.
- **INV-6 and INV-2 are untouched.** The change is a path join — no I/O is added, and no commit
  ceremony is altered.
- **The behaviour change is a narrowing.** After the fix the tool reads and writes strictly fewer
  paths than before, only those under the resolved root. No caller gains reach, no guarantee is
  relaxed, no check is removed.
- **The cost is permanent constraint.** The two ADDED requirements bind every future tool in the
  estate, and anything relying — knowingly or not — on cwd-relative resolution will now get a
  different verdict.
- **What breaks if this is wrong:** `render` mode writes. A root-resolution defect here does not fail
  loudly; it deploys one tree's code blocks into another tree's paths while reporting `ok`, which is
  the exact failure this change exists to close.

⚠ The `constitutional-diff-gate` is **report-only during burn-in and cannot fail the build**, so this
sign-off is the operative control, not CI.

⚠ Recorded eight days after this change was archived (2026-09-09). The branch was parked; the
sign-off was taken on 2026-09-17 after the rebase onto `main` (`5ed499d`). The 2026-09-13 sign-off
for `md-content-preservation-check` explicitly excluded this change, so the gap is deliberate and
this record closes it rather than backdating it.

- [x] 8.1 Tier-0 touch surfaced with its consequence; **Approved** — Keith Nielsen, 2026-09-17 15:30:17 GMT (+08:00 local)
      Given after the four sacrifices above were put to the operator explicitly, together with the
      state of the branch at the time of asking: rebased onto `main` (`5ed499d`) with one spec
      conflict resolved by keeping all six tail requirements in landing order and no requirement text
      altered; 8 markdownlint findings introduced by the rebase and repaired to 0 on the exact
      invocation `ci.yml` uses; suite 424 passed before and after; and `preflight.py --body-file`
      CLEAR at 13/16 CI jobs reproduced, scope-review PASS over all 10 files.
      The operator's words: *"Approved, Keith Nielsen"*, with the timestamp recorded in GMT and the
      local offset included at their instruction.
