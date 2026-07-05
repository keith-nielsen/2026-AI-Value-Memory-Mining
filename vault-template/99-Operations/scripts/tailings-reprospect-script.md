---
type: meta-script
deploy_target: ~/bin/vault-reprospect.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-05
---
## Rationale
Detection-only scan of the slag heap. Lists every slagged effort with its grade and
`slag_reason` so the operator can decide whether extraction economics have shifted
(cheaper model, new tool, capability jump) enough to justify re-digging. Promotion
back to `30-Sites/` with `status: dig` is a human-gated file-move — this script
writes nothing (INV-10). Trigger: after a meaningful capability or tooling change.
Root and frontmatter access via the shared `vault_lib` (ADR-0023, wave-2 adoption):
the bare invocation works without a pre-sourced environment.

## Implementation
```python
#!/usr/bin/env python3
import pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_lib import find_vault_root, fm  # vault-lib-script.md
vault = find_vault_root()
for idx in (p for p in (vault / "70-Tailings").glob("*/*.md") if p.stem == p.parent.name):
    m = fm(idx)
    print(f"SLAGGED {idx.parent.name}: grade={m.get('grade')} "
          f"reason={m.get('slag_reason', '?')}")
```
