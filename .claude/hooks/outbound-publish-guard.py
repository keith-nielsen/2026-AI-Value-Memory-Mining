#!/usr/bin/env python3
"""
Claude Code PreToolUse guard — outbound / exfil safety rail (INV-14).  PORTABLE.

Two jobs:
  1. HARD DENY any push / add-remote / repo-create / release whose EFFECTIVE TARGET is a deployed
     vault. The protected vault path is taken from $VAULT_ROOT (else $CLAUDE_PROJECT_DIR). The
     effective target is the directory/repo the command actually acts on — honoring a leading
     `cd <path> &&`, `git -C <path>`, and `gh … -R <owner/repo>` — not merely the shell's reported
     cwd, which in a live session is always the vault even when the command cd's into a sibling repo.
     When neither env var marks a vault (e.g. the public template repo), the vault-deny is inert.
  2. ASK (loud, unmissable banner) before ANY outward-replication or distribution publish that was
     not vault-denied — git push / remote-add / repo-create / release, and npm/twine/docker/… . An
     ASK cannot proceed without an explicit human Yes in any permission mode: no outward op silently
     defers. A read-only command that merely mentions a trigger token also raises the ASK (the guard
     is a conservative text matcher — an extra confirmation is the safe failure direction).

Output: Claude Code PreToolUse JSON on stdout. Exit 0 always (silent = defer to normal flow).
"""
import json
import os
import re
import sys
import time

VAULT = (os.environ.get("VAULT_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR") or "").rstrip("/")

# Endpoints whose REST form PUBLISHES, and must therefore raise this guard's ask.
#
# Publishing is a property of the endpoint, not of the command's spelling. The matchers below key on
# subcommand tokens, and that is exactly how the REST form escaped: measured 2026-09-19,
# `gh release create …` raised the full banner while
# `gh api -X POST repos/o/r/releases -f tag_name=v1.2.3` passed in SILENCE. A release published by
# REST leaves the machine just as irreversibly as one published by subcommand.
#
# IMPORTED, NOT AUTHORED HERE. Source of truth: the rows marked `outbound: yes` in the
# ```gh-write-endpoints block of docs/version-control-legal-moves.md §2b, held equal by
# tests/test_write_endpoint_set_parity.py. This guard is stdlib-only and offline (INV-6) and renders
# into roots with no docs/, so it cannot read that file at runtime.
OUTBOUND_ENDPOINTS = {
    ("POST", "/repos/{slug}/releases"),
    ("DELETE", "/repos/{slug}/releases/{id}"),
}

def _rest_publish_pattern():
    """Build the REST half of the rail FROM `OUTBOUND_ENDPOINTS`, so the constant is load-bearing.

    Hand-writing a second copy here would be the class-9 defect the endpoint block exists to
    prevent: the list would drift from the doc exactly when it mattered. Derived instead, so adding
    an `outbound: yes` row to docs §2b extends this rail automatically.

    A form matches only when BOTH hold — a write method appears, and the path is an outbound
    endpoint. Reads of the same collection publish nothing and must not raise the banner: a prompt
    that fires on everything teaches the operator to approve it without reading.
    """
    alts = []
    for method, tmpl in sorted(OUTBOUND_ENDPOINTS):
        path = re.escape(tmpl.lstrip("/"))
        # {slug} is owner/repo; one segment where a placeholder stands in (see the invocation guard).
        path = path.replace(re.escape("{slug}"), r"[^/\s]+(?:/[^/\s]+)?")
        # A lambda, not a replacement string: `\s` in a replacement is a template escape and
        # `re.sub` raises `bad escape \s`. Measured 2026-09-19 -- the guard crashed at import with
        # exit 1, which is NOT its documented fail-open behaviour (that covers a malformed payload
        # at runtime, not a module that will not load).
        path = re.sub(r"\\\{[a-z]+\\\}", lambda _: r"[^/\s]+", path)
        alts.append(
            r"\bgh\s+api\b"
            rf"(?=[^\n]*(?:-X|--method)[=\s]*{method}\b)"
            rf"(?=[^\n]*/?{path})"
        )
    # Release ASSETS do not go to the API host. A rail watching only api.github.com misses them,
    # and this shape also covers a plain `curl` upload, which no `gh` pattern would see.
    alts.append(r"\buploads\.github\.com\b")
    return "|" + "|".join(alts)


