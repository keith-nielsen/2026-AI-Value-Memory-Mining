## 1. Manifest — declare the two governance-content prefixes

- [x] 1.1 Add `96-Runbooks/` and `.claude/commands/` to `lockstep` in
      `tools/template-sync-manifest.json`, and update its `_comment` so the SEED list no longer
      implies `.claude/` is wholly seed — `.claude/settings.json` specifically remains seed.
      *Done when:* `python3 -c "import json;print(json.load(open('tools/template-sync-manifest.json'))['lockstep'])"`
      prints four prefixes.
- [x] 1.2 Confirm the change is detected, not assumed: `tools/template-parity.py $VAULT_ROOT` now
      reports **DRIFT** on the two known-stale files and exits `1`.
      *Done when:* the run names `session-bootstrap-loader.md` and `vmm-session-rebooted.md` and
      exits non-zero. **A pass here would mean the prefixes were not picked up.**

## 2. The `/vmm-repo-github` stub

- [x] 2.1 Add `vault-template/.claude/commands/vmm-repo-github.md` — the stable stub: the
      irreducible `pr-flow.py --plan` instruction inline, then a pointer to the content card, and a
      loud stop if the card is missing or carries no `CARD-VERSION:` marker.
      *Done when:* the file exists and its `description:` frontmatter names the trigger vocabulary.
- [x] 2.2 Verify the stub is under a lockstep prefix and therefore compared.
      *Done when:* `tools/template-parity.py $VAULT_ROOT` reports it `MISSING-IN-LIVE` before the
      mirror runs — proving the new prefix actually covers it.

## 3. Regression — the checks this repo already ships

- [x] 3.1 `openspec validate --all --strict` → 6 specs + this change, 0 failed.
- [x] 3.2 `python3 -m pytest tests/ -q` → green, with attention to `test_template_parity.py` and
      `test_template_mirror.py`, which encode the comparator's contract.
- [ ] 3.3 `tools/preflight.py . --body-file <PATH>` → CLEAR. ⚠ `--body-file` is not optional: without
      it step 7 prints `SKIP`, and a SKIP reads exactly like a PASS.

## 4. Land it

- [ ] 4.1 Archive this change on this feature branch, before the PR opens (ADR-0040).
- [ ] 4.2 Walk `tools/pr-flow.py` to `LIFECYCLE COMPLETE`. Never hand-compose the sequence.

## 5. Deploy-down — the point of the whole change

- [ ] 5.1 `tools/template-mirror.py` — carries the drifted runbook (43 lines), the drifted command
      (12 lines, including *"never hand-compose a `gh` mutation"*), and the new stub.
      *Done when:* the mirror reports the three files applied.
- [ ] 5.2 `tools/template-parity.py $VAULT_ROOT` → **0 drift**, exit `0`.
      *Done when:* observed. This is the evidence all three landed; task 1.2's expected failure is
      what makes this pass meaningful rather than vacuous.
- [ ] 5.3 Confirm the vault's `.claude/commands/vmm-repo-github.md` resolves its card, and that a
      deliberately renamed card produces the loud stop rather than silent degradation.
      *Done when:* both the success and the refusal have been observed.

## 6. Close the record

- [ ] 6.1 Mark hardening queue item 34 shipped, citing the parity run from 5.2.
- [ ] 6.2 Note that item 32 (hook registration) is untouched and still open — `.claude/settings.json`
      remains seed by design, so registration is still unverifiable by comparison.
