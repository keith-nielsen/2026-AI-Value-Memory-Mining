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


# --- the method split (change `prefer-rest-over-graphql-forms` §3) -------------------------------
#
# WRITTEN RED-FIRST, 2026-09-19. `gh api` was a blanket permit: every case in this block passed the
# guard when these tests were written, including the two that matter most —
#   * `gh api -X DELETE repos/o/r`, which deletes a repository and was permitted BY FORM; and
#   * `gh api -X POST graphql`, which is the ONLY shape a GraphQL mutation ever takes.
#
# The second was a measured hole in the shipped guard, not a new requirement. `positional` was built
# as "every token not starting with `-`", so the VALUE of `-X` occupied the slot the graphql check
# read. `gh api graphql` was refused; `gh api -X POST graphql` deferred. The estate's four recorded
# silent no-ops were all mutations, so the form actually capable of causing one was the form that
# got through. Layer 1's `Bash(gh api graphql:*)` prefix rule does not cover it either.

WRITE_REFUSALS = [
    ("gh api -X DELETE repos/o/r", "a repository delete, permitted by form before the split"),
    ("gh api -X DELETE /repos/o/r", "same, rooted path"),
    ("gh api --method DELETE repos/o/r/hooks/12", "long-form flag, unsanctioned endpoint"),
    ("gh api -X PATCH /repos/o/r/actions/permissions", "unsanctioned write"),
    ("gh api -X POST /repos/o/r/actions/runners/registration-token", "unsanctioned write"),
]


@pytest.mark.parametrize("cmd,why", WRITE_REFUSALS)
def test_a_write_to_an_unsanctioned_endpoint_is_refused(guard, cmd, why):
    """The safety property: an endpoint absent from the sanctioned set is refused BY DEFAULT."""
    decision, reason = decide(guard, cmd)
    assert decision == "deny", f"{why}: {cmd!r} was permitted"
    assert "endpoint" in reason.lower() or "sanctioned" in reason.lower(), (
        f"the refusal must teach which rule refused it, got: {reason[:160]}")


@pytest.mark.parametrize("cmd", [
    "gh api -X POST graphql -f query=x",
    "gh api --method POST graphql -f query=x",
    "gh api --method=POST graphql -f query=x",
    "gh api -XPOST graphql -f query=x",
])
def test_graphql_is_refused_even_when_a_method_flag_precedes_it(guard, cmd):
    """MEASURED HOLE, 2026-09-19: all four of these DEFERRED before the split.

    A GraphQL mutation is always a POST, so the refusal that existed covered the one graphql shape
    least able to cause the silent no-op it was written for.
    """
    decision, reason = decide(guard, cmd)
    assert decision == "deny", f"{cmd!r} reached GraphQL unrefused"
    assert "graphql" in reason.lower(), f"refused for the wrong reason: {reason[:160]}"


@pytest.mark.parametrize("cmd", [
    "gh api -X PUT /repos/o/r/rulesets/19666243 --input p.json",
    "gh api -X PATCH repos/o/r/rulesets/19666225",
    "gh api -X DELETE /repos/o/r/rulesets/19666243",
])
def test_a_deliberately_excluded_endpoint_says_so(guard, cmd):
    """An exclusion by DECISION must not read as an oversight.

    A bare 'not permitted' invites the next reader to add the row; the ruleset control plane is out
    by a recorded decision (docs §2b), and the refusal has to say which.
    """
    decision, reason = decide(guard, cmd)
    assert decision == "deny", f"{cmd!r} was permitted against the control plane"
    assert "excluded" in reason.lower() and "decision" in reason.lower(), (
        f"the refusal must name the exclusion as deliberate, got: {reason[:200]}")


@pytest.mark.parametrize("cmd", [
    # reads: unconstrained, and the fleet depends on them
    "gh api repos/o/r/pulls/51",
    "gh api /repos/o/r/actions/runs?head_sha=abc",
    "gh api -X GET repos/o/r/rulesets",
    "gh api --method GET /repos/o/r/rulesets/19666243",
    "gh auth status",
    # sanctioned writes, in the shapes the driver actually emits
    "gh api -X POST repos/o/r/pulls -f title=t -f head=h -f base=main -F body=@b.md",
    "gh api -X PATCH /repos/o/r/pulls/51 -f base=main",
    "gh api -X PUT /repos/o/r/pulls/51/merge -f merge_method=merge -f sha=abc",
    "gh api -X POST repos/o/r/releases -f tag_name=v1.2.3",
    "gh api -X DELETE /repos/o/r/releases/12345",
    "gh api -X POST repos/o/r/labels -f name=openspec-canary",
    "gh api -X POST repos/o/r/issues -f title=t -f 'labels[]=openspec-canary'",
    # a placeholder slug: the shipping detector flattens an f-string's interpolations to one token,
    # so the guard must accept a one-segment slug or it refuses the estate's own emissions
    "gh api -X PATCH /repos/X/pulls/X -f base=X",
    "gh api -X PUT /repos/X/pulls/X/merge -f sha=X",
])
def test_permitted_forms_still_pass(guard, cmd):
    """Tightening must not break the fleet: every form in real use is asserted to survive it."""
    decision, reason = decide(guard, cmd)
    assert decision == "defer", f"{cmd!r} was refused: {reason[:200]}"
