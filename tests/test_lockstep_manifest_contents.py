# SPDX-License-Identifier: Apache-2.0
"""The REAL `template-sync-manifest.json` declares the governance-content prefixes.

Gap found 2026-09-09 by asking what covered PR #115. `test_template_parity.py` builds its own
SYNTHETIC manifest (`{"lockstep": ["99-Operations/scripts/", "99-Operations/schemas/"]}`) to
exercise the comparator, which is correct for that purpose and means **nothing reads the shipped
manifest**. So the prefix set that decides what is compared against a deployed vault -- the thing
PR #115 changed -- had no test at all.

That matters because the failure is silent in the direction that hurts: dropping a prefix does not
break anything visibly. `template-parity` simply stops comparing those files and keeps reporting
`0 drift`, which is exactly how 41 lines of bootstrap runbook went missing from the live vault
undetected (hardening item 34).

These tests assert the shipped manifest, not a fixture.
"""
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = REPO / "tools/template-sync-manifest.json"

# Content the framework governs and an instance MUST NOT silently diverge from.
GOVERNANCE_PREFIXES = {
    "99-Operations/scripts/",   # INV-3 source-of-truth scaffold
    "99-Operations/schemas/",   # ditto
    "96-Runbooks/",             # spec-as-code runbooks
    ".claude/commands/",        # agent commands that carry ceremony
}


def _manifest():
    return json.loads(MANIFEST.read_text())


def test_every_governance_prefix_is_declared_lockstep():
    """Dropping one is invisible: parity just stops comparing and still reports 0 drift."""
    declared = set(_manifest()["lockstep"])
    missing = GOVERNANCE_PREFIXES - declared
    assert not missing, (
        f"governance content is not compared against a deployed vault: {sorted(missing)}. "
        "Parity will report 0 drift while these files rot or go missing.")


def test_per_instance_config_is_not_lockstep():
    """The other direction. `.claude/settings.json` carries per-instance permissions, sandbox
    scope and hook registration; comparing it byte-for-byte would fight legitimate local
    ownership and turn every instance into permanent drift."""
    declared = _manifest()["lockstep"]
    assert ".claude/" not in declared, (
        "`.claude/` is declared wholesale — that would make settings.json lockstep and break "
        "per-instance ownership. Only .claude/commands/ belongs here.")
    for p in declared:
        assert not p.rstrip("/").endswith("settings.json"), f"settings.json must stay seed: {p}"


def test_render_output_is_never_lockstep():
    """`99-Operations/bin/` is render OUTPUT, governed by reconcile against the note that
    produced it. Declaring it would report one drift per fleet member forever, and a check that
    is always red is a check nobody reads."""
    declared = _manifest()["lockstep"]
    assert "99-Operations/bin/" not in declared, (
        "render output declared lockstep — that is reconcile's jurisdiction, and vault-template/ "
        "ships no bin/, so parity would be permanently red")


def test_the_manifest_still_parses_and_carries_its_reasoning():
    """The comment keys are the only place the SEED/LOCKSTEP division is written down."""
    m = _manifest()
    assert isinstance(m.get("lockstep"), list) and m["lockstep"]
    assert isinstance(m.get("exclude"), list)
    joined = " ".join(v for k, v in m.items() if k.startswith("_"))
    assert "SEED" in joined and "LOCKSTEP" in joined, (
        "the manifest no longer explains the division it encodes")
