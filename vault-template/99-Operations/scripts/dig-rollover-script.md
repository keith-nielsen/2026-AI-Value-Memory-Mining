---
type: meta-script
deploy_target: ~/bin/vault-rollover.py
runtime: cron
schedule: "2 0 * * *"
class: script
created: 2026-06-14
updated: 2026-06-14
---
## Rationale
Runs one minute after the daily-note creator (daily-note.md). Scans `30-Sites/` for
efforts with `status: dig` and appends wikilinks under a `## Carry-over` heading in
today's daily note — so active digs are always visible at day-open without manual
linking. **Gated:** advancing (carry-over) requires the previous day to be `closed`
(strict-order close); if it is not, this exits without carrying over (the capture stub
still exists — close the prior day first). Idempotent: skips any link already present.
Produces exactly one commit if any links were added; silent exit if nothing changed
(no empty commits, INV-2).

## Implementation
```python
#!/usr/bin/env python3
import os, datetime, pathlib, subprocess, frontmatter
vault = pathlib.Path(os.environ["VAULT_ROOT"])
today = datetime.date.today().isoformat()
note = vault / "10-Logbook" / "Daily" / f"{today}.md"
if not note.exists():
    print(f"WARN: daily note missing, run vault-daily-note.py first"); exit(1)

# GATE: advancing (carry-over) requires the previous day to be closed (strict-order)
daily_dir = vault / "10-Logbook" / "Daily"
prev = sorted(p for p in daily_dir.glob("*.md")
              if len(p.stem) == 10 and p.stem < today)
if prev and not frontmatter.load(prev[-1]).metadata.get("closed"):
    print(f"BLOCKED: previous day {prev[-1].stem} not closed — run close-daily first"); exit(0)

# collect open dig efforts
open_digs = []
for idx in sorted(p for p in (vault / "30-Sites").glob("*/*.md") if p.stem == p.parent.name):
    m = frontmatter.load(idx).metadata
    if m.get("status") == "dig":
        open_digs.append(idx.parent.name)

if not open_digs:
    print("no open digs"); exit(0)

text = note.read_text()
heading = "## Carry-over"

# build lines to inject (skip any already present)
existing = text if heading in text else ""
to_add = [f"- [[30-Sites/{slug}/{slug}|{slug}]]" for slug in open_digs
          if f"30-Sites/{slug}/{slug}" not in existing]

if not to_add:
    print("carry-over already current"); exit(0)

if heading in text:
    text = text.replace(heading, heading + "\n" + "\n".join(to_add))
else:
    text = text + f"\n\n{heading}\n" + "\n".join(to_add) + "\n"

note.write_text(text)
subprocess.run(
    ["git", "-C", str(vault), "add", str(note.relative_to(vault))], check=True)
subprocess.run(
    ["git", "-C", str(vault), "commit", "-m",
     f"rollover: {len(to_add)} open dig(s) → {today}"], check=True)
print(f"rolled over {len(to_add)} effort(s) into {today}")
```
