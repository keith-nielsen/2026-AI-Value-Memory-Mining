<!-- SPDX-License-Identifier: Apache-2.0 -->
## 1. Spec delta

- [x] 1.1 `maintenance` — ADDED "Refine Executor Pre-Flight and Batch Isolation" + scenarios
      (batch isolation, INV-9 no-overwrite, pre-write link rejection, containment)

## 2. Implementation (vault-template)

- [x] 2.1 `bank-execute-script.md` — `check()` pre-flight (schema, containment, INV-11, INV-9,
      vocab, link targets); REJECT-and-continue for bad JSON/mode; all reasons printed; exit
      `1` on any reject / `0` clean; B3 atomic commit unchanged

## 3. Docs

- [x] 3.1 `CHANGELOG.md` — `[Unreleased]` entry

## 4. Regression (repo-side, before Gate 3 closes)

- [x] 4.1 `openspec validate bank-execute-pre-flight --strict` + `--all --strict`
- [x] 4.2 `bash .github/scripts/validate-scripts.sh` → `VALIDATION OK`
- [x] 4.3 Sandbox battery: malformed+valid batch (isolation, rc 1); create-collision
      (byte-identical target); missing-link (no note created); traversal; bad vocab;
      append-to-missing; clean batch rc 0

## 5. Gate 4 + publish + live apply (human-gated)

- [x] 5.1 [human] Gate-4 sign-off recorded (post-merge; provenance note in `proposal.md`)
- [x] 5.2 [human] PR #11; CI green; merged `cbfb6e7` (2026-07-05)
- [x] 5.3 [human] Applied live + rendered (vault `6e1fb8c`); `reconcile` zero drift
- [x] 5.4 [agent] Live probe green (2026-07-05): bare env-free run over the empty approved
      queue → rc 0 (exit contract live); rendered executor verified (pre-flight present,
      reconcile clean). Reject path sandbox-proven; live reject/good paths land at the next real
      refine (agent does not seed `_refine-approved/` — that directory IS the human gate, INV-4)
- [ ] 5.5 [human] Archive (ADDED-only — after the three queued deltas or alongside);
      CHANGELOG heading + tag per release cadence (push main before tagging)
