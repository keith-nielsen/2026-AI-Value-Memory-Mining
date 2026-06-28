---
type: meta-script
deploy_target: ~/bin/vault-orphans.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Reports Treasury bullion not linked from any Catalog index. An orphan note is not
broken — it is simply invisible to navigation. Run weekly (or before any Polish
session) to surface notes that need a Catalog entry. Detection only; no writes.

## Implementation
```python
#!/usr/bin/env python3
import os, pathlib, re
vault = pathlib.Path(os.environ["VAULT_ROOT"])
moc_text = "\n".join(p.read_text() for p in (vault / "40-Treasury" / "Catalog").glob("*.md"))
linked = set(re.findall(r"\[\[([^\]|#]+)", moc_text))
orphans = [p.stem for p in (vault / "40-Treasury").glob("*.md") if p.stem not in linked]
for o in sorted(orphans):
    print(f"ORPHAN {o}")
print(f"{len(orphans)} orphan(s)")
```
