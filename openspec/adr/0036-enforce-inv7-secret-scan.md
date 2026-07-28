<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0036 — Give INV-7 a mechanism: credential scanning at the commit boundary

**Status:** **Proposed** (Gate-4 pending — human-only sign-off, constitution §5)
**Date:** 2026-07-28
**Relates:** `access-control` (INV-7) · change `enforce-inv7-secret-scan` · **same defect class as
ADR-0030** (a rule enforced nowhere) and ADR-0029 · ADR-0022 (the enforcement posture this
completes for a second invariant) · live-vault Site `github-canary-barium-lunch-investigation`
(root causes RC-C, RC-D, RC-E, RC-F, cited throughout)

## Context

INV-7 — *"No secrets in any vault file"* — sits in the **Safety** band of Tier 0, the band the
constitution describes as *"highest blast radius if violated."* It was enforced by **nothing**:
no hook, no linter, no CI job, no test. A credential pasted into any note committed cleanly, in
the framework repo and in every deployed vault.

This was found by the 2026-07-28 Tier-0 enforcement audit, which read every hook,
`.claude/settings.json`, and all eleven CI jobs and asked one question per invariant: *what fires
without agent cooperation?* Of the nine live Tier-0 invariants, **three** had an answer — INV-4
and INV-5 (kernel, via ADR-0022) and INV-11 (the commit gate). **INV-6 and INV-7 had none at
all.** The audit was itself prompted by the INV-14 investigation, which established that an
invariant can be documented, deployed in three byte-identical homes, and drift-clean while never
having been shown to fire once.

**The spec already stated the rule, and verified the wrong thing.** `Requirement: Secrets
Prohibition (INV-7)` says *"No credentials, API keys, tokens, or passwords SHALL appear in any
vault file"* — and its **sole scenario inspects the contents of two config files.** That is a
Factor-A check (configuration is as expected) standing in for a Factor-B property (a secret
cannot be committed). It is root cause **RC-C** of the barium-lunch investigation, occurring in
the governance corpus that defines the invariant rather than in the code that was supposed to
enforce it.

This is the same shape ADR-0030 found in INV-11 — *"a rule that lives as a comment, enforced by
nothing"* — with one difference that matters for calibration: INV-11's floor at least existed as
dead code and a commented-out branch. INV-7 had **no artifact of any kind**. There was nothing to
switch on.

**Severity is low and should be stated as such.** A Phase-0 sweep run before this change, over
both repositories' full object databases — 610 + 889 blobs, plus 548 working-tree files — found
**zero** matches at either tier. Nothing has leaked. The instrument was validated first against a
control fixture carrying planted secrets in three states (live, deleted, and orphaned by a
discarded commit); all three were detected. **This ADR is prophylactic, not remedial**, and an
accurate diagnosis is worth more than a loud one.

**One dependency makes it timely.** The INV-14 finding established that the only barrier to
non-`git` egress from the agent channel is the **absence of a usable credential** — an accident,
never a designed control. Credential hygiene is therefore load-bearing right now. A secret
reaching a vault file is no longer only a disclosure risk in the ordinary sense; it is the input
that would convert a measured-reachable egress path into a credentialed one.

## Options

- **(a) Keep the prohibition as prose, rely on care.** Rejected. The operation's own record is
  that prose rules do not fire: F16, F20 (recurring twice *after* its corrective was written),
  and RC-D — whose paragraph stating the control-validity rule was violated by the very next
  measurement in the document containing it. A principle without a mechanical check is a wish.
- **(b) Adopt a third-party scanner (gitleaks / trufflehog / detect-secrets).** Rejected, though
  it is the industry default and better-maintained than anything authored here. Three reasons:
  it adds a dependency to the trust ring for a job the standard library does in ~150 lines
  (standing supply-chain posture: concept-extraction over adoption); its entropy heuristics
  over-deny badly on a corpus that *discusses* credentials constantly, which is this one; and it
  runs in CI, whereas the deployed vault has **no CI** — it has a commit gate, and that is the
  only boundary a deployed instance actually possesses.
- **(c) Entropy-based detection, authored here.** Rejected on the same over-denial ground. RC-E
  is explicit that over-denial is not benign but **camouflage**: a control that refuses
  constantly and harmlessly stops carrying information, and specifically taxes the audit most
  likely to find its defects. The INV-14 guard's six-of-fourteen over-deny rate is the worked
  example, and it ran for a year.
- **(d) Two-tier anchored-pattern scanner at the commit gate, plus a CI historical scan
  (chosen).** Anchored vendor formats gate; contextual patterns are advisory and never gate.
  Stdlib-only, environment-free, offline (INV-6), rendered as a Layer-0 meta-script so the
  operator owns its deployment.
