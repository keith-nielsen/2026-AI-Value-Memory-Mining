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
- [ ] 4.3 `tools/preflight.py . --body-file <PATH>` → CLEAR.
- [x] 4.4 Add the `constitutional-impact` declaration — archiving syncs this delta into
      `openspec/specs/maintenance/spec.md`, which carries `protects:`.

## 5. Land it

- [ ] 5.1 Archive on this feature branch, before the PR opens (ADR-0040).
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
