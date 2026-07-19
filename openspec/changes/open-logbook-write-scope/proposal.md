<!-- SPDX-License-Identifier: Apache-2.0 -->
# Constitution Override: open-logbook-write-scope

**Change type:** `constitution-override`
**Principle(s) affected:** Touches the `access-control` spec
(`protects: [CONST-02, INV-4, INV-5, INV-6, INV-7, INV-8, INV-14]`). **No Tier-0/Tier-1 element is
overridden or weakened.** CONST-02 places `10-Logbook/` in **Layer 2 (Workings, temporal)** — the
least-protected layer — and this change *aligns enforcement with the layer the constitution already
assigns, rather than changing the assignment*. INV-4 (`40-Treasury/`) and INV-5 (`99-Operations/`)
are untouched at both layers.
**Tier:** 1-adjacent — small diff, but it **withdraws a pre-action safety rail**, which is the class
of change that must never be inferred from a config diff. §5 AI hard-stop honored.
**Proposer:** Keith Nielsen (drafted by Claude Code at operator direction, 2026-07-19)
**Date:** 2026-07-19
**ADR:** ADR-0033 (carries an ADR because protection is *withdrawn*; ADR-0025 is the direct
precedent — the only previous deliberate widening of agent write scope)

---

## Why

Two facts, one of them new:

1. **The framework owns nothing in `10-Logbook/` any more.** ADR-0032 (v0.1.31) retired the daily
   note, its close cycle and the disposition sidecar. The `Edit(/10-Logbook/Daily/*.md)` rule and the
   sidecar carve-out went with them, because their subjects ceased to exist. What remained was the
   kernel `denyWrite` on the whole silo — a rail guarding a room the framework had moved out of.
2. **The rail is what emptied the silo.** ADR-0032's audit found **one** `daily:` commit in the
   project's entire history. The cause was this rail: agents were denied the path at both layers, so
   the only possible author was a human in Obsidian outside the harness. When that ritual lapsed the
   silo went dark the same week. **A working area no worker may enter is not protected; it is
   abandoned.**

**The operating frame (operator, 2026-07-18/19):** an external self-improving, memory-resident harness
(Hermes or equivalent) drives the effort cadence and will write its audit trail of effort into
`10-Logbook/`; this framework engages downstream, refining accumulated ore into banked value. The
instruction is explicit: *"The 10-Logbook will become a working area for Hermes and not
restricted/policed by this vmm framework until further notice."* Any orchestrator running as an agent
under this harness would otherwise inherit the same lockout that emptied the silo the first time.

## What Changes

- **`access-control` spec:** MODIFY `Area Access Matrix` (the `10-Logbook/` row moves Agent `R` → `RW`;
  new footnote ⁷ stating what is and is not withdrawn) and `OS/Harness-Enforced Agent Write Scope`
  (`10-Logbook/` leaves the denied set at both layers; adds the *re-establishing protection is a
  deliberate act* clause and a scenario requiring a governed change to open any protected area).
- **`vault-template/.claude/settings.json`:** remove `"./10-Logbook"` from
  `sandbox.filesystem.denyWrite`. **No tool-layer `Edit(...)` rule is added** — the previous one was
  removed in v0.1.31 with its subject.
- **`openspec/adr/0033-open-logbook-write-scope.md`** (new); README/tree ADR counts 32 → 33.
- **`CHANGELOG.md`:** `[Unreleased]` entry.

**Deliberately out of scope.**
(a) **No other area moves.** `40-Treasury/`, `99-Operations/`, `.claude/`, `96-Runbooks/`, `97-Molds/`
remain denied at both layers. This change moves exactly one array entry.
(b) **No Logbook content schema or format.** The silo stays unspecified pending its tenant;
designing a format for an unbuilt driver is ADR-0028's rejected option (c). Note this is narrower
than it first appears: `vault-lint.py` **already** walks `10-Logbook/` for INV-11 naming and keeps
doing so — what is absent is *content* validation, not all validation.
(c) **No change to the commit-gate.** INV-11 naming continues to apply to everything staged, including
`10-Logbook/` — this change withdraws *pre-action prevention*, not commit-time enforcement.

**External dependency being adopted: NONE.**

---

## Gate 1 — CHECK (Impact Analysis)

**Principle context (in my own words):**

> `access-control` protects CONST-02 and the INV-4/5 write-scope rails. The relevant question is
> whether opening `10-Logbook/` contradicts the layer model — and it does the opposite: CONST-02
> already classifies the silo as **Layer 2 (Workings)**, alongside `20-Claims/` and `30-Sites/`, both
> of which are agent-writable. The pre-ADR-0032 denial was not a layer statement; it was protection
> for a *specific script-owned artifact* (the daily note) plus its typed sidecar. With that artifact
> retired the denial no longer expresses anything about the layer, and keeping it would make
> `10-Logbook/` the only Layer-2 area sealed against the actor the layer exists to serve. The genuine
> cost is stated in the ADR's sacrifice section, not minimised here: the **F13 vector loses its
> structural block on this path**, and the mitigation is that F13's target artifact no longer exists —
> not that the rail improved.

**Blast radius — enumerated by transcript (ADR-0031), not composed.**

**A first draft of this section was *composed* and was wrong** — it listed 6 files. Recorded rather
than replaced silently, because that is F17 (blast radius reasoned instead of executed) and the
correction is the useful part. The executed sweep returns **16**:

