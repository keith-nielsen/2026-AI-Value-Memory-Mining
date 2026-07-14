#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Compare a PR diff against the Declared scope — self-contained, stdlib-only.

The declared-scope *concept* (authorized-vs-actual set arithmetic over a PR
diff) was evaluated in and informed by OverReach (MIT, Naveja00/OverReach);
this is a clean-room reimplementation so the gate carries **no runtime
dependency** — no registry fetch, no floating transitive tree, nothing outside
this file and the Python standard library (INV-6 posture at the CI layer).

Detectors (deliberately bounded to this repo's change surface):
  - files:  every path touched by the diff must match a declared entry —
            exact path, or directory prefix for entries ending "/". No
            basename, substring, token, or fuzzy matching (stricter than the
            evaluated tool by design).
  - env:    an added line introducing a key under an `env:` block in a
            workflow file (.github/workflows/*.yml) must be declared
            `env: NAME`.
  - deps:   an added `"name": "semver"` line inside a dependencies block of a
            package.json, or an added requirement line in requirements*.txt,
            must be declared `dep: name`.

Severity: undeclared file -> medium; undeclared env/dep -> high.
Threshold: any finding (medium+) -> exit 1. Malformed inputs -> exit 2
(fail-closed). Clean -> exit 0.

Usage: check-scope-findings.py <scope.json> <pr.diff>
"""
import json
import re
import sys

WORKFLOW_RE = re.compile(r"^\.github/workflows/.+\.ya?ml$")
ENV_BLOCK_RE = re.compile(r"^(\s*)env:\s*(#.*)?$")
ENV_KEY_RE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*):")
PKG_DEP_BLOCK_RE = re.compile(r'^\s*"(dependencies|devDependencies|peerDependencies|optionalDependencies)"\s*:')
PKG_DEP_RE = re.compile(r'^\+\s*"(?P<name>(@[\w.-]+/)?[\w.-]+)"\s*:\s*"[^"]*"')
REQ_RE = re.compile(r"^\+(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:[=<>!~;\[].*)?$")


def parse_diff(text):
    """Return (paths, env_added, deps_added) from a unified diff."""
    paths, env_added, deps_added = set(), set(), set()
    current = None
    in_env_block = env_indent = None
    in_dep_block = False
    for line in text.split("\n"):
        m = re.match(r"^diff --git a/(?P<a>.+) b/(?P<b>.+)$", line)
        if m:
            for p in (m.group("a"), m.group("b")):
                if p != "/dev/null":
                    paths.add(p)
            current = m.group("b")
            in_env_block = in_dep_block = False
            continue
        if current is None or not line.startswith("+") or line.startswith("+++"):
            # context/removed lines still steer the block trackers
            body = line[1:] if line[:1] in (" ", "-") else None
            if body is not None:
                if WORKFLOW_RE.match(current or ""):
                    eb = ENV_BLOCK_RE.match(body)
                    if eb:
                        in_env_block, env_indent = True, len(eb.group(1))
                    elif in_env_block and body.strip() and (len(body) - len(body.lstrip())) <= env_indent:
                        in_env_block = False
                if (current or "").endswith("package.json"):
                    if PKG_DEP_BLOCK_RE.match(body):
                        in_dep_block = True
                    elif in_dep_block and body.strip().startswith("}"):
                        in_dep_block = False
            continue
        body = line[1:]
        if WORKFLOW_RE.match(current or ""):
            eb = ENV_BLOCK_RE.match(body)
            if eb:
                in_env_block, env_indent = True, len(eb.group(1))
                continue
            if in_env_block:
                if body.strip() and (len(body) - len(body.lstrip())) <= env_indent:
                    in_env_block = False
                else:
                    k = ENV_KEY_RE.match(body)
                    if k:
                        env_added.add(k.group(2))
        if (current or "").endswith("package.json"):
            if PKG_DEP_BLOCK_RE.match(body):
                in_dep_block = True
                continue
            if in_dep_block:
                if body.strip().startswith("}"):
                    in_dep_block = False
                else:
                    d = PKG_DEP_RE.match(line)
                    if d:
                        deps_added.add(d.group("name"))
        if re.search(r"requirements[^/]*\.txt$", current or ""):
            r = REQ_RE.match(line)
            if r and not r.group("name").startswith("#"):
                deps_added.add(r.group("name"))
    return paths, env_added, deps_added


def file_authorized(path, allowed):
    for a in allowed:
        if a.endswith("/"):
            if path.startswith(a):
                return True
        elif path == a:
            return True
    return False


def main():
    if len(sys.argv) != 3:
        print("usage: check-scope-findings.py <scope.json> <pr.diff>", file=sys.stderr)
        sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            scope = json.load(fh)
        with open(sys.argv[2], encoding="utf-8") as fh:
            diff_text = fh.read()
        files_allowed = scope["files_allowed"]
        env_allowed = set(scope.get("env_allowed", []))
        deps_allowed = set(scope.get("deps_allowed", []))
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"scope-review: cannot read inputs ({exc}) — failing closed.", file=sys.stderr)
        sys.exit(2)
    if not diff_text.strip():
        print("scope-review: PASS (empty diff).")
        sys.exit(0)

    paths, env_added, deps_added = parse_diff(diff_text)
    findings = []
    for p in sorted(paths):
        if not file_authorized(p, files_allowed):
            findings.append(("MEDIUM", "scope.file", f'File "{p}" is not in the Declared scope.'))
    for e in sorted(env_added - env_allowed):
        findings.append(("HIGH", "scope.env", f'Added workflow env var "{e}" is not declared (env: {e}).'))
    for d in sorted(deps_added - deps_allowed):
        findings.append(("HIGH", "scope.dep", f'Added dependency "{d}" is not declared (dep: {d}).'))

    for sev, kind, detail in findings:
        print(f"  [{sev}] {kind}: {detail}")
    if findings:
        print(
            "scope-review: FAIL — the diff exceeds the Declared scope in the PR body. "
            "Shrink the diff, or amend the declaration deliberately.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"scope-review: PASS ({len(paths)} file(s), all declared).")
    sys.exit(0)


if __name__ == "__main__":
    main()
