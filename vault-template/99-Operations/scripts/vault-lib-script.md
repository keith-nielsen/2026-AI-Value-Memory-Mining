---
type: meta-script
deploy_target: ~/bin/vault_lib.py
runtime: manual
class: script
created: 2026-07-05
updated: 2026-07-05
---
## Rationale
Shared plumbing for the ops fleet (ADR-0023) — one home for the five things every script
previously improvised: vault-root resolution, config vocabulary, frontmatter reading, scoped
commits, and exit-code semantics. `find_vault_root()` accepts `$VAULT_ROOT` when it points at a
vault and otherwise walks up from the working directory to a `99-Operations/` config marker, so a
**bare rendered-script invocation works without a pre-sourced environment** — the drive-path
contract (exact excluded invocations, no env prefix) requires exactly this. `vocab()` resolves a
controlled vocabulary with the same precedence the shell sourcing order establishes: process
environment > `config.env` (instance) > `config.defaults.env` (framework) > declared code default —
one SSOT chain instead of three homes. `commit_paths()` is the INV-2 shape —
scoped `git add` plus a **pathspec-scoped commit** of exactly the named paths, never a sweep:
unrelated staged content is left staged, not committed (the F3/F4/F5 accident class, closed
structurally), and an unchanged result is a **clean no-op** — message, no commit, exit 0 — per the
INV-2 no-op clause (the kanban same-day re-render lesson, 2026-07-05). The fleet exit-code
contract (`0` ok · `1` violation · `2` needs-input · `3` gate-blocked) exists because drivers and
models key on codes, not prose. Consumers import it the way the linter already imports
`vault_naming`: `sys.path.insert(0, str(pathlib.Path.home() / "bin"))`. The `frontmatter` import is
lazy so the root/config helpers stay usable outside the venv (git hooks). Bootstrap exception:
`render-reconcile-script` deploys this module and therefore must not import it — it carries its own
inline copy of the resolution contract. Deterministic (INV-6): reads local files and env only;
config values are raw strings — no shell evaluation. Run bare for a read-only self-check.