```
$ grep -rln "10-Logbook" openspec/specs/ vault-template/ docs/ .github/ tools/ tests/ \
    README.md AGENTS.md CONTRIBUTING.md | sort
AGENTS.md
docs/diagrams.md
docs/glossary.md
docs/method.md
docs/naming-exemptions-rationale.md
docs/obsidian.md
docs/USING-THIS-TEMPLATE.md
openspec/specs/access-control/spec.md
openspec/specs/maintenance/spec.md
openspec/specs/naming-rules/spec.md
openspec/specs/vault-structure/spec.md
README.md
tests/test_fleet.py
vault-template/00-Docs/README.md
vault-template/99-Operations/schemas/publish-manifest.json
vault-template/99-Operations/scripts/knowledge-lint-script.md
```

`vault-template/.claude/settings.json` is absent from the list only because the entry had already
been removed when the sweep ran — the edit, not an oversight.

**Two hits falsified claims already written into ADR-0033, and both were corrected:**

- **`vault-template/99-Operations/scripts/knowledge-lint-script.md:90`** — the linter walks
  `["20-Claims", "10-Logbook", "40-Treasury/Catalog"]` and applies INV-11 naming to every `.md` stem.
  The ADR had asserted *"no linter inspects it."* **False.** Names in the Logbook are enforced twice
  (commit-gate + `vault-lint.py`); the ADR now says so and narrows the residual to *content*
  validation. **Not edited** — behaviour is correct and unchanged by this proposal.
- **`vault-template/99-Operations/schemas/publish-manifest.json:20`** — `10-Logbook/**` sits in
  `never_publish_examples`, so INV-14's path boundary still excludes the silo from public remotes.
  **Opening write scope does not open publication.** Recorded in the ADR as a surviving mitigation.
  **Not edited.**

Disposition of the remaining hits, each read rather than pattern-matched:

- `openspec/specs/access-control/spec.md` — **edited via this change's delta** (both Requirements).
- `openspec/specs/vault-structure/spec.md` — **not edited**; folder tree + CONST-04 ordering, settled
  by ADR-0032, silent on access.
- `openspec/specs/maintenance/spec.md`, `openspec/specs/naming-rules/spec.md` — **not edited**; the
  hits are the retained `YYYY-MM-DD` naming exemption and fleet prose, neither of which asserts a
  write rule.
- `tests/test_fleet.py` — **not edited**; the hit is the naming-exemption fixture (a date-stemmed
  file), which this change does not affect.
- `AGENTS.md`, `README.md`, `docs/*`, `vault-template/00-Docs/README.md` — **not edited**; all
  describe the silo as a reserved/working area (rewritten in v0.1.31). None states an access rule, so
  none becomes false. `AGENTS.md` was checked specifically because v0.1.31 rewrote its write-scope
  paragraph: it names the denied set generically and does not enumerate `10-Logbook`.

**Sweep-completeness note (the F22 lesson applied).** The pattern above is the *area name*. Because an
enforcement entry can name a path without naming the area in prose — the `vault-close-day.py` case
that hid a whole spec in the previous change — both settings files were additionally **parsed as
JSON** and their `deny` / `denyWrite` / `excludedCommands` arrays enumerated, rather than grepped.

## Gate 2 — PLAN (Migration + Regression)

- **Live-first, by circumstance.** The operator applied this to the deployed vault before the template
  carried it. Tolerable because `.claude/settings.json` is **SEED** in `template-sync-manifest.json`
  (instance-owned, never parity-compared) — but the *policy* belongs upstream so forks inherit a
  coherent default, which is what this change delivers. No mirror step is therefore required for the
  live vault; it is already in the target state.
- **A defect was found and fixed in the live file during review:** removing the last element of the
  `deny` and `denyWrite` arrays left **trailing commas**, making `settings.json` unparseable. For the
  duration, the harness was reading a permissions file it could not parse — guard state unverifiable.
  Recorded here because the same trap awaits anyone applying this change by hand to a fork.
- **Regression:** no CI job reads these arrays; `openspec validate --all --strict`,
  `adr-count-lint` (32 → 33), and the standard suite must stay green. `template-parity.py` is
  unaffected (SEED path).
- **Rollback:** re-add one string to one array in the template, and to each deployed vault.

## Gate 3 — EXECUTE + REGRESSION-TEST

*(Transcripts pasted here per ADR-0031.)*

- [ ] `openspec validate open-logbook-write-scope --strict` green
- [ ] `openspec validate --all --strict` green
- [ ] template `settings.json` parses; `denyWrite` has 5 entries, no `10-Logbook`; `deny` unchanged at 5
- [ ] live `settings.json` parses and matches the template's policy for the changed keys
- [ ] full local `pytest` + `validate-scripts.sh` green

## Gate 4 — RE-CHECK + HUMAN SIGN-OFF

- [ ] Blast radius re-checked against the final diff
- [ ] Consequences explicitly accepted (ADR-0033 "Consequence / sacrifice"): agents may write anything
      into `10-Logbook/` unsupervised and unvalidated by this framework — the first Layer-2 area it
      declines to police at all; the F13 vector loses its structural block on this path; re-protection
      requires a deliberate future change following `sidecar-typed-slot-pattern.md`
- [ ] Human sign-off recorded: **Approved — Keith Nielsen, <date>**
