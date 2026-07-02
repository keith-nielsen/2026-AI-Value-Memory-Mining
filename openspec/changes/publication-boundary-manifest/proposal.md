<!-- SPDX-License-Identifier: Apache-2.0 -->

# Constitution Override: publication-boundary-manifest

**Change type:** `constitution-override`
**Principle(s) affected:** `access-control` spec — `protects: [… INV-14]`. **Conforming amendment** — additive: adds a **path-level** enforcement layer under the existing INV-14 and separates public framework config from the private instance. **Strengthens INV-14; weakens nothing.** Extends **ADR-0018** (private-by-default publish guard).
**Tier:** 0 (INV-14) — additive/conforming
**Proposer:** Keith Nielsen (drafted by Claude Code; authorized by Keith)
**Date:** 2026-07-02

> **Ratify-in-place note.** The enforcement was implemented in the live vault ahead of this ceremony
> (a "disjointed time": Gate-3 implementation preceded Gates 1–2). This change documents and ratifies
> that work retroactively; nothing was pushed anywhere (the vault has no remote). The repo-side
> `vault-template/` mirror + regression + ADR + Gate-4 sign-off remain outstanding below.

---

## Why

ADR-0018/INV-14 makes a deployed vault private **at the remote level**: deny every push unless the
remote is in `PUSH_ALLOWLIST`. That leaves one gap — if the operator ever allowlists a remote intended
to receive only *framework* content (a public template mirror), nothing stops a push whose diff touches
**private** paths (Claims, Sites, Treasury, Warehouse, the live `config.env`). Publication is
irreversible; the guarantee should be **path-aware**, and the private config instance should not be
publishable at all. Principle: *publish the machine, never the ore.*

## What Changes

- **ADD** a **default-deny publication allowlist** schema `99-Operations/schemas/publish-manifest.json`:
  only explicitly-listed *framework* paths are publishable; everything else is private by default
  (fail-safe — a new/forgotten path stays private).
- **EXTEND** `push-guard-script` with a **path-level gate** for remotes in a new
  `PUBLIC_REMOTE_ALLOWLIST` (`config.env`): a push to such a remote whose diff touches any
  non-allowlisted path is refused. Layered on — never replacing — the existing remote-level INV-14 gate.
- **Framework/instance config separation:** ship public defaults in `99-Operations/config.defaults.env`
  (sourced first) + a refreshed `config.env.example`; the live `config.env` becomes personal overrides,
  **gitignored** (so the private instance is never published). `config.env` sources the defaults, so
  every existing `source config.env` still works.
- **New guard key:** `PUBLIC_REMOTE_ALLOWLIST` (empty by default → no public remote; posture unchanged).

## Capabilities

### New Capabilities
- _(none — the path-level boundary lands in the existing `access-control` capability, under INV-14)_

### Modified Capabilities
- `access-control`: ADD Requirement "Publication Boundary — Path-Level Manifest for Public Remotes (INV-14)"; MODIFY the `config.env` contents scenario to reflect the defaults/instance split.
- `maintenance`: MODIFY Script Inventory — `push-guard-script` purpose gains the path-level gate; note the `publish-manifest.json` schema it consumes.

## Impact

