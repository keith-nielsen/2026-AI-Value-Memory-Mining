#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract the Declared-scope block from a PR body into OverReach scope JSON.

Reads the pull-request body from the PR_BODY environment variable (passed via
`env:` in the workflow — never interpolated into shell, so body content cannot
inject commands). Finds the fenced ```scope block, validates its entries, and
prints OverReach's internal Scope JSON on stdout.

Fail-closed: a missing, empty, or malformed block exits non-zero with an
instructive message. Entry rules (enforced by the companion comparator,
check-scope-findings.py — exact path or directory prefix, nothing fuzzy):
  - one root-relative path per line; directories end with "/"
  - every path entry must contain "/" or "." (bare tokens are ambiguous)
  - no glob characters (*, ?, [ ) — matching is exact-path / dir-prefix only
  - non-file surfaces are declared with a prefix: "env: NAME", "dep: package",
    "endpoint: /route" (added after dogfood run 1, where the gate correctly
    flagged its own PR_BODY env var)
  - lines starting with "#" are comments
The emitted JSON shape (files_allowed / env_allowed / deps_allowed / ...)
originated as the evaluated tool's scope schema (OverReach, MIT) and is
retained as this repo's declaration schema.
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
    "env: MY_NEW_VAR\n"
    "dep: some-package\n"
    "```\n"
    "One root-relative path per line; directories end with '/'; no globs.\n"
    "Non-file surfaces use a prefix: 'env: NAME', 'dep: package', 'endpoint: /route'."
)

ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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

    files, envs, deps, endpoints = [], [], [], []
    for raw in m.group(1).replace("\r", "").split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("env:"):
            name = line[len("env:"):].strip()
            if not ENV_NAME_RE.match(name):
                fail(f"entry '{line}' — '{name}' is not a valid environment-variable name.")
            envs.append(name)
            continue
        if line.startswith("dep:"):
            name = line[len("dep:"):].strip()
            if not name or " " in name:
                fail(f"entry '{line}' — '{name}' is not a valid dependency name.")
            deps.append(name)
            continue
        if line.startswith("endpoint:"):
            route = line[len("endpoint:"):].strip()
            if not route.startswith("/"):
                fail(f"entry '{line}' — endpoints are declared as absolute routes ('/x/y').")
            endpoints.append(route)
            continue
        if GLOB_CHARS & set(line):
            fail(
                f"entry '{line}' contains a glob character — matching is "
                "exact-path / directory-prefix only; globs never match."
            )
        if "/" not in line and "." not in line:
            fail(
                f"entry '{line}' has neither '/' nor '.' — write directories "
                "with a trailing '/' and files as root-relative paths "
                "(or use an 'env:' / 'dep:' / 'endpoint:' prefix for non-file surfaces)."
            )
        files.append(line)

    if not files:
        fail("the ```scope block contains no path entries.")

    scope = {
        "files_allowed": files,
        "features_allowed": [],
        "endpoints_allowed": endpoints,
        "deps_allowed": deps,
        "env_allowed": envs,
        "behavioral_changes_allowed": [],
    }
    json.dump(scope, sys.stdout, indent=2)
    print()
    print(
        f"declared-scope: {len(files)} path, {len(envs)} env, {len(deps)} dep, "
        f"{len(endpoints)} endpoint entries extracted.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
