---
type: runbook
id: render-reconcile-runbook
title: Render / reconcile — the Layer-0 deploy and drift loop
trigger: "a meta-script note changed (merge, apply, edit) and the host must match Layer 0 — or you suspect a deployed script was hand-edited"
applies-to: vault
class: procedure
last-validated: 2026-07-06
---
# Runbook — Render / Reconcile

## Purpose

Keep the deployed fleet byte-identical to its literate sources (INV-3): `render` deploys every
note's single code fence to its `deploy_target`; `reconcile` detects drift and **never** fixes it.
This loop is the only path from `99-Operations/scripts/` to the host — hand-editing a deployed
script is drift by definition.

## Preconditions

- `[script]` `~/bin/vault-render.py` present (bootstrap: extract its code fence from
  `render-reconcile-script.md` once, on first install).
- Notes conform: exactly one `python|bash` fence each (the render lint enforces this —
  `VIOLATION`, exit 1, nothing rendered for a non-conforming note).

## Steps

1. `[gate]` Changed notes reached `99-Operations/scripts/` through the governed path (OpenSpec
   ceremony → merge → operator `cp`) — never ad-hoc edits.
2. `[script]` `~/bin/vault-render.py render` — deploys all notes; `chmod +x` applied. **Wholly
   operator-run: *every* target is agent-denied, not merely those under `.claude/` and
   `99-Operations/hooks/`.** `~/bin/` is out-of-vault and default-denied, so a sandboxed agent
   fails on the **first** note and deploys nothing (verified end-to-end against the live
   read-only mounts, P17). An agent attempt prints `BLOCKED: cannot write …`, names the
   operator-only reason, and exits **4** — not a traceback, and not a broken deploy.
3. `[script]` `~/bin/vault-render.py reconcile` — expect `ok:` for every note, exit 0.
4. `[human]` On `DRIFT:` output: diff the target against the note, decide which side is truth,
   route a real change through the ceremony if the *note* must change — then re-run `render`.

## Pitfalls

- Reconcile detects, never overwrites — resolving drift by hand-editing the *target* recreates
  the problem; the note is the source of truth.
- A `VIOLATION` (fence count ≠ 1) means nothing rendered for that note — fix the note, don't
  assume the old target is current.
- Bare invocation works with no sourced environment (root marker-walk), but rendering protected
  targets requires an operator shell — the agent's sandbox correctly denies them.

## Verification

- `~/bin/vault-render.py reconcile` exits 0 with `ok:` for all notes (17 at last validation).

## Rollback

- A bad render is repaired by fixing the note (governed) and re-rendering; deployed targets carry
  no state of their own.
