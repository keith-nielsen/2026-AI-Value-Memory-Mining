---
type: meta-script
deploy_target: ~/bin/vault-lint.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-02
---
## Rationale
Validates Treasury knowledge notes against the §10.1 frontmatter schema and checks
name conformance (INV-11) across Treasury, Sites, Tailings, Claims, and Logbook.
Imports the shared naming validator (naming.md → `~/bin/vault_naming.py`) so
frontmatter rules and name rules share one authority. Run manually or as a pre-commit
step; exits 1 on any violation so CI can block merges.

Honors the special-file exemptions (`is_exempt`): tool-mandated / convention filenames
(README.md, dailies, *.example, .obsidian/*.json, …) are skipped before the kebab /
≥3-token content rules. The ≥3-token content check is staged behind a flag (commented)
until mechanical enforcement is switched on; the exemption gate is wired now so that
switch is safe.

## Implementation
```python
#!/usr/bin/env python3
import os, sys, pathlib, frontmatter
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_naming import validate_name, is_valid_slug, is_exempt, has_min_hyphen_tokens  # naming.md
vault = pathlib.Path(os.environ["VAULT_ROOT"])
pillars = set(os.environ["PILLARS"].split())
grades = set(os.environ["GRADES"].split())
stages = set(os.environ["KNOWLEDGE_STAGES"].split())
violations = []

# --- frontmatter checks (Treasury knowledge notes) ---
for p in (vault / "40-Treasury").glob("*.md"):        # Catalog is in a subfolder, excluded
    m = frontmatter.load(p).metadata
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
# Treasury note stems must be valid kebab slugs (special-file exemptions skipped).
for p in (vault / "40-Treasury").glob("*.md"):
    if is_exempt(p.name):
        continue
    if not is_valid_slug(p.stem):
        violations.append((p, f"Treasury stem not a kebab slug: {validate_name(p.stem) or 'non-kebab'}"))
# Effort folders (Sites + Tailings) must be valid kebab slugs.
for area in ["30-Sites", "70-Tailings"]:
    for d in (vault / area).glob("*/"):
        if not is_valid_slug(d.name):
            violations.append((d, f"effort folder not a kebab slug: {validate_name(d.name) or 'non-kebab'}"))
# All other content file stems must at least be cross-platform-safe names.
for area in ["20-Claims", "10-Logbook", "40-Treasury/Catalog"]:
    for p in (vault / area).rglob("*.md"):
        if is_exempt(p.name):          # README.md, dailies, *.example, .obsidian/*.json, ...
            continue
        bad = validate_name(p.stem)
        if bad:
            violations.append((p, f"name violation: {bad}"))
        # --- staged: enable when mechanical >=3-token-kebab enforcement is switched on ---
        # elif not is_valid_slug(p.stem) or not has_min_hyphen_tokens(p.stem):
        #     violations.append((p, "stem not >=3-token kebab (INV-11)"))

for p, v in violations:
    print(f"LINT {p}: {v}")
sys.exit(1 if violations else 0)
```
