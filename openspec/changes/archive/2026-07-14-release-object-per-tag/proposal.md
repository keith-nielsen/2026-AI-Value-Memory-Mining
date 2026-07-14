<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: release-object-per-tag

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `maintenance` spec (`protects: [INV-2, INV-3, INV-6]`) —
**ADDS** one Requirement ("GitHub Release Object Per Version Tag"). Touches the `access-control`
spec (`protects: [..., INV-14]`) — **conforming clarification** of the harness-guard enforcement
of INV-14 (adds scenarios; the guard implementation is brought into conformance with the requirement
text it already carries). **No principle is overridden or weakened**; the guard change is a
false-positive fix plus a silent-gap closure that *strengthens* the INV-14 posture. Conforming
amendment per repo precedent (every archived change touching a protected spec ran this ceremony,
including conforming ones — `add-overreach-scope-review`, `fix-commit-gate-env-guard`, et al.).
**Tier:** 0-adjacent (touches the INV-14 Safety-band enforcement surface; §5 AI hard-stop honored —
surfaced for explicit sign-off at Gate 4).
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-14)
**Date:** 2026-07-14

---

## Why

Two defects surfaced when the operator noticed the GitHub Releases page (and the mirrored profile
badge) still showed **v0.1.13** as Latest, while the repo had shipped through **v0.1.22**.

1. **Process gap — the ship ceremony never created a GitHub *Release object*.** A git tag and a
   GitHub Release are different objects: pushing a tag does **not** create a Release. Searching the
   repo, `git tag` appears only in `provenance-seal-runbook` (a transcript-sealing procedure,
   unrelated), and no `RELEASE`/`CONTRIBUTING`/`AGENTS` doc describes the post-merge ship steps
   (tag → release → mirror) at all. Release-object creation was tribal knowledge, done ad-hoc, and
   silently stopped after v0.1.13 — most likely when the `gh` token expired: the plain-git
   `push --tags` kept working (so all 22 tags reached the remote) while every `gh release create`
   failed auth and was dropped. Nine tags (v0.1.14–v0.1.22) existed with no Release. There was no
   documented step and no verification, so the drift accumulated invisibly for two weeks.

