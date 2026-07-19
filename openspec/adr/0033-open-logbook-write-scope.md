<!-- SPDX-License-Identifier: Apache-2.0 -->
# ADR-0033 — Open `10-Logbook/` to agent writes: the framework stops policing a silo it no longer owns

**Status:** **Proposed** (Gate-4 pending — human-only sign-off, constitution §5)
**Date:** 2026-07-19
**Change:** `open-logbook-write-scope` (`constitution-override`, **conforming** — touches the
`access-control` spec [`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`]. **No
Tier-0/Tier-1 element is overridden.** CONST-02 places `10-Logbook/` in Layer 2 (Workings, temporal)
and is *upheld*, not weakened: this change aligns the enforcement with the layer the constitution
already assigns. INV-4/INV-5 protect `40-Treasury/` and `99-Operations/` — neither is touched.)
**Relates / extends:** ADR-0022 (OS-enforced agent write scope — establishes the rails this change
narrows); **ADR-0025** (`permit-agent-claims-capture` — the direct model: the previous deliberate
widening, for `20-Claims/`); ADR-0032 (retired the daily cycle, removing the last framework-owned
artifact in this silo)

## Context

ADR-0022 denied agent writes to `10-Logbook/` at **both** layers — the OS sandbox (`denyWrite`) and
the harness permission rules (`Edit(/10-Logbook/Daily/*.md)`) — with one deliberate gap: the
disposition sidecar `*.resolutions.json`, writable by **pattern disjointness**, which was the agent's
single typed slot in the daily-close cycle.

**ADR-0032 removed the reason for all of it.** With the daily note and its close cycle retired, the
silo contains no script-owned artifact, no sidecar, and no framework-generated content of any kind.
The `Edit(...)` rule and the carve-out were both removed in v0.1.31 because their subjects ceased to
exist. What remained was the kernel-level `denyWrite` on the silo as a whole — a rail guarding a room
the framework had moved out of.

**The evidence that this rail was already doing harm, not good.** ADR-0032's audit found exactly
**one** `daily:` commit in the project's history. The reason was this rail: agents were denied the
path at both layers, so the only actor that could ever write a daily was a human typing into Obsidian
outside the harness. The silo went dark the same week that ritual lapsed, because **nothing else was
permitted to write there.** A working area no worker can enter is not protected; it is abandoned.

**The operating frame (operator, 2026-07-18/19).** An external self-improving, memory-resident
harness — Hermes or equivalent — drives the effort cadence and will write its **audit trail of
effort** into `10-Logbook/`. This framework engages downstream: it refines accumulated ore into
banked value. The operator's instruction is explicit: *"The 10-Logbook will become a working area for
Hermes and not restricted/policed by this vmm framework until further notice."*

Under that frame the rail is not merely obsolete — it is **actively wrong**, because any orchestrator
running as an agent under this harness inherits the same lockout that emptied the silo the first
time. The failure mode is documented and dated in
`30-Sites/determinism-failure-modes-claude/sidecar-typed-slot-pattern.md`.

## Decision

**Remove `./10-Logbook` from `sandbox.filesystem.denyWrite`, and add no tool-layer `Edit(...)` rule
in its place.** The silo becomes an ordinary Layer-2 working area, writable by agents at both layers.

- **Whole silo, not a subpath.** `Daily/`, `Reviews/`, and anything the future harness creates are all
  opened. A partial opening would encode a distinction the framework no longer makes — it owns no
  artifact in there to distinguish.
- **No tool-layer twin.** A narrower `Edit(...)` rule is only justified when some artifact within a
  writable area is script-owned (the pre-ADR-0032 shape). Nothing in `10-Logbook/` is. Adding a rule
  with no subject would be the "spec describes a system that does not exist" defect ADR-0028 and
  ADR-0032 both set out to end.
- **Scope is precisely this silo.** `40-Treasury/`, `99-Operations/`, `.claude/`, `96-Runbooks/` and
  `97-Molds/` remain denied at both layers. This change moves one entry; it does not soften the model.

