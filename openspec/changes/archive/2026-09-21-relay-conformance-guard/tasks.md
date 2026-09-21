# Tasks — relay-conformance-guard

> **Durable plan.** Origin: determinism Site F43; hardening item 40. The recidivism GUARANTEE (item
> 39 made the correct relay lazy; this catches a wrong one). Bounded against a loop by construction.

## 0. END STATE

The driver writes `.git/pr-flow/relay-line.txt` (the canonical relay line) with every saved plan. A
`Stop` hook byte-checks the agent's relayed line against it and blocks a mismatch — at most ONCE per
emission (keyed on the sidecar), failing open on anything else. Registered in both roots' settings.

## 1. The driver sidecar

- [x] 1.1 In `emit()`, compute the relay line once (`bash <path><suffix>`), use it for the copy-whole
      block AND write it to `.git/pr-flow/relay-line.txt`. Wrap the write in try/except (a failed
      write must not break emission).

## 2. The Stop hook (literate note)

- [x] 2.1 `vault-template/99-Operations/scripts/relay-conformance-guard-script.md`, deploy target
      `.claude/hooks/relay-conformance-guard.py`. Stdlib-only, offline, deterministic (INV-6).
- [x] 2.2 Read JSON stdin: `last_assistant_message`, `cwd`. Extract a `bash …/next.sh` line that
      appears INSIDE a `START COPY` … `END COPY` block (the relay convention). No such line → exit 0.
- [x] 2.3 Read `<cwd>/.git/pr-flow/relay-line.txt` (bounded walk toward repo root). Absent → exit 0
      (fail open).
- [x] 2.4 Byte-compare. Match → exit 0. Mismatch → the block-once-guard:
      - marker = `<repo>/.git/pr-flow/relay-block-marker`, content = sha of the sidecar line.
      - if marker exists and == sha(sidecar) → already blocked THIS emission → print a warning to
        stderr, exit 0 (NO second block).
      - else → write marker = sha(sidecar), then BLOCK: exit 2, stderr names the correct line and
        says to copy the block verbatim.
- [x] 2.5 A matching relay clears the marker (so a later drift on a new step re-arms). Every
      exception path exits 0 (fail open) — the hook can never trap the session.

## 3. Registration

- [x] 3.1 Add the `Stop` hook to `.claude/settings.json` in BOTH roots (framework repo and
      vault-template), alongside the existing PreToolUse/SessionStart entries. SEED, per-instance;
      not verified by parity (item 32).

## 4. Tests (red-first)

- [x] 4.1 RED: a mismatched relayed line is not blocked before the hook exists (exit 0).
- [x] 4.2 Mismatch → exit 2, stderr names the correct line.
- [x] 4.3 Byte-exact relay → exit 0.
- [x] 4.4 No relay block in the message → exit 0.
- [x] 4.5 **Block-once proof:** a second identical mismatch for the same sidecar → exit 0 (marker
      present); a NEW sidecar → exit 2 again (re-armed).
- [x] 4.6 Fail-open: missing sidecar, malformed JSON, unreadable input → each exit 0, no block.
- [x] 4.7 The driver writes `relay-line.txt` byte-identical to the copy-whole block's command.

## 5. Consequences

- [x] 5.1 Render the hook (byte-identity test F29 — the note↔hook parity).
- [ ] 5.2 The vault memory `operator-command-formatting` gains a note that a Stop hook now enforces
      the relay (disk edit; gitignored).

## 6. Regression

- [x] 6.1 Full suite green.
- [x] 6.2 `openspec validate --all --strict` — 0 failed.
- [x] 6.3 markdownlint (CI's four `--ignore` paths) — 0 findings.
- [~] 6.4 `tools/preflight.py . --body-file <path>` → CLEAR.

## 7. Gate 4 — maintenance touch + new control surface

The delta ADDS a requirement to `openspec/specs/maintenance/spec.md` (`protects: [INV-2, INV-3,
INV-6]`), and the change registers a new `Stop` hook.

To be surfaced — **drafted by the agent; the sign-off is human-only:**

- **A new control surface exists** — a `Stop` hook that can block a turn. Bounded to one block per
  emission and fail-open, so it cannot trap the session, but it is a new refusal.
- **INV-6** — the hook is offline/stdlib-only/deterministic; it fails open.
- **What breaks if this is wrong:** a false positive blocks a legitimate turn once (then falls
  through); a missed drift lets a wrong relay through (the operator still catches it, as today). The
  block-once and fail-open tests are the guards.

- [x] 7.1 Tier-0 (maintenance touch + new control surface) surfaced; **Approved** — Keith Nielsen, 2026-09-21

## 8. Land it

⚠ **Archive BEFORE the first push** (the #121 lesson).

- [ ] 8.1 Archive on this branch.
- [ ] 8.2 PR body with a `scope` block covering the FINAL diff.
- [ ] 8.3 `tools/preflight.py . --body-file <path>` → CLEAR.
- [ ] 8.4 Walk `tools/pr-flow.py`; merge; cleanup.
- [ ] 8.5 ⚠ Deploy-down owed: the hook is a literate note AND needs settings.json registration in the
      live vault (the registration is NOT carried by template-mirror — settings.json is SEED). So the
      deploy-down is render + a manual settings.json edit in the vault. Operator-run.