2. **Safety-rail defect — the outbound-publish guard both over- and under-fires.** The INV-14
   harness guard (`.claude/hooks/outbound-publish-guard.py`) decides "am I acting on the vault?"
   from the tool's reported working directory (`cwd == VAULT or cwd.startswith(VAULT) or
   VAULT in cmd`). In a live agent session `VAULT_ROOT` is set and the Bash tool always reports
   `cwd == VAULT`, even when the command `cd`s into the **sibling framework repo**
   (`~/Documents/repo/value-memory-mining`, which is *not* vault content and *is* operator-authorized
   for agent publish). Result:
   - **Over-fires (false HARD DENY):** every `gh release create` / `git push` targeting the framework
     repo from a vault-rooted session is blocked as if it were a vault exfiltration — including, as
     observed, a read-only command that merely *contained* the string `gh release create` inside a
     `grep` pattern (the guard is a pure text match against the whole command).
   - **Under-fires (silent allow):** `PUBLISH` — the ASK set — does **not** include plain `git push`.
     So a framework-repo `git push` matches `OUTWARD` but not `PUBLISH`: with the `in_vault`
     false-positive removed it would fall straight through to silent defer, and in a permissive
     permission mode the agent could push a repo **with no prompt at all**. This is precisely the
     "the harness *can*, so it *will* — to be helpful" failure the operator wants foreclosed.

The operator's requirement (2026-07-14): each version tag must equate to a GitHub Release so the
public state stays current; and the mechanism must include a **structural hard stop** the agent
cannot skip, preceded by an **informed pause** (overview summary + the ability to read `proposal.md`
in full) before anything goes outward — automation proceeds *only* after deliberate human approval.

## What Changes

At the principle level nothing is overridden. Two things become true that were not before:

- **`maintenance` gains a Requirement:** the ship ceremony's final steps (tag → **GitHub Release** →
  mirror) are documented and mandatory, and a GitHub Release object is created and verified for every
  `vX.Y.Z` tag. Parity is a checked ceremony step, so the drift cannot silently re-accumulate.
- **`access-control` INV-14 guard enforcement is made accurate and complete** (conforming): the
  hard-DENY is scoped to commands whose *effective target* is inside the vault (honoring a leading
  `cd <path>` / `git -C <path>` / `gh -R <owner/repo>` redirect), so legitimate non-vault publishes
  are no longer false-denied; and **every** outward-replication or publish command that is *not*
  vault-denied — now including plain `git push` — raises the loud ASK hard-stop, never silently
  defers. Vault-outward commands are still HARD-DENIED exactly as today. The agent, before triggering
  any outward step, presents an overview summary plus the absolute path to the governing `proposal.md`
  and awaits explicit `Approved` (the informed pause; the ASK is its structural backstop).

Net effect on INV-14: **strictly stronger** — the class of commands that can go outward with *no*
human gate shrinks from "any `git push` not caught by `PUBLISH`" to **none**.

---

## Gate 1 — CHECK (Impact Analysis)

**Principle(s) being overridden (restated in my own words):**

> `maintenance` protects INV-2 (one mutation → one commit), INV-3 (operational steps live as literate
> meta-scripts; drift is *detected*, never auto-fixed), INV-6 (deterministic tooling is offline, no
> LLM calls). `access-control` protects INV-14 (private by default; no automated actor replicates
> outward except to an operator-allowlisted remote; public-facing publication needs deliberate human
> confirmation, never an agent's unprompted suggestion; enforced structurally, never by trust).
> This change *adds* a documented, verified release step under `maintenance` (no existing invariant
> relaxed — the guard code stays a literate meta-script, byte-identical across its three homes, so
> INV-3 holds; the release step is a human/agent ceremony action, not part of the deterministic
> offline fleet, so INV-6 is untouched). Under `access-control` it makes the INV-14 guard *match its
> own requirement text* ("hard-denies vault-outward commands and raises a loud, explicit confirmation
> before any public-facing publication") and closes a gap where a `git push` could pass unasked —
> tightening the Safety band, weakening nothing.

**Blast radius — every artifact this change touches:**

- [ ] `openspec/specs/maintenance/spec.md` — ADDED Requirement ("GitHub Release Object Per Version Tag") + scenarios (spec delta in this change)
- [ ] `openspec/specs/access-control/spec.md` — INV-14 requirement enforcement clause reworded (effective-target scoping; all-outward-ops ASK); +3 scenarios (spec delta in this change)
- [ ] `.claude/hooks/outbound-publish-guard.py` — guard implementation fix (effective-target `in_vault`; ASK on any non-denied outward/publish op; banner generalized to cover push and publish)
- [ ] `vault-template/.claude/hooks/outbound-publish-guard.py` — **byte-identical mirror** of the above
- [ ] `vault-template/99-Operations/scripts/outbound-publish-guard-script.md` — literate meta-script note: the ```python block updated byte-identical (INV-3 SSOT); Rationale note extended
- [ ] `CONTRIBUTING.md` — document the post-merge ship ceremony (tag → GitHub Release → mirror) as explicit steps after "Open a PR"
- [ ] `AGENTS.md` — +Operating-note: the informed-pause + hard-stop discipline before any outward op; release-per-tag is a required ship step
- [ ] `CHANGELOG.md` — `[Unreleased]` entry
- [ ] `.github/pull_request_template.md` — no structural change; this PR's body carries the required fenced ```scope block (v0.1.22 gate; Phase-A burn-in)
- [ ] `openspec/constitution.md` — **no change** (no principle text altered; INV IDs unchanged)
- [ ] `vault-template/` deployed-vault guard copy — the live vault's `.claude/hooks/…py` is updated by the operator mirror step post-merge (agent-write-denied in a live vault, per the note's own precedent) — **not** committed by this change
- [ ] ADR reference — **new ADR-0027 required** (see Gate 4)

**External dependency being adopted: NONE.** Uses the already-present `gh` CLI (operator-authenticated)
for release creation as a ceremony step; no new package, no CI network job, nothing added to the trust
ring.

---

## Gate 2 — PLAN (Migration + Regression)

**Migration plan (lockstep):**

