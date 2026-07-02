#!/usr/bin/env bash
# Validate the literate meta-scripts: render them, static-check (py_compile /
# bash -n / shellcheck), smoke-test the pipeline on a fresh vault, and prove the
# refine executor's INV-11 boundary. Sandboxed: HOME + VAULT_ROOT live in a temp dir.
#
# Usage: .github/scripts/validate-scripts.sh
# Requires: python3 with `python-frontmatter`; shellcheck optional (skipped if absent).
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="$(mktemp -d)"
export HOME="$WORK/home"
mkdir -p "$HOME/bin"
VAULT="$WORK/vault"
cp -r "$REPO/vault-template" "$VAULT"
trap 'rm -rf "$WORK"' EXIT

# Instantiate the private config from the example (as a user would: cp config.env.example config.env),
# then point it at the sandbox vault and source it. config.env sources config.defaults.env first
# (framework vocab + guard defaults), then applies this override.
cp "$VAULT/99-Operations/config.env.example" "$VAULT/99-Operations/config.env"
sed -i.bak "s|^export VAULT_ROOT=.*|export VAULT_ROOT=\"$VAULT\"|" "$VAULT/99-Operations/config.env"
rm -f "$VAULT/99-Operations/config.env.bak"
set -a; source "$VAULT/99-Operations/config.env"; set +a
export VAULT_ROOT="$VAULT"

FAIL=0
ok(){ echo "  ok    $1"; }
no(){ echo "  FAIL  $1"; FAIL=1; }
hdr(){ echo; echo "== $1 =="; }

cd "$VAULT"

hdr "render all scripts to the sandbox host"
# Bootstrap render from its source note, then deploy everything
python3 - <<'PY' || exit 2
import re, os, pathlib, frontmatter
note = pathlib.Path("99-Operations/scripts/render-reconcile-script.md")
code = re.search(r"^```python\n(.*?)^```", frontmatter.load(note).content, re.S | re.M).group(1)
out = pathlib.Path(os.path.expanduser("~/bin/vault-render.py"))
out.parent.mkdir(parents=True, exist_ok=True); out.write_text(code); out.chmod(0o755)
PY
python3 "$HOME/bin/vault-render.py" render >/dev/null || { no "render failed"; exit 2; }
python3 "$HOME/bin/vault_naming.py" >/dev/null
ok "render + naming-rules.json"

