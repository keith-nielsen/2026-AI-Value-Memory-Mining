#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prove a markdown change preserved PROSE, or name exactly what it altered.

WHY THIS EXISTS
---------------
A corpus-wide formatting sweep is unreviewable by eye: the diff is thousands of
lines of moved whitespace, and a single altered word hides in it perfectly. On
2026-08-27 a `markdownlint --fix` pass silently stripped the trailing space from
`` `trail ` `` in `openspec/specs/naming-rules/spec.md` -- a code span whose
trailing space WAS the test input -- leaving a scenario asserting that a valid
name must be rejected. The autofix cannot distinguish a significant space from a
sloppy one, and no reviewer found it. This tool did.

WHAT IT DOES, EXACTLY
---------------------
It compares the TOKEN MULTISET of two revisions of a file with every whitespace
run collapsed, so reflow, blank-line insertion and table realignment vanish and
only real content differences survive. Structural tokens -- fences, table
separator rows, bare pipes -- are excluded, because a formatter legitimately adds
and reshapes them.

    identical  : same tokens, same order   -> formatting only
    reordered  : same tokens, new order    -> content moved but nothing lost
    changed    : tokens added or removed   -> prose was altered

WHAT IT DOES NOT DO
-------------------
It is not a renderer and makes no claim that two files LOOK the same. Emphasis
style (`_x_` vs `*x*`) is a token change and is reported, correctly -- judging it
cosmetic is the reviewer's call, not this tool's. It says what differs; it never
says whether the difference is acceptable.

    The tool reports; it does not approve.

STATED BLIND SPOT
-----------------
Tokens made only of pipes, colons, hyphens and spaces are classified structural,
so list bullets and `ul-style` changes (`-` vs `*`) are deliberately invisible.
The cost is real and is accepted knowingly: a prose edit whose ONLY difference is
a standalone dash -- "a - b" becoming "a b" -- is not detected. Word-level edits
either side of the dash still are. This is the one class of change the tool is
known to miss; it is recorded here rather than discovered later, and
`test_documents_the_standalone_dash_blind_spot` pins it so it cannot regress
silently into a wider hole.

Stdlib only, no network (INV-6 posture). Exit: 0 no prose change | 1 prose
changed | 2 malformed input (fail-closed).
"""
import argparse
import collections
import re
import subprocess
import sys

# A fence (```lang / ````), a table separator row (|---|:--:|), or a bare pipe run.
FENCE_RE = re.compile(r"^`{3,}[A-Za-z0-9+#_-]*$")
TABLE_SEP_RE = re.compile(r"^\|?[\s:|-]*-[\s:|-]*\|?$")
BARE_PIPE_RE = re.compile(r"^\|+$")
# A list bullet. `-` and `*` are interchangeable under MD004/ul-style, so a
# formatter may swap them freely. Matched EXPLICITLY rather than falling through
# TABLE_SEP_RE by accident -- see STATED BLIND SPOT above for what this costs.
BULLET_RE = re.compile(r"^[-*+]$")


def is_structural(token):
    """True for tokens a formatter may freely add, remove or reshape."""
    return bool(FENCE_RE.match(token) or TABLE_SEP_RE.match(token)
                or BARE_PIPE_RE.match(token) or BULLET_RE.match(token))


def prose_tokens(text):
    """Whitespace-collapsed, structure-free token stream of a markdown document."""
    flat = re.sub(r"\s+", " ", text).strip()
    if not flat:
        return []
    return [t for t in flat.split(" ") if t and not is_structural(t)]


def compare(old_text, new_text):
    """Return (verdict, removed, added) where verdict is one of the three states."""
    old, new = prose_tokens(old_text), prose_tokens(new_text)
    c_old, c_new = collections.Counter(old), collections.Counter(new)
    if c_old != c_new:
        return "changed", list((c_old - c_new).elements()), list((c_new - c_old).elements())
    return ("identical" if old == new else "reordered"), [], []


# --- git plumbing ----------------------------------------------------------------------------

def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def _show(repo, ref, path):
    r = _git(repo, "show", f"{ref}:{path}")
    return r.stdout if r.returncode == 0 else None


def check_range(repo, base, head, allow=()):
    """Compare every .md file changed between base and head. Returns (rows, changed)."""
    merge_base = _git(repo, "merge-base", base, head).stdout.strip() or base
    listing = _git(repo, "diff", "--name-only", f"{merge_base}..{head}", "--", "*.md")
    if listing.returncode != 0:
        raise RuntimeError(listing.stderr.strip() or "git diff failed")
    rows, changed = [], []
    for path in [p for p in listing.stdout.splitlines() if p.strip()]:
        old, new = _show(repo, merge_base, path), _show(repo, head, path)
        if old is None or new is None:
            rows.append((path, "added-or-removed", [], []))
            continue
        verdict, removed, added = compare(old, new)
        rows.append((path, verdict, removed, added))
        if verdict == "changed" and path not in allow:
            changed.append(path)
    return rows, changed


# --- selftest --------------------------------------------------------------------------------

SELFTEST_BASE = """# Title