1. Write the two spec deltas (`maintenance` ADD; `access-control` conforming rewording + scenarios).
2. Edit the guard `.py` in all **three** byte-identical homes together (repo hook, vault-template hook,
   ```python block in the meta-script note); update the note's Rationale to record the effective-target
   fix and the git-push ASK closure. `render --check`/`reconcile` must report zero drift across the three.
3. Document the ship ceremony in `CONTRIBUTING.md` (tag → `gh release create --verify-tag --latest` →
   verify `gh release view` → mirror), and add the AGENTS operating-note (informed pause + hard stop).
4. `[Unreleased]` CHANGELOG entry.
5. **Backfill already done** out-of-band (operator ran v0.1.14–v0.1.22 release creation on 2026-07-14;
   v0.1.22 is now Latest) — this change makes the step permanent and documented so it cannot lapse again.

**Regression tests that MUST pass before Gate 3:**

- [ ] `openspec validate --all` passes (new deltas + archive round-trip)
- [ ] `constitution-lint` passes (protected-spec change carries this ceremony + ADR)
- [ ] `vocabulary-lint`, `spec-lint`, `md-lint`, `link-check`, `naming-validator` pass
- [ ] `validate-scripts` / `reconcile` — guard code byte-identical across its three homes (INV-3)
- [ ] `scope-review` (Phase-A, report-only) — this PR's diff matches its declared ```scope block
- [ ] Guard unit checks (new, local): (a) framework-repo `gh release create` from a vault-rooted
      session → ASK, not DENY; (b) framework-repo `git push` (incl. `git -C … push`) → ASK (not
      silent); (c) vault-outward `git push` → DENY (unchanged); (d) `git commit -m "…push…"` → defer
      (no false positive); (e) read-only command merely *mentioning* a trigger token with a non-vault
      effective target → ASK (conservative — the guard is a text matcher; an extra confirmation is the
      safe failure direction, far better than the former false DENY)

---

## Gate 3 — EXECUTE + REGRESSION TEST

**Implementation complete:** ☑ — spec deltas (maintenance ADD, access-control MODIFY), guard fix
across all three byte-identical homes, `CONTRIBUTING.md` + `AGENTS.md` ceremony docs, CHANGELOG,
ADR-0027.

**All regression tests green (local, 2026-07-14):** ☑
- `openspec validate --all` → 8 passed / 0 failed (incl. `change/release-object-per-tag`)
- `validate-scripts.sh` → VALIDATION OK; **`reconcile` zero drift** (guard byte-identical across the
  three homes — INV-3)
- Guard behavior matrix 11/11: framework-repo release / push / `git -C … push` → ASK; vault-outward
  (cwd, `git -C`, vault-path operand) → DENY; `git commit -m "…push…"` → defer (no false positive);
  non-vault trigger-token mention → ASK (conservative)
- `scope-review` (Phase-A) → PASS, 12 files all declared

**CI green on this PR:** ☐ (pending push — each push/PR is an ASK hard-stop)

---

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

<!-- Human only — agents may not sign. -->

**Second review confirms blast radius was fully addressed:** ☑
**Consequences explicitly accepted:**

> - Every ship now includes a release-creation + verification step and a mirror of the guard to the
>   live vault — a few extra ceremony steps, and a running `gh` auth dependency (a lapsed token now
>   fails loudly at a documented step instead of silently dropping releases).
> - The INV-14 guard now raises the ASK hard-stop on **every** outward op it does not hard-deny —
>   including routine `git push` to the framework repo. This is deliberate (the operator's "must hard
>   stop before push" requirement); the cost is one conscious approval per push. It is the correct,
>   requested friction, not incidental. (A per-repo allowlist to soften it later would itself be a
>   governed change.)
> - Sacrifice: none material — a false-positive is removed, a silent-allow gap is closed, and a
>   previously undocumented, lapsing step is made permanent and verified. The Safety band is tightened.

**Open question flagged at sign-off (operator, 2026-07-14):** whether *mandatory* release-per-tag is
the right long-run rule, or whether a tag should be allowed to ship **without** a Release (deferrable
release) as a supported option. Accepted **for now** as mandatory (simple, keeps public state current,
prevents silent drift); revisiting it to make a Release **deferrable/optional** is a sanctioned future
`maintenance` change — the requirement is written as a self-contained ceremony step so relaxing it
touches only that Requirement + the CONTRIBUTING/AGENTS steps, no guard logic. See ADR-0027 Consequences.

**ADR created:** `openspec/adr/0027-release-object-per-tag-and-guard-conformance.md` ☑
**ADR captures:** context / options / choice / consequence / **sacrifice** ☑

**SIGN-OFF** (human only — agents may not sign):
Name: **Keith Nielsen** (operator reviewed in session and replied `Approved`, 2026-07-14; caveat above
recorded — approved *for now*, mandatory-release-per-tag may be relaxed to deferrable later)
Date: **2026-07-14**
