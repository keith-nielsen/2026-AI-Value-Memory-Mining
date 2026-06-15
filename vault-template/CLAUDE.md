# Vault conventions — Value Mining (read before any operation)

This vault is a Value Mining operation governed by 99-Operations/ and the build PRD.
Content flows: Capture (20-Claims) -> Prospect -> Dig -> Ore -> Sort -> Refine ->
  bullion deposited in 40-Treasury -> Polish (perpetual).
Side paths: Slagged (70-Tailings, retained, re-minable) and Spoil (71-Spoil, terminal:
  spent husks + waste).
Downstream (future): 50-Mint (dated editions), 60-Forge (bespoke wares).
Special: 80-Crucible (rare, by-exception, independent model/operator, direct inject
  with crucible: true).

Always obey:
- Content is Markdown + YAML frontmatter only, UTF-8. (INV-1)
- Pillars are metadata + tags + Catalog (MOC) links, never folders under 40-Treasury. (INV-12)
- Internal links use [[wikilinks]]. (INV-13)
- NEVER write to 40-Treasury/ or 99-Operations/ autonomously. Agents write only to
  their assigned 30-Sites/<slug>/ working area and 20-Claims/_refine-proposals/.
  Scripts write to 40-Treasury/ only when applying a human-approved proposal from
  20-Claims/_refine-approved/. (INV-4, INV-5)
- Every automated change = exactly one git commit, structured message. (INV-2)
- Operational scripts live in 99-Operations/scripts/ as literate meta-script notes
  and reach the host via `render`; drift is detected via `reconcile`, never
  auto-fixed. (INV-3)
- Refined value (40-Treasury) is never archived or deleted by automation. Only effort
  husks go to Spoil; only waste is discarded. Tailings are retained. (INV-9, INV-10)
- No secrets in any vault file. (INV-7)
- Deterministic scripts: no network, no LLM calls. (INV-6)
- Crucible uses an independent model/operator; main agent excluded. (INV-8)
- All file/folder names conform to the naming ruleset (99-Operations/schemas/naming-rules.json):
  cross-platform-safe chars, no reserved names, kebab-case slugs for effort folders and
  Treasury stems. Enforced by the linter, the refine executor, and the pre-commit hook —
  never trust a producer to self-comply. (INV-11)
- grade = value only (coal<bronze<silver<gold); never an effort measure.
- Config lives in 99-Operations/config.env. Pillar list there is authoritative.

Build order: Phase 0 -> 1 -> 2. Phase 3 is spec-only/disabled. Phase 4 is deferred.
Run each phase's acceptance tests (PRD §13) and report before continuing.