OUTWARD = re.compile(
    r"\bgit\s+(?:-[Cc]\s+\S+\s+)*push\b"  # `git push`, incl. `git -C <path> push` / `-c k=v`
    r"|\bgit\s+(?:-[Cc]\s+\S+\s+)*remote\s+(add|set-url)\b"  # incl. `git -C <path> remote add` (item 36)
    r"|\bgh\s+repo\s+create\b"
    r"|\bgh\s+release\s+(create|edit|upload)\b"
    + _rest_publish_pattern(),
    re.IGNORECASE,
)

PUBLISH = re.compile(
    r"\bgh\s+repo\s+create\b"
    r"|\bgh\s+repo\s+edit\b[^\n]*--visibility\s+public"
    r"|\bgh\s+release\s+(create|edit|upload)\b"
    r"|\bnpm\s+publish\b"
    r"|\b(?:yarn|pnpm)\s+publish\b"
    r"|\btwine\s+upload\b"
    r"|\bpython\b[^\n]*-m\s+twine\s+upload"
    r"|\bdocker\s+push\b"
    r"|\bcargo\s+publish\b"
    r"|\bgem\s+push\b"
    + _rest_publish_pattern(),
    re.IGNORECASE,
)

# Redirect forms that move a command's effective target off the reported cwd.
_LEAD_CD = re.compile(r"^\s*cd\s+(?P<path>'[^']*'|\"[^\"]*\"|[^\s;&|]+)\s*(?:&&|;)")
_GIT_C = re.compile(r"\bgit\s+-C\s+(?P<path>'[^']*'|\"[^\"]*\"|[^\s;&|]+)")
_GH_R = re.compile(r"\bgh\s[^\n]*?\s-R(?:=|\s+)(?P<repo>'[^']*'|\"[^\"]*\"|[^\s;&|]+)")

# A plain `git push` of a BRANCH — the one reversible outward form. Its ref can be force-pushed or
# deleted, so it keeps the ASK; every other outward op (tag push, remote add, repo create, release,
# package publish) is irreversible and is DENIED (item 37). A tag push (`refs/tags/` or `--tags`) is
# excluded because a published `v*` tag is frozen by the ruleset.
_GIT_PUSH = re.compile(r"\bgit\s+(?:-[Cc]\s+\S+\s+)*push\b", re.IGNORECASE)
_TAG_REF = re.compile(r"refs/tags/|(?<![\w-])--tags\b", re.IGNORECASE)


def is_reversible_outbound(cmd: str) -> bool:
    """True iff `cmd` is a branch push — the only outward form whose effect git can roll back."""
    if not _GIT_PUSH.search(cmd):
        return False
    if _TAG_REF.search(cmd):
        return False
    return True


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        s = s[1:-1]
    return s


def _effective_path(cmd: str, cwd: str) -> str:
    """The directory a command actually acts on, resolved from RAW TEXT.

    Returns "" when an explicit `-R owner/repo` names a GitHub repo rather than a local tree.
    """
    if _GH_R.search(cmd):
        return ""
    m = _GIT_C.search(cmd) or _LEAD_CD.match(cmd)
    if m:
        return os.path.abspath(os.path.expanduser(_unquote(m.group("path")))).rstrip("/")
    return cwd


def _current_branch(repo: str) -> str:
    """Read HEAD directly.

    NOT via subprocess: this note is AST-analysed by `inv6-offline-check` and is one of the two most
    security-relevant scripts in the fleet. It stays free of process invocation entirely.
    """
    try:
        with open(os.path.join(repo, ".git", "HEAD"), encoding="utf-8") as fh:
            head = fh.read().strip()
    except OSError:
        return ""
    prefix = "ref: refs/heads/"
    return head[len(prefix):] if head.startswith(prefix) else ""


def _emission(path: str) -> dict:
    """The live driver emission for the repository containing `path`, or {}.

    A repository is GOVERNED exactly when a driver has emitted for it. The record names its own
    subject, so this needs no environment variable and cannot be silently disabled by an unset one.

    ⚠ EVERY failure here returns {} and therefore falls through to the ASK raised today — absent,
    unreadable, unparseable, expired, wrong-branch are all identical to "no record". **This function
    cannot cause a refusal.** That is the invariant the mechanism rests on: the record may only ever
    DOWNGRADE a confirmation to an allowance, never create one.
    """
    if not path:
        return {}
    p = path
    for _ in range(8):  # bounded walk toward the repo root
        try:
            with open(os.path.join(p, ".git", "pr-flow", "emitted.json"), encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, ValueError):
            nxt = os.path.dirname(p)
            if nxt == p:
                return {}
            p = nxt
            continue
        if not isinstance(rec, dict):
            return {}
        try:
            if float(rec.get("expires", 0)) <= time.time():
                return {}
        except (TypeError, ValueError):
            return {}
        want = str(rec.get("branch") or "")
        if want and want != _current_branch(p):
            return {}
        return rec
    return {}


