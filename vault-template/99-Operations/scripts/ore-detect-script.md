---
type: meta-script
deploy_target: ~/bin/vault-refine-detect.py
runtime: cron
schedule: "0 6 * * *"
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Scans Sites for ore that has cleared the Sort grade gate (default: silver, gold) and
writes the queue to `20-Claims/_refine-queue.json` (gitignored). This is a read-only
detection step — no proposals are generated and no writes happen outside the queue
file. The human reviews the queue and decides which efforts to route through the
Refine pipeline. The `[agent]` harness (Phase 3) reads from this queue to pick its
next Site.

## Implementation
```python
#!/usr/bin/env python3
import os, json, pathlib, frontmatter
vault = pathlib.Path(os.environ["VAULT_ROOT"])
gate = set(os.environ["REFINE_GATE_GRADES"].split())
queue = []
for idx in (p for p in (vault / "30-Sites").glob("*/*.md") if p.stem == p.parent.name):
    m = frontmatter.load(idx).metadata
    if m.get("status") == "ore" and m.get("grade") in gate:
        queue.append(str(idx.parent.relative_to(vault)))
(vault / "20-Claims" / "_refine-queue.json").write_text(json.dumps(queue, indent=2))
print(f"queued {len(queue)} for refining")
```
