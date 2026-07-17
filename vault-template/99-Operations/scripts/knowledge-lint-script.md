---
type: meta-script
deploy_target: ~/bin/vault-lint.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-17
---
## Rationale
Validates Treasury knowledge notes against the §10.1 frontmatter schema and checks
name conformance (INV-11) across Treasury, Sites, Tailings, Claims, and Logbook.
Imports the shared naming validator (naming.md → `~/bin/vault_naming.py`) so
frontmatter rules and name rules share one authority. Run manually or as a pre-commit
step; exits 1 (`EXIT_VIOLATION`) on any violation so CI can block merges. Root and the
`PILLARS`/`GRADES`/`KNOWLEDGE_STAGES` vocabularies resolve via the shared `vault_lib`
(process env > config files; all three are required — no code default), so the bare
invocation works without a pre-sourced environment (ADR-0023, wave-2 adoption).

Validates the `PILLARS` vocabulary itself before using it (ADR-0029): every token must be a
valid kebab slug, because a pillar token is interpolated directly into its Catalog index name
(`<pillar>-domain-index.md`) and must satisfy the grammar that filename does. The ≥3-token floor
governs `.md` stems, not name fragments, so it is **not** applied — `mental` is a valid pillar,
`mental-health` is one pillar, `Mental_Health` is a violation. A malformed vocabulary exits
immediately rather than cascading: every note's `pillars` would otherwise fail the subset check
below, burying the single real fault under a pile of false ones.

Honors the special-file exemptions (`is_exempt`): tool-mandated / convention filenames
(README.md, dailies, *.example, .obsidian/*.json, …) are skipped before the kebab /
≥3-token content rules. The ≥3-token content check is staged behind a flag (commented)
until mechanical enforcement is switched on; the exemption gate is wired now so that
switch is safe.

## Implementation
```python
#!/usr/bin/env python3
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_naming import validate_name, is_valid_slug, is_exempt, has_min_hyphen_tokens  # naming.md
from vault_lib import EXIT_VIOLATION, find_vault_root, fm, vocab
vault = find_vault_root()
pillars = set(vocab("PILLARS"))
# --- vocabulary integrity: PILLARS tokens must be kebab slugs (ADR-0029) ---
# A pillar token is interpolated straight into the Catalog index name
# <pillar>-domain-index.md, so it must satisfy the same slug grammar the filename does.
# The >=3-token floor (INV-11) governs .md *stems*, not name fragments — deliberately
# NOT applied here, so single-word pillars like `mental` stay valid.
# Exits immediately: a malformed vocabulary makes every note's `pillars` fail the
# subset check below, burying the one real fault under a cascade of false ones.
bad_pillars = [t for t in sorted(pillars) if not is_valid_slug(t)]
if bad_pillars:
    for t in bad_pillars:
        print(f"LINT PILLARS: token {t!r} is not a kebab slug: {validate_name(t) or 'non-kebab'}")
    sys.exit(EXIT_VIOLATION)
grades = set(vocab("GRADES"))
stages = set(vocab("KNOWLEDGE_STAGES"))
violations = []

# --- frontmatter checks (Treasury knowledge notes) ---
for p in (vault / "40-Treasury").glob("*.md"):        # Catalog is in a subfolder, excluded
    m = fm(p)
    if m.get("type") != "knowledge":
        violations.append((p, "type must be 'knowledge'"))
    pset = set(m.get("pillars") or [])
    if not pset or not pset <= pillars:
        violations.append((p, f"pillars must be non-empty subset of {sorted(pillars)}"))
    if m.get("grade") not in grades:
        violations.append((p, f"grade must be one of {sorted(grades)}"))
    if m.get("stage") not in stages:
        violations.append((p, f"stage must be one of {sorted(stages)}"))

# --- name conformance (INV-11) ---
# Content stems carry the full rule: kebab + the >=3-token floor (ADR-0015's rule, switched
# on by ADR-0030 — conformance reached, so nothing is grandfathered here any more).
# Treasury note stems (special-file exemptions skipped).
for p in (vault / "40-Treasury").glob("*.md"):
    if is_exempt(p.name):
        continue
    if not is_valid_slug(p.stem):
        violations.append((p, f"Treasury stem not a kebab slug: {validate_name(p.stem) or 'non-kebab'}"))
    elif not has_min_hyphen_tokens(p.stem):
        violations.append((p, "Treasury stem not >=3-token kebab (INV-11)"))
# Effort folders (Sites + Tailings) — kebab slugs carrying the content floor.
for area in ["30-Sites", "70-Tailings"]:
    for d in (vault / area).glob("*/"):
        if not is_valid_slug(d.name):
            violations.append((d, f"effort folder not a kebab slug: {validate_name(d.name) or 'non-kebab'}"))
        elif not has_min_hyphen_tokens(d.name):
            violations.append((d, "effort folder not >=3-token kebab (INV-11)"))
# All other content file stems.
for area in ["20-Claims", "10-Logbook", "40-Treasury/Catalog"]:
    for p in (vault / area).rglob("*.md"):
        if is_exempt(p.name):          # README.md, dailies, *.example, .obsidian/*.json, ...
            continue
        bad = validate_name(p.stem)
        if bad:
            violations.append((p, f"name violation: {bad}"))
        elif not is_valid_slug(p.stem) or not has_min_hyphen_tokens(p.stem):
            violations.append((p, "stem not >=3-token kebab (INV-11)"))

for p, v in violations:
    print(f"LINT {p}: {v}")
sys.exit(EXIT_VIOLATION if violations else 0)
```
