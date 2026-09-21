<!-- SPDX-License-Identifier: Apache-2.0 -->
# Change: deny-irreversible-outbound

## Why

The INV-14 outbound guard raises a loud **ASK** on any outward-replication or publish, and the
`access-control` spec asserts that ASK *"cannot proceed without an explicit human confirmation in any
permission mode."* **That claim is false, and it was measured false** (adversarial probe, 2026-09-20,
determinism Site `harness-permission-control-deep-dive/adversarial-probe-plan-and-recovery`; dev-store
hardening item 37): under **auto mode** the ASK verdict **silently proceeds** — it neither prompts nor
blocks. Two commands confirmed it (a commit whose message tripped the matcher; `git remote add …`),
each cross-checked against the guard returning `ask`. A control that overstates its strength is the
F31 defect this estate has had to correct before.

The consequence is not uniform, and that is the key: for a **branch push** the silent-proceed is
tolerable — the ref is reversible (force-push / delete) and the disclosure to the public framework
repo is an accepted residual. For an **irreversible** outbound — a published release, a frozen `v*`
tag, an added remote, a created repository — silent-proceed is not tolerable, because git and the
server-side ruleset cannot roll it back.

So the fix buckets outbound by **reversibility**. The one reversible outbound (a branch push) keeps
the ASK, with its auto-mode limitation now stated honestly. Everything else outward becomes a
**hard DENY** on the agent's channel — mode-independent, because DENY is not subject to the
silent-proceed — making irreversible outbound **operator-only**: the operator runs it in their own
terminal (via the ceremony), where this hook does not fire. DENY was measured to hold under every
probe, including three that tripped it inadvertently.

## What Changes

- The harness outbound guard (`outbound-publish-guard-script.md`) gains a branch, evaluated **before**
  the driver-emission downgrade: an outward command that is **not** a plain branch push — a `v*` tag
  push (`refs/tags/`), `git remote add|set-url`, `gh repo create` / `repo edit --visibility public`,
  a release publish/edit/upload (subcommand and the REST endpoints), a release asset upload, or a
  package publish — is **hard-DENIED**, with a message directing the operator to run it themselves.
- A branch push (a `git push` that is not a tag push, effective target not the vault) is unchanged: it
  falls through to the downgrade (byte-exact driver emission) or the ASK.
- The vault HARD DENY (effective target inside the vault) is unchanged and still evaluated first.

## Impact

- **A new refusal exists on the agent's channel.** Irreversible outbound can no longer be run by the
  agent in any mode. Wrong in the strict direction, it blocks work that was fine.
- **Ceremony consequence, handled as a follow-up:** ship-release currently has the *agent* run the
  tag-push and release-create under the ASK. They now hit this DENY; per guard-denial-→-stop the agent
  hands them to the operator. This is correct (irreversible = operator-only) but leaves a rough edge
  in the release ceremony. Making ship-release *emit* those as explicit operator steps (its own
  `next.sh` + the item-39 relay block) is a **separate queued change** (hardening item 41), not this
  one — it is a tooling refactor, a different concern from this INV-14 control change, and no release
  is being cut now.
- Specs: MODIFIES the `access-control` "Private by Default" requirement (corrects the false all-modes
  ASK claim) and ADDS a requirement for the irreversible-outbound DENY.

## Constitutional impact

The delta touches `openspec/specs/access-control/spec.md`
(`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`).

- **INV-14 — strengthened, and corrected.** The outbound rail gains a hard stop it lacked in auto
  mode for the highest-consequence forms; the reversible branch push is unchanged. The false
  "any permission mode" claim is narrowed to what the ASK actually does (prompts interactively; does
  not surface in auto mode), which is why irreversible outbound is DENIED rather than asked. This is
  a control reported at the strength it has (F31), and a **narrowing** of what may leave the machine.
- **INV-6** — untouched; the guard remains stdlib-only and offline.
- **INV-4/5/7/8, CONST-02** — not engaged; no write target, credential, Crucible, or governance-flow
  change.

```constitutional-impact
touches: openspec/specs/access-control/spec.md
protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]
overrides: none
basis: strengthen-and-correct
```

## Verification

- Red-first: an irreversible outbound (tag push, `gh repo create`, `git remote add`, REST release
  write, `uploads.github.com`) is **asked** before the change and **denied** after; a branch push is
  **asked** both before and after (unchanged).
- A mutation matrix: deleting the irreversible-DENY branch flips a tag push back to ask (the rule is
  shown to matter).
- The vault HARD DENY still fires on a vault-targeted outbound (unchanged).
- The driver-emission downgrade still ALLOWS a byte-exact branch-push emission (the reversible path is
  not broken).
- Full suite, `openspec validate --all --strict`, and markdownlint all clean.
