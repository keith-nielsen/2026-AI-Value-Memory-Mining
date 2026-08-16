---
type: runbook
id: session-bootstrap-loader
title: Session bootstrap loader (cold-start prime)
trigger: "a fresh or /clear'd agent session begins, before any vault/repo work — load env, engage the gates, probe capabilities, know the pointers"
applies-to: both
class: procedure
last-validated: 2026-08-16
---
# Runbook — Session Bootstrap Loader

## Purpose

Prime a cold-start agent session with the **minimum** context for **maximum** governance confidence:
set the environment, engage the non-negotiable gates, and know where to read the rest just-in-time —
so the agent never operates from an empty or degraded context (the failure class catalogued in the
`llm-context-reboot` dig). Minimum bootstrap = small card + JIT pointers; maximum confidence = the
gates + verification, not loading the whole rulebook.

Context alone is not enough: what the agent *may do* is environment state that changes between
sessions without notice, so the prime also **measures** its own reach rather than recalling it.

## Preconditions

- Operating in the live vault (`$VAULT_ROOT`).
- The harness auto-loads `CLAUDE.md` / `AGENTS.md` and the memory `MEMORY.md` index — this runbook is
  their single source of truth; the SessionStart hook surfaces it automatically.

## Steps

1. `[script]` **Env** — `source 99-Operations/config.env` (sets the estate — `VAULT_ROOT` and
   `FRAMEWORK_ROOT` — plus `PILLARS` and the venv on `PATH`). Re-source per shell (it does not
   persist). Kills the `VAULT_ROOT` wall, and declares the second root step 3 needs.
2. `[gate]` **Engage the operating card** — acknowledge these five, don't merely possess them:
   - **Governance-first** — before any structural / naming / spec / mold / script change, *read*
     the invariants in `CLAUDE.md` and the governing schema in `99-Operations/schemas/`; a
     deployed vault carries no governance corpus of its own — framework changes are made upstream
     and deployed down, never improvised in the vault.
   - **Re-read before acting** — apply an established rule from its artifact (spec / memory / runbook),
     never from recollection.
   - **Autonomy bans** — no autonomous writes to `40-Treasury/` or `99-Operations/` (INV-4/5).
   - **Clean ops** — hooks and the script fleet are env-free (root self-resolution, ADR-0023);
     source `config.env` only for operator-shell conveniences (venv on `PATH`, vocabulary
     overrides); separate the action from its verification.
   - **Measure, don't infer** — never assert a *capability* limit (write scope, network reach, auth)
     that has not been probed **this session**. One error message is not a capability finding; a
     denial names the command that failed, not the class it belongs to. Capabilities are environment
     state — config changes silently between sessions, so recollection goes stale without any event
     the agent can observe. Probe (step 3), then speak.
3. `[agent]` **Capability probe** — measure the session's own reach BEFORE the first claim about it.
   **Reference the instrument; never hand-roll or restate one.** The `maintenance` Requirements
   *"Platform Capability Is Probed, Not Recalled"* and *"GitHub Reads Degrade To An Unauthenticated
   Channel"* already own this criterion — import it. The capability reporter is the meta-script the
   harness adapter names; it reports channel · state · **runs / authority**, and exits `0` even when a
   channel fails, because a probe that crashes teaches its caller to stop probing.
   It measures the **declared estate** — `VAULT_ROOT` and `FRAMEWORK_ROOT`, both set by step 1 — and
   **prints the roots it used**. It derives no subject from the working directory, so where you run it
   from does not change the answer.

   Read its output as **independent layers — never infer one from another**:
   - **vault remotes** — a remoteless vault is **INV-14 holding**, not a broken channel. A vault that
     has a remote is a **violation**: the existence of the capability is the breach. See Pitfalls.
   - **write scope** — authoritative and volatile; re-probe every session, never recall. The probe
     **attempts a real write** into each protected subtree, because a protection assumed is not a
     protection measured.
   - **`gh` credential** — an operator keyring is unreadable from a confined session; a tool reporting
     its own token "invalid" is describing *that process*, not the operator's account.
   - **`git` credential** — a **separate channel**, which may succeed while `gh` mutations do not. A
     credential-*lock* error naming a read-only filesystem is a write failure, **not** a network verdict.
   - **reachability** — reads may succeed against hosts absent from any configured allowlist, where
     that allowlist suppresses prompts rather than denying traffic.

   **`UNDECLARED` is not `FAILED`.** With `FRAMEWORK_ROOT` empty the framework layers report
   `UNDECLARED` and the probe still exits `0` — a deployed vault with no framework repository beside
   it is a supported configuration. Say so and continue; **do not substitute the current directory,
   and do not hand-roll a replacement probe.**

   Then separate **can** from **may**: a channel the agent *can* run may still be the operator's to
   authorize (INV-14). This step measures capability; it never confers authority.
