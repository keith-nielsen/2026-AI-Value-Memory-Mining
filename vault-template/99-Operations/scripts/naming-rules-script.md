---
type: meta-script
deploy_target: ~/bin/vault_naming.py
runtime: manual
class: script
created: 2026-06-14
updated: 2026-07-02
---
## Rationale
Single source of truth for all vault name and slug rules (INV-11). Imported by the
linter, the refine executor, and the pre-commit hook — changing the rules here
propagates everywhere via `render`. Run with no args to (re)write the language-neutral
`naming-rules.json` mirror; `--check NAME` validates one path component (exit 1 on
violation). Makes no network or LLM calls (INV-6) and is never auto-modified (INV-5).

Carries the **special-file exemptions** (INV-11): tool-mandated / convention filenames
(README.md, CLAUDE.md, dailies, *.example, …) are exempt from the kebab / ≥3-token
content rules because an external tool or universal convention depends on the exact name.
`is_exempt(filename)` is the gate (matches on the basename). Editor state under
`.obsidian/` is out of scope via `.gitignore`, not via an exemption. Rationale in
`docs/naming-exemptions-rationale.md`.

## Implementation
```python
#!/usr/bin/env python3
"""vault_naming — single source of truth for vault name/slug rules (INV-11).
Run with no args to (re)write naming-rules.json; --check NAME validates one
path component and exits 1 on violation."""
import re, json, unicodedata, pathlib, os, sys, fnmatch

# --- declarative rules (the SSOT data; mirrored to naming-rules.json) ---
RULES = {
    "slug_pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    "min_hyphen_tokens": 3,
    "forbidden_chars": list('[]#^|\\/:*"?<>'),
    "reserved_names": ["CON", "PRN", "AUX", "NUL"]
                      + [f"COM{i}" for i in range(1, 10)]
                      + [f"LPT{i}" for i in range(1, 10)],
    "exempt_names": ["README.md", "LICENSE", "LICENSE.md", "CLAUDE.md", "AGENTS.md",
                     "MEMORY.md", ".gitignore", ".gitkeep", ".gitattributes",
                     "config.env", "config.defaults.env", "config.env.example"],
    # exempt_globs match the FILENAME (basename), so keep them basename-shaped.
    # .obsidian/ is NOT listed here — it is governed by .gitignore (editor-owned, out of
    # naming scope), not by a per-name exemption.
    "exempt_globs": ["*.example",
                     "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md"],
    "exempt_rationale_doc": "docs/naming-exemptions-rationale.md",
    "max_bytes": 255,
    "normalization": "NFC",
}
_slug_re = re.compile(RULES["slug_pattern"])
_forbidden = set(RULES["forbidden_chars"])
_reserved = {n.upper() for n in RULES["reserved_names"]}

def slugify(text):
    """Best-effort deterministic kebab-case slug; ASCII-only output."""
    t = unicodedata.normalize("NFKD", text)
    t = t.encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "untitled"

def is_exempt(filename):
    """True if a FULL filename (with extension) is exempt from the kebab / min-token
    content rules — a tool/convention depends on the exact name. See exempt_rationale_doc."""
    if filename in RULES["exempt_names"]:
        return True
    return any(fnmatch.fnmatch(filename, g) for g in RULES["exempt_globs"])

def has_min_hyphen_tokens(stem):
    """True if a stem carries >= min_hyphen_tokens hyphen-delimited tokens (INV-11 floor)."""
    return stem.count("-") + 1 >= RULES["min_hyphen_tokens"]

def validate_name(name):
    """Return a list of violation strings; empty == valid.
    `name` is ONE path component (folder or file stem), no extension."""
    v = []
    if name == "":
        return ["empty name"]
    if name != unicodedata.normalize("NFC", name):
        v.append("not NFC-normalised")
    if name.startswith("."):
        v.append("starts with a dot")
    if name != name.strip() or name.endswith("."):
        v.append("leading/trailing space or trailing dot")
    if any(ord(c) < 32 for c in name):
        v.append("contains control character(s)")
    bad = sorted(_forbidden & set(name))
    if bad:
        v.append("forbidden char(s): " + " ".join(bad))
    if name.upper() in _reserved:
        v.append("reserved device name: " + name)
    if len(name.encode("utf-8")) > RULES["max_bytes"]:
        v.append("exceeds %d bytes" % RULES["max_bytes"])
    return v

def is_valid_slug(slug):
    """Stricter check for machine-generated names (effort folders, Treasury stems)."""
    return bool(_slug_re.match(slug)) and not validate_name(slug)

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--check":
        viol = validate_name(sys.argv[2])
        if viol:
            print("INVALID '%s': %s" % (sys.argv[2], "; ".join(viol)))
            sys.exit(1)
        sys.exit(0)
    out = (pathlib.Path(os.environ["VAULT_ROOT"]) / "99-Operations"
           / "schemas" / "naming-rules.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(RULES, indent=2))
    print("naming-rules.json written -> %s" % out)
```
