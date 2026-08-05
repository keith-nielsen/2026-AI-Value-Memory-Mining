## 1. Spec (ordinary change — ADDED only, no existing requirement touched)

- [~] 1.1 `maintenance` ADDED: *The Session Prime Measures Capability Before Asserting It* (4 scenarios)
- [x] 1.2 Confirm nature is ordinary, not override — derived from `constitution.md` §3 + the
      `constitution-lint` job body, not paraphrased. ADD-only, nothing weakened; no sacrifice to accept

## 2. Runbook (SSOT)

- [~] 2.1 Fifth gate **measure-don't-infer** ("these four" -> "these five")
- [~] 2.2 Step 3 `[agent]` **Capability probe** — references the reporter, states the four layers
- [~] 2.3 Renumber 3->4, 4->5; update Purpose, Pitfalls, Verification
- [~] 2.4 Frontmatter: `trigger` gains "probe capabilities"; `last-validated` -> 2026-08-05
- [x] 2.5 Runbook-Format conformance: probe **references** the meta-script, no inlined `gh`/`curl`,
      no harness-specific path as SSOT — earlier draft violated this; caught by 3.1 and rewritten

## 3. Blast radius (swept, lockstep)

- [x] 3.1 Corpus sweep, re-runnable transcript in `proposal.md` — 2 live adapters found enumerating
      the gates by name; found the Runbook-Format violation in the draft (2.5)
- [~] 3.2 `vault-template/CLAUDE.md` updated (gate list)
- [~] 3.3 `vault-template/.claude/commands/vmm-session-rebooted.md` updated (gate count + probe step)
- [x] 3.4 Confirmed no-change set: `AGENTS.md` (count-agnostic), `.claude/settings.json`
      (content-agnostic `cat`), ADR-0017/0032 + 6 archived changes (immutable history)

## 4. Regression

- [x] 4.1 `runbook-lint` (CI job reproduced locally) — **4 checked, 0 errors, exit 0**
- [x] 4.2 `openspec validate --all --strict` — **7 passed, 0 failed, exit 0**; CLI `1.6.0` == pin
- [x] 4.3 `vault-template/.claude/settings.json` valid JSON
- [ ] 4.4 `validate-scripts.sh` sandboxed (no `.py` touched — expect no-op)
- [ ] 4.5 CI green on the pull request

## 5. Dogfood — the probe must be RUN, not merely written

**Definition of Done: `[~]` = built, `[x]` = tested.** A prose-only runbook edit passes vacuously —
the exact failure this change exists to prevent.

- [x] 5.1 `tools/pr-flow.py --capabilities` run this session; output recorded in F35
- [x] 5.2 The two conflated facts report **independently** — `gh` UNAVAILABLE coexisting with
      `READ github state OK via anon-rest` and `WRITE git push OK`
- [x] 5.3 Probe **contradicted a wrong recollection** in-session: the memory claiming "commit but
      never push" was disproved by measurement 20 minutes after it was written, and corrected
- [ ] 5.4 Adversarial: mutate the write scope, re-probe, confirm the **new** scope is reported
      (partially evidenced — the operator's live `allowWrite` edit was detected without a restart)

## 6. Release + deploy-down

- [x] 6.1 Gate-4 authorization — operator replied **Approved** 2026-08-05. ⚠ Recorded with a defect:
      the standard prompt (absolute `view <path>` + "reply Approved") was **not issued first**; the
      operator pre-empted it and the path was supplied immediately after, for confirmation against
      the artifact. Sign-off stands unless the operator says otherwise.
- [ ] 6.2 `/opsx:archive` + CHANGELOG + tag
- [ ] 6.3 Deploy-down to live vault: runbook + `CLAUDE.md` + `vmm-session-rebooted.md`
      (operator-applied — `denyWrite`)
- [ ] 6.4 Outbound to GitHub — **operator-authorized (INV-14)**; agent can execute `git`, may not decide

## 7. Raised, not fixed here

- [ ] 7.1 `constitution.md` §4 misdescribes `constitution-lint` (no diff analysis exists) — class 9 +
      class 8; queue to GitHub-platform-hardening, do **not** bundle into this change
- [ ] 7.2 Named residual: no capability reporter exists for a vault deployed without the framework
      repo; INV-6 bars the deterministic fleet from the two network layers
- [ ] 7.3 INV-14 commit-message parser false-positive — 5th reproduction (matched "push" inside a
      `git commit -m` body); already queued
