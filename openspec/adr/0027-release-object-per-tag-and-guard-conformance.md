<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0027 — Release object per version tag; outbound-guard effective-target conformance

**Status:** Accepted (Gate-4, 2026-07-14; operator-approved in session)
**Date:** 2026-07-14
**Change:** `release-object-per-tag` (`constitution-override`, conforming — touches the `maintenance`
spec [`protects: [INV-2, INV-3, INV-6]`, ADDS one Requirement] and the `access-control` spec
[`protects: […, INV-14]`, MODIFIES the INV-14 harness-guard enforcement clause]; **no Tier-0/1 element
overridden or weakened**)
**Relates / extends:** ADR-0018 (private-by-default publish guard — the original two-job design);
ADR-0008 (frozen INV IDs)

## Context

The operator noticed the repository's GitHub Releases page (and the mirrored profile badge) still
showed **v0.1.13** as Latest while the repo had shipped through **v0.1.22**. Investigation found two
independent defects.

1. **The ship ceremony never created a GitHub *Release object*.** A git tag and a GitHub Release are
   distinct objects; pushing a tag does not create a Release, and the "latest release" surfaces track
   the newest Release, not the newest tag. No `RELEASE`/`CONTRIBUTING`/`AGENTS`/runbook doc described
   the post-merge tag → release → mirror steps — `git tag` appeared only in the unrelated
   `provenance-seal-runbook`. Release-object creation was tribal knowledge, done ad-hoc, and silently
   stopped after v0.1.13 (most likely when the `gh` token expired: plain-git `push --tags` kept
   working, so all 22 tags reached the remote, while every `gh release create` failed auth and was
   dropped). With no documented step and no verification, the drift accumulated invisibly for two weeks.

2. **The INV-14 harness guard (ADR-0018) both over- and under-fired.** It decided "am I acting on the
   vault?" from the tool's reported cwd (`cwd == VAULT or cwd.startswith(VAULT) or VAULT in cmd`). In a
   live agent session `VAULT_ROOT` is set and the Bash tool always reports `cwd == VAULT`, even when the
   command `cd`s into the sibling framework repo. Result: **over-fire** — every framework-repo
   `gh release create` / `git push` was HARD-DENIED as a vault exfiltration (including a read-only
   command that merely *contained* the trigger text inside a `grep` pattern); and **under-fire** — the
   ASK set (`PUBLISH`) excluded plain `git push`, and `OUTWARD`'s `\bgit\s+push\b` even missed
   `git -C <path> push`, so such pushes could defer unprompted. This is precisely the "the harness
   *can*, so it *will* — to be helpful" hazard the operator wants foreclosed by a real hard stop.

The operator's requirement (2026-07-14): each version tag must equate to a GitHub Release so public
state stays current; and the mechanism must be a **structural hard stop the agent cannot skip**,
preceded by an **informed pause** (overview summary + the ability to read `proposal.md` in full), with
automation proceeding only after deliberate human approval.

## Decision

- **Release-per-tag (maintenance, ADDED Requirement).** The ship ceremony's final steps — annotated
  tag → `gh release create <tag> --verify-tag --latest` → `gh release view <tag>` parity check →
  mirror — are documented (`CONTRIBUTING.md`, `AGENTS.md`) and mandatory. Because creation and
  verification happen in the same ceremony that cuts the tag, a tag can never again strand without its
  Release. This is a ceremony action (agent/operator, gated by the outbound guard), not a
  deterministic-fleet script — it legitimately calls authenticated `gh`, so INV-6 is not engaged; no
  networked CI parity job is added.

- **Effective-target guard (access-control, conforming MODIFY).** `outbound-publish-guard.py` now
  judges "targets the vault" from the command's **effective target** — honoring a leading `cd <path>`,
  `git -C <path>`, and `gh -R <owner/repo>` redirect, plus the conservative "vault path named as an
  operand" case — not the reported cwd alone. Non-vault publishes (the framework repo) therefore fall
  to the ASK instead of a false HARD-DENY. The ASK now fires on **any** non-denied outward op
  (`OUTWARD or PUBLISH`), and `OUTWARD` catches `git -C <path> push`, so no outward command can silently
  defer. Vault-outward commands remain HARD-DENIED. The guard is a structural stop (an ASK cannot
  proceed without a human Yes in any permission mode); the *informed* half — overview summary + absolute
  `proposal.md` path before triggering it — is codified as ceremony, generalizing the standing Gate-4
  ritual to all outward ops. The guard code stays a literate meta-script, byte-identical across its
  three homes (INV-3), verified by `reconcile`.

## Options considered

- **(a) Document release-per-tag + make the guard effective-target-aware (chosen).** Fixes both defects
  at the root: the release step can no longer lapse (documented + verified), and the guard stops
  false-denying legitimate publishes while closing the silent-push gap. Net INV-14 posture is *stronger*.
- **(b) Keep the guard as-is; make release-creation a purely manual operator step.** Rejected: it leaves
  the false-positive HARD-DENY in place (the agent trips it even reading a file that mentions the token)
  and leaves the silent `git push` gap open; and it adds standing copy/paste busywork the operator
  explicitly did not want.
- **(c) Weaken the guard to auto-allow framework-repo publishes.** Rejected outright: it removes the
  hard stop — exactly the "push to be helpful" failure the operator requires foreclosed. The correct
  behavior is ASK (human-gated), not allow.
- **(d) A networked CI job that scans tag/Release parity.** Rejected: it needs an authenticated GitHub
  call, against the INV-6 offline-fleet posture, and it detects drift after the fact rather than
  preventing it. A mandatory verified ceremony step prevents the drift at ship time.

## Consequence / sacrifice

- Every ship now includes release-creation + a parity check and a guard-mirror step, and carries a
  running `gh`-auth dependency — a lapsed token now fails loudly at a documented step instead of
  silently dropping releases.
- The guard raises the ASK on **every** outward op it does not hard-deny, including routine framework-repo
  `git push`. This is the operator's deliberately-chosen friction ("must hard stop before push"); the
  cost is one conscious approval per push (softening it via a per-repo allowlist would be its own
  governed change). A read-only command that merely mentions a trigger token also raises the ASK — the
  safe failure direction for a text-based guard, and far better than the former false HARD-DENY.
- **Sacrifice:** none material. A false-positive is removed, a silent-allow gap is closed, and a
  previously undocumented, lapsing step is made permanent and verified. The Safety band is tightened,
  no principle weakened; INV-1–14 unchanged (ADR-0008 frozen IDs hold).

- **Open question / sanctioned future relaxation (operator, Gate-4 2026-07-14).** Whether release
  creation must be *mandatory* per tag is deliberately left open. It is adopted as mandatory **for
  now** — simplest rule, keeps the public "latest release" current, prevents the silent drift this ADR
  fixes. A future `maintenance` change MAY make a Release **deferrable/optional** (a tag intentionally
  shipped without a Release). The requirement is authored as a self-contained ceremony step precisely
  so that relaxation touches only that Requirement plus the `CONTRIBUTING.md`/`AGENTS.md` steps — **no
  guard logic and no other invariant** — making the later change small and low-risk. This is a policy
  knob, not a Safety-band element.
