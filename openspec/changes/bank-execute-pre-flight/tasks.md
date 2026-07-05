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

- [ ] 5.1 [human] Gate-4 sign-off in `proposal.md`
- [ ] 5.2 [human] PR from `ops/bank-execute-pre-flight`; CI green; merge (INV-14: agent cannot)
- [ ] 5.3 [human] `cp` the note into live `99-Operations/scripts/`; `~/bin/vault-render.py
      render` + `reconcile` (zero drift)
- [ ] 5.4 [agent] Live probe: reject path (seeded invalid proposal → REJECT + rc 1 + no write,
      cleaned up); good-path bank at the operator's next real refine
- [ ] 5.5 [human] Archive (ADDED-only — after the three queued deltas or alongside);
      CHANGELOG heading + tag per release cadence (push main before tagging)
