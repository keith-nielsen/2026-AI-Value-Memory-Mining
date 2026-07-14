---
type: meta-script
deploy_target: .claude/hooks/outbound-publish-guard.py
runtime: harness hook
class: script
created: 2026-06-29
updated: 2026-07-14
---
## Rationale
Claude Code `PreToolUse` guard — the INV-14 outbound/exfil safety rail (ADR-0018, refined by
ADR-0027). Hard-denies any push / remote-add / repo-create / release whose **effective target** is a
deployed vault; raises a loud ASK hard-stop before any other outward-replication or distribution
publish. Previously operational code **outside the render inventory** (fleet-review R8): it lived only
at `.claude/hooks/`, so `reconcile` could not see it drift. This note is now its source of truth
(INV-3) — the code block is byte-identical to the shipped hook; `render` deploys it and `reconcile`
guards it like every other fleet member. `.claude/` is agent-write-denied in a live vault, so
rendering there is an operator action, matching the `99-Operations/hooks/*` precedent. Deterministic
(INV-6): reads env + stdin only.

**ADR-0027 refinement (2026-07-14):** the vault check now keys on the command's **effective target**
(a leading `cd <path>`, `git -C <path>`, or `gh -R <owner/repo>`), not the shell's reported cwd —
which in a live session is always the vault, so the old `cwd == VAULT` test false-denied every
legitimate publish to a sibling repo (e.g. the framework repo's `gh release create`). It also closes a
silent gap: the ASK now fires on **any** non-denied outward op (`OUTWARD or PUBLISH`), so a plain
`git push` can no longer defer unprompted. Vault-outward commands are still hard-denied; the change
only removes a false-positive and closes an under-fire — the Safety band is tightened, not relaxed.

## Implementation
```python
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

VAULT = (os.environ.get("VAULT_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR") or "").rstrip("/")

OUTWARD = re.compile(
    r"\bgit\s+(?:-[Cc]\s+\S+\s+)*push\b"  # `git push`, incl. `git -C <path> push` / `-c k=v`
    r"|\bgit\s+remote\s+(add|set-url)\b"
    r"|\bgh\s+repo\s+create\b"
    r"|\bgh\s+release\s+(create|edit|upload)\b",
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
    r"|\bgem\s+push\b",
    re.IGNORECASE,
)

# Redirect forms that move a command's effective target off the reported cwd.
_LEAD_CD = re.compile(r"^\s*cd\s+(?P<path>'[^']*'|\"[^\"]*\"|[^\s;&|]+)\s*(?:&&|;)")
_GIT_C = re.compile(r"\bgit\s+-C\s+(?P<path>'[^']*'|\"[^\"]*\"|[^\s;&|]+)")
_GH_R = re.compile(r"\bgh\s[^\n]*?\s-R(?:=|\s+)(?P<repo>'[^']*'|\"[^\"]*\"|[^\s;&|]+)")


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        s = s[1:-1]
    return s


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
            ),
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
```
