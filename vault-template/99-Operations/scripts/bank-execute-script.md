---
type: meta-script
deploy_target: ~/bin/vault-refine-execute.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Applies approved refine proposals from `20-Claims/_refine-approved/` (the human gate,
INV-4). The human gate is the act of moving a proposal from `_refine-proposals/` to
`_refine-approved/` — this script never promotes proposals itself. Validates the
proposed `target_note` stem against the naming ruleset (INV-11) before any write;
non-conforming names are rejected with a REJECT message, not written. After writing
the knowledge note it appends wikilinks to the named Catalog MOCs and deletes the
consumed proposal. One note per proposal; multiple proposals can be batched.

## Implementation
```python
#!/usr/bin/env python3
import os, json, pathlib, datetime, sys, frontmatter
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_naming import is_valid_slug  # naming.md
vault = pathlib.Path(os.environ["VAULT_ROOT"])
today = datetime.date.today().isoformat()
approved = vault / "20-Claims" / "_refine-approved"
for prop in sorted(approved.glob("*.json")):
    p = json.loads(prop.read_text())
    note = vault / p["target_note"]
    if not is_valid_slug(note.stem):                  # INV-11: reject at the boundary
        print(f"REJECT {prop.name}: target_note stem '{note.stem}' is not a valid kebab slug")
        continue
    note.parent.mkdir(parents=True, exist_ok=True)
    if p["mode"] == "create":
        post = frontmatter.Post(
            p["insight_md"],
            type="knowledge", title=note.stem,
            pillars=p["frontmatter"]["pillars"],
            grade=p["frontmatter"]["grade"],
            stage="refined",
            crucible=p["frontmatter"].get("crucible", False),
            created=today, updated=today,
        )
        note.write_text(frontmatter.dumps(post)
                        + f"\n\n## Provenance / Changelog\n{p['provenance_md']}\n")
    elif p["mode"] == "append":
        note.write_text(note.read_text()
                        + f"\n\n{p['insight_md']}\n\n## Provenance\n{p['provenance_md']}\n")
    else:
        raise ValueError(f"bad mode: {p['mode']}")
    for link in p["index_links"]:
        mp = vault / link
        mp.write_text(mp.read_text() + f"\n- [[{note.stem}]]")
    prop.unlink()
    print(f"refined -> {note}")
```
