<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: fix-commit-gate-env-guard

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**MODIFIES** the Requirement "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)" by one
additive clause (governance hooks honor the bare-drive guarantee) + one scenario. **No principle
is overridden or weakened**; INV-11 enforcement by the hook is byte-for-byte unchanged in
behavior. Conforming amendment per repo precedent (every archived change touching a protected
spec ran this ceremony, including conforming ones — `spec-as-code-runbooks` et al.).
**Tier:** 0-adjacent (repairs the *implementation* of an existing requirement; §5 AI hard-stop
honored — surfaced with explicit sign-off at Gate 4)
**Proposer:** Keith Nielsen (drafted by Claude Code at Keith's direction, 2026-07-05 — "format up
the one-line fix for the next unblocker")
**Date:** 2026-07-05

---

## Why

The Phase-1a live acceptance for `add-shared-vault-lib` (2026-07-05) proved SE-5 and exposed the
next-layer defect in the same run: the bare-exact drive invocation resolved the vault root,
rendered `kanban.md`, staged it — and died at the **commit-gate hook**, whose guard
`: "${VAULT_ROOT:?VAULT_ROOT must be set}"` demands the environment a bare invocation
contractually cannot have. The v0.1.16 `maintenance` requirement already mandates bare-no-env
drive-path operation; the hook violated that guarantee at the final step.

Audit: `VAULT_ROOT` appears in the hook exactly once — the guard itself. The body reads only
staged git state and calls `${HOME}/bin/vault_naming.py` (stdlib-only). The guard is dead code.
The companion `push-guard` hook already self-locates (`${VAULT_ROOT:-.}` + conditional config
sourcing) and needs no change.

## What Changes

- **`commit-gate-script.md`:** delete the vestigial guard line; Rationale documents the
  environment-free property and its burn-in provenance; `updated:` bumped. The naming check,
  blocking behavior, and exit semantics are unchanged.
- **`maintenance` spec:** MODIFY "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)" —
  ADD the clause that the bare-drive guarantee extends through governance hooks (a hook needing
  the vault root derives it from `git rev-parse --show-toplevel`, never the caller's env) + a
  scenario pinning the commit-gate's env-free operation.
- **CHANGELOG** `[Unreleased]` entry.
- **No ADR:** a one-line dead-code removal restoring an already-decided contract (ADR-0023
  documents the contract; this change is its enforcement reaching the hook layer).

**Explicitly NOT in this change:** any behavioral change to naming enforcement; the `runtime:`
enum alignment; wave-2 `vault_lib` adoption; B3/B4.

## Capabilities

### New Capabilities
- _(none)_

### Modified Capabilities
- `maintenance`: MODIFIED Requirement "Shared Fleet Plumbing and Exit-Code Contract (vault_lib)"
  (additive hook clause + scenario).

## Impact

- Spec delta (synced at archive): `maintenance`, one requirement modified additively.
- Implementation: `vault-template/99-Operations/scripts/commit-gate-script.md` (−1 guard line,
  Rationale +4 lines).
- Live vault (operator-applied, out of band): `cp` the note into live `99-Operations/scripts/`,
  `render` (deploys `99-Operations/hooks/pre-commit`), `reconcile` zero drift; then the agent
  re-runs the bare kanban drive end-to-end — expected fully green, closing Phase-1a.
- Residual risk: none identified — the hook gains no behavior and loses a precondition nothing
  consumed.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** INV-11's commit-gate must fire on every commit and block
bad names — that behavior is untouched; the diff removes only a precondition about *who may run
the hook* (callers with sourced env), which was never part of the invariant and actively broke
the drive path INV-2/INV-3 machinery depends on. The spec clause being added is the general rule
the burn-in taught: pre-action guards must not assume operator-shell context, because the
agent-facing drive path is contractually context-free.

**Blast radius:**
- [x] `openspec/specs/maintenance/spec.md` — MODIFIED requirement (delta now; sync at archive)
- [x] `vault-template/99-Operations/scripts/commit-gate-script.md` — the fix
- [x] `push-guard-script.md` — audited, conforms already, untouched
- [x] `.github/scripts/validate-scripts.sh` — untouched; exercises the hook (`bash -n`,
      shellcheck, every smoke commit runs through `core.hooksPath`)
- [x] `CHANGELOG.md` — `[Unreleased]`
- [x] `constitution.md` / `project.md` / ADR index — untouched
- [x] `vocabulary-lint` — no off-metaphor terms

**Discrepancies surfaced for Gate 4:** none new. (The `runtime:` enum inconsistency on this very
note — `manual` vs `git hook` — remains the known, separately-queued follow-up; deliberately not
bundled.)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** merge → operator copies the one note into live `99-Operations/scripts/` → `render`
→ `reconcile` zero drift → agent end-to-end bare-drive probe.

**Regression tests that MUST pass before Gate 3 completes:**
- [ ] `openspec validate fix-commit-gate-env-guard --strict` + `openspec validate --all --strict`
- [ ] `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [ ] End-to-end on a rendered sandbox vault with `core.hooksPath` set and `VAULT_ROOT` unset:
      bare `~/bin/vault-kanban-render.py` → write + **commit through the hook** succeed
- [ ] Negative control, same env-free setup: a staged `.md` with a violating name is still
      `BLOCKED` (INV-11 unchanged)

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — fix, spec delta, CHANGELOG
**All repo-side regression tests green (local, 2026-07-05):** ☑
- `openspec validate fix-commit-gate-env-guard --strict` ✓ · `--all --strict` ✓ (8/8)
- `.github/scripts/validate-scripts.sh` → `VALIDATION OK`
- Env-free end-to-end (sandbox vault, `core.hooksPath` set, `VAULT_ROOT` unset): bare
  `~/bin/vault-kanban-render.py` → render + **commit through the hook**, rc 0
- Negative control, same env-free setup: staged `bad:name.md` (forbidden `:`) →
  `INVALID … forbidden char(s): :` + `BLOCKED … (INV-11)` + commit rc 1. (First control attempt
  used `Bad Name!.md`, which *correctly* passed — space/`!` are within the enforced
  cross-platform floor; kebab enforcement is deferred by design, ADR-0015. Recorded so a future
  reader doesn't mistake that for a hook failure.)
**CI green on this PR:** ☐ (runs on push — human)
**Live acceptance:** ☐ (post-apply, agent-executed)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑ (2026-07-05 — the 5-file branch
diff at `517d8cf` matches the Gate-1 list: maintenance delta, hook note, CHANGELOG, proposal,
tasks; no `protects:` frontmatter changed)
**Consequences explicitly accepted:**

> Sacrifice (proposed wording for sign-off): none of substance — the hook loses a precondition
> that nothing consumed, and the spec gains the clause making that permanent: future hook authors
> may not lean on a sourced operator shell and must derive context from git. The only cost is
> that constraint on future hook design, accepted deliberately.

**ADR:** none (enforcement of the ADR-0023 contract at the hook layer; no new decision)

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen
Date: 2026-07-05

> Provenance of this record: the operator executed the Gate-4 publish sequence deliberately —
> reviewed the handoff, pushed the branch, merged PR #8 (`23e0198`) with CI green, applied the
> change live (`7f9b33a`), and confirmed completion in-session ("No errors"). The sign-off block
> was left unfilled at merge time; the drafting agent recorded it post-merge. The operator's push
> of this record to origin is the confirming act — agents may not originate sign-off, and did not.
