## MODIFIED Requirements

### Requirement: Template–Live Parity Check (Mirror Completeness)

The framework repo SHALL provide a deterministic, offline, detection-only tool that verifies a
deployed vault's LOCKSTEP scaffold is byte-identical to what the repo's `vault-template/` ships, so
a post-merge mirror can be proven complete rather than assumed. It answers the axis `reconcile`
cannot: `reconcile` compares a script note to its deployed target, wherever its own
`deploy_target` declares (note → deployed copy); this
compares repo-shipped scaffold to live-deployed scaffold (template → vault). It is a
maintainer/mirror-time check — NOT part of the deployed vault (which is standalone and never
references the repo) and NOT a CI gate (CI has no live vault to compare against).

- **Lockstep scope is an explicit manifest.** A repo-owned `tools/template-sync-manifest.json`
  declares `lockstep` directory prefixes, and an `exclude` list for files under a lockstep prefix
  that the live vault legitimately GENERATES (the template ships the generator, not its output; e.g.
  `99-Operations/schemas/naming-rules.json`, emitted by `vault_naming.py`).
- **The dividing line is GOVERNANCE CONTENT versus PER-INSTANCE CONFIGURATION.** Lockstep covers
  what the framework governs and an instance MUST NOT silently diverge from: the INV-3
  source-of-truth scaffold (`99-Operations/scripts/`, `99-Operations/schemas/`), the spec-as-code
  runbooks (`96-Runbooks/`), and the agent commands that carry ceremony (`.claude/commands/`).
  A runbook and a ceremony command are single-source-of-truth artifacts by their own definition; an
  instance that edits one has forked the governance, which is drift by construction rather than
  legitimate local ownership.
- **Everything outside a lockstep prefix is per-instance seed and SHALL NOT be compared** —
  `CLAUDE.md`, config, `40-Treasury/`, Catalog indexes, README, and `.claude/settings.json`.
  ⚠ `.claude/settings.json` is seed **deliberately**: it carries per-instance permissions, sandbox
  scope and hook registration. Because it is never compared, **hook registration cannot be verified
  by parity at all** — a hook may be deployed, byte-correct and unloaded while this check reports
  zero drift. That gap is real, is out of scope for this requirement, and requires an assertion
  rather than a comparison.
- **Comparison is byte-exact and bidirectional.** For each prefix the union of files under the prefix
  in BOTH trees is compared: a file present in one tree but absent from the other is drift
  (`MISSING-IN-LIVE` / `MISSING-IN-TEMPLATE`); a differing file is drift (`DIFFERS`). Directory-prefix
  scope means a newly-shipped file under a lockstep prefix is compared automatically — it cannot go
  silently unchecked.
- **Detection only, never auto-fix.** Like `reconcile` (INV-3) the tool reports drift and exits
  non-zero; it never writes. A human re-runs the mirror to resolve drift.
- **Evidence, not assertion.** The tool prints the count of files actually compared (the denominator)
  alongside the drift count, so an empty drift list cannot be mistaken for a broken comparison.
- **Stdlib-only, offline, no LLM** — the INV-6 determinism posture applied at the mirror-time
  maintenance layer. Exit contract mirrors the fleet: `0` in parity · `1` drift · `3` blocked
  (no resolvable live vault, or a manifest with no lockstep prefixes).

#### Scenario: A clean mirror reports zero drift
- **WHEN** `tools/template-parity.py <VAULT_ROOT>` runs after a complete mirror
- **THEN** every non-excluded file under each lockstep prefix is byte-identical between
  `vault-template/` and the live vault, it prints the count of files checked with `0 drift`, and
  exits `0`

#### Scenario: A hand-edited or unmirrored lockstep file is drift
- **WHEN** a deployed lockstep file differs from the template it was shipped from (an incomplete
  mirror, or a local edit)
- **THEN** the tool prints `DIFFERS: <path>` and exits `1` — the incomplete apply is surfaced, and
  the tool does not modify either tree

#### Scenario: A lockstep file present in only one tree is drift
- **WHEN** a file under a lockstep prefix exists in the template but not the live vault (or the
  reverse)
- **THEN** the tool prints `MISSING-IN-LIVE: <path>` (or `MISSING-IN-TEMPLATE: <path>`) and exits `1`

#### Scenario: A generated artifact under a lockstep prefix is excluded, not flagged
- **WHEN** a file listed in the manifest `exclude` (e.g. `naming-rules.json`) exists only in the live
  vault because the vault generates it
- **THEN** the tool does NOT report it as drift; it is counted as excluded and the run can still exit
  `0`

#### Scenario: No resolvable live vault is a blocked run, not a false pass
- **WHEN** the tool is invoked with neither a live-vault argument nor `$VAULT_ROOT`, or against a
  path that is not a vault
- **THEN** it prints a `BLOCKED:` line and exits `3` — it never reports parity by silence

#### Scenario: A drifted runbook or ceremony command is detected, not silently tolerated
- **WHEN** a deployed vault's `96-Runbooks/` or `.claude/commands/` file differs from the template
  it was shipped from — including by being an older revision that never received a mirror
- **THEN** the tool reports it as `DIFFERS` and exits `1`, so a governance artifact that exists in
  the framework but never arrived in the vault cannot read as deployed

#### Scenario: Per-instance configuration is not compared
- **WHEN** a deployed vault's `.claude/settings.json`, `CLAUDE.md` or Catalog indexes differ from the
  template
- **THEN** the tool does NOT report drift — these are seed, owned by the instance, and comparing them
  would convert legitimate local ownership into a permanent false positive
