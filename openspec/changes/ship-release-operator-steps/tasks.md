# Tasks — ship-release-operator-steps

> **Durable plan.** Origin: GitHub platform hardening queue item 41 — the clean half of item 37's
> DENY-conversion, deferred until a release was imminent (it now is). Extract the operator-handoff
> machinery into one module both drivers import; make ship-release emit its irreversible steps as
> operator handoffs. NO behaviour change to pr-flow (pure extraction).

## 0. END STATE

`tools/driver_handoff.py` holds the driver-agnostic operator-handoff machinery. `pr-flow.py` imports
it (thin adapters preserve every call site/test). `ship-release.py` emits its tag-push and
release-create as operator handoffs — a saved `next.sh` + the item-39 copy-whole relay block, sidecar
written for the item-40 Stop hook — with a ship-release re-invocation verify tail.

## 1. The shared module

- [x] 1.1 `tools/driver_handoff.py`: `PLAN_TTL_SECONDS`, `saved_plan_path`, `emission_record_path`,
      `relay_line_path`, `write_emission_record`, `discard_saved_plan`, `plan_history_suffix`
      (globals→params, with an explicit `target`), `write_saved_plan` (skeleton; caller supplies
      `assert_lines`/`verify_lines`), `emit_operator_handoff` (block + sidecar). Stdlib-only, offline.

## 2. Rewire pr-flow (behaviour-preserving)

- [x] 2.1 `import driver_handoff`; convert the moved functions to delegations that inject
      `BODY_FILE`/`PR_NUMBER` and build pr-flow's `--assert-preconditions` line + `--after-mutation`
      verify tail. Signatures unchanged (`write_saved_plan(..., assert_args=None)`).
- [x] 2.2 `emit()` uses `driver_handoff.emit_operator_handoff` for the operator relay block.
- [x] 2.3 Whole pre-existing suite green after the extraction (byte-preserving).

## 3. Rewire ship-release

- [x] 3.1 `import driver_handoff` + `shlex`; drop the dynamic `pr-flow.py` import for the record.
- [x] 3.2 `_emit_next` writes a `next.sh` + emits the copy-whole block, keying the history suffix off
      the version and using a ship-release re-invocation verify tail (`_ship_verify_lines`). The raw
      command stays on a `NEXT:` line (operator may run it; the walk test reads it). Fails safe to the
      bare handoff if no branch/write.
- [x] 3.3 Both call sites (tag-push, release-create) pass `version, ns, step`. Emission shape
      unchanged (`_emit_next(f"…")`), so the cwd-independence tests still parse it.

## 4. Tests

- [x] 4.1 `tests/test_driver_handoff.py`: skeleton wraps the caller's verify tail; assert-before-mutation;
      empty-branch ValueError; relay block == sidecar byte-for-byte; explicit-target suffix; record
      round-trip; discard removes plan + record.
- [x] 4.2 `tests/test_ceremony_tools.py`: ship-release emits `next.sh` + `START COPY` for the tag-push
      and release-create; the plan's VERIFY tail re-invokes ship-release (not pr-flow); sidecar matches
      the block; the raw `NEXT:` command is still runnable verbatim.
- [x] 4.3 The pre-existing emission-shape / ceremony / gh-form tests stay green (the extraction did not
      change what ship-release emits, only how it hands it over).

## 5. Regression

- [x] 5.1 Full suite green.
- [ ] 5.2 `openspec validate --all --strict` — 0 failed.
- [ ] 5.3 markdownlint (CI's four `--ignore` paths) — 0 findings.
- [ ] 5.4 `tools/preflight.py . --body-file <path>` → CLEAR.
- [x] 5.5 Real-repo smoke: `ship-release.py v0.1.55` loads and refuses at the CHANGELOG guard.

## 6. Gate 4 — maintenance touch

The delta MODIFIES a requirement in `openspec/specs/maintenance/spec.md` (`protects: [INV-2, INV-3,
INV-6]`). No new control surface, no new refusal (the DENY that governs these already exists, item 37).

To be surfaced — **drafted by the agent; the sign-off is human-only:**

- **What this touches** — generalises "The Operator Handoff Is Emitted As A Copy-Whole Block" from
  pr-flow to both drivers via a shared module. A pure tooling refactor + a spec generalisation.
- **INV-6** — the new module is offline/stdlib-only/deterministic.
- **What breaks if this is wrong:** a bug in the extraction would surface as a pr-flow test failure
  (the suite is the guard) or a broken ship-release handoff (the ceremony test is the guard). No
  control weakens — the item-37 DENY is unchanged.

- [x] 6.1 Tier-0 (maintenance touch) surfaced; **Approved** — Keith Nielsen, 2026-09-22

## 7. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 7.1 Archive on this branch.
- [ ] 7.2 PR body with a `scope` block covering the FINAL diff.
- [ ] 7.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 7.4 Walk `tools/pr-flow.py`; merge; cleanup.
- [ ] 7.5 No deploy-down owed: `tools/` is repo-only (not part of the deployed vault).