**What still binds inside `10-Logbook/` — "unpoliced" would be inaccurate.** The `core.hooksPath`
pre-commit gate reads **all** staged filenames with no silo exemption, so **INV-11 naming enforcement
continues to apply** (with the standing `YYYY-MM-DD.md` exemption, retained by ADR-0032 for the
existing dailies). INV-1 (Markdown + YAML, UTF-8) and INV-2 (one mutation, one commit) are unchanged.
What is withdrawn is **pre-action write prevention**, not the commit-time and format rails.

## Options considered

- **(a) Open the whole silo, no tool-layer rule (chosen).** Matches the stated purpose, matches what
  the framework actually owns there (nothing), and is the smallest coherent statement.
- **(b) Open `10-Logbook/Daily/` only, keep `Reviews/` denied.** Rejected: `Reviews/` is empty, has no
  framework-owned content and no generator. Protecting it would guard an empty room for symmetry.
- **(c) Open at the kernel layer, restore a narrow tool-layer `Edit(...)` rule.** Rejected: a rule
  needs a subject. There is no script-owned artifact left to shield, so the rule would assert a
  false ownership and mislead the next reader into thinking one exists.
- **(d) Leave it closed; let the future harness write via a `excludedCommands` drive path.** Rejected
  as the shape that already failed. It presumes the writer is a *script this framework renders* —
  Hermes is an independent harness, not a fleet member, and ADR-0028 settled that the driver lives
  outside the vault. Requiring the vault to pre-authorize each of an external driver's invocations
  re-creates the lockout in a more brittle form.
- **(e) Do nothing — the silo is empty, so who cares.** Rejected on the ADR-0032 evidence: the rail is
  what *kept* it empty. Leaving it is choosing the outcome that already happened once.

## Consequence / sacrifice

- **Agents can now write anything into `10-Logbook/` without pre-action prevention.** That is the
  explicit instruction ("not restricted/policed … until further notice") and it is accepted knowingly.
  **But "unpoliced" would be false, and the Gate-1 sweep proved it** — two rails survive and were
  found by transcript, not assumed:
  - **Names are still enforced, twice.** The `core.hooksPath` pre-commit gate reads all staged
    filenames, *and* `knowledge-lint-script.md` walks `["20-Claims", "10-Logbook",
    "40-Treasury/Catalog"]` applying the INV-11 kebab/token rules to every `.md` stem (honouring the
    `YYYY-MM-DD.md` exemption ADR-0032 retained). A junk filename in the Logbook still fails the
    linter and still blocks a commit.
  - **Publication is still denied.** `publish-manifest.json` lists `10-Logbook/**` under
    `never_publish_examples`, so INV-14's path-level boundary continues to exclude the silo from any
    public remote. **Opening write scope does not open publication** — the two are independent rails
    and only one moves here.
  What is genuinely withdrawn is **pre-action write prevention** and **content validation**: no
  frontmatter schema governs Logbook files (the `daily` type retired with ADR-0032), so a
  well-*named* but semantically spurious file is not detected until a human looks. That is the honest
  residual — narrower than "unpoliced", and it is the first Layer-2 area whose *content* the
  framework declines to govern at all.
- **The F13 vector formally loses its structural block for this path.** F13 was an agent
  hand-authoring a `[script]`-owned daily note out of order; the rail that made a recurrence
  impossible is being removed. The mitigating fact is not that the rail got better — it is that
  **the artifact F13 attacked no longer exists**. Should a future driver introduce a governed artifact
  here, the block must be **re-established deliberately**, and the four-layer shape for doing so is
  recorded in the Site's `sidecar-typed-slot-pattern.md`. This ADR is the reason that note was written
  before the scripts were deleted.
- **Reversal is one line in two files** (the template and each deployed vault's
  `.claude/settings.json`), with no migration and no data to unwind.
- **Blast radius is genuinely one silo.** The change touches a single array entry. The reason it
  warrants an ADR is not its size but its *direction*: it is the second deliberate widening of agent
  write scope in the project's history (after ADR-0025), and a widening recorded only as a config
  diff is one no future reader can distinguish from an accident.
- **Live-first, by circumstance.** The operator applied this to the deployed vault before the template
  carried it — the inverse of the framework's normal upstream-then-deploy flow. That is tolerable
  because `.claude/settings.json` is **SEED** in `template-sync-manifest.json` (instance-owned, not
  parity-compared), but the *policy* belongs upstream so forks inherit a coherent default, which is
  what this change delivers.
