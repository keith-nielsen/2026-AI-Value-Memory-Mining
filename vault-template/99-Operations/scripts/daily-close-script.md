---
type: meta-script
deploy_target: ~/bin/vault-close-day.py
runtime: manual
class: script
created: 2026-06-17
updated: 2026-06-17
---
## Rationale
The deterministic engine for the `close-daily` runbook. It assigns every item of a daily
note exactly one disposition from the controlled `DISPOSITIONS` vocabulary, writes an
append-only `## Close` manifest, and sets `closed:`. It is `[script]` (INV-6): it classifies
by rule and **emits an `unknown/other` worklist** for an agent/human to resolve — it never
calls a model. Invariants enforced: append-only (it only appends below `## Close`),
total-disposition (refuses to seal while any item is unresolved), and strict-order close
(refuses while an earlier day is open). `--check` is the `close-lint` mode. One commit (INV-2).

## Implementation
```python
#!/usr/bin/env python3
import os, sys, re, json, datetime, pathlib, subprocess
from collections import Counter, defaultdict

VAULT = pathlib.Path(os.environ["VAULT_ROOT"])
DAILY = VAULT / "10-Logbook" / "Daily"
DISPOSITIONS = os.environ.get(
    "DISPOSITIONS",
    "claim site crucible banked slagged spoiled realized recorded passover").split()
CLOSE = "## Close"
LIST_SECTIONS = {"Intentions", "Captured"}
LINK_RULES = [
    (r'30-Sites/', 'site'),
    (r'20-Claims/', 'claim'),
    (r'40-Treasury/', 'banked'),
    (r'70-Tailings/', 'slagged'),
    (r'71-Spoil/', 'spoiled'),
    (r'80-Crucible', 'crucible'),
]
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')


def split_fm(text):
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        return {}, "", text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, m.group(1), text[m.end():]


def is_closed(path):
    fm, _, _ = split_fm(path.read_text())
    return bool(fm.get("closed"))


def items_of(body):
    head = body.split("\n" + CLOSE)[0]
    section, sections = None, {}
    for line in head.splitlines():
        m = re.match(r'^##\s+(.+)', line)
        if m:
            section = m.group(1).strip()
            sections.setdefault(section, [])
        elif section is not None:
            sections[section].append(line)
    items = []
    for sec, lines in sections.items():
        if not "\n".join(lines).strip():
            continue
        if sec in LIST_SECTIONS:
            for ln in lines:
                s = ln.strip()
                if not s:
                    continue
                items.append((sec, "item", re.sub(r'^[-*]\s+', '', s)))
        else:
            items.append((sec, "block", sec))
    return items


def classify(sec, kind, text, resolutions, idx):
    if str(idx) in resolutions and resolutions[str(idx)]:
        return resolutions[str(idx)], "resolved"
    if kind == "block":
        return "recorded", "section-default"
    for pat, disp in LINK_RULES:
        if re.search(pat, text):
            return disp, "link"
    if re.match(r'(?i)idea\s*:', text):
        return "claim", "idea-rule"
    if text.rstrip().endswith("?"):
        return None, "question"
    return None, "other"


def set_closed(text, day):
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    fm, after = m.group(1), text[m.end():]
    if re.search(r'(?m)^closed:', fm):
        fm = re.sub(r'(?m)^closed:.*$', f'closed: {day}', fm)
    else:
        fm = fm + f"\nclosed: {day}"
    return f"---\n{fm}\n---\n{after}"


def main():
    argv = sys.argv[1:]
    check = "--check" in argv
    pos = [a for a in argv if not a.startswith("--")]
    if not pos:
        sys.exit("usage: vault-close-day.py <YYYY-MM-DD> [--check]")
    day = pos[0]
    path = DAILY / f"{day}.md"
    if not path.exists():
        sys.exit(f"no daily note: {path}")
    fm, _, body = split_fm(path.read_text())

    if check:
        ok = True
        if not fm.get("closed"):
            print("FAIL: closed: not set"); ok = False
        if CLOSE not in path.read_text():
            print("FAIL: no ## Close manifest"); ok = False
        for d in re.findall(r'`([a-z]+)`', path.read_text().split(CLOSE)[-1]):
            if d not in DISPOSITIONS and d in ("claim","site","crucible","banked",
                    "slagged","spoiled","realized","recorded","passover"):
                print(f"FAIL: disposition not in vocab: {d}"); ok = False
        print("close-lint OK" if ok else "close-lint FAIL")
        sys.exit(0 if ok else 1)

    for earlier in sorted(DAILY.glob("*.md")):
        if DATE_RE.match(earlier.name) and earlier.stem < day and not is_closed(earlier):
            sys.exit(f"BLOCKED: earlier day {earlier.stem} is not closed (strict-order close)")
    if fm.get("closed"):
        print(f"already closed: {day}"); sys.exit(0)

    sidecar = DAILY / f"{day}.resolutions.json"
    resolutions = json.loads(sidecar.read_text()) if sidecar.exists() else {}

    manifest, others = [], []
    for idx, (sec, kind, txt) in enumerate(items_of(body)):
        disp, why = classify(sec, kind, txt, resolutions, idx)
        (others if disp is None else manifest).append(
            (idx, sec, kind, txt, disp, why))

    if others:
        print(f"{len(others)} item(s) need resolution (unknown/other) — resolve then re-run:")
        worklist = {}
        for idx, sec, kind, txt, disp, why in others:
            print(f"  [{idx}] ({sec}/{why}) {txt[:80]}")
            worklist[str(idx)] = ""
        if not sidecar.exists():
            sidecar.write_text(json.dumps(worklist, indent=2) + "\n")
            print(f"worklist → {sidecar.name}; fill one disposition each and re-run")
        sys.exit(2)

    today = datetime.date.today().isoformat()
    counts, bysec = Counter(), defaultdict(list)
    for idx, sec, kind, txt, disp, why in manifest:
        bysec[sec].append((kind, txt, disp))
        counts[disp] += 1
    out = [f"\n{CLOSE}\n",
           f"**Closed** {today} — deterministic `vault-close-day.py` sweep.\n",
           "**Disposition manifest** — every item accounted for:\n"]
    for sec, rows in bysec.items():
        out.append(f"\n*{sec}*")
        for kind, txt, disp in rows:
            out.append(f"- {'(block)' if kind == 'block' else txt[:72]} — `{disp}`")
    out.append("\n**Counts:** " + " · ".join(f"{d} {n}" for d, n in counts.items())
               + " · untagged 0\n")

    sealed = set_closed(path.read_text().rstrip() + "\n" + "\n".join(out), today)
    path.write_text(sealed)
    if sidecar.exists():
        sidecar.unlink()
    subprocess.run(["git", "-C", str(VAULT), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(VAULT), "commit", "-m",
                    f"close: {day} daily — disposition sweep ({len(manifest)} items)"],
                   check=True)
    print(f"closed {day}: {len(manifest)} items dispositioned")


if __name__ == "__main__":
    main()
```