def _unresolved_redirect_hint(cmd: str) -> list:
    """Explain a deny caused by a redirect this guard could not resolve.

    The 2026-08-16 denial was CORRECT and completely opaque. The command carried
    `git -C "$R"`; this guard reads raw text, so `"$R"` resolved to nothing, the redirect was
    ignored, and the effective target fell back to the reported cwd — the vault. The reader saw
    "you are pushing the vault" while believing they had targeted a sibling repository, and spent a
    day reasoning from that. A guard that reports only its verdict makes its reader derive the cause
    at the moment they have already shown they cannot.
    """
    m = _GIT_C.search(cmd) or _LEAD_CD.match(cmd)
    if not m:
        return []
    raw = _unquote(m.group("path"))
    resolved = os.path.abspath(os.path.expanduser(raw)).rstrip("/")
    if os.path.isdir(resolved):
        return []
    return [
        "  ⚠️  THE REDIRECT IN THIS COMMAND DID NOT RESOLVE, so the target fell back to the cwd:",
        f"        written:  {raw}",
        f"        resolved: {resolved}   (no such directory)",
        "     A shell variable is not expanded before this guard sees it, and a leading `cd` only",
        "     counts when it is genuinely leading. Use a LITERAL path — run the driver's emitted",
        "     command verbatim rather than rewrapping it.",
        "",
    ]


def _targets_vault(cmd: str, cwd: str) -> bool:
    """True iff the command's effective target resolves inside the protected vault."""
    if not VAULT:
        return False
    # Conservative: an outward op naming the vault path as an operand is treated as vault-outward.
    if VAULT in cmd:
        return True
    # An explicit `-R owner/repo` names a GitHub repo, not the local vault working tree.
    if _GH_R.search(cmd):
        return False
    # `git -C <path>` or a leading `cd <path> &&` redirect the effective directory.
    m = _GIT_C.search(cmd) or _LEAD_CD.match(cmd)
    if m:
        path = os.path.abspath(os.path.expanduser(_unquote(m.group("path")))).rstrip("/")
        return path == VAULT or path.startswith(VAULT + "/")
    # No redirect: fall back to the reported cwd.
    return cwd == VAULT or cwd.startswith(VAULT + "/")


