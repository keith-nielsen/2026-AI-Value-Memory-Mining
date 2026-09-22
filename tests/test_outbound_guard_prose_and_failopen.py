# SPDX-License-Identifier: Apache-2.0
"""Item 33 — the outbound guard must judge COMMANDS, not prose, and must never fail OPEN.

Four measured defects, each tested red-first against the pre-change guard:

  D1  a commit message that NAMES an outward command must not raise the rail.
  D2  the mandated `source <config>; cd <path> && …` idiom must resolve the effective target.
  D3  a vault-outward deny must explain the common "no redirect recognised" case.
  D4  an unset environment must NOT fail open — a vault is identified by its marker.

THE NOTE IS THE ORACLE (INV-3): the guard is extracted from its literate note and run as a real
subprocess, so the hook's own exit behaviour stays observable. Crucially, every test asserts a
TRUE-POSITIVE is preserved alongside the false-positive it removes — a guard made permissive is the
silent-success class this queue exists to catch.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template/99-Operations/scripts/outbound-publish-guard-script.md"
BLOCK = re.compile(r"^## Implementation\s*\n```python\n(.*?)^```", re.S | re.M)


@pytest.fixture(scope="module")
def guard(tmp_path_factory):
    m = BLOCK.search(NOTE.read_text(encoding="utf-8"))
    assert m, f"no python implementation block in {NOTE.name}"
    p = tmp_path_factory.mktemp("guard33") / "outbound-publish-guard.py"
    p.write_text(m.group(1), encoding="utf-8")
    return p


def decide(guard_path, cmd, *, cwd="/home/someone/repo", vault="/home/someone/Vault"):
    """-> (decision, reason). 'defer' = exit 0, no output. vault='' leaves VAULT_ROOT unset."""
    env = dict(os.environ)
    if vault:
        env["VAULT_ROOT"] = vault
    else:
        env.pop("VAULT_ROOT", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run([sys.executable, str(guard_path)],
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd},
                                         "cwd": cwd}),
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, f"a hook must exit 0 even when refusing; got {r.returncode}"
    if not r.stdout.strip():
        return "defer", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


VAULT = "/home/someone/Vault"

# --- D1: prose in a -m/-F body must not trigger the rail -----------------------------------------

def test_d1_a_commit_message_naming_a_publish_does_not_trip_the_guard(guard):
    """The measured false positive: a purely local commit whose message documents a publish call was
    hard-denied. The tokens live in the message, which is data — the guard must stand aside."""
    cmd = 'git commit -m "docs: converted the gh release create call to REST"'
    decision, _ = decide(guard, cmd, cwd=VAULT, vault=VAULT)
    assert decision == "defer", f"a local commit was gated on its message text: {decision}"


def test_d1_an_F_body_file_message_does_not_trip_the_guard(guard):
    cmd = 'git commit -F .git/COMMIT_MSG'  # the body file could name anything; it is data
    decision, _ = decide(guard, cmd, cwd=VAULT, vault=VAULT)
    assert decision == "defer", decision


def test_d1_true_positive_a_real_publish_with_a_message_is_still_denied(guard):
    """Stripping the MESSAGE must not hide the COMMAND. A real release-create carrying a --notes
    message is still a publish (—notes is not a stripped flag), and a real push next to a stripped
    -m message still pushes."""
    d1, _ = decide(guard, 'gh release create v1.2.3 --notes "shipped it"', cwd=VAULT, vault=VAULT)
    assert d1 == "deny", "a real release-create was hidden by message stripping"
    d2, _ = decide(guard, 'git commit -m "note: gh release create" && git push origin main',
                   cwd=VAULT, vault=VAULT)
    assert d2 == "deny", "a real vault push next to a stripped message slipped through"


# --- D2: the mandated source; cd idiom resolves the effective target -----------------------------

def test_d2_source_then_cd_resolves_to_the_sibling_not_the_cwd(guard):
    """`source cfg; cd $SIBLING && git push` — the bootstrap idiom — has a non-leading cd. It was
    mis-attributed to cwd (the vault) and hard-denied. It must resolve to the sibling → not a
    vault-outward DENY."""
    # The mandated idiom sources config.env RELATIVE (CLAUDE.md: `source 99-Operations/config.env`),
    # so the vault abspath never appears as an operand — only the non-leading cd needs recognising.
    cmd = "source 99-Operations/config.env; cd /home/someone/repo/fw && git push origin br"
    decision, _ = decide(guard, cmd, cwd=VAULT, vault=VAULT)
    assert decision != "deny", f"the sibling-targeted idiom was hard-denied as vault-outward: {decision}"


def test_d2_true_positive_source_then_cd_into_the_vault_is_still_denied(guard):
    """The relaxation must not open the vault: the same idiom pointed AT the vault is still denied."""
    cmd = "source /x/config.env; cd /home/someone/Vault && git push origin main"
    decision, _ = decide(guard, cmd, cwd="/home/someone/repo", vault=VAULT)
    assert decision == "deny", "source; cd INTO the vault must still be hard-denied"


# --- D3: a vault-outward deny explains the no-redirect case --------------------------------------

def test_d3_a_no_redirect_deny_names_its_cause(guard):
    decision, reason = decide(guard, "git push origin main", cwd=VAULT, vault=VAULT)
    assert decision == "deny"
    assert "NO REDIRECT" in reason.upper(), f"the deny did not explain the cwd fallback: {reason[:200]}"


# --- D4: an unset environment must not fail open ------------------------------------------------

def test_d4_env_unset_but_marked_vault_is_still_denied(guard, tmp_path):
    """The serious one: with VAULT_ROOT unset the guard used to return False and fail open. It must
    instead identify the vault by its marker (99-Operations/config.env) at the effective target."""
    v = tmp_path / "vault"
    (v / "99-Operations").mkdir(parents=True)
    (v / "99-Operations" / "config.env").write_text("export VAULT_ROOT=x\n")
    decision, _ = decide(guard, "git push origin main", cwd=str(v), vault="")  # env unset
    assert decision == "deny", "env unset + a marked vault must NOT fail open"


def test_d4_env_unset_and_no_marker_stays_inert(guard, tmp_path):
    """A plain repo (no marker) with the env unset is not a vault — the vault-deny stays inert; the
    outward ASK still applies (so it is not silently allowed either)."""
    d = tmp_path / "plain-repo"
    (d / ".git").mkdir(parents=True)
    decision, _ = decide(guard, "git push origin main", cwd=str(d), vault="")
    assert decision != "deny", "a non-vault tree was hard-denied as vault-outward"
    assert decision == "ask", f"a non-vault outward push should still ASK, got {decision}"


def test_d4_env_set_path_is_unchanged(guard):
    """The light-touch guarantee: when VAULT_ROOT is set (every normal session) the marker branch is
    unreachable, so the env path behaves exactly as before — a vault push denies, a sibling asks."""
    assert decide(guard, "git push origin main", cwd=VAULT, vault=VAULT)[0] == "deny"
    assert decide(guard, "git -C /home/someone/repo/fw push origin br", cwd=VAULT, vault=VAULT)[0] == "ask"
