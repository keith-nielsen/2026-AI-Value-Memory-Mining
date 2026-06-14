---
type: meta-script
deploy_target: ~/bin/vault-render.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
GitOps-style deploy/drift-detection for Layer-0 scripts (INV-3). `render` extracts
each script's code block to its `deploy_target` and marks it executable; `reconcile`
compares deployed files to source and reports drift without overwriting — auto-fix is
explicitly prohibited. Human must re-run `render` to resolve drift. This script
bootstraps itself: run it directly from the source note on first install, then it
manages all subsequent scripts.

## Implementation
```python
#!/usr/bin/env python3
"""Render Layer-0 code blocks to host targets, or reconcile (detect drift)."""
import os, re, sys, pathlib, frontmatter
vault = pathlib.Path(os.environ["VAULT_ROOT"])
mode = sys.argv[1] if len(sys.argv) > 1 else "reconcile"   # render | reconcile
assert mode in ("render", "reconcile")
CODE = re.compile(r"^```(?:python|bash)\n(.*?)^```", re.S | re.M)
drift = 0
for note in sorted((vault / "99-Operations" / "scripts").glob("*.md")):
    post = frontmatter.load(note)
    target = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))
    m = CODE.search(post.content)
    if not m:
        print(f"WARN: no code block in {note.name}"); continue
    src = m.group(1)
    if mode == "render":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(src); target.chmod(0o755)
        print(f"rendered {note.name} -> {target}")
    else:
        deployed = target.read_text() if target.exists() else ""
        if deployed != src:
            print(f"DRIFT: {target} differs from {note.name}"); drift += 1
        else:
            print(f"ok: {target}")
sys.exit(1 if (mode == "reconcile" and drift) else 0)
```