Some prose that is quite long and will be reflowed by a formatter later on.

| a | b |
|---|---|
| 1 | 2 |

```
code
```

The validator rejects `trail ` (trailing space).
"""

# Formatting-only: reflowed, blank lines added, table realigned, fence labelled.
SELFTEST_FORMATTED = """# Title

Some prose that is quite long and will be
reflowed by a formatter later on.

| a | b |
| --- | --- |
| 1 | 2 |

```text
code
```

The validator rejects `trail ` (trailing space).
"""

# The real 2026-08-27 defect: the significant trailing space is gone.
SELFTEST_DEFECT = SELFTEST_FORMATTED.replace("`trail `", "`trail`")


def selftest():
    """A check that cannot fail proves nothing. Prove both directions."""
    ok = True
    verdict, _, _ = compare(SELFTEST_BASE, SELFTEST_FORMATTED)
    if verdict != "identical":
        print(f"SELFTEST FAIL: formatting-only reported as {verdict!r}", file=sys.stderr)
        ok = False
    verdict, removed, added = compare(SELFTEST_FORMATTED, SELFTEST_DEFECT)
    if verdict != "changed":
        print("SELFTEST FAIL: the real trailing-space defect was NOT detected", file=sys.stderr)
        ok = False
    if ok:
        print("selftest: formatting is ignored, and the trailing-space defect is caught")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default="main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--allow", action="append", default=[],
                    help="path whose prose change is reviewed and accepted (repeatable)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    try:
        rows, changed = check_range(args.repo, args.base, args.head, allow=set(args.allow))
    except RuntimeError as exc:
        print(f"MALFORMED: {exc}", file=sys.stderr)
        return 2

    counts = collections.Counter(v for _, v, _, _ in rows)
    print(f"md-content-check: {len(rows)} markdown file(s) compared "
          f"({args.base}..{args.head})")
    for state in ("identical", "reordered", "changed", "added-or-removed"):
        if counts[state]:
            print(f"  {state:<18} {counts[state]}")
    for path, verdict, removed, added in rows:
        if verdict in ("changed", "reordered"):
            mark = "ALLOWED" if path in set(args.allow) else "PROSE CHANGED"
            if verdict == "reordered":
                mark = "REORDERED (nothing added or removed)"
            print(f"\n  {mark}: {path}")
            if removed:
                print(f"    removed ({len(removed)}): {removed[:20]}")
            if added:
                print(f"    added   ({len(added)}): {added[:20]}")
    if changed:
        print(f"\nPROSE CHANGED in {len(changed)} undeclared file(s). Review each, then "
              f"re-run with --allow <path> for every one you accept.", file=sys.stderr)
        return 1
    print("\nNo undeclared prose change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
