---
type: meta-script
deploy_target: ~/bin/vault-rollover.py
runtime: cron
schedule: "2 0 * * *"
class: script
created: 2026-06-14
updated: 2026-07-05
---
## Rationale
Runs one minute after the daily-note creator (daily-note.md). Scans `30-Sites/` for
efforts with `status: dig` and appends wikilinks under a `## Carry-over` heading in
today's daily note — so active digs are always visible at day-open without manual
linking. **Gated:** advancing (carry-over) requires the previous day to be `closed`
(strict-order close); a refusal — missing daily note or unclosed prior day — exits
`3` (`EXIT_BLOCKED`, the vault_lib fleet contract, ADR-0023) so a driver can tell
"gate held" from a successful no-op (`0`); previously a refusal exited `0` and was
indistinguishable from success. Idempotent: skips any link already present. Produces
exactly one commit if any links were added (scoped `commit_paths`, INV-2); silent
zero-commit exit if nothing changed. Root, `closed` semantics, and the commit come
from the shared `vault_lib`.

## Implementation
```python
#!/usr/bin/env python3
import datetime, pathlib, sys
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_lib import EXIT_BLOCKED, commit_paths, find_vault_root, fm, is_closed, say
vault = find_vault_root()
today = datetime.date.today().isoformat()
note = vault / "10-Logbook" / "Daily" / f"{today}.md"
if not note.exists():
    say("BLOCKED", "daily note missing, run vault-daily-note.py first")
    raise SystemExit(EXIT_BLOCKED)

# GATE: advancing (carry-over) requires the previous day to be closed (strict-order).
# A refusal exits EXIT_BLOCKED(3) so a driver can tell "gate held" from "no-op" (0).
daily_dir = vault / "10-Logbook" / "Daily"
prev = sorted(p for p in daily_dir.glob("*.md")
              if len(p.stem) == 10 and p.stem < today)
if prev and not is_closed(prev[-1]):
    say("BLOCKED", f"previous day {prev[-1].stem} not closed — run daily-close first")
    raise SystemExit(EXIT_BLOCKED)

# collect open dig efforts
open_digs = []
for idx in sorted(p for p in (vault / "30-Sites").glob("*/*.md") if p.stem == p.parent.name):
    if fm(idx).get("status") == "dig":
        open_digs.append(idx.parent.name)

if not open_digs:
    print("no open digs"); raise SystemExit(0)

text = note.read_text()
heading = "## Carry-over"

# build lines to inject (skip any already present)
existing = text if heading in text else ""
to_add = [f"- [[30-Sites/{slug}/{slug}|{slug}]]" for slug in open_digs
          if f"30-Sites/{slug}/{slug}" not in existing]

if not to_add:
    print("carry-over already current"); raise SystemExit(0)

if heading in text:
    text = text.replace(heading, heading + "\n" + "\n".join(to_add))
else:
    text = text + f"\n\n{heading}\n" + "\n".join(to_add) + "\n"

note.write_text(text)
commit_paths(vault, [note], f"rollover: {len(to_add)} open dig(s) → {today}")
print(f"rolled over {len(to_add)} effort(s) into {today}")
```