4. `[agent]` **Know the just-in-time pointers** (read only when a task touches them):
   - Built-but-unexercised ops + their docs → the `llm-context-reboot` Site load-list.
   - Deferred / not-built — do **not** attempt or assume available: Crucible, Mint, Forge, Hermes, n8n.
   - Other runbooks: `provenance-seal-runbook`.
   - Durable rules: the auto-loaded memories (`MEMORY.md`).
5. `[script]` **Verify** — `: "${VAULT_ROOT:?}"` (env set); optionally `vault-render.py reconcile`
   (zero drift).

## Pitfalls

- Passive auto-load is **not** sufficient — the 2026-06-26 governance breach happened with `CLAUDE.md`
  already loaded. The `[gate]` acknowledgment is the whole point; do not skip it.
- **Do not reason from a single error to a capability class.** A `git fetch` that dies on
  `unable to get credential storage lock: Read-only file system` is a *write* failure — reading it as
  "no network" (2026-08-05) produced a confidently wrong "I can't reach GitHub", and an unnecessary
  verification ritual built on the false premise. The corpus already held the answer; the gate was
  skipped, not missing. **More prose does not fix a skipped gate — step 3 is an *action* that yields
  evidence, which is why it is a probe and not a paragraph.**
- **Never bank a capability *answer*; bank the probe.** Write scope changed silently under the
  ADR-0035 strict flip, invalidating a previously-true "I can push to that repo" with no observable
  event. Memory holds *architecture* (keyring is unreachable from the sandbox — durable); the probe
  holds *state* (path lists — stale on the next config edit).
- Do **not** inline the Constitution / specs / load-list here — *name and point*; read just-in-time.
  Inlining bloats context and is what this runbook deliberately avoids.
- Env does not survive between shells — re-source `config.env` in each new shell.
- ⚠ **A REMOTELESS VAULT IS THE INVARIANT HOLDING, NOT A BROKEN CHANNEL.** The vault has no remotes
  *because INV-14 requires it to have none* — it is private by default and deliberately has nowhere to
  push. Before this was fixed, the probe took its subject from the working directory, so a cold start
  in the vault measured the **vault** and printed `slug UNRESOLVED`, `github state FAILED`,
  `ls-remote FAILED`, `push FAILED`. **Not one of those was a defect.** An agent reading that output
  can bank *"GitHub is unreachable this session"* — precisely the false belief this probe exists to
  prevent. The inverse matters more and had no report at all: **if the vault can push, that is an
  alarm, not a pass.**
- ⚠ **Do not hand-roll a replacement probe.** When the reporter looked broken, earlier sessions
  substituted their own write-scope check — twice. Both hand-rolls failed the same ways the real
  layer is built to avoid: an `rm` whose result was discarded (leaving silent residue), and
  `96-Runbooks/` quietly dropped in favour of the subtrees the prober happened to want. If the probe
  cannot run, say so and continue; a substitute you wrote in the moment is not an instrument.

## Verification

- `VAULT_ROOT` is exported and resolves to the vault root.
- The five gates are acknowledged before any governed action this session.
- The step-3 probe has been run against the DECLARED estate and its layers reported, before
  any capability claim. `VAULT_ROOT` and `FRAMEWORK_ROOT` are both echoed by the probe itself.
- (Optional) `vault-render.py reconcile` reports zero drift.

## Rollback

- None required — the prime only loads context and sets the environment; it mutates no vault content.
  If `config.env` was sourced from the wrong path, re-source the correct one.
