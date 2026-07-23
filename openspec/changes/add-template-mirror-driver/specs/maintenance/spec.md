<!-- SPDX-License-Identifier: Apache-2.0 -->
## ADDED Requirements

### Requirement: Template→Live Mirror (Repo→Live Apply)

The framework repo SHALL provide a deterministic, offline mirror tool that APPLIES the repo's
LOCKSTEP scaffold onto a deployed vault in the single direction governance allows — `vault-template/`
→ live, one way, never the reverse, never a delete — so a post-merge mirror is performed by one
reviewed invocation instead of a hand-composed `cp`. It is the write-capable counterpart to the
detection-only Template–Live Parity Check: parity ANSWERS "is the mirror complete?", this tool MAKES
it complete. It is a maintainer/mirror-time tool — NOT part of the deployed vault (which is standalone
and never references the repo), NOT a fleet script (no `deploy_target`, never rendered), and NOT a CI
gate.

- **Same manifest, no second source of truth.** The tool reads the existing
  `tools/template-sync-manifest.json` unmodified — the same `lockstep` prefixes and `exclude` list the
  parity check uses. The detector and the fixer MUST agree on one definition of "governed scaffold";
  a divergent manifest is a coordination hazard for no benefit. The shared tree-walk and comparison
  logic live in one module both tools call, never a forked second copy.
- **Direction is strictly repo → live, and the diff is computed, not enumerated.** The tool walks
  both trees itself and acts on what it finds — never on a file list typed from memory. For each
  LOCKSTEP file (excluding the manifest's `exclude`): `MISSING-IN-LIVE` → copy repo → live (creating
  parent directories); `DIFFERS` → overwrite live with the repo's bytes.
- **A live-only file is reported, never resolved.** A file present under a LOCKSTEP prefix in the
  live vault but absent from the template (`MISSING-IN-TEMPLATE`) means something happened outside
  governance; the tool prints it under its own header and leaves it untouched. Deleting it or adopting
  it as canonical is a human's decision, not a silent default.
- **Non-destructive by construction; recovery is git.** The tool never writes to the repo and never
  deletes; the worst case is overwriting a live file with the repo's already-reviewed bytes,
  recoverable from `git status` on the live vault. It never `git add`/commits — committing the mirrored
  change stays the operator's explicit INV-2 step (one commit, structured message).
- **Ends by re-deriving parity; evidence, not assertion.** After acting the tool re-walks both trees
  and prints the identical denominator'd tally the parity check prints (files checked, prefixes,
  excluded, drift) — never a bare success word. A second run against an already-mirrored state copies
  nothing and reports `0 drift` (idempotent).
- **Stdlib-only, offline, no LLM** — the INV-6 determinism posture at the mirror-time maintenance
  layer. Exit contract: `0` mirror complete (0 drift and no `MISSING-IN-TEMPLATE`) · `2` one or more
  `MISSING-IN-TEMPLATE` files found and left untouched (a human decides — distinct from a clean
  success) · `3` blocked (no resolvable live vault, or a manifest with no LOCKSTEP prefixes).

#### Scenario: An already-mirrored vault is a no-op
- **WHEN** `tools/template-mirror.py <VAULT_ROOT>` runs against a vault already byte-identical to the
  template's LOCKSTEP scaffold
- **THEN** it copies nothing, the filesystem is unchanged, it prints the denominator'd tally with
  `0 drift`, and exits `0`

#### Scenario: A missing lockstep file is mirrored forward
- **WHEN** a LOCKSTEP file exists in `vault-template/` but is absent from the live vault
- **THEN** the tool copies it repo → live (creating parent directories), re-derives parity showing
  `0 drift`, and exits `0`

#### Scenario: A differing lockstep file is overwritten with the repo's bytes
- **WHEN** a LOCKSTEP file exists in both trees with differing content (an incomplete or hand-edited
  mirror)
- **THEN** the tool overwrites the live copy with the template's bytes, re-verifies byte-identical,
  and exits `0` — it never writes to the repo

#### Scenario: A live-only lockstep file is reported, not deleted
- **WHEN** a file exists under a LOCKSTEP prefix in the live vault only, with no counterpart in the
  template
- **THEN** the tool does NOT delete or modify it, prints it under a distinct `MISSING-IN-TEMPLATE`
  header, and exits `2` — success and "found something needing a human" are visibly different states

#### Scenario: An excluded generated artifact is never touched
- **WHEN** a file listed in the manifest `exclude` (e.g. `naming-rules.json`, generated into the live
  vault by `vault_naming.py`) differs between the two trees
- **THEN** the tool leaves it untouched and does not count it in the checked/drift tally, matching the
  parity check's behavior exactly

#### Scenario: No resolvable live vault is a blocked run, not a false pass
- **WHEN** the tool is invoked with neither a live-vault argument nor `$VAULT_ROOT`, or against a path
  that is not a vault
- **THEN** it prints a `BLOCKED:` line and exits `3` — it never reports a mirror by silence