def emit(decision: str, reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    cwd = (data.get("cwd", "") or "").rstrip("/")

    # 1) HARD DENY: an outward op whose effective target is the deployed vault (INV-14).
    if OUTWARD.search(cmd) and _targets_vault(cmd, cwd):
        emit(
            "deny",
            "\n".join(
                [
                    "",
                    "  ⛔⛔⛔  BLOCKED — VAULT IS PRIVATE BY DEFAULT (INV-14)  ⛔⛔⛔",
                    "",
                    "  This command would push / expose / create a remote for the deployed vault,",
                    "  which is PRIVATE and must NEVER be replicated to a public or external remote.",
                    "",
                    "  Refusing. A deliberate PRIVATE off-machine backup is set up by the operator,",
                    "  manually (allowlist a private remote in config.env) — never via an agent.",
                    "",
                    f"  command: {cmd}",
                    "",
                ]
                + _unresolved_redirect_hint(cmd)
            ),
        )
        sys.exit(0)

    # 1a) IRREVERSIBLE OUTBOUND is operator-only, in EVERY mode (item 37). DENY, not ASK: the ASK
    #     silently PROCEEDS under auto mode (measured 2026-09-20), and git + the server-side ruleset
    #     cannot roll back a published release, a frozen v* tag, an added remote, or a created repo.
    #     The one reversible outward form is a branch push (its ref can be force-pushed or deleted);
    #     everything else outward is denied here. Evaluated BEFORE the driver-emission downgrade, so a
    #     byte-matched irreversible emission is STILL denied — the operator runs these in their own
    #     terminal, via the ceremony, where this hook does not fire.
    if (OUTWARD.search(cmd) or PUBLISH.search(cmd)) and not is_reversible_outbound(cmd):
        emit(
            "deny",
            "\n".join(
                [
                    "",
                    "  ⛔  IRREVERSIBLE OUTBOUND — OPERATOR-ONLY (INV-14)",
                    "",
                    "  This publishes or creates something git and the server-side ruleset cannot",
                    "  roll back — a release, a v* tag, a remote, or a repository. It is refused on",
                    "  the agent's channel in every mode: the outbound ASK silently proceeds under",
                    "  auto mode, so an irreversible action must not rely on it. The OPERATOR runs",
                    "  this in their own terminal, via the ceremony, where this hook does not fire.",
                    "",
                    f"  command: {cmd}",
                    "",
                ]
            ),
        )
        sys.exit(0)

    # 1b) DOWNGRADE: an outward op on a repository a driver governs, run EXACTLY as the driver
    #     emitted it. Allowed without a prompt, because the driver already derived and printed it.
    #
    #     ⚠ THIS PATH CAN ONLY ALLOW. It never denies. Anything that is not an exact match on a
    #     live record falls through to the ASK below — which is the behaviour today — so this
    #     cannot make the guard stricter than it already is, and needs no burn-in.
    #
    #     A match is NOT an authorisation and is never reported as one: it means the command is
    #     byte-identical to what the driver emitted. The record lives in the agent's own write
    #     scope and is therefore FORGEABLE by the agent it governs. It addresses ERROR, not intent
    #     — a mangled retype does not also produce a matching record — which is consistent with
    #     ADR-0018's posture: safe-by-default and a governed guarantee, not a physical
    #     impossibility; a tripwire for a cooperating agent.
    if OUTWARD.search(cmd):
        # Two lookups on purpose. A MANGLED redirect is exactly the case this exists to catch, and a
        # mangled redirect is also the case where the effective path cannot be resolved — so the
        # repository the caller is standing in is consulted as well. Found by a test: the motivating
        # 2026-08-16 command resolves `-C "$R"` to nothing, so the effective-path lookup alone found
        # no record and the diff was never shown.
        rec = _emission(_effective_path(cmd, cwd)) or _emission(cwd)
        if rec:
            if rec.get("command") == cmd:
                emit("allow", "matched the driver's emitted command for step "
                              f"'{rec.get('step', '?')}' (branch '{rec.get('branch', '?')}'). "
                              "Matched a record — not an authorisation.")
                sys.exit(0)
            # A live record exists and this is NOT it. Fall through to ASK, but name what differs:
            # a mangled command differs in ways its author cannot see by re-reading it.
            emit(
                "ask",
                "\n".join([
                    "",
                    "  ⚠️  NOT THE COMMAND THE DRIVER EMITTED",
                    "",
                    f"  emitted:  {rec.get('command', '')}",
                    f"  you ran:  {cmd}",
                    "",
                    "  A driver emission is live for this repository and this is not it. Run the",
                    "  emitted command VERBATIM — no variables, no timeout prefix, no rewrapping:",
                    "  the guard resolves targets from raw text, so rewriting changes what it sees.",
                    "  Or re-run the driver to derive a current command.",
                    "",
                ]),
            )
            sys.exit(0)

    # 2) ASK (loud): any outward-replication / publish not vault-denied — a structural hard stop.
    if OUTWARD.search(cmd) or PUBLISH.search(cmd):
        emit(
            "ask",
            "\n".join(
                [
                    "",
                    "  *********************************************************************",
                    "  **  ⚠️  OUTBOUND — CODE / DATA LEAVING THIS MACHINE — HARD STOP  ⚠️  **",
                    "  *********************************************************************",
                    "",
                    "  THIS COMMAND SENDS CODE OR DATA TO A REMOTE (push / release / publish).",
                    "  A PUSHED OR PUBLISHED RECORD IS CACHED, MIRRORED, AND INDEXED — TREAT IT",
                    "  AS EFFECTIVELY IRREVERSIBLE.",
                    "",
                    "  CONFIRM ALL THREE BEFORE APPROVING:",
                    "    (1) it contains NO private / vault / confidential / personal data;",
                    "    (2) sending it to this remote is genuinely intended;",
                    "    (3) you are doing this DELIBERATELY — not on autopilot or while tired,",
                    "        having reviewed the overview summary + proposal.md.",
                    "",
                    "  If you are not certain of all three: choose NO.",
                    "",
                    f"  command: {cmd}",
                    "  *********************************************************************",
                    "",
                ]
            ),
        )
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
