---
type: meta-script
deploy_target: ~/bin/vault-refine-detect.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-17
---
## Rationale
Scans Sites for ore that has cleared the Sort grade gate (default: silver, gold) and
writes the queue to `20-Claims/_refine-queue.json` (gitignored). This is a read-only
detection step — no proposals are generated and no writes happen outside the queue
file. The human reviews the queue and decides which efforts to route through the
Refine pipeline. The `[agent]` harness (Phase 3) reads from this queue to pick its
next Site. **Run at the point of need, not on a tick** (ADR-0028): the queue is
consumed at the moment someone refines — the Sort step of `site-sort` invokes it as
its gate proof — so a timed run would write a gitignored file nobody has asked for.
The previously declared `cron` / `schedule:` was a decoration no mechanism honoured.
Root and the `REFINE_GATE_GRADES` gate resolve via the shared `vault_lib`
(ADR-0023, wave-2 adoption): the bare invocation works without a pre-sourced
environment.

## Implementation
```python
#!/usr/bin/env python3
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_lib import find_vault_root, fm, vocab  # vault-lib-script.md
vault = find_vault_root()
gate = set(vocab("REFINE_GATE_GRADES"))
queue = []
for idx in (p for p in (vault / "30-Sites").glob("*/*.md") if p.stem == p.parent.name):
    m = fm(idx)
    if m.get("status") == "ore" and m.get("grade") in gate:
        queue.append(str(idx.parent.relative_to(vault)))
(vault / "20-Claims" / "_refine-queue.json").write_text(json.dumps(queue, indent=2))
print(f"queued {len(queue)} for refining")
```
