#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""PreToolUse hook — `gh` invocation-form allowlist (ADR-0045).

Emits a `deny` decision, or nothing at all. Never emits `allow`: see the note's Rationale.
Deterministic (INV-6) — reads stdin, spawns no subprocess, touches no network.

Fails OPEN by construction: any parse failure exits 0 with no output. That is why the enumerated
`permissions.deny` entries are retained alongside this hook rather than replaced by it.
"""
import json
import shlex
import sys

# The permitted set. Derived from a measured platform constraint, not from incident history:
# GitHub's GraphQL endpoint requires auth unconditionally, REST does not.
SEPARATORS = {"&&", "||", ";", "|", "&", "\n"}

REST_HINT = (
    "Use `gh api` with an explicit REST path instead — e.g. "
    "`gh api repos/{owner}/{repo}/pulls`. Permitted forms: `gh api <REST path>`, `gh auth status`."
)


def segments(command):
    """Split a command line into segments on shell separators, quote-aware.

    `shlex` with punctuation_chars emits `&&`, `||`, `;` and `|` as their own tokens while leaving
    quoted text intact — so `echo "a && b"` is one segment, and `cd /tmp && gh pr list` is two.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    out, current = [], []
    for tok in lexer:
        if tok in SEPARATORS:
            out.append(current)
            current = []
        else:
            current.append(tok)
    out.append(current)
    return [s for s in out if s]


def is_env_assignment(token):
    """`VAR=value` in command-word position is an assignment, not the command."""
    if "=" not in token:
        return False
    name = token.split("=", 1)[0]
    return bool(name) and (name[0].isalpha() or name[0] == "_") and \
        all(c.isalnum() or c == "_" for c in name)


def verdict(segment):
    """-> reason string to deny with, or None to stand aside."""
    args = list(segment)
    while args and is_env_assignment(args[0]):
        args.pop(0)
    if not args:
        return None

    # Compare by basename so an absolute path cannot walk past the matcher.
    if args[0].rsplit("/", 1)[-1] != "gh":
        return None

    rest = args[1:]
    positional = [a for a in rest if not a.startswith("-")]
    sub = positional[0] if positional else ""

    if sub == "api":
        # `gh api` is permitted EXCEPT the one form that cannot work: graphql.
        if len(positional) > 1 and positional[1] == "graphql":
            return (
                "`gh api graphql` is refused: GitHub's GraphQL endpoint requires authentication "
                "unconditionally, and this session's `gh` credential is unauthenticated, so it "
                "returns 401 rather than data. " + REST_HINT
            )
        return None

    if sub == "auth" and len(positional) > 1 and positional[1] == "status":
        return None

    named = f"`gh {sub}`" if sub else "this `gh` form"
    return (
        f"{named} is refused: the `gh` invocation-form allowlist permits only `gh api` with a REST "
        f"path and `gh auth status`; every other form is refused by default rather than permitted "
        f"by omission (ADR-0045). " + REST_HINT
    )


def main():
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
        if not isinstance(command, str):
            raise TypeError
        parts = segments(command)
    except Exception:
        return  # fail open — silence, exit 0

    for segment in parts:
        reason = verdict(segment)
        if reason:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }))
            return


main()
