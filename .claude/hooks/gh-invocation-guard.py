#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""PreToolUse hook — `gh` invocation-form allowlist (ADR-0045).

Emits a `deny` decision, or nothing at all. Never emits `allow`: see the note's Rationale.
Deterministic (INV-6) — reads stdin, spawns no subprocess, touches no network.

Fails OPEN by construction: any parse failure exits 0 with no output. That is why the enumerated
`permissions.deny` entries are retained alongside this hook rather than replaced by it.
"""
import json
import re
import shlex
import sys

# The permitted set. Derived from a measured platform constraint, not from incident history:
# GitHub's GraphQL endpoint requires auth unconditionally, REST does not.
SEPARATORS = {"&&", "||", ";", "|", "&", "\n"}

REST_HINT = (
    "Use `gh api` with an explicit REST path instead — e.g. "
    "`gh api repos/{owner}/{repo}/pulls`. Permitted forms: `gh api <REST path>`, `gh auth status`."
)

# The sanctioned WRITE set. `gh api` is a wider permission than the subcommands it replaces --
# `gh api -X DELETE /repos/{owner}/{repo}` is permitted by form alone -- so GET is unconstrained
# and every write method reaches only these endpoints.
#
# IMPORTED, NOT AUTHORED HERE. The source of truth is the ```gh-write-endpoints block in
# docs/version-control-legal-moves.md §2b; tests/test_write_endpoint_set_parity.py fails if this
# copy drifts from it. The copy exists because this guard is stdlib-only, offline and deterministic
# (INV-6) and renders into roots that have no docs/ directory -- it cannot read that file at runtime.
# Edit the doc block, then this constant, never one alone.
#
# Flags that consume the NEXT token as their value. Needed so a flag's value is never mistaken for
# a positional -- see non_flag_tokens() for the hole this closes.
VALUE_FLAGS = {
    "-X", "--method", "-f", "--field", "-F", "--raw-field", "-H", "--header",
    "-q", "--jq", "-t", "--template", "--input", "--hostname", "-p", "--preview",
    "--cache", "-R", "--repo",
}

# `GET` is unconstrained; everything else must name a sanctioned endpoint. HEAD and OPTIONS are
# reads by definition and are treated the same way.
READ_METHODS = {"GET", "HEAD", "OPTIONS"}

# {slug} spans two path segments (owner/repo); {n} and {id} are numeric.
SANCTIONED_WRITES = {
    ("POST", "/repos/{slug}/pulls"),
    ("PATCH", "/repos/{slug}/pulls/{n}"),
    ("PUT", "/repos/{slug}/pulls/{n}/merge"),
    ("POST", "/repos/{slug}/releases"),
    ("DELETE", "/repos/{slug}/releases/{id}"),
    ("POST", "/repos/{slug}/labels"),
    ("POST", "/repos/{slug}/issues"),
}

# Excluded BY DECISION, not by oversight -- so the refusal can say which. Absence alone is already a
# refusal; this set exists only so the message teaches. Source of truth: the
# ```gh-write-endpoints-excluded block in docs/version-control-legal-moves.md §2b, held equal by
# tests/test_write_endpoint_set_parity.py.
EXCLUDED_WRITES = {
    ("PUT", "/repos/{slug}/rulesets/{id}"),
    ("PATCH", "/repos/{slug}/rulesets/{id}"),
    ("DELETE", "/repos/{slug}/rulesets/{id}"),
}


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


def non_flag_tokens(tokens):
    """-> the tokens that are genuinely positional: flags removed, AND their values with them.

    MEASURED DEFECT this replaces, 2026-09-19. The old rule was "every token not starting with
    `-`", so the VALUE of a flag occupied a positional slot. `gh api graphql` was refused while
    `gh api -X POST graphql` DEFERRED -- and a GraphQL mutation is always a POST, so the only shape
    capable of the silent no-op this guard exists to stop was the shape that got through. Layer 1's
    `Bash(gh api graphql:*)` prefix rule does not cover it either.
    """
    out, skip = [], False
    for tok in tokens:
        if skip:
            skip = False
            continue
        if tok.startswith("-"):
            # `--flag=value` and `-Xvalue` carry their value; `--flag value` consumes the next token.
            if "=" not in tok and tok in VALUE_FLAGS:
                skip = True
            continue
        out.append(tok)
    return out


def api_call(tokens):
    """-> (METHOD, endpoint or None) for a `gh api` invocation. Default method is GET."""
    method, endpoint, skip = "GET", None, False
    for i, tok in enumerate(tokens):
        if skip:
            skip = False
            continue
        if tok.startswith("-"):
            if tok.startswith("--method="):
                method = tok.split("=", 1)[1]
            elif tok.startswith("-X") and len(tok) > 2:
                method = tok[2:]
            elif tok in ("-X", "--method"):
                method = tokens[i + 1] if i + 1 < len(tokens) else ""
                skip = True
            elif "=" not in tok and tok in VALUE_FLAGS:
                skip = True
            continue
        if tok == "api":
            continue
        if endpoint is None:
            endpoint = tok
    return method.upper(), endpoint


def matches_any(endpoint, templates, method):
    """True iff `endpoint` matches a template in `templates` carrying the same method."""
    path = endpoint.split("?", 1)[0].split("#", 1)[0]
    if "://" in path:  # a full URL is the same call spelled longer
        path = "/" + path.split("://", 1)[1].split("/", 1)[-1] if "/" in path.split("://", 1)[1] \
            else "/"
    path = "/" + path.strip("/")
    for tmpl_method, tmpl in templates:
        if tmpl_method != method:
            continue
        # {slug} is owner/repo -- TWO segments in a real command, but ONE where a placeholder stands
        # in. The shipping detector flattens an f-string's interpolations to a single token, so a
        # guard demanding two segments would refuse the estate's own emitted commands. Accepting one
        # loosens nothing: the collection path after the slug must still match exactly.
        pattern = re.escape(tmpl)
        pattern = pattern.replace(re.escape("{slug}"), r"[^/]+(?:/[^/]+)?")
        pattern = re.sub(r"\\\{[a-z]+\\\}", r"[^/]+", pattern)
        if re.fullmatch(pattern, path):
            return True
    return False


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
    positional = non_flag_tokens(rest)
    sub = positional[0] if positional else ""

    if sub == "api":
        method, endpoint = api_call(rest)
        if method not in READ_METHODS:
            if endpoint is None:
                return (
                    "a `gh api` write was refused: no endpoint path could be read from the "
                    "command, so the sanctioned-endpoint rule cannot be applied. " + REST_HINT
                )
            if matches_any(endpoint, EXCLUDED_WRITES, method):
                return (
                    f"`gh api -X {method} {endpoint}` is refused: this endpoint is **excluded by "
                    f"decision**, not by oversight. GitHub rulesets are the only server-side "
                    f"control in this estate (ADR-0034) and a ruleset write replaces the entire "
                    f"rules array, so it can silently drop `pull_request`, `deletion` or "
                    f"`non_fast_forward` (ADR-0038). Ruleset changes are the operator's, run from "
                    f"their own terminal. The reasoning is in "
                    f"docs/version-control-legal-moves.md §2b; reopening it is a change with its "
                    f"own Gate 4, never an edit made in passing."
                )
            if not matches_any(endpoint, SANCTIONED_WRITES, method):
                return (
                    f"`gh api -X {method} {endpoint}` is refused: `GET` is unconstrained, but a "
                    f"write method reaches only the sanctioned endpoint set, because `gh api` is a "
                    f"WIDER permission than the subcommands it replaces. Sanctioned writes: "
                    + " · ".join(f"{m} {p}" for m, p in sorted(SANCTIONED_WRITES))
                    + ". The set's source of truth is the ```gh-write-endpoints block in "
                    "docs/version-control-legal-moves.md §2b."
                )
        # `gh api` is permitted EXCEPT the one form this estate has measured unsuitable: graphql.
        # The reason states only what is invariant. A hook is deterministic and offline (INV-6), so
        # it can never measure the session's credential -- any message asserting one would be a
        # claim the control cannot check, and was wrong in the field on 2026-08-26.
        if len(positional) > 1 and positional[1] == "graphql":
            return (
                "`gh api graphql` is refused: GitHub's GraphQL endpoint has failed "
                "non-deterministically in this estate four times, each a SILENT NO-OP -- the "
                "mutation reported nothing actionable and changed nothing (F21, F21-3). A channel "
                "that reports success without effect is unsuitable for production use. " + REST_HINT
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
