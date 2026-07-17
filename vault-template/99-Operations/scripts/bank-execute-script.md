---
type: meta-script
deploy_target: ~/bin/vault-refine-execute.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-05
---
## Rationale
Applies approved refine proposals from `20-Claims/_refine-approved/` (the human gate,
INV-4). The human gate is the act of moving a proposal from `_refine-proposals/` to
`_refine-approved/` — this script never promotes proposals itself. Root
resolution comes from the shared `vault_lib` (ADR-0023) so the bare drive invocation
works without a pre-sourced environment. **Owns its commits** (B3, commit-ownership):
each banked proposal is one atomic scoped commit — the knowledge note, its Catalog
index links, and the consumed proposal's deletion (`bank: <stem>`); the close-day
sweep no longer collects Treasury writes. **Pre-flights before any write** (B4):
every proposal is validated whole — JSON schema, path containment (target inside
`40-Treasury/`, links inside `40-Treasury/Catalog/`), the INV-11 stem boundary,
**create never overwrites** (INV-9 pre-action), append target must exist,
`grade`/`pillars` against the config vocabularies, and every link target present.
A proposal failing any check is REJECTed whole, with all reasons printed and **no
partial write**; the batch continues — one bad proposal cannot block or half-apply
another. Any reject exits `1` (`EXIT_VIOLATION`); a clean batch exits `0`.
One note per proposal; multiple proposals can be batched. **Catalog linking is idempotent**
(INV-12): a link is appended to an index only if that index does not already carry it — so an
`append` to an already-catalogued note extends the note without duplicating its existing bullet,
while a genuinely new index is still linked.

## Implementation
```python
#!/usr/bin/env python3
import datetime, json, pathlib, sys, frontmatter
sys.path.insert(0, str(pathlib.Path.home() / "bin"))
from vault_naming import is_valid_slug, has_min_hyphen_tokens  # naming.md
from vault_lib import EXIT_VIOLATION, commit_paths, find_vault_root, vocab

vault = find_vault_root()
today = datetime.date.today().isoformat()
approved = vault / "20-Claims" / "_refine-approved"
TREASURY = (vault / "40-Treasury").resolve()
CATALOG = (vault / "40-Treasury" / "Catalog").resolve()
GRADES = set(vocab("GRADES"))
PILLARS = set(vocab("PILLARS"))
# INV-12 reachability: an empty index_links defaults here so a banked note is never an orphan.
# This holding index is the visible "awaiting-catalog" queue; the operator creates it once.
PENDING_CATALOG = "40-Treasury/Catalog/pending-catalog-index.md"


def check(p):
    """Pre-flight (B4): schema, containment, INV-11 boundary, INV-9 overwrite guard,
    config vocabularies, link targets. Returns reasons; empty == bankable.
    Nothing is written before a clean pass."""
    v = []
    for key, typ in (("target_note", str), ("mode", str), ("insight_md", str),
                     ("provenance_md", str), ("index_links", list)):
        if not isinstance(p.get(key), typ):
            v.append(f"missing/invalid field '{key}'")
    if v:
        return v
    note = vault / p["target_note"]
    if not note.resolve().is_relative_to(TREASURY):
        v.append(f"target_note escapes 40-Treasury: {p['target_note']}")
    if not is_valid_slug(note.stem):                  # INV-11: reject at the boundary
        v.append(f"target_note stem '{note.stem}' is not a valid kebab slug")
    elif not has_min_hyphen_tokens(note.stem):        # INV-11 floor (ADR-0015 / ADR-0030)
        # Must reject BEFORE any write: the commit gate now enforces the floor too, so a
        # sub-3 stem that got past pre-flight would be written and then blocked at commit,
        # stranding the executor half-applied.
        v.append(f"target_note stem '{note.stem}' has fewer than 3 hyphen-tokens (INV-11)")
    if p["mode"] == "create":
        if note.exists():
            v.append(f"create would overwrite existing {p['target_note']} (INV-9)")
        fmt = p.get("frontmatter")
        if not isinstance(fmt, dict):
            v.append("missing/invalid field 'frontmatter'")
        else:
            pil = set(fmt.get("pillars") or [])
            if not pil or not pil <= PILLARS:
                v.append(f"pillars must be non-empty subset of {sorted(PILLARS)}")
            if fmt.get("grade") not in GRADES:
                v.append(f"grade must be one of {sorted(GRADES)}")
    elif p["mode"] == "append":
        if not note.exists():
            v.append(f"append target missing: {p['target_note']}")
    else:
        v.append(f"bad mode: {p['mode']}")
    for link in p["index_links"]:
        lp = vault / link
        if not lp.resolve().is_relative_to(CATALOG):
            v.append(f"index link escapes 40-Treasury/Catalog: {link}")
        elif not lp.is_file():
            v.append(f"index link target missing: {link}")
    return v


rejects = 0
for prop in sorted(approved.glob("*.json")):
    try:
        p = json.loads(prop.read_text())
    except json.JSONDecodeError as e:
        print(f"REJECT {prop.name}: invalid JSON ({e})")
        rejects += 1
        continue
    # INV-12 reachability: an empty index_links is not a rejection — default it to the
    # pending-catalog holding index so every banked note stays reachable via >=1 Catalog
    # index. A missing / non-list index_links is still a schema rejection in check().
    if isinstance(p.get("index_links"), list) and not p["index_links"]:
        p["index_links"] = [PENDING_CATALOG]
    problems = check(p)
    if problems:
        for reason in problems:
            print(f"REJECT {prop.name}: {reason}")
        rejects += 1
        continue                                  # batch isolation: next proposal
    note = vault / p["target_note"]
    note.parent.mkdir(parents=True, exist_ok=True)
    if p["mode"] == "create":
        post = frontmatter.Post(
            p["insight_md"],
            type="knowledge", title=note.stem,
            pillars=p["frontmatter"]["pillars"],
            grade=p["frontmatter"]["grade"],
            stage="refined",
            crucible=p["frontmatter"].get("crucible", False),
            created=today, updated=today,
        )
        note.write_text(frontmatter.dumps(post)
                        + f"\n\n## Provenance / Changelog\n{p['provenance_md']}\n")
    else:                                         # append (pre-flighted: target exists)
        note.write_text(note.read_text()
                        + f"\n\n{p['insight_md']}\n\n## Provenance\n{p['provenance_md']}\n")
    for link in p["index_links"]:
        mp = vault / link
        # Idempotent (INV-12): only add the catalog link if the index does not already carry it.
        # append mode extends a note that is usually already catalogued — an unconditional write
        # would duplicate its existing bullet; a genuinely new index is still linked.
        if f"[[{note.stem}]]" not in mp.read_text():
            mp.write_text(mp.read_text() + f"\n- [[{note.stem}]]")
    prop.unlink()
    # atomic bank (B3): note + index links + consumed proposal, one scoped commit
    commit_paths(vault, [note, *(vault / l for l in p["index_links"]), prop],
                 f"bank: {note.stem}")
    print(f"refined -> {note}")

sys.exit(EXIT_VIOLATION if rejects else 0)
```
