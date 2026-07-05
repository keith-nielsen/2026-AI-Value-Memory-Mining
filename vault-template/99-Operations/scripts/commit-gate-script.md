---
type: meta-script
deploy_target: 99-Operations/hooks/pre-commit
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-05
---
## Rationale
Unbypassable commit-gate for INV-11. Fires on every commit — by human, script, agent,
or external sync tool — and blocks on any added or renamed `.md` file whose stem
violates the naming ruleset. Lives in a tracked folder so it ships with the repo;
activated once per clone via `git config core.hooksPath 99-Operations/hooks`.
`render` must mark it executable (`chmod +x`) after deployment. The hook is
**environment-free by design**: it reads only the staged git state and calls the
naming SSOT at `${HOME}/bin/vault_naming.py`, so it works on commits made by the
bare-exact drive path, which by contract carries no pre-sourced environment
(a vestigial `VAULT_ROOT` guard — set but never used — previously broke exactly
that path; removed 2026-07-05, Phase-1a burn-in finding).

## Implementation
```bash
#!/usr/bin/env bash
set -euo pipefail
fail=0
# only newly added or renamed files; existing names are grandfathered
while IFS= read -r f; do
    [[ "$f" == *.md ]] || continue
    base="$(basename "$f")"; stem="${base%.md}"
    if ! python3 "${HOME}/bin/vault_naming.py" --check "$stem"; then
        echo "BLOCKED: '$f' violates naming rules (INV-11)" >&2
        fail=1
    fi
done < <(git diff --cached --name-only --diff-filter=AR)
exit "$fail"
```
