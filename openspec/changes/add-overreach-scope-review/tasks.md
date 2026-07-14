<!-- SPDX-License-Identifier: Apache-2.0 -->
# Tasks: add-overreach-scope-review

## 1. Probe (pre-implementation)
- [x] 1.1 Verify `overreach@0.7.0` interface: `--scope` shape (internal Scope, not DSL), exit-code
      semantics (1 only on HIGH), matching semantics (dir-prefix + exact path; no globs), telemetry
      surface (init-only; `OVERREACH_TELEMETRY=0`), no repo writes in scope-injection mode

## 2. Implementation
- [x] 2.1 `.github/scripts/extract-declared-scope.py` (fail-closed, injection-safe, glob-rejecting)
- [x] 2.2 `.github/scripts/check-scope-findings.py` (MEDIUM+ threshold; fail-closed on malformed)
- [x] 2.3 `ci.yml` `scope-review` job (pull_request only; dependabot exempt; Phase-A
      `continue-on-error: true`; `OVERREACH_TELEMETRY=0`)
- [x] 2.4 PR template: Declared-scope section + checklist line
- [x] 2.5 README CI comment line
- [x] 2.6 CHANGELOG `[Unreleased]` entry incl. evaluation hat-tip (operator attribution policy)
- [x] 2.7 Spec delta: maintenance +1 ADDED Requirement, 4 scenarios
- [x] 2.8 Non-file declaration primitive (`env:` / `dep:` / `endpoint:` prefixes) — added after
      dogfood run 1 flagged the job's own `PR_BODY` env var (true positive; gap was the
      declaration language, not the detector)
- [x] 2.9 Agent priming: AGENTS.md Operating-notes bullet (survives context resets via the repo's
      auto-loaded adapter chain; CI fail-closed error remains the memory-independent floor)
- [x] 2.10 **Trust-ring minimization (operator direction 2026-07-14):** clean-room stdlib
      reimplementation of the comparator; npx invocation + Node setup + OVERREACH_TELEMETRY
      removed; `permissions: contents: read` added; OverReach re-credited as concept source
      (no code copied). Dogfood run 2: the stricter comparator caught OVERREACH_TELEMETRY as an
      undeclared env var on this PR's own diff — a finding the evaluated tool missed.

## 3. Verification
- [x] 3.1 Local script matrix T1–T6 (extract: valid/missing/glob/tokenish · threshold:
      MEDIUM+→1, garbage→2) + end-to-end clean-path PASS (recorded in the vault Site 2026-07-14)
- [x] 3.2 `openspec validate --all` green locally
- [ ] 3.3 PR CI green, including `scope-review` PASS on this PR's own declaration (dogfood)

## 4. Ceremony
- [ ] 4.1 Gate-4 human sign-off (operator replies Approved; recorded in proposal.md)
- [ ] 4.2 Merge; archive the change per batch-archive-in-merge-order practice
- [ ] 4.3 Burn-in watch: ≥3–5 PRs, record false-positive rate; then propose the Phase-B blocking
      flip as its own change
