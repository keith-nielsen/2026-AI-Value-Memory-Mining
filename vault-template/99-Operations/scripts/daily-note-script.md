---
type: meta-script
deploy_target: ~/bin/vault-daily-note.py
runtime: cron
schedule: "1 0 * * *"
class: script
created: 2026-06-14
updated: 2026-07-05
---
## Rationale
Capture must always have a guaranteed home, so today's daily note is created from
the Mold at 00:01 — **unconditionally** (capture is never gated). Idempotent: does
nothing if the note already exists. Runs one minute before the roll-over script so the
note is present when carry-over links are appended. If the previous day is not yet
`closed`, the new note is still created but carries a `⚠ BLOCKED` banner — capture is
fine; *advancing* (carry-over) is what's gated (see rollover). Root resolution and the
`closed` test come from the shared `vault_lib` (ADR-0023): the bare drive invocation
works without a pre-sourced environment, and `closed` is YAML-typed (`closed: false`
counts as open; the previous regex treated any non-empty value as closed).

## Implementation
```python
#!/usr/bin/env python3
import datetime, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_lib import find_vault_root, is_closed  # vault-lib-script.md
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
    print(f"created {note}" + (" [BLOCKED banner]" if blocked else ""))
```
