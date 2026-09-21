#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stop hook — relay-conformance guard (item 40).

Byte-checks the `bash …/next.sh` line the agent relayed (inside a START COPY/END COPY block) against
the driver's canonical sidecar. Blocks a mismatch AT MOST ONCE per emission (a self-contained
loop guard), and fails OPEN on everything else. Deterministic and offline (INV-6).
"""
import hashlib
import json
import os
import re
import sys

# A `bash <path>/next.sh …` line. LEADING whitespace is captured on purpose: an indented paste is
# mangled (operator-command-formatting), so an indented relay must read as drift, not be normalised
# away. Trailing whitespace is dropped (invisible, not a paste hazard). The ```bash fence line does
# not match — it starts with backticks, not `bash`.
_RELAY = re.compile(r"^([ \t]*bash\s+\S*?/\.git/pr-flow/next\.sh\b[^\n]*?)[ \t]*$", re.MULTILINE)


def _relay_in_message(msg):
    """The relayed next.sh line inside a START COPY/END COPY block, or None.

    The line is returned WITH any leading whitespace: a flush-left relay equals the sidecar; an
    indented one does not, so the byte-check catches the indentation drift.
    """
    for block in re.findall(r"START COPY\s*(.*?)\s*END COPY", msg, re.DOTALL):
        m = _RELAY.search(block)
        if m:
            return m.group(1)
    return None


def _repo_root_with_sidecar(cwd):
    """Walk up from cwd to the dir whose .git/pr-flow/relay-line.txt exists; return (root, line)."""
    p = cwd
    for _ in range(8):
        f = os.path.join(p, ".git", "pr-flow", "relay-line.txt")
        try:
            with open(f, encoding="utf-8") as fh:
                return p, fh.read().strip()
        except OSError:
            nxt = os.path.dirname(p)
            if nxt == p:
                return None, None
            p = nxt
    return None, None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # fail open

    msg = data.get("last_assistant_message") or ""
    cwd = (data.get("cwd") or "").rstrip("/")
    if not isinstance(msg, str) or not cwd:
        sys.exit(0)

    relayed = _relay_in_message(msg)
    if relayed is None:
        sys.exit(0)  # no relay block in this message — nothing to check

    root, canonical = _repo_root_with_sidecar(cwd)
    if not canonical:
        sys.exit(0)  # no sidecar — fail open

    marker = os.path.join(root, ".git", "pr-flow", "relay-block-marker")
    want = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    if relayed == canonical:
        # Correct relay — clear any marker so a later drift on a new step re-arms.
        try:
            os.remove(marker)
        except OSError:
            pass
        sys.exit(0)

    # Mismatch. Block AT MOST ONCE per emission (keyed on the sidecar).
    try:
        with open(marker, encoding="utf-8") as fh:
            already = fh.read().strip()
    except OSError:
        already = ""

    if already == want:
        # Already blocked this emission — do NOT block again (loop guard). Warn only.
        sys.stderr.write(
            "relay-conformance: the relayed next.sh line still does not match the driver's "
            "emission, but this emission was already flagged once — not blocking again. "
            f"Correct line: {canonical}\n")
        sys.exit(0)

    try:
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(want)
    except OSError:
        sys.exit(0)  # cannot record the block -> fail open rather than risk a loop

    sys.stderr.write(
        "relay-conformance: the next.sh line you relayed is not byte-identical to the one the "
        "driver emitted — the F43 relay drift. Copy the driver's START COPY/END COPY block verbatim; "
        "do not retype it, drop the tag, or swap the path form.\n"
        f"  driver emitted: {canonical}\n"
        f"  you relayed:    {relayed}\n")
    sys.exit(2)  # block once


main()
