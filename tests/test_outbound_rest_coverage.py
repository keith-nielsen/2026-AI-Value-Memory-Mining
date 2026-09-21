# SPDX-License-Identifier: Apache-2.0
"""The INV-14 outbound rail must see a publish in its REST spelling, not only its subcommand one.

WRITTEN RED-FIRST, 2026-09-19, against a measured gap rather than a suspected one:

    gh release create v1.2.3 --verify-tag --notes-file n.md   -> ask   (the full banner)
    gh api -X POST repos/o/r/releases -f tag_name=v1.2.3      -> SILENCE, exit 0

`OUTWARD` and `PUBLISH` keyed on the literal token `gh release (create|edit|upload)`, so converting
the release path to REST — which the change `prefer-rest-over-graphql-forms` §4.4 does — would have
DELETED an INV-14 ask on the one path that publishes artifacts to the world. Publishing is a
property of the ENDPOINT, not of the command's spelling.

These are barium lunches B8 and B9 from the vault battery
(`30-Sites/estate-gap-reconciliation/rest-conversion-test-battery.md`), which pre-registered both
before either was built:

  B9  the REST form must be asked — RED before 3a.1, green after.
  B8  the subcommand form must STILL be asked — and *"a B9 that is green on both sides proves
      nothing"*, so B8 is proved BY MUTATION rather than by observing green twice. A test that only
      ever sees the post-change world cannot show the original clause survived the rewrite, and
      losing an alternation is exactly what widening a regex does wrong.

THE NOTE IS THE ORACLE. The guard is extracted from its literate note (INV-3) and run as a real
subprocess, the way the harness runs it — never imported, so the hook's own fail-open path stays
observable.
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

SUBCOMMAND_PUBLISH = "gh release create v1.2.3 --verify-tag --notes-file n.md"
REST_PUBLISH = "gh api -X POST repos/o/r/releases -f tag_name=v1.2.3"


def _extract(text, dest):
    m = BLOCK.search(text)
    assert m, f"no python implementation block in {NOTE.name}"
    dest.write_text(m.group(1), encoding="utf-8")
    return dest


@pytest.fixture(scope="module")
def guard(tmp_path_factory):
    assert NOTE.exists(), f"{NOTE.relative_to(REPO)} is missing; the rail has no source of truth"
    return _extract(NOTE.read_text(encoding="utf-8"),
                    tmp_path_factory.mktemp("outbound") / "outbound-publish-guard.py")


def decide(guard_path, cmd, *, cwd="/home/someone/repo", vault="/home/someone/Vault"):
    """-> (decision, reason). 'defer' = exit 0 with no output: the rail stands aside.

    `VAULT_ROOT` and `cwd` are passed explicitly. The guard's vault decision keys on both, and a
    test that inherited the real ones would pass or fail depending on where it was run from.
    """
    env = dict(os.environ)
    env["VAULT_ROOT"] = vault
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run(
        [sys.executable, str(guard_path)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}),
        capture_output=True, text=True, env=env)
    assert r.returncode == 0, (
        f"guard exited {r.returncode}; a hook must exit 0 even when refusing. {r.stderr[:300]}")
    if not r.stdout.strip():
        return "defer", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


# --- B9: the new coverage -----------------------------------------------------------------------

@pytest.mark.parametrize("cmd", [
    REST_PUBLISH,
    "gh api --method POST repos/o/r/releases -f tag_name=v1.2.3",
    "gh api -X POST /repos/o/r/releases -F body=@notes.md",
    "gh api -X DELETE /repos/o/r/releases/12345",
    "gh api -XDELETE repos/o/r/releases/12345",
])
def test_b9_a_rest_publish_raises_the_outbound_ask(guard, cmd):
    """RED before 3a.1: every one of these returned silence, exit 0."""
    decision, reason = decide(guard, cmd)
    assert decision == "ask", f"{cmd!r} published without raising the INV-14 ask"
    assert "OUTBOUND" in reason, f"asked, but not with the outbound banner: {reason[:160]}"


def test_an_asset_upload_host_is_outward(guard):
    """Release assets do not go to the API host. A rail that watches only api.github.com misses them."""
    decision, _ = decide(guard, "curl -X POST https://uploads.github.com/repos/o/r/releases/1/assets")
    assert decision == "ask"


# --- B8: the regression half, proved by MUTATION ------------------------------------------------

def test_b8_the_subcommand_form_still_raises_the_ask(guard):
    """Necessary but NOT sufficient on its own — see the mutation test below."""
    decision, reason = decide(guard, SUBCOMMAND_PUBLISH)
    assert decision == "ask", "the original subcommand clause was lost in the rewrite"
    assert "OUTBOUND" in reason


def test_b8_fails_against_a_guard_missing_the_release_clause(tmp_path):
    """THE MUTATION. Delete the clause from a COPY and require the B8 assertion to fail.

    This is what makes B8's green mean something. Observing green twice asserts history; this
    demonstrates the assertion can fail, which is the only evidence that it discriminates.

    ⚠ Nothing is deleted from the shipped guard. The mutant lives in `tmp_path`; the note, the
    rendered hooks and the live rail are untouched.
    """
    source = BLOCK.search(NOTE.read_text(encoding="utf-8")).group(1)
    clause = r"|\bgh\s+release\s+(create|edit|upload)\b"
    mutant_source, n = source.replace(clause, ""), source.count(clause)

    assert n == 2, (
        f"expected the release clause in both OUTWARD and PUBLISH, found {n} occurrence(s). "
        f"A clause that was renamed or reflowed means this test mutates NOTHING and silently "
        f"reverts to theatre — fix the literal, do not relax the count.")

    mutant = tmp_path / "mutant-guard.py"
    mutant.write_text(mutant_source, encoding="utf-8")

    decision, _ = decide(mutant, SUBCOMMAND_PUBLISH)
    assert decision == "defer", (
        "the mutant still asked on the subcommand form, so the B8 assertion above would pass "
        "even with the clause deleted — it is not testing what it claims to test")

    # ...and the REST clause must carry its own weight: the two are independently covered.
    decision, _ = decide(mutant, REST_PUBLISH)
    assert decision == "ask", (
        "with the subcommand clause removed the REST publish also stopped being asked — the two "
        "clauses are not independent, so one rewrite can silently take out both")


# --- no new noise -------------------------------------------------------------------------------

@pytest.mark.parametrize("cmd", [
    "gh api repos/o/r/releases",
    "gh api -X GET /repos/o/r/releases/12345",
    "gh api repos/o/r/releases/latest",
    "gh api -X POST repos/o/r/pulls -f title=t",
    "gh api -X PUT /repos/o/r/pulls/51/merge -f sha=abc",
    "gh auth status",
])
def test_reads_and_non_publishing_writes_are_not_asked(guard, cmd):
    """A banner that fires on everything teaches the operator to approve without reading it.

    Reads of the releases collection publish nothing, and a merge is not a publish — the outbound
    axis is about what LEAVES the machine, not about what mutates.
    """
    decision, reason = decide(guard, cmd)
    assert decision == "defer", f"{cmd!r} raised an outbound prompt it should not: {reason[:160]}"


# --- 3a.4: what the vault HARD DENY does to the REST form ---------------------------------------

VAULT = "/home/someone/Vault"


def test_the_rest_form_is_denied_from_a_vault_cwd_even_for_another_repo(guard):
    """DECIDED 2026-09-19: the asymmetry is ACCEPTED, and pinned here so it cannot drift silently.

    `_targets_vault()` early-outs on an explicit `-R owner/repo` ("names a GitHub repo, not the
    local vault working tree"), then falls back to the reported cwd. `gh api` carries the slug
    INLINE and has no `-R`, so it never reaches that early-out. Measured consequence:

        gh api -X POST repos/other/repo/releases   from a vault cwd -> DENY
        gh release create v1 -R other/repo         from a vault cwd -> ask

    The REST form is therefore STRICTER than the subcommand it replaces. Accepted rather than
    closed, because closing it means teaching `_targets_vault` to parse an inline slug — more code
    inside a control, to move a DENY to an ASK, for a case with no demand: releases are the
    operator's and run from their own terminal, where no hook exists at all. The estate does not
    loosen a control without a workflow that needs it.
    """
    decision, reason = decide(guard, "gh api -X POST repos/other/repo/releases -f tag_name=v1",
                              cwd=VAULT, vault=VAULT)
    assert decision == "deny", "the vault HARD DENY no longer covers the REST publish"
    assert "VAULT" in reason.upper()


def test_the_subcommand_form_with_an_explicit_repo_still_only_asks(guard):
    """The other half of the pinned pair — the `-R` early-out is unchanged by this work."""
    decision, _ = decide(guard, "gh release create v1 -R other/repo --notes x",
                         cwd=VAULT, vault=VAULT)
    assert decision == "ask"


def test_the_rest_form_asks_normally_outside_the_vault(guard):
    """Away from a vault cwd the REST publish is an ordinary outbound ask, not a denial."""
    decision, _ = decide(guard, "gh api -X POST repos/other/repo/releases -f tag_name=v1",
                         cwd="/home/someone/repo", vault=VAULT)
    assert decision == "ask"
