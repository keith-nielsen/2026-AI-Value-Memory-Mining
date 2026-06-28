---
type: meta-script
deploy_target: ~/bin/vault-daily-note.py
runtime: cron
schedule: "1 0 * * *"
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Capture must always have a guaranteed home, so today's daily note is created from
the Mold at 00:01 — **unconditionally** (capture is never gated). Idempotent: does
nothing if the note already exists. Runs one minute before the roll-over script so the
note is present when carry-over links are appended. If the previous day is not yet
`closed`, the new note is still created but carries a `⚠ BLOCKED` banner — capture is
fine; *advancing* (carry-over) is what's gated (see rollover).

## Implementation
```python
#!/usr/bin/env python3
import os, datetime, pathlib, re
vault = pathlib.Path(os.environ["VAULT_ROOT"])
today = datetime.date.today().isoformat()
ddir = vault / "10-Logbook" / "Daily"
note = ddir / f"{today}.md"
note.parent.mkdir(parents=True, exist_ok=True)


def closed(p):
    m = re.match(r'^---\n(.*?)\n---\n', p.read_text(), re.S)
    return bool(m and re.search(r'(?m)^closed:\s*\S', m.group(1)))


prev = sorted(p for p in ddir.glob("*.md") if len(p.stem) == 10 and p.stem < today)
blocked = bool(prev) and not closed(prev[-1])

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
