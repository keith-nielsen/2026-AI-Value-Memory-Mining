# Extend LOCKSTEP to governance content, and add the repo-work prime

## Why

A vault-rooted session doing framework-repo work loads **none of the repo's governance** — the
harness loads `CLAUDE.md` for the project directory, so `CLAUDE.md`, `AGENTS.md` and
`CONTRIBUTING.md` (576 lines) are invisible. On 2026-09-06 that produced three rounds of
hand-composed pull-request sequence against a repo whose `CONTRIBUTING.md` opens *"Walk it; do not
hand-compose the sequence"* — failure class 10, the pattern the ledger records as invoked eight times
and tallied never.

The step that would have prevented it **already exists and never arrived**. Measured 2026-09-08:

| Artifact | template | live vault |
|---|---|---|
| `96-Runbooks/session-bootstrap-loader.md` | 182 lines | **141** |
| `.claude/commands/vmm-session-rebooted.md` | 33 lines | **23** |

The 12 missing command lines say, verbatim: *"invoke the driver, never describe it from memory …
**Never hand-compose a `gh` mutation**."*

Nothing detected this. `template-parity.py` reports `0 drift` **correctly** — it compares only the
two declared LOCKSTEP prefixes, and neither of these paths is one. The gap is manifest **coverage**,
not tool reach.

## What Changes

1. **`tools/template-sync-manifest.json`** — add `96-Runbooks/` and `.claude/commands/` to
   `lockstep`. This is the enabling step, not extra scope: `template-mirror.py` carries only files
   declared LOCKSTEP, so it **cannot** deploy these paths until they are declared.
2. **`vault-template/.claude/commands/vmm-repo-github.md`** — a new `/vmm-repo-github` prime, loaded
   when repo work is *proposed*, not when it is executed.
3. **Spec delta** — the `maintenance` requirement *Template–Live Parity Check (Mirror Completeness)*
   enumerates the lockstep prefixes and states that everything outside one is per-instance seed that
   `SHALL NOT` be compared. Adding prefixes contradicts it as written, so the requirement is MODIFIED
   to separate **governance content** (lockstep) from **per-instance configuration** (seed).

### The stub/card split

The command is deliberately **two-part**: a stable stub that ships here, pointing at a content card
under `30-Sites/` that can be iterated without ceremony while the content settles. The stub carries
the irreducible instruction itself (`pr-flow.py --plan`, never hand-compose) so the highest-value
line survives even if the card is absent, and it **stops loudly** on a missing or unmarked card
rather than degrading to recollection.

⚠ A vault deployed elsewhere receives a pointer to a `30-Sites/` path it does not have. **Accepted
knowingly** — the failure is loud, not silent, and the card is promoted into a protected Ops location
once refined.

## Impact

- **Not constitutional.** Neither target carries a `protects:` frontmatter key; the diff gate keys on
  that, never on a substring.
- **Deployed vaults lose runbook autonomy.** LOCKSTEP is byte-identical, so a vault that customized a
  runbook would have it overwritten by the mirror. Consistent with `AGENTS.md` calling runbooks *"the
  single, harness-agnostic source of truth"*, but it is a real narrowing and is chosen deliberately.
- **`.claude/settings.json` stays SEED.** Only `commands/` is declared. Registration remains
  per-instance and therefore still unverifiable by comparison — hardening item 32, unchanged by this
  change and explicitly out of scope.
- **Closes hardening item 34** as a by-product.

## Constitutional impact

Archiving syncs this change's delta into `openspec/specs/maintenance/spec.md`, which carries a
`protects:` frontmatter key. The gate requires the question be answered **in the tree**, in writing.

Checked against each protected invariant rather than asserted:

- **INV-3** (*drift is detected, never auto-fixed*) — the modified requirement retains
  **"Detection only, never auto-fix"** verbatim. Parity still reports and exits non-zero; a human
  re-runs the mirror. Coverage widens; the posture does not change.
- **INV-6** (*deterministic scripts: no network, no LLM*) — retained verbatim as
  **"Stdlib-only, offline, no LLM"**. Adding directory prefixes changes what is compared, never how.
- **INV-2** (*one commit per automated change*) — untouched; this change alters no commit ceremony.

The change **widens what an existing detector observes**. It grants no new authority, relaxes no
guarantee, and removes no check.

```constitutional-impact
touches: openspec/specs/maintenance/spec.md
protects: [INV-2, INV-3, INV-6]
overrides: none
basis: MODIFIED requirement widens LOCKSTEP coverage to governance content; INV-3 detection-only and INV-6 stdlib-only/offline both retained verbatim in the delta; no authority granted, no check removed
```

## Verification

Post-merge, in order — each step has its own proof:

1. `tools/template-mirror.py` — now able to carry the drifted runbook, the drifted command, and the
   new stub in one guarded invocation.
2. `tools/template-parity.py` — must report **0 drift**, which is the evidence all three landed.

Measured before proposing: of the five files these prefixes bring under lockstep, **three are already
identical**; the two drifted ones differ only by being older (43 and 12 template-only lines; the
vault-only lines are renumbered steps). **The deploy-down destroys nothing**, and the file sets match,
so there are no `MISSING-IN-TEMPLATE` cases needing adjudication.
