# Tasks — deny-irreversible-outbound

> **Durable plan.** Origin: adversarial probe 2026-09-20 (item 37); the DENY-conversion bucketed by
> irreversibility. Scope is **(a) guard-only**; the ship-release routing refactor is a separate
> queued change (hardening item 41), not this one.

## 0. END STATE

The harness outbound guard hard-DENIES every outward command that is not a plain branch push — tag
push, remote add/set-url, repo create/make-public, release publish/edit/upload (subcommand + REST),
release asset upload, package publish — evaluated BEFORE the driver-emission downgrade. A branch push
is unchanged (downgrade / ASK). The vault HARD DENY is unchanged and first. The `access-control`
"Private by Default" requirement no longer claims the ASK holds in every permission mode.

## 1. The guard change

- [x] 1.1 In `outbound-publish-guard-script.md`, add `is_reversible_outbound(cmd)` — true iff the
      command is a `git push` that is NOT a tag push (`refs/tags/`) and not a remote op.
- [x] 1.2 In `main()`, after the vault HARD DENY and BEFORE the driver-emission downgrade, add:
      if `(OUTWARD or PUBLISH) and not is_reversible_outbound(cmd)` → emit `deny` with a message that
      (a) says the form is irreversible and operator-only, (b) names the operator as who runs it, and
      (c) states DENY is used because the ASK does not surface in auto mode. Placed before the
      downgrade so a byte-matched irreversible emission is still denied.
- [x] 1.3 The reversible branch push is untouched: it reaches the downgrade (allow on byte-match) or
      the ASK, exactly as before.

## 2. Tests (red-first)

- [x] 2.1 RED: a tag push, `gh repo create`, `git remote add`, a REST release write, and
      `uploads.github.com` are each **ask** before 1.2 and **deny** after.
- [x] 2.2 A branch push (`git push origin <branch>`, non-vault) is **ask** both before and after
      (unchanged); a vault-targeted push is **deny** both (unchanged).
- [x] 2.3 An irreversible form that byte-matches a live driver emission is STILL denied (the check
      precedes the downgrade) — write an emission record, then assert deny.
- [x] 2.4 A branch-push that byte-matches a live driver emission is STILL allowed (downgrade intact).
- [x] 2.5 Mutation: delete the irreversible-DENY branch from a copy of the guard; a tag push flips
      back to ask (the rule is shown to matter). Assert the anchor replaced exactly once.

## 3. Consequences

- [x] 3.1 Render the hook to `.claude/hooks/outbound-publish-guard.py` (byte-identity test F29).
- [x] 3.2 `docs/version-control-legal-moves.md` §1.3 (the ASK list) is updated: the release/tag/
      remote/repo-create forms move from ASK to DENY; a branch push stays ASK. Same-change edit
      (restating a rule without updating its documented copy is class 9).
- [x] 3.3 File the ship-release routing refactor as hardening-queue **item 41** (make ship-release
      emit the tag-push/release as operator steps with the item-39 relay block, so the release
      ceremony does not hit a mid-flow DENY). Not built here.

## 4. Regression

- [x] 4.1 Full suite green.
- [x] 4.2 `openspec validate --all --strict` — 0 failed.
- [x] 4.3 markdownlint (CI's four `--ignore` paths) — 0 findings.
- [~] 4.4 `tools/preflight.py . --body-file <path>` → CLEAR.

## 5. Gate 4 — access-control touch (protected, INV-14)

The delta MODIFIES the `access-control` "Private by Default" requirement and ADDS the
irreversible-outbound requirement. `protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`.

To be surfaced — **drafted by the agent; the sign-off is human-only and is NOT recorded until given:**

- **A new refusal exists.** Irreversible outbound is denied on the agent's channel in every mode.
  Wrong in the strict direction, it blocks work that was fine.
- **The ceremony changes shape:** ship-release's tag-push/release now hit a DENY and are handed to the
  operator (until item 41 routes them cleanly). No release is being cut now.
- **A false claim is corrected:** the "ASK holds in any permission mode" statement is narrowed to what
  was measured. This strengthens INV-14 (adds a mode-independent stop) and corrects F31.
- **What breaks if this is wrong:** an over-broad DENY blocks a legitimate reversible push, or a
  too-narrow reversible test lets an irreversible form through as ask. The red-first and mutation
  tests are the guards.

- [x] 5.1 Tier-0 (access-control / INV-14) touch surfaced; **Approved** — Keith Nielsen, 2026-09-21

## 6. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson): `openspec archive deny-irreversible-outbound`
applies the delta to `access-control`, then the pushed diff includes the archived paths and the scope
block covers the final state.

- [ ] 6.1 Archive on this branch.
- [ ] 6.2 PR body with a `scope` block covering the FINAL diff.
- [ ] 6.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 6.4 Walk `tools/pr-flow.py`; run each emitted step; merge; cleanup.
- [ ] 6.5 ⚠ Deploy-down owed (with prefer-rest's): the guard is a literate note, so the live vault
      keeps the old guard until `template-mirror` + `vault-render`. Operator-run; batch with #121's.
