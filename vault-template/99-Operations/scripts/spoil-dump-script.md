---
type: meta-script
deploy_target: ~/bin/vault-dump.sh
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Moves a spent effort husk to `71-Spoil/` after its bullion has been banked in
Treasury. Call after `refine-execute` has written the knowledge note and the operator
has verified the Treasury entry. Produces exactly one atomic commit (INV-2). The
`40-Treasury/` entry is never touched — this only moves the residue. Usage:
`vault-dump.sh <slug>`

## Implementation
```bash
#!/usr/bin/env bash
set -euo pipefail
: "${VAULT_ROOT:?}"
slug="$1"
git -C "$VAULT_ROOT" mv "30-Sites/$slug" "71-Spoil/$slug"
git -C "$VAULT_ROOT" add -A
git -C "$VAULT_ROOT" commit -m "dump: $slug -> 71-Spoil (spent)"
```
