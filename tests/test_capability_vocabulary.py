# SPDX-License-Identifier: Apache-2.0
"""The capability report's state vocabulary (hardening item 29, ADR-pending).

`test_every_emitted_state_is_declared` is the load-bearing one. Without it the constants are
documentation and a typo still invents a state — which is the condition that let eleven ad-hoc
literals, three of them containing whitespace, accumulate unobserved.
"""
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("pr_flow_vocab", REPO / "tools" / "pr-flow.py")
pf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pf)


def probe_json(declare_estate=True):
    """Run the real probe and return its machine-readable rows.

    The estate is DECLARED by default. Without it the framework layers correctly report UNDECLARED,
    and a suite that measured only that would never exercise the credential row it exists to check —
    the vacuous-pass shape the Definition of Done names.
    """
    import os
    env = dict(os.environ)
    if declare_estate:
        env["FRAMEWORK_ROOT"] = str(REPO)
    else:
        env.pop("FRAMEWORK_ROOT", None)
    r = subprocess.run([sys.executable, str(REPO / "tools" / "pr-flow.py"),
                        "--capabilities", "--json"],
                       capture_output=True, text=True, cwd=str(REPO), env=env)
    blob = r.stdout[r.stdout.index("{"):]
    return json.loads(blob)


def test_an_undeclared_estate_reports_undeclared_not_a_credential_verdict():
    """UNDECLARED is an honest absence, not a measurement. It must not masquerade as one."""
    rows = [r for r in probe_json(declare_estate=False)["rows"]
            if r["channel"] == "gh credential"]
    assert rows and rows[0]["state"] == pf.S_UNDECLARED


# --------------------------------------------------------------------------
# Closure — the only part that ENFORCES the vocabulary
# --------------------------------------------------------------------------

def test_every_emitted_state_is_declared():
    for row in probe_json()["rows"]:
        assert row["state"] in pf.CAPABILITY_STATES, (
            f"{row['channel']!r} emitted an undeclared state {row['state']!r}. "
            "Add it to CAPABILITY_STATES deliberately, or fix the typo.")


def test_cap_row_refuses_an_undeclared_state():
    """The guard that makes closure real: a stray token cannot reach the report."""
    with pytest.raises(AssertionError, match="undeclared capability state"):
        pf.cap_row("READ", "invented", "TOTALLY_MADE_UP", pf.AGENT, pf.AGENT, pf.EV_INSPECTED)


def test_no_declared_state_contains_whitespace():
    for s in pf.CAPABILITY_STATES:
        assert not any(c.isspace() for c in s), f"state {s!r} contains whitespace"


def test_retired_tokens_are_gone():
    """UNAVAILABLE was RETIRED, not narrowed — a reused token makes past transcripts ambiguous."""
    assert "UNAVAILABLE" not in pf.CAPABILITY_STATES
    states = {r["state"] for r in probe_json()["rows"]}
    assert "UNAVAILABLE" not in states
    assert not any(" " in s for s in states), "a multi-word state reached the report"


# --------------------------------------------------------------------------
# The credential row: three conditions, three tokens
# --------------------------------------------------------------------------

def test_credential_row_is_named_for_what_it_measures():
    """`gh auth status` measures a CREDENTIAL. The runbook has said `gh credential` since
    2026-08-06; the instrument printed `gh mutations` — named for what it INFERS."""
    channels = {r["channel"] for r in probe_json()["rows"]}
    assert "gh credential" in channels
    assert "gh mutations" not in channels


def test_credential_row_uses_one_of_the_three_decided_tokens():
    rows = [r for r in probe_json()["rows"] if r["channel"] == "gh credential"]
    assert rows, "no gh credential row"
    assert rows[0]["state"] in {pf.S_AUTHENTICATED, pf.S_UNAUTHENTICATED, pf.S_ABSENT}


def test_absent_is_a_different_token_from_unauthenticated():
    """The axis trap, asserted rather than left to a comment: ABSENT describes the TOOL and leaves
    the credential state UNKNOWN. Collapsing it into UNAUTHENTICATED hides a different remedy."""
    assert pf.S_ABSENT != pf.S_UNAUTHENTICATED


# --------------------------------------------------------------------------
# Evidence: inspection vs attempt
# --------------------------------------------------------------------------

def test_every_row_carries_evidence():
    for row in probe_json()["rows"]:
        assert row["evidence"], f"{row['channel']!r} carries no evidence field"


def test_attempted_evidence_names_the_channel_exercised():
    """`attempted` alone would not have prevented F40. Naming the exercised channel is what makes a
    subprocess-vs-shell divergence visible in the OUTPUT rather than only in the source."""
    for row in probe_json()["rows"]:
        ev = row["evidence"]
        if ev.startswith("attempted"):
            assert ":" in ev and ev.split(":", 1)[1], f"{row['channel']!r}: bare {ev!r}"
        else:
            assert ev == pf.EV_INSPECTED, f"{row['channel']!r}: unknown evidence kind {ev!r}"


def test_the_credential_row_is_inspected_not_attempted():
    """It reads `gh auth status`; it never attempts a mutation. Reporting it as attempted is the
    exact confusion that produced F40."""
    row = [r for r in probe_json()["rows"] if r["channel"] == "gh credential"][0]
    assert row["evidence"] == pf.EV_INSPECTED


# --------------------------------------------------------------------------
# The two renderings must agree
# --------------------------------------------------------------------------

def test_json_and_table_report_the_same_states():
    r = subprocess.run([sys.executable, str(REPO / "tools" / "pr-flow.py"),
                        "--capabilities", "--json"],
                       capture_output=True, text=True, cwd=str(REPO))
    table, blob = r.stdout.split("{", 1)
    for row in json.loads("{" + blob)["rows"]:
        assert row["state"] in table, (
            f"{row['channel']!r} state {row['state']!r} is in the JSON but not the table")
