---
type: meta-script
deploy_target: ~/bin/vault-render.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-06
---
## Rationale
GitOps-style deploy/drift-detection for Layer-0 scripts (INV-3). `render` extracts
each script's code block to its `deploy_target` and marks it executable; `reconcile`
compares deployed files to source and reports drift without overwriting — auto-fix is
explicitly prohibited. Human must re-run `render` to resolve drift. This script
bootstraps itself: run it directly from the source note on first install, then it
manages all subsequent scripts. Enforces the exactly-one-code-fence rule (B5): a note
with zero or multiple `python|bash` fences is a VIOLATION — nothing renders for it and
the run exits 1 — because the extractor would otherwise silently take the first fence. Because it deploys `vault_lib.py` it must not import
it — it carries an inline copy of the same root-resolution contract (`$VAULT_ROOT` if
it marks a vault, else walk up from cwd to a `99-Operations/` config marker; ADR-0023).

## Implementation
```python
#!/usr/bin/env python3
"""Render Layer-0 code blocks to host targets, or reconcile (detect drift)."""
import os, re, sys, pathlib, frontmatter


# Bootstrap exception (ADR-0023): render deploys vault_lib itself, so it must not
# import it. Inline copy of the vault_lib.find_vault_root() resolution contract.
def _vault_root():
    env = os.environ.get("VAULT_ROOT")
    cands = [pathlib.Path(env)] if env else [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]
    for c in cands:
        if any((c / "99-Operations" / f).is_file()
               for f in ("config.defaults.env", "config.env")):
            return c
    print("BLOCKED: no vault root — export VAULT_ROOT or run from inside the vault")
    raise SystemExit(3)


vault = _vault_root()
mode = sys.argv[1] if len(sys.argv) > 1 else "reconcile"   # render | reconcile
assert mode in ("render", "reconcile")
CODE = re.compile(r"^```(?:python|bash)\n(.*?)^```", re.S | re.M)
drift = 0
bad = 0
for note in sorted((vault / "99-Operations" / "scripts").glob("*.md")):
    post = frontmatter.load(note)
    target = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))
    blocks = CODE.findall(post.content)
    if len(blocks) != 1:
        # exactly-one-fence rule (spec: "a single fenced code block") — a second fence
        # would silently never render; fail loud instead of guessing which block is real
        print(f"VIOLATION: {note.name} has {len(blocks)} code fences (exactly 1 required)")
        bad += 1
        continue
    src = blocks[0]
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
sys.exit(1 if (bad or (mode == "reconcile" and drift)) else 0)
```
