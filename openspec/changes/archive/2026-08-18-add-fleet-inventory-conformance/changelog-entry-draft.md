<!-- SPDX-License-Identifier: Apache-2.0 -->
# CHANGELOG entry — draft for the release that carries this change

**Not to be committed to `CHANGELOG.md` on this branch.** CONTRIBUTING §"Standard contribution
flow": *"The changelog is stamped at release, in a single `release(vX.Y.Z)` commit on the release
branch. That is the practice without exception."* Measured: 22 of the last 22 CHANGELOG commits
before this branch were `release(...)` commits.

Task A2.6 originally said "CHANGELOG.md entry" and was **wrong**. The text below is kept here so
the release stamp does not have to re-derive it.

---

### Added

- **Conformance checks for the corpus's fleet enumerations, and the corrections they caught**
  (`add-fleet-inventory-conformance`). Three checks govern the Layer-0 fleet — `render`/`reconcile`
  for note → deployed, `template-parity` for template → live vault — and between them they left one
  seam open: **nothing governed spec → note**. A script could ship, deploy and enforce an invariant
  while absent from the specification that governs it, indefinitely, with every build green.

  That was not hypothetical. `secret-scan-script.md` → `vault_secrets.py` enforces INV-7, shipped
  2026-07-28 under ADR-0036, reconciles clean — and appeared **zero times** in
  `openspec/specs/maintenance/spec.md`. Ungoverned for 21 days. Simultaneously `README.md` headed its
  table *"Operational Scripts (13)"* above **10 rows**, for a fleet of **14** — wrong twice, in two
  directions, in one section.

  These survived because **an absence has no string to match**: no search-based sweep can find a
  missing row, only an enumeration compared against ground truth. The wider pattern is that every
  drift found in this corpus was a **hand-maintained duplicate of a machine-checkable fact**. The
  executable layer never drifted, because `reconcile` checks it.

  Added: inventory conformance for both enumerations, asserting **both directions** — a note with no
  row, and a row with no note, since a check that detects only omissions passes on a table naming a
  script deleted last month; a stated-count check; cadence conformance; and resolution checking for
  every script path in both `.claude/settings.json` files, where `excludedCommands` appeared nowhere
  in `tests/`, `.github/` or `tools/` and nothing verified that an **exact-match** exclusion named a
  real artifact.

  Also added behavioural coverage for `vault-orphans.py` and `vault-reprospect.py`, which had **none**
  in either harness, taking fleet coverage from 9 of 11 members to 11 of 11. Each carries a
  confirming-half test — a script reporting *everything* must not pass — and a detection-only
  assertion (commit count unchanged, working tree clean), because for a reporting tool a silent no-op
  and a correct report are indistinguishable from an exit code alone.

  **Stated limit, carried in the spec rather than left to be discovered:** the settings check
  establishes that a declared path *resolves*. It cannot establish that the exclusion *matches* at
  the harness layer, because no automated test traverses Claude Code. Only a real agent invocation
  confirms that, and it is therefore an operator step, not a gate.

### Fixed

- **Five statements that contradicted the tree.** The `maintenance` Script Inventory gained its
  missing `secret-scan-script.md` row; `README.md`'s operational-script table gained
  `vault_secrets.py`, `vault_lib.py`, `pre-push` and `outbound-publish-guard.py`, and its heading now
  matches its own rows; `treasury-orphan` is recorded as `manual`, matching its note.

- **Two docstrings that described the fleet as entirely host-deployed.** `tools/template-parity.py`
  said `reconcile` compares a note to its *"`~/bin` target (note → host)"* and `tests/conftest.py`
  said the fixture renders *"into `$HOME/bin`"*. Both have been inaccurate since the git hooks and
  the harness guard became deploy targets: **3 of the 14 targets are in-tree**, and the word "host"
  silently excluded them. Both now describe the mechanism — *the `deploy_target` each note declares* —
  which is what the code has always actually done.

- **Three ADR-0028 cadence stragglers.** `README.md` advertised a `0 6 * * *` schedule for
  `vault-refine-detect.py`, and `docs/USING-THIS-TEMPLATE.md` instructed readers to *"edit the
  `schedule:` field"* — a field nothing reads, on notes of which **zero** declare `schedule:` or
  `runtime: cron`. Both contradicted `maintenance/spec.md`, which had stated the truth correctly all
  along. The customization table now says plainly that there are no cron schedules to customize and
  that installing a cadence is the operator's own business, rather than removing the row and leaving
  the reader to guess. Cadence declarations are Tier-2 conventions (constitution §2), so this needed
  no ceremony.
