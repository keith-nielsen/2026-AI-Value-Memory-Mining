#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract the Declared-scope block from a PR body into OverReach scope JSON.

Reads the pull-request body from the PR_BODY environment variable (passed via
`env:` in the workflow — never interpolated into shell, so body content cannot
inject commands). Finds the fenced ```scope block, validates its entries, and
prints OverReach's internal Scope JSON on stdout.

Fail-closed: a missing, empty, or malformed block exits non-zero with an
instructive message. Entry rules (matched to OverReach 0.7.0 `memberPath`
semantics — probed 2026-07-14):
  - one root-relative path per line; directories end with "/"
  - every entry must contain "/" or "." (keeps matching in the strict
    path branch, out of the fuzzy token branches)
  - no glob characters (*, ?, [ ) — globs silently never match in 0.7.0
  - lines starting with "#" are comments
"""
import json
import os
import re
import sys

FENCE_RE = re.compile(r"```scope[ \t]*\r?\n(.*?)```", re.DOTALL)
GLOB_CHARS = set("*?[")

HOW_TO_FIX = (
    "Add a fenced scope block to the PR body (see .github/pull_request_template.md):\n"
    "```scope\n"
    "openspec/changes/<change-id>/\n"
    "CHANGELOG.md\n"
    "```\n"
    "One root-relative path per line; directories end with '/'; no globs."
)


def fail(msg: str) -> None:
    print(f"declared-scope: {msg}\n\n{HOW_TO_FIX}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    body = os.environ.get("PR_BODY", "")
    if not body.strip():
        fail("PR body is empty — no Declared-scope block found.")

    m = FENCE_RE.search(body)
    if not m:
        fail("no ```scope fenced block found in the PR body.")

    entries = []
    for raw in m.group(1).replace("\r", "").split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if GLOB_CHARS & set(line):
            fail(
                f"entry '{line}' contains a glob character — OverReach 0.7.0 "
                "matches directory prefixes and exact paths only; globs never match."
            )
        if "/" not in line and "." not in line:
            fail(
                f"entry '{line}' has neither '/' nor '.' — write directories "
                "with a trailing '/' and files as root-relative paths."
            )
        entries.append(line)

    if not entries:
        fail("the ```scope block contains no path entries.")

    scope = {
        "files_allowed": entries,
        "features_allowed": [],
        "endpoints_allowed": [],
        "deps_allowed": [],
        "env_allowed": [],
        "behavioral_changes_allowed": [],
    }
    json.dump(scope, sys.stdout, indent=2)
    print()
    print(f"declared-scope: {len(entries)} entries extracted.", file=sys.stderr)


if __name__ == "__main__":
    main()
