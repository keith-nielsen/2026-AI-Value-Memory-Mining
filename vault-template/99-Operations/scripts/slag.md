---
type: meta-script
deploy_target: ~/bin/vault-slag.sh
runtime: manual
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Moves an uneconomic effort to `70-Tailings/` in one atomic commit (INV-2). The
operator must first set `status: slagged` and `slag_reason` in the effort's
frontmatter — the reason is required so `reprospect` can surface economics-shift
context later. Tailings are retained and re-minable; this is not a discard.
Usage: `vault-slag.sh <slug>`

## Implementation
```bash
#!/usr/bin/env bash
set -euo pipefail
: "${VAULT_ROOT:?}"
slug="$1"
git -C "$VAULT_ROOT" mv "30-Sites/$slug" "70-Tailings/$slug"
git -C "$VAULT_ROOT" add -A
git -C "$VAULT_ROOT" commit -m "slag: $slug -> 70-Tailings"
```
