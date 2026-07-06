---
type: meta-script
deploy_target: .claude/hooks/outbound-publish-guard.py
runtime: harness hook
class: script
created: 2026-06-29
updated: 2026-07-06
---
## Rationale
Claude Code `PreToolUse` guard — the INV-14 outbound/exfil safety rail (ADR-0018). Hard-denies
any push / remote-add / repo-create / release touching a deployed vault; loud ASK before any
public distribution-hub publish. Previously operational code **outside the render inventory**
(fleet-review R8): it lived only at `.claude/hooks/`, so `reconcile` could not see it drift.
This note is now its source of truth (INV-3) — the code block is byte-identical to the shipped
hook; `render` deploys it and `reconcile` guards it like every other fleet member. `.claude/` is
agent-write-denied in a live vault, so rendering there is an operator action, matching the
`99-Operations/hooks/*` precedent. Deterministic (INV-6): reads env + stdin only.

## Implementation
```python
#!/usr/bin/env python3
"""
Claude Code PreToolUse guard — outbound / exfil safety rail (INV-14).  PORTABLE.

Two jobs:
  1. HARD DENY any push / add-remote / repo-create / release that touches a deployed vault.
     The protected vault path is taken from $VAULT_ROOT (else $CLAUDE_PROJECT_DIR). When neither
     marks a vault (e.g. running in the public template repo), the vault-deny is inert and only
     job (2) applies.
  2. ASK (loud, unmissable banner) before ANY public repo creation or publish to a de-facto
     distribution hub — a PERMANENT, PUBLIC-FACING, effectively-irreversible record.

Output: Claude Code PreToolUse JSON on stdout. Exit 0 always (silent = defer to normal flow).
"""
import json
import os
import re
import sys

VAULT = (os.environ.get("VAULT_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR") or "").rstrip("/")

OUTWARD = re.compile(
    r"\bgit\s+push\b"
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

    in_vault = bool(VAULT) and (cwd == VAULT or cwd.startswith(VAULT + "/") or VAULT in cmd)

    # 1) HARD DENY: vault data leaving the machine (INV-14).
    if in_vault and OUTWARD.search(cmd):
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

    # 2) ASK (loud): public / distribution-hub publishing, anywhere.
    if PUBLISH.search(cmd):
        emit(
            "ask",
            "\n".join(
                [
                    "",
                    "  *********************************************************************",
                    "  **  ⚠️  PERMANENT  PUBLIC-FACING  RECORD  —  READ  BEFORE  YES  ⚠️  **",
                    "  *********************************************************************",
                    "",
                    "  THIS COMMAND PUBLISHES TO A PUBLIC, EXTERNALLY-DISTRIBUTED LOCATION.",
                    "  ONCE LIVE IT IS CACHED, MIRRORED, AND INDEXED — IT CANNOT BE RELIABLY",
                    "  UN-PUBLISHED.  TREAT IT AS IRREVERSIBLE.",
                    "",
                    "  CONFIRM ALL THREE BEFORE APPROVING:",
                    "    (1) it contains NO private / vault / confidential / personal data;",
                    "    (2) PUBLIC distribution is genuinely intended;",
                    "    (3) you are doing this DELIBERATELY — not on autopilot or while tired.",
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
