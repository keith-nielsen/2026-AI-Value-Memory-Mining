<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [x] 1.1 `maintenance` ADDED: *An Outward Command Is Checked Against The Driver's Emission* (6 scenarios)
- [x] 1.2 `maintenance` ADDED: *A Downgrade Record Is Forgeable And Says So* (2 scenarios)
- [x] 1.3 Confirm nature is ordinary, not override — ADD-only against `maintenance`
      [`protects: [INV-2, INV-3, INV-6]`]; the change cannot create a refusal, so it removes no
      permission. Precedent: PR #53 / #80 / #87

## 2. The emission record

- [x] 2.1 Define the record: `command` (verbatim), `step`, `branch`, `expires`. Written to
      `.git/pr-flow/emitted.json`, beside the saved plan, reusing `PLAN_TTL_SECONDS`
- [x] 2.2 `tools/pr-flow.py` `emit()` (`:498`) writes it for **every** step, not only
      `runs == OPERATOR` — the asymmetry this change exists to correct
- [x] 2.3 `discard_saved_plan()` also discards the emission record at LIFECYCLE COMPLETE. **A record
      that outlives its step is an authorisation left on the desk** — the item-20 shape
- [~] 2.4 **BUILT, UNTESTED** — `_record_emission()` imports pr-flow.py's writer rather than
      re-implementing it (a second copy of the record format would be a fork with no merge).
      No test exercises it; `[x]` is not available. `tools/ship-release.py` writes records through the same helper (design decision 2), else
      its pushes regress to ASK

## 3. The guard — via the META-SCRIPT NOTE, never the rendered hook

⚠ **INV-3.** The source of truth is
`vault-template/99-Operations/scripts/outbound-publish-guard-script.md`; its frontmatter carries
`deploy_target: .claude/hooks/outbound-publish-guard.py`. The rendered artifact is **never** edited
directly, and drift is detected by `reconcile`, never auto-fixed.

- [x] 3.1 Generalise `_targets_vault(cmd, cwd)` → `_zone(cmd, cwd)` returning `vault | governed |
      elsewhere`. `governed` is `$FRAMEWORK_ROOT` (already declared in `config.env` by
      `estate-scoped-capability-probe`). Reuse the existing `cd` / `-C` / `-R` resolution — do not
      write a second resolver
- [x] 3.2 `vault` → existing HARD DENY, unchanged. `elsewhere` → existing ASK, unchanged
- [x] 3.3 `governed` + byte-identical live record for the current branch → **ALLOW**, printing the
      step that matched (design decision 1)
- [x] 3.4 `governed` + no match → **ASK plus a diff naming what differs** — not merely "mismatch"
- [x] 3.5 **The invariant, as code and as a test:** no path added here returns `deny`. Absent,
      expired, wrong-branch, unparseable and comparison-fault all fall through to ASK
- [x] 3.6 Stdlib only, no network, no `subprocess` — the guard is AST-analysed by
      `inv6-offline-check.py` and is one of the two most security-relevant scripts in the fleet
      (`maintenance` spec, *naming-versus-calling*). `pathlib` + `json` only
- [ ] 3.7 ⛔ **BLOCKED — OPERATOR-ONLY, AND IT BLOCKS THE MERGE.** `vault-render.py render`
      refuses for the agent by design. The two tracked rendered copies
      (`.claude/hooks/` and `vault-template/.claude/hooks/`) were byte-identical to the note
      at HEAD and are now DRIFTED because this change edits the note. `reconcile` confirms:
      `DRIFT: .claude/hooks/outbound-publish-guard.py differs from outbound-publish-guard-script.md`.
      Hand-extracting the block myself would be class-10 stage 1 inside its own fix, so it is
      not done. **Nothing in CI checks these two paths** — `template-sync-manifest.json` covers
      only `99-Operations/scripts|schemas`, so this drift would ship silently. Separate finding

## 4. Tests — the fall-through cases first

