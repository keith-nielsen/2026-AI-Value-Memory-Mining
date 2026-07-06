---
type: meta-script
deploy_target: ~/bin/vault-dump.sh
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-06
---
## Rationale
Moves a spent effort husk to `71-Spoil/` after its bullion has been banked in
Treasury. Call after `refine-execute` has written the knowledge note and the operator
has verified the Treasury entry. Produces exactly one atomic commit (INV-2). The
`40-Treasury/` entry is never touched — this only moves the residue. Usage:
`vault-dump.sh <slug>`. Conforms to the fleet contract (shell-pair change): root
self-resolution (inline bash copy of the `vault_lib` contract — bash cannot import
it), INV-11 slug validation via `vault_naming.py --check`, source/destination gates
(`BLOCKED` exit 3), and a **pathspec-scoped commit of exactly the moved effort** —
the former `add -A` sweep is gone; unrelated staged content stays staged.

## Implementation
```bash
#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 1 ]] || { echo "usage: vault-dump.sh <site-slug>" >&2; exit 1; }
slug="$1"
# root: inline copy of the vault_lib resolution contract (ADR-0023)
root="${VAULT_ROOT:-$PWD}"
if [[ -n "${VAULT_ROOT:-}" ]]; then
  if [[ ! -f "$root/99-Operations/config.defaults.env" && ! -f "$root/99-Operations/config.env" ]]; then
    echo "BLOCKED: VAULT_ROOT=$root has no 99-Operations config marker" >&2; exit 3
  fi
else
  while [[ "$root" != "/" ]]; do
    if [[ -f "$root/99-Operations/config.defaults.env" || -f "$root/99-Operations/config.env" ]]; then
      break
    fi
    root="$(dirname "$root")"
  done
  if [[ "$root" == "/" ]]; then
    echo "BLOCKED: no vault marker at or above $PWD — cd into the vault or export VAULT_ROOT" >&2
    exit 3
  fi
fi
python3 "${HOME}/bin/vault_naming.py" --check "$slug" || exit 1   # INV-11 boundary
src="30-Sites/$slug"; dest="71-Spoil/$slug"
[[ -d "$root/$src" ]] || { echo "BLOCKED: no such site: $src" >&2; exit 3; }
[[ ! -e "$root/$dest" ]] || { echo "BLOCKED: destination exists: $dest" >&2; exit 3; }
git -C "$root" mv "$src" "$dest"
# scoped: git mv staged the rename; commit exactly the moved effort (never add -A)
git -C "$root" commit -m "dump: $slug -> 71-Spoil (spent)" -- "$src" "$dest"
```
