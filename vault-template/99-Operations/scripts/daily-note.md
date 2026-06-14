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
the Mold at 00:01. Idempotent: does nothing if the note already exists. Runs one
minute before the roll-over script (§12.9) so the note is always present when
carry-over links are appended.

## Implementation
```python
#!/usr/bin/env python3
import os, datetime, pathlib
vault = pathlib.Path(os.environ["VAULT_ROOT"])
today = datetime.date.today().isoformat()
note = vault / "20-Logbook" / "Daily" / f"{today}.md"
note.parent.mkdir(parents=True, exist_ok=True)
if note.exists():
    print(f"exists {note}")
else:
    tmpl = (vault / "97-Molds" / "daily.md").read_text()
    note.write_text(tmpl.replace("{{date}}", today))
    print(f"created {note}")
```