The invariant is the safety property, so the adversarial cases lead. A suite proving only the happy
path proves nothing about "cannot create a refusal".

- [x] 4.1 No record → **ASK** (not deny)
- [x] 4.2 Expired record → **ASK**
- [x] 4.3 Record for another branch → **ASK**
- [x] 4.4 Corrupt / unparseable record → **ASK** (fail toward the prompt, never toward allow or deny)
- [x] 4.5 Mangled command with a live record → **ASK**, and the diff names the cause. Fixture: the
      real 2026-08-16 command, `R=…; cd "$R"; timeout 180 git -C "$R" p[u]sh …`
- [x] 4.6 Verbatim command with a live record → **ALLOW**, naming the step
- [x] 4.7 Vault target **with** a valid-looking record → still **DENY**. The record must not be able
      to unlock INV-14; this is the test that proves the downgrade is scoped
- [x] 4.8 Ungoverned repository → behaviour byte-identical to today, record or no record
- [x] 4.9 `inv6-offline-check.py` still passes on the note; `tests/test_inv6_offline.py` still passes
- [x] 4.10 Every test above observed **failing without the change** before its box is ticked

## 5. Documents this makes true or false

- [x] 5.1 The script note's Rationale describes the third zone and **states the record is forgeable**
- [x] 5.2 ADR-0043 — context / options / choice / consequence, citing ADR-0018's tripwire posture and
      ADR-0027's effective-target refinement
- [x] 5.3 `CONTRIBUTING.md` — one line under *Landing a change*: run the emitted command verbatim;
      deviation now prompts with a diff
- [x] 5.4 Verify no document claims the mechanism authorises or verifies a command. It matches a
      record. **Requirement 2 exists because that distinction is exactly what this repo has had to
      retract before**

## 6. Deliberately NOT in this change

- [ ] 6.1 **Stages 2 and 3 of class 10** — misreading a failure, and instituting a workaround
      unilaterally. This change addresses stage 1 only, and the operator's standing concern that the
      recidivism is unsolvable is **not** claimed to be answered
- [ ] 6.2 **Making the record unforgeable.** Out of scope by design, not by omission — see
      requirement 2 and ADR-0018's stated posture
- [ ] 6.3 **Item 29's vocabulary work** (`AUTHENTICATED`/`UNAUTHENTICATED`/`ABSENT`, the `gh
      credential` rename, `--json`). Separate change; do not fold

## 7. Landing

- [x] 7.1 `python3 tools/preflight.py .` **CLEAR** (caught a real README ADR-count drift first:
      42 claimed, 43 present — the second time pre-flight has caught exactly that)
- [ ] 7.2 Driven landing via `tools/pr-flow.py`; **run the emitted command verbatim** — this change is
      about that, and hand-composing it would be the class-10 stage-1 shape inside its own fix
- [ ] 7.3 PR body carries a `scope` block; the archive rename declares **both** sides
- [ ] 7.4 Archive on the feature branch in the same PR (ADR-0040)
- [ ] 7.5 Deploy-down to the live vault is **operator-applied** (the note and the rendered hook sit in
      `denyWrite`); verify byte-identical afterwards — and remember the SEED/LOCKSTEP distinction:
      `99-Operations/scripts/` **is** lockstep, so byte-identity is the correct test here

## 8. Gate 4 — human sign-off (not agent-delegatable)

- [x] 8.1 **Approved** — Keith Nielsen, 2026-08-17. Reviewed the proposal, this task file and the
      spec delta. Decisions reviewed and accepted as recommended:
      (a) **silent allow vs logged allow** — recommended: allow but print the matched step, so the
      downgrade is auditable in the transcript;
      (b) **the record is forgeable by the agent** — accepted deliberately under ADR-0018's tripwire
      posture, and written into the spec as a requirement rather than a footnote;
      (c) **`ship-release.py` included** rather than deferred, to avoid shipping a known ASK regression.
