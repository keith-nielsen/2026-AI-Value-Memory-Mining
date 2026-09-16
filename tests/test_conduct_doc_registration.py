"""The standing-conduct runbook exists, is lockstep-covered, and is REGISTERED in both roots.

WHY THIS EXISTS
---------------
`agent-conduct-standing-rules.md` only does its job if the SessionStart hook actually cats it. A
runbook can be byte-perfect, lockstep-verified and mirrored into the live vault while no session ever
loads it, because `template-parity.py` compares FILES and hook registration lives in
`.claude/settings.json`, which is SEED and deliberately not compared.

That is platform-hardening item 32 — *nothing verifies hook registration in either root* — reduced to
the one artifact this change ships. A control nobody loads is the silent-success failure the queue
exists to catalogue.

STATED LIMIT — read before trusting this file:

    These tests establish that the registration STRING names the runbook, and that the runbook is
    under a lockstep prefix so the mirror will carry it. They CANNOT establish that Claude Code
    actually executes the hook, because no automated test traverses the harness. Only a real cold
    start confirms that, and it is therefore an operator step, not a gate.

    The live vault's own `.claude/settings.json` is NOT checked here: it is per-instance, outside
    this repository, and updated by merging the delta rather than copying the template.
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
DOC_REL = "96-Runbooks/agent-conduct-standing-rules.md"
DOC = REPO / "vault-template" / DOC_REL

SETTINGS = {
    "framework": (REPO / ".claude/settings.json", f"vault-template/{DOC_REL}"),
    "template": (REPO / "vault-template/.claude/settings.json", DOC_REL),
}


def _session_start_commands(path):
    hooks = json.loads(path.read_text()).get("hooks", {}).get("SessionStart", [])
    return [h["command"] for entry in hooks for h in entry.get("hooks", [])]


def test_the_runbook_exists():
    assert DOC.is_file(), f"{DOC_REL} is missing from vault-template/"


def test_the_runbook_is_under_a_lockstep_prefix():
    manifest = json.loads((REPO / "tools/template-sync-manifest.json").read_text())
    assert any(DOC_REL.startswith(p) for p in manifest["lockstep"]), (
        f"{DOC_REL} is not under a lockstep prefix, so the mirror would not carry it "
        "and drift would go undetected"
    )


def test_it_is_not_excluded_from_parity():
    manifest = json.loads((REPO / "tools/template-sync-manifest.json").read_text())
    assert DOC_REL not in manifest.get("exclude", []), (
        "the conduct runbook must not be parity-excluded — it is authored, not generated"
    )


def test_registered_on_session_start_in_both_roots():
    for label, (path, expected_rel) in SETTINGS.items():
        cmds = _session_start_commands(path)
        assert cmds, f"{label}: no SessionStart hook at all"
        assert any(expected_rel in c for c in cmds), (
            f"{label}: SessionStart does not name {expected_rel}. The runbook would ship, pass "
            f"parity, mirror into the vault -- and never load. Commands found: {cmds}"
        )


def test_the_bootstrap_loader_is_still_registered():
    """Adding the conduct doc must not displace the loader -- both are required."""
    for label, (path, _) in SETTINGS.items():
        cmds = _session_start_commands(path)
        assert any("session-bootstrap-loader.md" in c for c in cmds), (
            f"{label}: the bootstrap loader is no longer registered on SessionStart"
        )


def test_every_rule_declares_terminal_or_a_gate():
    """A rule that names neither is unfalsifiable: nothing says who enforces it."""
    text = DOC.read_text(encoding="utf-8")
    blocks = text.split("\n### ")[1:]
    undeclared = [
        b.split("\n")[0]
        for b in blocks
        if "`terminal`" not in b and "`gate:" not in b
    ]
    assert not undeclared, (
        "these rules declare neither `terminal` nor `gate:`, so nothing states whether a control "
        f"reaches them: {undeclared}"
    )


def test_every_rule_carries_a_cost_line():
    """The cost IS the criticality metric. A rule without one reads as arbitrary preference."""
    text = DOC.read_text(encoding="utf-8")
    blocks = text.split("\n### ")[1:]
    missing = [b.split("\n")[0] for b in blocks if "`cost:`" not in b]
    assert not missing, f"rules missing a `cost:` line: {missing}"
