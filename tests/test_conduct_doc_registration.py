# SPDX-License-Identifier: Apache-2.0
"""The standing-conduct runbook exists, is lockstep-covered, and is REACHED at session start in both roots.

WHY THIS EXISTS
---------------
`agent-conduct-standing-rules.md` only does its job if a session actually reaches it. A runbook can be
byte-perfect, lockstep-verified and mirrored into the live vault while no session ever loads it,
because `template-parity.py` compares FILES and hook registration lives in `.claude/settings.json`,
which is SEED and deliberately not compared (platform-hardening item 32, reduced to this artifact).

HOW IT IS REACHED — two harness-agnostic-first paths:

1. The SessionStart output NAMES it, as its FIRST line. Long SessionStart output reaches the agent only
   as a 2 KB preview (a 12.6 KB output was cut that way on 2026-09-25), so anything after the
   bootstrap would never be seen. The doc is deliberately NOT `cat`ed there: 17 KB behind a 2 KB
   preview is not delivery.
2. Step 2 of `session-bootstrap-loader` points to it, so the fully-read bootstrap path reaches it on
   any harness.

STATED LIMIT: these tests establish the registration STRING and the runbook text. They cannot
establish that Claude Code executes the hook or shows its preview — only a real cold start does, and
that check is AGENT-measured: the preview is delivered to the agent, never shown to the operator
(measured 2026-09-26), so the agent reads line 1 of the hook's saved output. It is not a gate. The
live vault's own `.claude/settings.json` is not
checked here: it is per-instance, and is updated by merging the delta, never by copying the template.
Runbook FORMAT is not re-checked here either: CI's `runbook-lint` owns it (import, never restate).
"""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
DOC_REL = "96-Runbooks/agent-conduct-standing-rules.md"
BOOT_REL = "96-Runbooks/session-bootstrap-loader.md"
DOC = REPO / "vault-template" / DOC_REL
BOOT = REPO / "vault-template" / BOOT_REL

SETTINGS = {
    "framework": (REPO / ".claude/settings.json", "vault-template/"),
    "template": (REPO / "vault-template/.claude/settings.json", ""),
}


def _session_start_commands(path):
    hooks = json.loads(path.read_text()).get("hooks", {}).get("SessionStart", [])
    return [h["command"] for entry in hooks for h in entry.get("hooks", [])]


def _rules():
    """Rule entries are the `#### N.` blocks under `## Standing rules`."""
    return DOC.read_text(encoding="utf-8").split("\n#### ")[1:]


def test_the_runbook_exists():
    assert DOC.is_file(), f"{DOC_REL} is missing from vault-template/"


def test_the_runbook_is_under_a_lockstep_prefix():
    manifest = json.loads((REPO / "tools/template-sync-manifest.json").read_text())
    assert any(DOC_REL.startswith(p) for p in manifest["lockstep"]), (
        f"{DOC_REL} is not under a lockstep prefix, so the mirror would not carry it "
        "and drift would go undetected"
    )
    assert DOC_REL not in manifest.get("exclude", []), "the conduct runbook must not be parity-excluded"


def test_session_start_names_it_first_in_both_roots():
    """Named, not `cat`ed, and BEFORE the bootstrap — or it falls outside the 2 KB preview."""
    for label, (path, prefix) in SETTINGS.items():
        cmds = _session_start_commands(path)
        assert cmds, f"{label}: no SessionStart hook at all"
        doc, boot = f"{prefix}{DOC_REL}", f"{prefix}{BOOT_REL}"
        hits = [c for c in cmds if doc in c]
        assert hits, f"{label}: SessionStart never names {doc}; the runbook would ship and never load"
        c = hits[0]
        assert boot in c and c.index(doc) < c.index(boot), (
            f"{label}: the conduct pointer must come BEFORE the bootstrap's output, or it lands "
            f"beyond the 2 KB SessionStart preview. Command: {c}"
        )
        assert not re.search(r"\bcat\b[^;|&]*" + re.escape(doc), c), (
            f"{label}: the conduct doc is `cat`ed into SessionStart — 17 KB behind a 2 KB preview "
            "is not delivery; name it instead"
        )


def test_the_bootstrap_loader_is_still_registered():
    """Adding the pointer must not displace the loader — both are required."""
    for label, (path, prefix) in SETTINGS.items():
        assert any(f"{prefix}{BOOT_REL}" in c for c in _session_start_commands(path)), (
            f"{label}: the bootstrap loader is no longer registered on SessionStart"
        )


def test_the_bootstrap_step_2_points_here():
    """The harness-agnostic path: whoever follows the bootstrap reaches the rules."""
    text = BOOT.read_text(encoding="utf-8")
    m = re.search(r"^2\. `\[gate\]`.*?(?=^3\. `)", text, re.S | re.M)
    assert m, "could not locate step 2 of the bootstrap loader"
    assert "agent-conduct-standing-rules" in m.group(0), "bootstrap step 2 does not point at the conduct runbook"


def test_rules_are_numbered_contiguously():
    nums = [int(re.match(r"(\d+)\.", r).group(1)) for r in _rules()]
    assert nums, "no `#### N.` rule entries found — the checks below would pass vacuously"
    assert nums == list(range(1, len(nums) + 1)), f"rule numbering is not contiguous: {nums}"


def test_every_rule_declares_terminal_or_a_gate():
    """A rule that names neither is unfalsifiable: nothing says who enforces it."""
    undeclared = [r.split("\n")[0] for r in _rules() if "`terminal`" not in r and "`gate:" not in r]
    assert not undeclared, f"rules declaring neither `terminal` nor `gate:`: {undeclared}"


def test_every_rule_carries_a_cost_line():
    """The cost IS the criticality metric. A rule without one reads as arbitrary preference."""
    missing = [r.split("\n")[0] for r in _rules() if "`cost:`" not in r]
    assert not missing, f"rules missing a `cost:` line: {missing}"


def test_the_cold_start_check_is_agent_measured():
    """The SessionStart preview is delivered to the AGENT; the operator cannot observe it.

    §Verification once called the cold-start check "operator-observed" — routing an unobservable check
    to the one party who cannot see it (measured 2026-09-26: the agent read the pointer as line 1 of the
    saved hook output).
    """
    text = DOC.read_text(encoding="utf-8")
    m = re.search(r"^## Verification\n(.*?)(?=^## )", text, re.S | re.M)
    assert m, "could not locate the runbook's ## Verification section"
    section = m.group(1)
    line = [b for b in section.split("\n- ") if "cold start" in b]
    assert line, "§Verification no longer names the cold-start check — the checks below would pass vacuously"
    assert "operator-observed" not in section, "§Verification routes the cold-start check to the operator, who cannot see the preview"
    assert "agent-measured" in line[0], "§Verification must name the cold-start check as agent-measured"
