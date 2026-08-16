#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Refuse a diff that touches a protected spec without declaring its constitutional impact.

Self-contained, stdlib-only, no network (INV-6 posture at the CI layer). No YAML
library: the frontmatter this reads is a flat `key: value` block, and a runtime
dependency for one field would enlarge the trust ring for nothing.

WHAT THIS GATE DOES, EXACTLY
----------------------------
It establishes that the constitutional question was ANSWERED IN WRITING and that
the answer is in version control. It does NOT evaluate whether the answer is
correct -- deciding whether a change overrides a principle is the human judgement
`constitution.md` Section 5 reserves, and a gate that guessed would refuse
legitimate work while lending false authority to its own verdict.

    The gate refuses silence, not work.

SUBJECT SET
-----------
A file is protected iff its YAML FRONTMATTER carries a `protects:` key. Never a
substring match: 17 files in this repo quote `protects:` in prose -- including
CHANGELOG.md, ci.yml, and constitution.md itself -- and matching them would
refuse the changelog, refuse the workflow that implements this gate, and
deadlock the constitution.

DECLARATION
-----------
A fenced ```constitutional-impact block in the change's own proposal.md, read
from the TREE and not from pull-request metadata (a PR body can be edited after
its checks report green; the record and the check must be the same versioned
object). Located at either the live path `openspec/changes/<slug>/` or the
archived path `openspec/changes/archive/<date>-<slug>/`, because archiving syncs
deltas into protected specs by construction.

    ```constitutional-impact
    touches: openspec/specs/maintenance/spec.md
    protects: [INV-2, INV-3, INV-6]
    overrides: none
    basis: ADD-only; no existing requirement modified
    ```

`overrides: none` passes. Any identifier in `overrides:` requires a
constitution-override change directory carrying the four gate sections. `basis:`
is free text and is deliberately NOT parsed -- it exists for the human reviewer,
and this gate makes no claim about it.

Exit: 0 clean (incl. not-applicable) | 1 findings | 2 malformed input (fail-closed).

Usage: check-constitutional-impact.py <pr.diff> [--root DIR]
"""
import re
import sys
from pathlib import Path

FRONTMATTER_KEY_RE = re.compile(r"^protects:\s*(?P<val>.*)$")
CHANGE_DIR_RE = re.compile(r"^openspec/changes/(?:archive/)?(?P<dir>[^/]+)/")
DECL_BLOCK_RE = re.compile(
    r"^```constitutional-impact\s*$(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
# `\W*` spans the markdown the real template wraps this in: `**Change type:** ` +
# backticks. Matched against openspec/templates/constitution-override/proposal.md
# by test_the_real_template_is_recognised_as_a_ceremony.
OVERRIDE_TYPE_RE = re.compile(r"change\s+type:\W*constitution-override", re.IGNORECASE)
GATE_SECTION_RE = re.compile(r"^##\s*Gate\s*(?P<n>[1-4])\b", re.MULTILINE)

# The ONE exception to "any declared override needs the ceremony". constitution.md
# Section 2 puts INV-13 (and naming/vocabulary conventions) in Tier 2 -- "ordinary
# OpenSpec change, no ceremony required". Only the exception is encoded here, not a
# restatement of the whole tier table: a paraphrase of another artifact's rule is a
# fork with no merge (the class-9 defect). test_tier2_exception_matches_constitution
# fails if Section 2 stops saying this.
TIER_2_IDS = {"INV-13"}

BLOCK_TEMPLATE = """\
```constitutional-impact
touches: {touches}
protects: [{ids}]
overrides: none
basis: <why no Tier-0/Tier-1 element is overridden -- free text, not parsed>
```"""


def parse_diff_paths(text):
    """Return the set of paths a unified diff touches (both sides, minus /dev/null)."""
    paths = set()
    for line in text.split("\n"):
        m = re.match(r"^diff --git a/(?P<a>.+) b/(?P<b>.+)$", line)
        if m:
            for p in (m.group("a"), m.group("b")):
                if p != "/dev/null":
                    paths.add(p)
    return paths


def frontmatter_protects(path):
    """Return the protects: value from a file's YAML frontmatter, or None.

    Strict by design: the file must OPEN with a `---` fence. A `protects:` line
    anywhere else in the document is prose and is not a tag.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[4:end].split("\n"):
        m = FRONTMATTER_KEY_RE.match(line)
        if m:
            return m.group("val").strip()
    return None


def parse_id_list(raw):
    """`[INV-2, INV-3]` / `INV-2, INV-3` / `none` -> a set of identifiers."""
    raw = (raw or "").strip().strip("[]").strip()
    if not raw or raw.lower() in ("none", "nothing", "[]"):
        return set()
    return {tok.strip() for tok in raw.split(",") if tok.strip()}


def find_declaration(root, change_dirs):
    """Return (decl_fields, source_path) from the first change dir carrying a block."""
    for rel in sorted(change_dirs):
        proposal = root / rel / "proposal.md"
        if not proposal.is_file():
            continue
        try:
            text = proposal.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        m = DECL_BLOCK_RE.search(text)
        if not m:
            continue
        fields = {}
        for line in m.group("body").split("\n"):
            if ":" in line:
                k, _, v = line.partition(":")
                fields[k.strip().lower()] = v.strip()
        return fields, f"{rel}/proposal.md"
    return None, None


def find_override_ceremony(root, change_dirs):
    """Return the path of a change dir holding a constitution-override with 4 gates."""
    for rel in sorted(change_dirs):
        proposal = root / rel / "proposal.md"
        if not proposal.is_file():
            continue
        try:
            text = proposal.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not OVERRIDE_TYPE_RE.search(text):
            continue
        gates = {m.group("n") for m in GATE_SECTION_RE.finditer(text)}
        if gates >= {"1", "2", "3", "4"}:
            return f"{rel}/proposal.md"
    return None


def main(argv):
    root = Path(".")
    args = []
    rest = list(argv[1:])
    while rest:
        a = rest.pop(0)
        if a == "--root":
            if not rest:
                print("MALFORMED: --root needs a directory", file=sys.stderr)
                return 2
            root = Path(rest.pop(0))
        elif a.startswith("--root="):
            root = Path(a.split("=", 1)[1])
        elif a.startswith("--"):
            print(f"MALFORMED: unknown option {a}", file=sys.stderr)
            return 2
        else:
            args.append(a)
    if len(args) != 1:
        print(__doc__.strip().split("\n")[-1], file=sys.stderr)
        return 2
    try:
        diff_text = Path(args[0]).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"MALFORMED: cannot read diff: {exc}", file=sys.stderr)
        return 2

    touched = parse_diff_paths(diff_text)

    # Subject set: frontmatter only. A deleted file cannot be read, and a change
    # that deletes a protected spec is a structural act the reviewer will see.
    protected = {}
    for rel in sorted(touched):
        val = frontmatter_protects(root / rel)
        if val is not None:
            protected[rel] = parse_id_list(val)

    if not protected:
        print("constitutional-diff-gate: no protected element touched -- not applicable")
        return 0

    change_dirs = set()
    for rel in touched:
        m = CHANGE_DIR_RE.match(rel)
        if m:
            change_dirs.add(rel[: m.end()].rstrip("/"))

    all_ids = sorted({i for ids in protected.values() for i in ids})
    print("constitutional-diff-gate: protected elements touched by this diff")
    for rel, ids in sorted(protected.items()):
        print(f"  {rel}  protects: [{', '.join(sorted(ids))}]")

    # A complete constitution-override is never refused by the gate that demands it.
    ceremony = find_override_ceremony(root, change_dirs)
    if ceremony:
        print(f"  PASS: constitution-override ceremony present ({ceremony}); four gates found")
        return 0

    decl, source = find_declaration(root, change_dirs)
    if decl is None:
        print("", file=sys.stderr)
        print("REFUSED: no constitutional-impact declaration found in this diff.", file=sys.stderr)
        print("", file=sys.stderr)
        print("This gate does not judge whether your change overrides a principle.", file=sys.stderr)
        print("It requires that the question is answered in writing, in the tree.", file=sys.stderr)
        print("A declaration in the pull-request body does not count: a body can be", file=sys.stderr)
        print("edited after its checks report green.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Add this to your change's proposal.md:", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            BLOCK_TEMPLATE.format(touches=", ".join(sorted(protected)), ids=", ".join(all_ids)),
            file=sys.stderr,
        )
        if not change_dirs:
            print("", file=sys.stderr)
            print("NOTE: this diff carries no openspec/changes/ directory. A change that", file=sys.stderr)
            print("modifies a protected spec takes a proposal (CONTRIBUTING.md).", file=sys.stderr)
        return 1

    overrides = parse_id_list(decl.get("overrides", ""))
    ceremony_needed = overrides - TIER_2_IDS
    if not ceremony_needed:
        waived = overrides & TIER_2_IDS
        note = f" (Tier-2 only: {', '.join(sorted(waived))})" if waived else ""
        print(f"  PASS: declaration at {source} overrides nothing requiring ceremony{note}")
        return 0

    print("", file=sys.stderr)
    print(f"REFUSED: {source} declares an override of: {', '.join(sorted(ceremony_needed))}", file=sys.stderr)
    print("", file=sys.stderr)
    print("An override of a Tier-0/Tier-1 element is a first-class change of type", file=sys.stderr)
    print("`constitution-override` and must pass four gates in order", file=sys.stderr)
    print("(constitution.md Section 3). No such change directory is present in this diff.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Start from: openspec/templates/constitution-override/proposal.md", file=sys.stderr)
    print("Gate 4 requires a human sign-off; agents may not sign.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
