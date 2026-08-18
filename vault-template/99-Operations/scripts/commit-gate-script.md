---
type: meta-script
deploy_target: 99-Operations/hooks/pre-commit
runtime: git hook
class: script
created: 2026-06-14
updated: 2026-07-06
---
## Rationale
Unbypassable commit-gate for **INV-11 (names) and INV-7 (staged content)**. Fires on every commit — by human, script, agent,
or external sync tool — and blocks on any added or renamed `.md` file whose name
violates the naming ruleset: cross-platform safety, kebab-case, and the ≥3-token floor
(`--check-strict`, ADR-0030 switching on the rule ADR-0015 deferred). Exemption-aware —
`README.md`, `CLAUDE.md`, dailies, `*.example` and friends pass untouched. Scoped to
`--diff-filter=AR`, so **existing names stay grandfathered**: the gate structurally
cannot block a commit over a name that was already there. Lives in a tracked folder so it ships with the repo;
activated once per clone via `git config core.hooksPath 99-Operations/hooks`.
`render` must mark it executable (`chmod +x`) after deployment. The hook is
**environment-free by design**: it reads only the staged git state and calls the
naming SSOT at `99-Operations/bin/vault_naming.py`, resolved from the hook's own location, so it works on commits made by the
bare-exact drive path, which by contract carries no pre-sourced environment
(a vestigial `VAULT_ROOT` guard — set but never used — previously broke exactly
that path; removed 2026-07-05, Phase-1a burn-in finding).

**INV-7 half (added 2026-07-28).** The same hook then calls `99-Operations/bin/vault_secrets.py --staged`,
which scans staged **content** — not names — for anchored credential formats. Three deliberate
asymmetries with the naming half: it covers **every** file type (a secret in a `.json` or `.env`
counts), it covers **modified** files too (`--diff-filter=ACM`, not `AR`), and it is **never
grandfathered**. A pre-existing bad name is a cosmetic debt; a pre-existing live credential is an
active compromise. Only the `HIGH` tier gates — see `secret-scan-script` for why the advisory tier
is excluded from the gate (RC-E: over-denial is camouflage). The scanner runs its own selftest
before every scan and refuses to report clean if its patterns cannot be shown to fire.

## Implementation
```bash
#!/usr/bin/env bash
set -euo pipefail
# The fleet is a sibling silo of this hook (99-Operations/hooks -> 99-Operations/bin).
# Resolved from the hook's OWN location, never $HOME: a hook must work for any user
# and in any invocation, including git's (which sets cwd to the repo top level).
BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")/../bin" && pwd)"
fail=0
# only newly added or renamed files; existing names are grandfathered
while IFS= read -r f; do
    [[ "$f" == *.md ]] || continue
    base="$(basename "$f")"
    # --check-strict takes the BASENAME: the exemption gate matches full filenames
    # (README.md, dailies, *.example). Exempt names pass without a kebab/floor check.
    if ! python3 "$BIN/vault_naming.py" --check-strict "$base"; then
        echo "BLOCKED: '$f' violates naming rules (INV-11)" >&2
        fail=1
    fi
done < <(git diff --cached --name-only --diff-filter=AR)

# INV-7 (Tier-0): scan staged CONTENT for credential formats. Deliberately wider than the
# naming check above — every added/copied/modified path, any file type, and NOT grandfathered:
# a name that predates the rule is tolerable, a live credential never is.
if ! python3 "$BIN/vault_secrets.py" --staged; then
    fail=1
fi

exit "$fail"
```