## Implementation
```python
#!/usr/bin/env python3
"""vault_lib — shared plumbing for the vault ops fleet (ADR-0023).

Contract (importable module + read-only CLI):
  find_vault_root() -> Path   $VAULT_ROOT if it marks a vault, else walk up from cwd to
                              the first directory whose 99-Operations/ holds
                              config.defaults.env or config.env; SystemExit(3) if neither.
  load_config(vault) -> dict  raw KEY=VALUE pairs: config.defaults.env overlaid by
                              config.env (instance wins). No shell evaluation.
  vocab(key, default, vault) -> list[str]
                              precedence: process env > config.env > config.defaults.env
                              > default; SystemExit(3) if required (default=None) and absent.
  fm(path) -> dict            YAML frontmatter metadata — the fleet's single parser.
  commit_paths(vault, paths, message)
                              scoped `git add` + pathspec-scoped commit of exactly the named
                              paths (INV-2); never sweeps — unrelated staged content stays
                              staged, uncommitted; clean no-op (message, no commit) when the
                              named paths are unchanged; consumed paths (deleted + never
                              tracked) are tolerated, tracked deletions are staged.
  say(tag, msg)               uniform "TAG: msg" output line.
Fleet exit-code contract (drivers key on codes, not prose):
  0 EXIT_OK · 1 EXIT_VIOLATION · 2 EXIT_NEEDS_INPUT · 3 EXIT_BLOCKED
  4 EXIT_OPERATOR_ONLY — a write refused (EROFS) on a path the Area Access Matrix
    withholds from the agent. Distinct from 1 so a driver can tell "denied by design,
    re-run as the operator" from a genuine fault. Raised directly by render/naming,
    not through this module: both amend code paths that cannot import it (ADR-0023's
    bootstrap exception; naming's lazy import).
CLI: no args -> read-only self-check (resolved root + vocabulary summary), exits 0/3.
"""
import os, re, sys, pathlib, subprocess

EXIT_OK, EXIT_VIOLATION, EXIT_NEEDS_INPUT, EXIT_BLOCKED = 0, 1, 2, 3
EXIT_OPERATOR_ONLY = 4
_OPS = "99-Operations"
_CONFIGS = ("config.defaults.env", "config.env")   # read in this order; later wins
_KV = re.compile(r"^(?:export\s+)?([A-Z][A-Z0-9_]*)=(.*)$")


def say(tag, msg):
    print(f"{tag}: {msg}")


def _is_vault(path):
    return any((path / _OPS / c).is_file() for c in _CONFIGS)


def find_vault_root():
    env = os.environ.get("VAULT_ROOT")
    if env:
        root = pathlib.Path(env)
        if _is_vault(root):
            return root
        say("BLOCKED", f"VAULT_ROOT={env} has no {_OPS} config marker")
        raise SystemExit(EXIT_BLOCKED)
    cwd = pathlib.Path.cwd()
    for cand in (cwd, *cwd.parents):
        if _is_vault(cand):
            return cand
    say("BLOCKED", f"no VAULT_ROOT set and no vault marker at or above {cwd} — "
                   "cd into the vault or export VAULT_ROOT")
    raise SystemExit(EXIT_BLOCKED)


def load_config(vault=None):
    vault = vault or find_vault_root()
    cfg = {}
    for name in _CONFIGS:
        f = vault / _OPS / name
        if not f.is_file():
            continue
        for line in f.read_text().splitlines():
            m = _KV.match(line.strip())
            if not m:
                continue
            k, v = m.group(1), m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            cfg[k] = v
    return cfg


def vocab(key, default=None, vault=None):
    val = os.environ.get(key)
    if val is None:
        val = load_config(vault).get(key)
    if val is not None:
        return val.split()
    if default is not None:
        return list(default)
    say("BLOCKED", f"required config key {key} not in environment or config files")
    raise SystemExit(EXIT_BLOCKED)


def fm(path):
    import frontmatter  # lazy: root/config helpers must work outside the venv (git hooks)
    return frontmatter.load(path).metadata


def commit_paths(vault, paths, message):
    rels = []
    for p in paths:
        p = pathlib.Path(p)
        rels.append(str(p.resolve().relative_to(vault.resolve())) if p.is_absolute() else str(p))
    if not rels:
        say("WARN", "commit_paths: no paths — nothing committed")
        return
    # tolerate consumed paths (deleted, never tracked — e.g. an untracked worklist a
    # script just unlinked): a bare `git add` refuses such pathspecs outright
    known = subprocess.run(["git", "-C", str(vault), "ls-files", "--", *rels],
                           capture_output=True, text=True).stdout.splitlines()
    rels = [r for r in rels if (vault / r).exists() or r in known]
    if not rels:
        say("ok", "nothing known to git among the named paths — no commit needed")
        return
    subprocess.run(["git", "-C", str(vault), "add", "--", *rels], check=True)
    if subprocess.run(["git", "-C", str(vault), "diff", "--cached", "--quiet",
                       "--", *rels]).returncode == 0:
        say("ok", f"unchanged — no commit needed ({', '.join(rels)})")
        return
    # pathspec-scoped: commits exactly rels even if unrelated content is staged
    subprocess.run(["git", "-C", str(vault), "commit", "-m", message, "--", *rels], check=True)


if __name__ == "__main__":
    root = find_vault_root()
    say("ok", f"vault root: {root}")
    for key in ("PILLARS", "GRADES", "EFFORT_STATUSES", "KNOWLEDGE_STAGES",
                "REFINE_GATE_GRADES", "SPOIL_STATUSES"):
        vals = vocab(key, default=[], vault=root)
        say("ok" if vals else "WARN", f"{key} = {' '.join(vals) or '(unset)'}")
    raise SystemExit(EXIT_OK)
```
