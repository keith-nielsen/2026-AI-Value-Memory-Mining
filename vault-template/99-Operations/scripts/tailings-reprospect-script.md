---
type: meta-script
deploy_target: ~/bin/vault-reprospect.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Detection-only scan of the slag heap. Lists every slagged effort with its grade and
`slag_reason` so the operator can decide whether extraction economics have shifted
(cheaper model, new tool, capability jump) enough to justify re-digging. Promotion
back to `30-Sites/` with `status: dig` is a human-gated file-move — this script
writes nothing (INV-10). Trigger: after a meaningful capability or tooling change.

## Implementation
```python
#!/usr/bin/env python3
import os, pathlib, frontmatter
vault = pathlib.Path(os.environ["VAULT_ROOT"])
for idx in (p for p in (vault / "70-Tailings").glob("*/*.md") if p.stem == p.parent.name):
    m = frontmatter.load(idx).metadata
    print(f"SLAGGED {idx.parent.name}: grade={m.get('grade')} "
          f"reason={m.get('slag_reason', '?')}")
```
