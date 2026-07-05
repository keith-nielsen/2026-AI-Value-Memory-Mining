<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `maintenance` — MODIFIED "One Mutation, One Commit (INV-2)": ownership clause +
      scenarios (daily-note commit; atomic bank; scoped seal vs. unrelated changes)
- [x] 1.2 `maintenance` — MODIFIED "Script Inventory": daily-note / bank-execute / daily-close
      purpose cells

## 2. Implementation (vault-template)

- [x] 2.1 `daily-note-script.md` — commit the created note (`daily: opened <date>`); `exists`
      path commit-free
- [x] 2.2 `bank-execute-script.md` — one atomic scoped commit per banked proposal
      (`bank: <stem>`: note + index links + consumed proposal)
- [x] 2.3 `daily-close-script.md` — `add -A` sweep → `commit_paths(VAULT, [daily, sidecar], …)`;
      `subprocess` import dropped; message `close: <day> daily — N items dispositioned`
- [x] 2.4 `vault-lib-script.md` — `commit_paths` tolerates consumed paths (deleted + never
      tracked); tracked deletions staged

## 3. Docs

- [x] 3.1 `CHANGELOG.md` — `[Unreleased]` entry

## 4. Regression (repo-side, before Gate 3 closes)

- [x] 4.1 `openspec validate commit-ownership-de-sweep --strict` + `--all --strict`
- [x] 4.2 `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [x] 4.3 Sandbox battery: daily-note commit probe (+ `exists` no-op); tracked-proposal atomic
      bank probe; tracked-sidecar scoped-seal probe with unrelated staged file; untracked
      consumed-path tolerance (sidecar + proposal)

## 5. Gate 4 + publish + live apply (human-gated)

- [x] 5.1 [human] Gate-4 sign-off recorded (post-merge; provenance note in `proposal.md`)
- [x] 5.2 [human] Merged in order: wave-2 PR #9 (`c3174b0`) → B3 PR #10 (`2bc348c`), CI green
      (2026-07-05)
- [ ] 5.3 [human] Combined live apply: `cp` all changed notes; `~/bin/vault-render.py render` +
      `reconcile` (zero drift)
- [ ] 5.4 [agent] Live probes: wave-2 battery + daily-note commit + (at operator's close time)
      scoped seal; record in the Site
- [ ] 5.5 [human] Archive order: `fix-commit-gate-env-guard` → `wave-2-vault-lib-adoption` →
      this change; CHANGELOG heading + tag per release cadence (push main before tagging)
