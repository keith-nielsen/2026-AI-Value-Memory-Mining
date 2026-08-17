<!-- SPDX-License-Identifier: Apache-2.0 -->

Marker discipline (standing Definition of Done): `[ ]` not started · `[~]` built, untested ·
`[x]` tested — and `[x]` only where the test was **observed to FAIL without the change**, reproduces
the real geometry, and cites its evidence. Never the same marker for built and tested.

## 1. Spec (ordinary change — ADDED only)

- [ ] 1.1 `maintenance` ADDED: *A Capability State Is A Single Word Naming What Was Found* (5 scenarios)
- [ ] 1.2 `maintenance` ADDED: *A Capability Report Distinguishes Inspection From Attempt* (3 scenarios)
- [ ] 1.3 Confirm ordinary, not override — ADD-only; reporting change, no invariant's meaning altered

## 2. The vocabulary (item 29 C + D)

- [ ] 2.1 Declare every state as a module constant beside `AGENT`/`OPERATOR` (`:61-62`), with the
      naming rule in the docstring: **a state names what was FOUND IN THIS PROCESS, never what is
      possible in the world**
- [ ] 2.2 Credential row: `AUTHENTICATED` / `UNAUTHENTICATED` / `ABSENT` (operator decision
      2026-08-16). **Retire `UNAVAILABLE` rather than narrow it** — a reused token makes every past
      transcript ambiguous
- [ ] 2.3 Document the axis trap where the constants are declared: `ABSENT` means the credential state
      is **UNKNOWN**, not "unauthenticated". A consumer treating them as one axis is the failure

## 3. Single-word states (item 29 E)

- [ ] 3.1 `INV-14 HOLDING` → `HOLDING`
- [ ] 3.2 `OK (dry-run)` → `OK` + `evidence: attempted:<channel>`
- [ ] 3.3 `UNMEASURED (channel unreachable)` → `UNMEASURED` + a separate reason field
- [ ] 3.4 `OK via <channel>` → `OK` + a separate channel field
- [ ] 3.5 Keep `OK` where it honestly means "the operation succeeded" (design decision 1) — do **not**
      fork per-row synonyms. Keep `UNPROTECTED+RESIDUE`: single token, no space, parses fine

## 4. The row name (item 29 B)

- [ ] 4.1 `gh mutations` → `gh credential`. **The runbook already says this** — step 3 of
      `session-bootstrap-loader`. The instrument drifted from its own spec; this closes the drift
- [ ] 4.2 Whether mutations are possible stays in `runs / authority`, which already carries it

## 5. Evidence + `--json` (item 29 A + F)

- [ ] 5.1 Every row records `attempted:<channel>` or `inspected`. **`attempted` alone is not enough** —
      naming the exercised channel is what makes the subprocess-vs-Bash divergence visible in the
      OUTPUT rather than only in the source (item 29-A, latent divergence)
- [ ] 5.2 `--capabilities --json` emitting `{channel, state, runs, authority, evidence, subject}`
- [ ] 5.3 The human table stays the default and stays free to change

## 6. Tests — closure first, because it is the only part that enforces the rest

- [ ] 6.1 **Every emitted state is in the declared set.** Observed failing by introducing a stray
      token — without this the constants are documentation and a typo still invents a state
- [ ] 6.2 No emitted state contains whitespace
- [ ] 6.3 The three credential conditions each produce their own token (present+auth, present+no-cred,
      tool absent) — the third must not collapse into the second
- [ ] 6.4 `--json` round-trips: every row in the table appears with the same state in the JSON
- [ ] 6.5 Evidence is present on every row and names a channel wherever it says `attempted`
- [ ] 6.6 Every test above observed **failing without the change**

## 7. Documents this makes true or false

- [ ] 7.1 `vault-template/96-Runbooks/session-bootstrap-loader.md` step 3 — add the token set so the
      runbook and the instrument agree on names, not just on layers
- [ ] 7.2 `tests/test_pr_flow.py` — update any assertion binding the old tokens
- [ ] 7.3 Verify no document claims the probe reports what is *possible*; it reports what was *found*

## 8. Deliberately NOT in this change

- [ ] 8.1 **Item 29-A2** — whether AGENT-run outward steps need a saved plan. Its original premise was
      wrong (push is the agent's step), and ADR-0043's emission record now covers the hazard.
      Answered on paper in the proposal; **not built**
- [ ] 8.2 **The `next.sh` history suffix** — separate bare fix, same file, different concern
- [ ] 8.3 **The fleet relocation** (`~/bin` → `99-Operations/bin/`) — operator's call, its own context

## 9. Landing

- [ ] 9.1 `preflight.py` CLEAR before any push
- [ ] 9.2 Driven landing; **run each emitted command verbatim** (class 10, stage 1)
- [ ] 9.3 PR body with a `scope` block; the archive rename declares both sides
- [ ] 9.4 Archive on the feature branch (ADR-0040)
- [ ] 9.5 Deploy-down: the runbook is a vault artifact — **operator-applied**, and `96-Runbooks/` is
      **not** a lockstep prefix, so byte-identity is a finding to check, not a pass to assume

## 10. Gate 4 — human sign-off (not agent-delegatable)

- [ ] 10.1 **Approved** — <operator>, <YYYY-MM-DD>. Awaiting sign-off. Decisions warranting review:
      (a) **`OK` is kept** where it means "the operation succeeded", rather than forking per-row
      synonyms — the channel/evidence it used to smuggle moves into fields;
      (b) **`UNAVAILABLE` is retired, not narrowed**;
      (c) **evidence names the exercised channel**, not just attempted-vs-inspected.
