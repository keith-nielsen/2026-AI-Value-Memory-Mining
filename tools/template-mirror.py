#!/usr/bin/env python3
"""Template->live mirror driver — the write-capable counterpart to `template-parity.py`.

`template-parity.py` DETECTS drift between the repo's `vault-template/<prefix>` and a deployed
live vault; this tool FIXES it, in the one direction governance allows: repo -> live, one way,
never the reverse, never a delete. The repo is the governed source of truth for LOCKSTEP scaffold
(it passed PR review, CI, Gate-4); the live vault is the deploy target. For each LOCKSTEP file
declared in `template-sync-manifest.json`:

  MISSING-IN-LIVE  -> copy repo -> live (creating parent dirs).
  DIFFERS          -> overwrite live with the repo's bytes.
  MISSING-IN-TEMPLATE -> REPORT ONLY, never touched. A file present only in the live tree under a
                      lockstep prefix means something happened outside governance; resolving it
                      (delete? adopt as canonical?) is a human's decision, not a silent default.

Why this exists: it replaces the one handover CONTRIBUTING still described as prose — "Mirror any
vault-template hook/guard change into the live vault (operator action)" — with a single guarded
invocation, the same move `ship-release.py` made for the release ceremony. F26 (the live-vault
Site's determinism record): a hand-composed, line-wrapping multi-arg `cp` handed to the operator
degraded into a 2-arg overwrite and clobbered a repo file. A reviewed script invoked by one short
line cannot wrap into a different, destructive command.

Non-destructive by construction: it only ever overwrites a live file with the repo's
already-reviewed bytes, or creates a missing one — recoverable from `git status` on the live vault
exactly as F26 was, and never able to touch the repo (it never writes there). It re-derives parity
after acting and prints the same denominator'd tally `template-parity.py` prints; it never `git
add`/commits (that stays the operator's explicit INV-2 step). Idempotent: a second run performs
zero copies and reports 0 drift.

Stdlib-only, offline, no LLM (INV-6 mirror-time posture). Repo-only maintainer tool; not a fleet
script, no deploy_target, never rendered.

Usage:  tools/template-mirror.py [LIVE_VAULT]     # LIVE_VAULT defaults to $VAULT_ROOT
Exit:   0 mirror complete, 0 drift and no untracked live-only files ·
        2 MISSING-IN-TEMPLATE files were found and left untouched (a human decides) ·
        3 blocked (no resolvable live vault / bad manifest).
"""
import pathlib
import sys

import template_sync as ts

EXIT_OK = 0
EXIT_NEEDS_INPUT = 2


def main(argv):
    here = pathlib.Path(__file__).resolve().parent          # tools/
    template, live, prefixes, exclude = ts.resolve_trees(here, ts.live_arg_from(argv))

    # Compute the diff ourselves — never act on an enumeration typed from memory (F17/F23).
    _, _, drift = ts.compare(template, live, prefixes, exclude)

    mirrored = []                                            # (rel, prior_reason)
    untracked = []                                           # rel present only in live
    for rel, reason in drift:
        if reason in (ts.MISSING_IN_LIVE, ts.DIFFERS):
            src, dst = template / rel, live / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            mirrored.append((rel, reason))
        elif reason == ts.MISSING_IN_TEMPLATE:
            untracked.append(rel)                            # report only — never touched

    for rel, reason in mirrored:
        print(f"MIRRORED: {rel} (was {reason})")
    if untracked:
        # Distinct header: these are deliberately NOT resolved — surfaced for a human.
        print("MISSING-IN-TEMPLATE (present only in the live vault — left untouched, "
              "a human decides):")
        for rel in untracked:
            print(f"{ts.MISSING_IN_TEMPLATE}: {rel}")

    # Re-derive parity from the world after acting, exactly as template-parity.py measures it.
    checked, excluded, post = ts.compare(template, live, prefixes, exclude)
    for rel, reason in post:
        if reason != ts.MISSING_IN_TEMPLATE:
            print(f"{reason}: {rel}")                        # residual drift a copy did not resolve
    print(ts.tally_line(checked, prefixes, excluded, len(post)))
    return EXIT_OK if not post else EXIT_NEEDS_INPUT


if __name__ == "__main__":
    sys.exit(main(sys.argv))
