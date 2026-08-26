# SPDX-License-Identifier: Apache-2.0
"""Tests for the `gh` invocation-form allowlist guard (ADR-0045).

WRITTEN RED-FIRST. At the time of writing, `gh-invocation-guard-script.md` does not exist:
every test here fails at the fixture. That is the point — a matcher whose tests were written
after it cannot demonstrate that they would have caught anything.

**Refusing cases come first.** A suite that proved only the permitted forms would pass against
an implementation that allowed everything, which is the exact failure this guard exists to
prevent. The allowlist's safety property is *"an unlisted form is refused by default"*, so the
default-refusal cases are the ones that must be seen to fail without the guard.

The guard is exercised as a REAL SUBPROCESS against its rendered form, the way the harness runs
it — not by importing functions out of the note. The note is the source of truth (INV-3), so the
rendered artifact is extracted here rather than read from `.claude/hooks/`, which may be stale or
absent in a fresh clone. Pattern copied from `test_emission_record.py`.

Scope, stated so the suite is not credited with more than it covers: these tests bind the matcher's
decision on a command STRING. They say nothing about whether the hook is registered — no unit test
traverses hook registration, which is why task G4.2 is an operator step in a live session.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template/99-Operations/scripts/gh-invocation-guard-script.md"


@pytest.fixture(scope="module")
def guard(tmp_path_factory):
    """Extract the python block from the meta-script note — the same body `render` deploys."""
    assert NOTE.exists(), (
        f"{NOTE.relative_to(REPO)} does not exist — this is the RED state these tests were "
        "written in (task G2, before G3.1 builds the note)."
    )
    text = NOTE.read_text(encoding="utf-8")
    m = re.search(r"^## Implementation\s*\n```python\n(.*?)^```", text, re.S | re.M)
    assert m, "no python implementation block in the gh invocation guard note"
    p = tmp_path_factory.mktemp("ghguard") / "gh-invocation-guard.py"
    p.write_text(m.group(1), encoding="utf-8")
    return p


def decide(guard, cmd, *, raw=None):
    """-> (decision, reason). 'defer' means exit 0 with no output: the hook stands aside."""
    payload = raw if raw is not None else json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": cmd}})
    r = subprocess.run([sys.executable, str(guard)], input=payload,
                       capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, (
        f"guard exited {r.returncode}; a hook must exit 0 even when refusing — a crashing "
        f"hook teaches the harness to stop consulting it. stderr={r.stderr[:300]}"
    )
    if not r.stdout.strip():
        return "defer", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


# ---------------------------------------------------------------------------
# REFUSING CASES FIRST
# ---------------------------------------------------------------------------

def test_g2_3_gh_api_graphql_is_the_one_api_form_that_must_not_pass(guard):
    """G2.3 — `gh api` is permitted, but `gh api graphql` is excepted back into deny.

    GraphQL is prohibited for non-determinism, not for authentication: four recorded silent
    no-ops (F21, F21-3), a channel that reports success without effect. The ground is deliberately
    session-independent -- an auth-based ground was measured false on 2026-08-26.
    It is the single carve-out inside the permitted prefix, and an allowlist that matched on
    `gh api` alone would let it through.
    """
    decision, reason = decide(guard, 'gh api graphql -f query=\'{viewer{login}}\'')
    assert decision == "deny", f"gh api graphql must be refused, got {decision}"
    assert "REST" in reason or "rest" in reason, (
        "G3.3: the refusal must carry the working replacement, not merely refuse"
    )


@pytest.mark.parametrize("cmd", [
    "gh pr list",
    "gh issue list",
    "gh run list",
    "gh workflow view ci.yml",
])
def test_g2_4_unlisted_subcommands_are_refused_by_default(guard, cmd):
    """G2.4 — the inversion itself.

    `gh run` and `gh workflow` are absent from the Layer-1 enumeration and run today; they are
    the red this change exists to turn green. An enumeration cures the forms already known to
    have failed and permits every subcommand GitHub ships next — that is enumeration drift, and
    curing it with a longer enumeration reproduces the disease.
    """
    decision, _ = decide(guard, cmd)
    assert decision == "deny", f"unlisted form {cmd!r} must be refused by default, got {decision}"


def test_g2_5_absolute_path_invocation_is_refused(guard):
    """G2.5 — a matcher anchored on the bare token `gh` is defeated by an absolute path."""
    decision, _ = decide(guard, "/usr/bin/gh pr list")
    assert decision == "deny", "absolute-path invocation must not evade the matcher"


def test_g2_6_leading_env_assignment_is_refused(guard):
    """G2.6 — `VAR=x gh …` puts an assignment before the command word."""
    decision, _ = decide(guard, "GH_TOKEN=x gh pr list")
    assert decision == "deny", "a leading env assignment must not evade the matcher"


def test_g2_7_compound_command_is_refused(guard):
    """G2.7 — the refused form as the second stage of a compound command.

    `cd /tmp && gh pr list` is one Bash tool call carrying two commands; a matcher that inspects
    only the first word sees `cd`.
    """
    decision, _ = decide(guard, "cd /tmp && gh pr list")
    assert decision == "deny", "a refused form after `&&` must still be refused"


# ---------------------------------------------------------------------------
# PERMITTED CASES
# ---------------------------------------------------------------------------

def test_g2_1_gh_api_rest_path_is_allowed(guard):
    """G2.1 — the form the estate's own capability instruments depend on.

    `gh_read.py:112` runs `["gh","api",path]`. A policy that refused it would refuse the
    measurement it relies on, which the spec forbids: the permitted set SHALL include any form
    on which the estate's own instruments depend.
    """
    decision, _ = decide(guard, "gh api repos/o/r/pulls")
    assert decision != "deny", "gh api with a REST path must not be refused"


def test_g2_2_gh_auth_status_is_allowed(guard):
    """G2.2 — `pr-flow.py:1419` runs `["gh","auth","status"]` to measure the credential layer."""
    decision, _ = decide(guard, "gh auth status")
    assert decision != "deny", "gh auth status must not be refused"


def test_g2_8_the_token_as_data_is_not_a_command(guard):
    """G2.8 — a guard that refuses prose about itself is unusable.

    The agent must be able to write, quote and explain a refused form without triggering a
    refusal. Execution is governed; suggestion is not.
    """
    decision, _ = decide(guard, 'echo "run gh pr list"')
    assert decision != "deny", "a refused form quoted as data must not trigger a refusal"


def test_g2_9_unrelated_commands_fall_through_untouched(guard):
    """G2.9 — this guard must not perturb INV-14 enforcement.

    `git push` is the outbound guard's business, not this one's. This guard must DEFER — emit
    nothing at all — so the outbound guard's decision on the same command is byte-identical to
    its pre-change behaviour. Emitting `allow` here would not be neutral: an allow is a decision,
    and this change must not introduce one on the exfil path.
    """
    decision, _ = decide(guard, "git push origin main")
    assert decision == "defer", (
        f"expected no output at all for an unrelated command, got {decision!r} — this guard must "
        "not express an opinion on the outbound guard's subject matter"
    )


# ---------------------------------------------------------------------------
# FAILURE MODE
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", ["", "not json", "{}", '{"tool_input":{}}'])
def test_g2_10_malformed_input_fails_open_and_says_so(guard, raw):
    """G2.10 — malformed or empty stdin exits 0 with no output.

    This FAILS OPEN, deliberately and explicitly. A hook that crashes exits non-zero and the
    harness defers anyway, so failing closed is not available to a hook at all — which is the
    documented reason the enumerated Layer-1 `permissions.deny` entries are RETAINED alongside
    this guard rather than replaced by it. Their failure direction is opposite: harness-enforced,
    needing no process to start.
    """
    decision, _ = decide(guard, None, raw=raw)
    assert decision == "defer", "malformed input must produce no decision, not a refusal"


def test_g2_11_uncaught_evasions_are_recorded_not_claimed():
    """G2.11 — the cases this matcher provably does NOT catch.

    Recorded as an assertion about the DOCUMENTATION, not as a behavioural test: the guard is a
    text matcher, and these defeat any text matcher. Writing them as xfail behavioural tests
    would require executing an evasion of a live control, which the standing guard-denial rule
    makes operator-instructed only.

    A control whose limits are undocumented gets trusted past them, so the note must name them:

      - variable indirection   `C=gh; $C pr list`
      - shell alias / function `alias g=gh; g pr list`
      - encoded execution      `echo Z2ggcHIgbGlzdA== | base64 -d | sh`
      - subprocess invocation  any tool that calls `gh` internally (measured in G0.2: EVERY
                               fleet call site is one, and the hook sees none of them)

    The threat model is the agent FORGETTING, not EVADING — a tripwire for a cooperating agent.
    """
    assert NOTE.exists(), (
        f"{NOTE.relative_to(REPO)} does not exist — RED state, task G3.1 builds it"
    )
    text = NOTE.read_text(encoding="utf-8").lower()
    for limit in ("indirection", "alias", "base64", "subprocess"):
        assert limit in text, (
            f"the note must name '{limit}' among the evasions it does not catch; a control whose "
            "limits are undocumented gets trusted past them"
        )