- **Spec deltas (synced at archive):** `access-control` (ADDED Requirement + MODIFIED config scenario), `maintenance` (MODIFIED Script Inventory).
- **Implementation (live vault — DONE, ratify-in-place):** `99-Operations/schemas/publish-manifest.json`; `push-guard-script.md` path-gate → rendered `pre-push`; `config.defaults.env` + gitignored `config.env` + refreshed `config.env.example`; `PUBLIC_REMOTE_ALLOWLIST=""`.
- **Implementation (repo `vault-template/` — TODO, for forks to inherit):** same artifacts mirrored into the template.
- **Docs:** `docs/USING-THIS-TEMPLATE.md` (config defaults/instance + PUBLIC_REMOTE_ALLOWLIST); README counts.
- **New ADR-0020** (Gate 4).
- **Honest limit (recorded in ADR):** inherits ADR-0018's — `--no-verify`/hook-strip bypass; a public export tool must also honor the manifest.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) restated (own words):** INV-14 (Tier-0, Safety) says a deployed vault is private by
default and no automated actor may replicate its content outward except to an operator-allowlisted
remote; public publication needs deliberate human action. **What breaks if mishandled:** private,
irreversible-if-leaked content reaches a public remote — cached, mirrored, indexed, unrecoverable. This
change is **purely additive**: it does not relax the remote-level deny-by-default rule or any other
invariant. It *adds* a second, path-level check that only ever **refuses more** (never permits a push
the old rule would have denied), and it makes the private `config.env` unpublishable by gitignoring it
behind public defaults. INV-14 is reinforced; the frozen-ID rule (ADR-0008) is untouched (no invariant
added or renumbered — this is enforcement depth under the existing INV-14).

**Blast radius (checked off in Gate 3):**

- [ ] `openspec/specs/access-control/spec.md` — ADDED path-level publication-boundary Requirement; MODIFIED config-contents scenario
- [ ] `openspec/specs/maintenance/spec.md` — MODIFIED Script Inventory (`push-guard-script` + `publish-manifest.json`)
- [ ] `vault-template/99-Operations/schemas/publish-manifest.json` (new)
- [ ] `vault-template/99-Operations/scripts/push-guard-script.md` (path-gate)
- [ ] `vault-template/99-Operations/config.defaults.env` (new) + `config.env.example` (stub) + `.gitignore` (ignore live `config.env`)
- [ ] `.github/scripts/validate-scripts.sh` — sandbox now instantiates `config.env` from the example (config-split blast radius)
- [ ] `.github/workflows/ci.yml` — `vocabulary-lint` reads `config.defaults.env` instead of the removed `config.env` (config-split blast radius)
- [ ] `docs/USING-THIS-TEMPLATE.md`; `README.md` counts
- [ ] `openspec/adr/0020-publication-boundary-manifest.md` (new)

---

## Gate 2 — PLAN (Migration + Regression)

**Migration:** additive. Existing vaults keep working — `config.env` now sources `config.defaults.env`
first then applies overrides (bash last-write-wins), so every `source config.env` is unchanged in
effect. `PUBLIC_REMOTE_ALLOWLIST` empty ⇒ the new path-gate is inert until a public remote is
deliberately configured; the remote-level INV-14 gate is unchanged. No existing push that was permitted
becomes denied except a push of private paths to a *public-designated* remote — which is the intent.
The live vault was migrated this session (ratify-in-place); the `vault-template/` mirror lands here so
forks inherit it.

**Regression that MUST pass before Gate 3:** `openspec validate publication-boundary-manifest --strict`
+ `--all --strict`; `constitution-lint`; `vocabulary-lint`; push-guard unit checks (private→public
blocked; public/empty allowed; non-allowlisted denied; guard-off allowed; private-backup allowed —
already exercised green in the live vault this session); CI green.

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — live vault + `vault-template/` mirror + docs DONE
**All regression tests green (local suite):** ☑ — `validate-scripts.sh` VALIDATION OK; `openspec validate --all --strict` 9/9; push-guard dry-runs green
**CI green on this PR:** ☐ (runs on push)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> Sacrifice: additive — strengthens INV-14, weakens nothing. Cost = more guard logic + a
> publish-manifest to maintain; a future public-export tool must also honor the manifest. Honest limit
> inherited from ADR-0018 (`--no-verify`/hook-strip bypass; not an unbreakable cage).

**ADR created:** `openspec/adr/0020-publication-boundary-manifest.md` ☑ (Accepted)
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: Keith Nielsen — "Authorized." (transcribed by Claude Code at Keith's explicit instruction; the decision is the human's)
Date: 2026-07-02
