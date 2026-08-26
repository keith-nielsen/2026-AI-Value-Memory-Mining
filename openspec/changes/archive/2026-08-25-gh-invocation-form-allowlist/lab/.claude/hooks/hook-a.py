#!/usr/bin/env python3
"""G1.1 precedence probe — hook A (registered FIRST).

Emits a PreToolUse decision only for the three marker commands below; silent
(exit 0, no output) for everything else, so it cannot affect ordinary work.

Contract copied from the live outbound-publish-guard.py, not guessed:
  {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                          "permissionDecision": "allow"|"deny"|"ask",
                          "permissionDecisionReason": "..."}}
"""
import json
import sys

ROLE = "A"

# marker -> {role: decision}.  Registration order is A then B.
CASES = {
    "PRECEDENCE_AD":      {"A": "allow", "B": "deny"},   # earlier allow vs later deny
    "PRECEDENCE_DA":      {"A": "deny",  "B": "allow"},  # earlier deny  vs later allow
    "PRECEDENCE_ASKDENY": {"A": "ask",   "B": "deny"},   # G1.2: ask vs deny
}


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open, exactly as the real guard does

    cmd = (payload.get("tool_input") or {}).get("command", "")
    for marker, roles in CASES.items():
        if marker in cmd:
            decision = roles[ROLE]
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason":
                        f"[probe hook {ROLE}] {decision.upper()} for {marker}",
                }
            }))
            sys.exit(0)
    sys.exit(0)


main()
