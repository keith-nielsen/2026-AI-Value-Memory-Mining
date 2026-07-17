---
type: meta-script
deploy_target: ~/bin/vault-daily-note.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-17
---
## Rationale
Capture must always have a guaranteed home, so today's daily note is created from the
Mold **unconditionally** (capture is never gated) — on demand, when the operator sits
down to capture. Idempotent: does nothing if the note already exists. **Run on demand,
never on a tick** (ADR-0028): the vault is a *self-priming pump, not a driven one* —
nothing outside it ticks it, and the previously declared `cron` / `schedule:` was a
decoration no mechanism ever honoured (`render` deploys code; it does not install
schedules). A stub minted by a timer on a day nobody wrote is an obligation, not a
capture surface — it would still demand a strict-order close. If the previous day is
not yet `closed`, the note is still created but carries a `⚠ BLOCKED` banner — capture
is fine; closing **in order** is what's enforced (see `daily-close`). Root resolution
and the
`closed` test come from the shared `vault_lib` (ADR-0023): the bare drive invocation
works without a pre-sourced environment, and `closed` is YAML-typed (`closed: false`
counts as open; the previous regex treated any non-empty value as closed). **Owns its
commit** (B3, commit-ownership): a created note is committed immediately
(`daily: opened <date>`, scoped) — the close-day sweep no longer collects it; the
`exists` path stays commit-free (INV-2 no-op).

## Implementation
```python
#!/usr/bin/env python3
import datetime, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_lib import commit_paths, find_vault_root, is_closed  # vault-lib-script.md
vault = find_vault_root()
today = datetime.date.today().isoformat()
ddir = vault / "10-Logbook" / "Daily"
note = ddir / f"{today}.md"
note.parent.mkdir(parents=True, exist_ok=True)

prev = sorted(p for p in ddir.glob("*.md") if len(p.stem) == 10 and p.stem < today)
blocked = bool(prev) and not is_closed(prev[-1])

if note.exists():
    print(f"exists {note}")
else:
    text = (vault / "97-Molds" / "daily-mold-blank.md").read_text().replace("{{date}}", today)
    if blocked:
        banner = (f"> ⚠ BLOCKED: close {prev[-1].stem} before advancing "
                  f"(capture is fine; carry-over is gated).\n\n")
        text = re.sub(r'(^# .*\n)', lambda m: m.group(1) + "\n" + banner, text, count=1)
    note.write_text(text)
    commit_paths(vault, [note], f"daily: opened {today}")
    print(f"created {note}" + (" [BLOCKED banner]" if blocked else ""))
```
