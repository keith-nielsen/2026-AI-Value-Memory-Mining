#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Enforce the scope-review threshold on OverReach JSON output.

OverReach 0.7.0's own exit code fires only on scope_creep_score == HIGH, and an
out-of-scope *file* is a medium finding — the primary case for this repo would
pass a bare exit-code gate silently (probed 2026-07-14). This check reads the
JSON result and applies the repo's threshold instead:

  - score LOW            -> exit 0 (low-severity findings printed as advisory)
  - score MEDIUM or HIGH -> exit 1, findings listed
  - missing / malformed result (e.g. the overreach invocation crashed)
                         -> exit 2 (fail-closed)

Usage: check-scope-findings.py <result.json>
"""
import json
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: check-scope-findings.py <result.json>", file=sys.stderr)
        sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            result = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"scope-review: cannot read OverReach result ({exc}) — failing closed.", file=sys.stderr)
        sys.exit(2)

    score = result.get("scope_creep_score")
    findings = result.get("findings", [])
    if result.get("schema_version") != "1.0" or score not in ("LOW", "MEDIUM", "HIGH"):
        print("scope-review: unrecognized OverReach output shape — failing closed.", file=sys.stderr)
        sys.exit(2)

    for f in findings:
        sev = f.get("severity", "?").upper()
        print(f"  [{sev}] {f.get('kind', '?')}: {f.get('detail', '')}")

    if score == "LOW":
        print(f"scope-review: PASS (score {score}, {len(findings)} advisory finding(s)).")
        sys.exit(0)

    print(
        f"scope-review: FAIL (score {score}) — the diff exceeds the Declared scope "
        "in the PR body. Shrink the diff, or amend the declaration deliberately.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