hdr "static checks — python compiles"
for py in "$HOME"/bin/*.py; do
  if python3 -m py_compile "$py" 2>/tmp/pc.txt; then ok "py_compile $(basename "$py")"; else no "py_compile $(basename "$py")"; cat /tmp/pc.txt; fi
done

hdr "static checks — bash syntax + shellcheck"
SH_FILES=("$HOME"/bin/*.sh "$VAULT/99-Operations/hooks/pre-commit")
for sh in "${SH_FILES[@]}"; do
  base="$(basename "$sh")"
  bash -n "$sh" 2>/tmp/bn.txt && ok "bash -n $base" || { no "bash -n $base"; cat /tmp/bn.txt; }
  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck -S warning "$sh" >/tmp/sc.txt 2>&1 && ok "shellcheck $base" || { no "shellcheck $base"; cat /tmp/sc.txt; }
  fi
done
command -v shellcheck >/dev/null 2>&1 || echo "  (shellcheck not installed — skipped)"

hdr "fresh-vault smoke"
git init -q -b main; git config user.name ci; git config user.email ci@ci; git config core.hooksPath 99-Operations/hooks
git add -A; git commit -qm init --no-verify
# reconcile zero drift
python3 "$HOME/bin/vault-render.py" reconcile >/dev/null && ok "reconcile zero drift" || no "reconcile drift"
# daily-note idempotent
python3 "$HOME/bin/vault-daily-note.py" | grep -q created && \
python3 "$HOME/bin/vault-daily-note.py" | grep -q exists && ok "daily-note idempotent" || no "daily-note"
# linter passes on empty treasury
lint_out=$(python3 "$HOME/bin/vault-lint.py" 2>&1); lint_rc=$?
[ $lint_rc -eq 0 ] && ok "lint clean (empty treasury)" || { no "lint (rc=$lint_rc)"; echo "$lint_out" | sed 's/^/        /'; }
# refine-detect on empty sites
python3 "$HOME/bin/vault-refine-detect.py" | grep -q "queued 0" && ok "refine-detect empty" || no "refine-detect"
# kanban renders
python3 "$HOME/bin/vault-kanban-render.py" >/dev/null && [ -f "$VAULT/10-Logbook/kanban.md" ] && ok "kanban render" || no "kanban"

hdr "close-daily lifecycle"
mk_day(){ cat > "$VAULT/10-Logbook/Daily/$1.md" <<EOF
---
type: daily
date: $1
closed:
---
# $1

## Log
Work happened.

## Captured
- Idea: something worth a claim later.
EOF
}
mk_day 2020-01-01; mk_day 2020-01-02
git add -A; git commit -qm "smoke days" --no-verify
# strict-order gate: cannot close 01-02 while 01-01 is open
# (capture-then-grep: the script exits non-zero by design, which pipefail would propagate)
gate_out=$(python3 "$HOME/bin/vault-close-day.py" 2020-01-02 2>&1 || true)
echo "$gate_out" | grep -q BLOCKED && ok "close strict-order gate" || no "close gate"
# close in order; deterministic items seal with no unknown/other
python3 "$HOME/bin/vault-close-day.py" 2020-01-01 >/dev/null 2>&1
python3 "$HOME/bin/vault-close-day.py" 2020-01-02 >/dev/null 2>&1
D1="$VAULT/10-Logbook/Daily/2020-01-01.md"
if grep -qE '^closed: 2[0-9]{3}-' "$D1" && grep -q '## Close' "$D1"; then ok "close-daily seals + manifest"; else no "close-daily seal"; fi
python3 "$HOME/bin/vault-close-day.py" --check 2020-01-01 2>&1 | grep -q "close-lint OK" && ok "close-lint --check" || no "close-lint"

hdr "INV-11 executor boundary (A3.3 executor side)"
# A non-conforming target_note must be rejected with no Treasury write.
cat > "$VAULT/20-Claims/_refine-approved/bad.json" <<'JSON'
{ "target_note": "40-Treasury/Bad:Name.md", "mode": "create",
  "insight_md": "x", "provenance_md": "y", "index_links": [],
  "frontmatter": {"pillars": ["technology"], "grade": "gold", "crucible": false} }
JSON
out=$(python3 "$HOME/bin/vault-refine-execute.py" 2>&1)
if echo "$out" | grep -q REJECT && [ ! -e "$VAULT/40-Treasury/Bad:Name.md" ]; then
  ok "executor rejects non-kebab target_note, no Treasury write"
else
  no "executor boundary (out: $out)"
fi
rm -f "$VAULT/20-Claims/_refine-approved/bad.json"
# A conforming one must be applied.
cat > "$VAULT/20-Claims/_refine-approved/good.json" <<'JSON'
{ "target_note": "40-Treasury/good-insight.md", "mode": "create",
  "insight_md": "Durable value.", "provenance_md": "Tried X.",
  "index_links": ["40-Treasury/Catalog/technology-domain-index.md"],
  "frontmatter": {"pillars": ["technology"], "grade": "gold", "crucible": false} }
JSON
python3 "$HOME/bin/vault-refine-execute.py" >/dev/null 2>&1
[ -f "$VAULT/40-Treasury/good-insight.md" ] && ok "executor applies conforming proposal" || no "executor good-path"

echo
[ $FAIL -eq 0 ] && echo "VALIDATION OK" || echo "VALIDATION FAILED"
exit $FAIL
