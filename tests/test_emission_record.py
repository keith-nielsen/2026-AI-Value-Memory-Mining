# SPDX-License-Identifier: Apache-2.0
"""Tests for the driver-emission downgrade in the outbound guard.

Ordered so the FALL-THROUGH cases come first. The safety property of this change is the
invariant "the record may only downgrade an ASK to an allow, never create a refusal" — a
suite that proved only the happy path would prove nothing about it, and would pass against
an implementation that denied everything it did not recognise.

The guard is exercised as a REAL SUBPROCESS against its rendered form, the way the harness
runs it — not by importing functions out of the note. The note is the source of truth
(INV-3), so the rendered artifact is extracted here rather than read from `.claude/hooks/`.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template/99-Operations/scripts/outbound-publish-guard-script.md"


@pytest.fixture(scope="module")
def guard(tmp_path_factory):
    """Extract the python block from the meta-script note — the same body `render` deploys."""
    text = NOTE.read_text(encoding="utf-8")
    m = re.search(r"^## Implementation\s*\n```python\n(.*?)^```", text, re.S | re.M)
    assert m, "no python implementation block in the guard note"
    p = tmp_path_factory.mktemp("guard") / "outbound-publish-guard.py"
    p.write_text(m.group(1), encoding="utf-8")
    return p


def run_guard(guard, cmd, cwd, vault=""):
    env = dict(os.environ, VAULT_ROOT=vault, CLAUDE_PROJECT_DIR=vault)
    # The guard runs with the SESSION's working directory, and `os.path.abspath` resolves an
    # unresolvable redirect against it — that is precisely why the 2026-08-16 command landed inside
    # the vault. A harness that leaves the subprocess cwd unset does not reproduce that geometry.
    r = subprocess.run([sys.executable, str(guard)], input=json.dumps(
        {"tool_name": "Bash", "cwd": str(cwd), "tool_input": {"command": cmd}}),
        capture_output=True, text=True, env=env, cwd=str(cwd))
    if not r.stdout.strip():
        return "defer", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


@pytest.fixture
def repo(tmp_path):
    d = tmp_path / "governed"
    (d / ".git" / "pr-flow").mkdir(parents=True)
    (d / ".git" / "HEAD").write_text("ref: refs/heads/feat/x\n")
    return d


def put_record(repo, command, branch="feat/x", step="pushed", ttl=3600):
    (repo / ".git" / "pr-flow" / "emitted.json").write_text(json.dumps({
        "command": command, "step": step, "branch": branch,
        "repo": str(repo), "expires": int(time.time()) + ttl}))


PUSH = "git -C {} push -u origin feat/x"


# --------------------------------------------------------------------------
# THE INVARIANT: every failure mode falls through to ASK. None of them denies.
# --------------------------------------------------------------------------

def test_no_record_asks_and_does_not_deny(guard, repo):
    d, _ = run_guard(guard, PUSH.format(repo), repo)
    assert d == "ask"


def test_expired_record_asks(guard, repo):
    cmd = PUSH.format(repo)
    put_record(repo, cmd, ttl=-1)
    d, _ = run_guard(guard, cmd, repo)
    assert d == "ask"


def test_record_for_another_branch_asks(guard, repo):
    cmd = PUSH.format(repo)
    put_record(repo, cmd, branch="some/other-branch")
    d, _ = run_guard(guard, cmd, repo)
    assert d == "ask"


def test_corrupt_record_asks(guard, repo):
    cmd = PUSH.format(repo)
    (repo / ".git" / "pr-flow" / "emitted.json").write_text("{not json at all")
    d, _ = run_guard(guard, cmd, repo)
    assert d == "ask"


def test_record_that_is_not_an_object_asks(guard, repo):
    cmd = PUSH.format(repo)
    (repo / ".git" / "pr-flow" / "emitted.json").write_text('["a list"]')
    d, _ = run_guard(guard, cmd, repo)
    assert d == "ask"


def test_ungoverned_repo_behaviour_is_unchanged(guard, tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    d, _ = run_guard(guard, PUSH.format(other), other)
    assert d == "ask"


def test_the_record_cannot_unlock_the_vault(guard, tmp_path):
    """The downgrade is scoped. A valid-looking record must NOT open INV-14."""
    vault = tmp_path / "Vault"
    (vault / ".git" / "pr-flow").mkdir(parents=True)
    (vault / ".git" / "HEAD").write_text("ref: refs/heads/feat/x\n")
    cmd = PUSH.format(vault)
    put_record(vault, cmd)
    d, reason = run_guard(guard, cmd, vault, vault=str(vault))
    assert d == "deny", f"a record unlocked the vault deny: {reason}"


# --------------------------------------------------------------------------
# The mangled-retype case this change exists for
# --------------------------------------------------------------------------

def test_mangled_command_asks_and_names_the_difference(guard, repo):
    """The real 2026-08-16 shape: the emitted command wrapped in a shell variable."""
    emitted = PUSH.format(repo)
    put_record(repo, emitted)
    mangled = f'R={repo}; cd "$R"; timeout 180 git -C "$R" push -u origin feat/x'
    d, reason = run_guard(guard, mangled, repo)
    assert d == "ask"
    assert "NOT THE COMMAND THE DRIVER EMITTED" in reason
    assert emitted in reason and mangled in reason


def test_verbatim_command_is_allowed_and_named_as_a_match(guard, repo):
    cmd = PUSH.format(repo)
    put_record(repo, cmd, step="pushed")
    d, reason = run_guard(guard, cmd, repo)
    assert d == "allow"
    assert "pushed" in reason
    # Requirement 2: a match is reported as a match, never as an authorisation.
    assert "not an authorisation" in reason.lower()
    assert "authorised" not in reason.lower().replace("not an authorisation", "")


def test_vault_deny_explains_an_unresolved_redirect(guard, tmp_path):
    """Reproduces 2026-08-16 exactly: the denial was correct and completely opaque.

    `git -C "$R" push` — the guard reads raw text, `"$R"` resolves to nothing, the redirect is
    ignored, and the target falls back to cwd (the vault). Previously the reader saw only "you are
    pushing the vault" while believing they had targeted a sibling repo. The deny still stands; it
    now says WHY.
    """
    vault = tmp_path / "Vault"
    vault.mkdir()
    mangled = 'R=/home/x/repo; cd "$R"; timeout 180 git -C "$R" push -u origin feat/x'
    d, reason = run_guard(guard, mangled, vault, vault=str(vault))
    assert d == "deny"
    assert "THE REDIRECT IN THIS COMMAND DID NOT RESOLVE" in reason
    assert "no such directory" in reason


def test_a_resolvable_redirect_adds_no_hint(guard, tmp_path):
    """The hint must not fire on a well-formed command — noise on correct input trains readers
    to skim the denial, which is how the real cause gets missed next time."""
    vault = tmp_path / "Vault"
    vault.mkdir()
    d, reason = run_guard(guard, f"git -C {vault} push -u origin main", vault, vault=str(vault))
    assert d == "deny"
    assert "DID NOT RESOLVE" not in reason


def test_non_outward_command_is_untouched(guard, repo):
    d, _ = run_guard(guard, "git -C %s status" % repo, repo)
    assert d == "defer"
