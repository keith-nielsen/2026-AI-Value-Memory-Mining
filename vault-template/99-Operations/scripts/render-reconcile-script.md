---
type: meta-script
deploy_target: 99-Operations/bin/vault-render.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-09-22
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

`reconcile` also DETECTS a deployed-but-unregistered git-hook set (item 35): the INV-11/INV-7 hooks
render into `99-Operations/hooks/`, but git ignores that directory until `core.hooksPath` points at
it — LOCAL config no tracked file or render run can set. It reports the gap (byte-perfect hooks that
enforce nothing) and prints the operator fix; it never sets `core.hooksPath` itself (detect, never
auto-fix). The framework repo deliberately does not run this gate locally — CI is its backstop.

## Implementation
```python
#!/usr/bin/env python3
"""Render Layer-0 code blocks to host targets, or reconcile (detect drift)."""
import errno, os, re, subprocess, sys, pathlib, frontmatter


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
    # Resolve the target against the SAME root the notes came from. A `deploy_target` is
    # written relative in every note, so a bare Path() resolved it against the process CWD
    # while the notes came from _vault_root() -- env-first. When those two disagreed the tool
    # compared one vault's notes against another vault's files and printed `ok`, and in
    # render mode it would have WRITTEN this vault's code into that tree. Measured
    # 2026-09-08 with VAULT_ROOT on the live vault and cwd in a clone.
    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))
    target = _dt if _dt.is_absolute() else (vault / _dt)
    blocks = CODE.findall(post.content)
    if len(blocks) != 1:
        # exactly-one-fence rule (spec: "a single fenced code block") — a second fence
        # would silently never render; fail loud instead of guessing which block is real
        print(f"VIOLATION: {note.name} has {len(blocks)} code fences (exactly 1 required)")
        bad += 1
        continue
    src = blocks[0]
    if mode == "render":
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(src); target.chmod(0o755)
        except OSError as exc:
            if exc.errno != errno.EROFS:
                raise
            # Denied by design, not broken. EVERY deploy_target lives in an area the
            # Area Access Matrix withholds from the agent (99-Operations/ and .claude/
            # are A:-), so a sandboxed agent can render NOTHING. Relocating the fleet
            # INTO 99-Operations/bin/ does not change that: containment and permission
            # are independent axes, and the agent must not be able to rewrite its own
            # guards. Without this branch the reader sees a bare traceback and debugs
            # a deploy fault that does not exist. Inline rather than in vault_lib:
            # ADR-0023's bootstrap exception forbids this script importing it.
            print(f"BLOCKED: cannot write {target}")
            print("  render is an OPERATOR-ONLY path - the agent is denied by design.")
            print("  This is not a broken deploy, a missing dep, or a bad sandbox config.")
            print("  Run `vault-render.py render` as the operator.")
            print("  `vault-render.py reconcile` is read-only and remains available.")
            raise SystemExit(4)
        print(f"rendered {note.name} -> {target}")
    else:
        deployed = target.read_text() if target.exists() else ""
        if deployed != src:
            print(f"DRIFT: {target} differs from {note.name}"); drift += 1
        else:
            print(f"ok: {target}")

# INV-11/INV-7 git hooks enforce NOTHING until core.hooksPath points at them. render deploys the hook
# FILES into 99-Operations/hooks/, but git ignores that directory until it is registered, and
# core.hooksPath is LOCAL git config that no tracked file or render run can set (item 35, D2). This
# DETECTS the deployed-but-unregistered state — byte-perfect hooks that enforce nothing, reporting
# clean — and never SETS it: registration is a documented operator deploy step (INV-3: reconcile
# detects drift, never auto-fixes). It runs in both modes so a fresh `render` warns the moment the
# hooks land unregistered; only `reconcile` counts it as drift (exit 1), matching render's contract.
_hooks_rel = "99-Operations/hooks"
_hooks_dir = vault / _hooks_rel
if _hooks_dir.is_dir() and any(p.is_file() and p.name != ".gitkeep" for p in _hooks_dir.iterdir()):
    try:
        _hp = subprocess.run(["git", "-C", str(vault), "config", "core.hooksPath"],
                             capture_output=True, text=True).stdout.strip()
    except OSError:
        _hp = ""
    if _hp == _hooks_rel or (_hp and pathlib.Path(_hp) == _hooks_dir):
        print(f"ok: git hooks registered (core.hooksPath = {_hp})")
    else:
        print(f"HOOKS-UNREGISTERED: git hooks are deployed to {_hooks_rel} but core.hooksPath is "
              f"'{_hp or 'unset'}' — git ignores them, so the INV-11/INV-7 commit gate enforces "
              f"nothing. Fix (operator): git -C {vault} config core.hooksPath {_hooks_rel}")
        drift += 1

sys.exit(1 if (bad or (mode == "reconcile" and drift)) else 0)
```