- **(e) Solve custody first — adopt a secret manager (`pass` / 1Password).** Deferred, not
  rejected, and recorded on the roadmap. It addresses a *different* problem (credential
  lifecycle, not vault content), it is unnecessary for a single operator on one machine whose
  credentials already sit in the OS keyring, and — given (the INV-14 finding) that credential
  absence is currently the only egress barrier — **a broker the agent can invoke would make
  things actively worse.** Any future adoption carries a hard acceptance condition: demonstrable
  unreachability from the agent's Bash channel, proven by a probe with a negative control.

## Decision

Adopt (d).

- A new Layer-0 literate meta-script, `secret-scan-script.md` → `~/bin/vault_secrets.py`, is the
  single source of truth for credential-format detection. The fleet goes from 13 scripts to 14.
- The existing commit gate calls it on staged **content**. Three deliberate asymmetries with the
  gate's INV-11 half: **every file type** (a secret in `.json` counts), **modified files too**
  (`--diff-filter=ACM`, not `AR`), and **never grandfathered** — a pre-existing non-conforming
  name is cosmetic debt, a pre-existing credential is an active compromise.
- **Only the HIGH tier gates.** ADVISORY matches are reported by the standalone tool and never
  consulted by the hook. This is RC-E applied on purpose.
- **Findings are redacted** to a four-character prefix and a length. A scanner that echoes what
  it found writes the secret to a terminal, a shell history, and possibly a commit message —
  violating INV-7 in the act of enforcing it.
- **The scanner selftests before every scan** and refuses to report a clean result if its own
  patterns cannot be shown to fire. This is the E5 exit-3 gate reused: a detector that cannot be
  shown to detect prints "clean" for a clean corpus and a broken pattern set alike.
- **CI scans the full object database including unreachable objects** — discarded commits and
  dropped rebases — because a credential committed and later "removed" survives exactly there and
  is invisible to `git rev-list`.
- The spec gains an **ADDED** Requirement, *Secrets Prohibition Is Enforced at the Boundary*. The
  existing prohibition Requirement is left intact (the ADR-0030 pattern: add the enforcement
  Requirement beside the prohibition; do not rewrite the prohibition).
- **No new invariant.** This is INV-7 enforcement, not a new principle; the frozen-ID rule
  (ADR-0008) is untouched and INV-7's text and tier are unchanged.

## Consequences

- INV-7 moves from *stated* to *mechanical*. Tier-0 invariants that fire without agent
  cooperation go from **3 of 9 to 4 of 9**.
- Every commit gains one subprocess. On this corpus that is not measurable against the naming
  check already running.
- **The deployed vault gains nothing until the operator runs `render`** — an operator-only path
  by design (ADR-0022; the agent receives `EROFS`). The repo half is live at merge; the vault
  half is a deliberate human act. Until then INV-7 remains unenforced in the live vault, and
  saying otherwise would repeat the exact error this ADR documents.
- Forks inherit a gate that can block their commits on a format-shaped string.
- **INV-6 is now the only live Tier-0 invariant with no mechanism at all** — named here so it
  does not go another year unremarked, which is precisely how INV-7 got to today.

## Sacrifice (what is knowingly given up)

**Completeness, permanently.** This detects *known formats*. A shapeless password, a secret split
across lines, an encoded or encrypted one, or a novel vendor prefix all pass. **A clean scan is
therefore not proof that no secret exists** — and the temptation to cite it as one is exactly the
Factor-A substitution this ADR exists to correct. That bound is written into the spec text and
the script's own rationale so it travels with the artifact and cannot be quietly dropped by a
later summary.

**Detection power, traded for signal value.** The advisory tier is deliberately toothless. Real
secrets that happen to look like `password = "…"` will pass the gate. That is accepted in
exchange for a gate whose denials still mean something — RC-E's finding is that the alternative
is not a stricter control but an ignored one, and an ignored control is worse than an absent one
because it also produces false assurance.

**Absoluteness.** `--no-verify` bypasses it, as it does the naming gate. This protects against
accident, not against its own operator; a gate that the operator cannot override is a different
and much larger decision.

**And an honest bound on the trust chain.** The scanner is itself subject to RC-F — the
instrument is inside the system under test. The mitigation is structural rather than rhetorical:
the script lives under `99-Operations/` (kernel `denyWrite` to the agent), reaches the host only
through operator-run `render`, and its deployment is drift-checked by `reconcile`. An agent can
invoke it and cannot alter it. That is the strongest available property, and it is not the same
as the scanner being correct.
