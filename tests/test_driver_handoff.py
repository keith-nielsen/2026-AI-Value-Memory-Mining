# SPDX-License-Identifier: Apache-2.0
"""The shared operator-handoff module (item 41): the saved-plan skeleton, the emission record, the
history suffix, and the copy-whole relay block — the machinery pr-flow.py and ship-release.py both
import so the format the outbound guard and the relay-conformance Stop hook compare against has one
source, not a fork (the class-9 defect the extraction closes).
"""
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import driver_handoff as dh  # noqa: E402


def test_write_saved_plan_wraps_the_callers_verify_tail(tmp_path):
    """The skeleton is generic; the driver supplies the VERIFY tail. The writer must emit the
    expiry guard, the branch guard, the `cd`, the mutation, and then the caller's lines verbatim."""
    verify = ["", "# VERIFY — driver-specific", 'echo "landed"', "some-driver --re-run x"]
    path = dh.write_saved_plan(str(tmp_path), "tag", "git -C /r push origin refs/tags/v1",
                               approve=None, branch="main",
                               assert_lines=None, verify_lines=verify)
    text = pathlib.Path(path).read_text()
    assert "set -euo pipefail" in text
    assert "date +%s" in text and "EXPIRED" in text            # expiry guard
    assert '_want=main' in text and "branch --show-current" in text   # branch guard
    assert "git -C /r push origin refs/tags/v1" in text        # the mutation
    # the caller's tail appears AFTER the mutation, verbatim
    assert "# VERIFY — driver-specific" in text
    assert "some-driver --re-run x" in text
    assert text.index("push origin refs/tags/v1") < text.index("some-driver --re-run x")


def test_write_saved_plan_places_assert_lines_before_the_mutation(tmp_path):
    """A precondition assertion is worthless after the mutation; `set -e` only stops what precedes."""
    path = dh.write_saved_plan(str(tmp_path), "merge", "gh api -X PUT /x", approve="merges #7",
                               branch="feat/x",
                               assert_lines=["python3 /r/tools/pr-flow.py --assert-preconditions pr=7"],
                               verify_lines=["echo done"])
    text = pathlib.Path(path).read_text()
    assert "--assert-preconditions pr=7" in text
    assert text.index("--assert-preconditions") < text.index("gh api -X PUT /x")
    # with an assertion the header takes the consent wording, not the no-assertion note
    assert "Consent was given for the state asserted below" in text
    assert "no live-state assertion is made here" not in text


def test_write_saved_plan_requires_a_branch(tmp_path):
    """A guard that is silently absent is worse than none — the file still reads as safe."""
    with pytest.raises(ValueError):
        dh.write_saved_plan(str(tmp_path), "tag", "git -C /r push origin refs/tags/v1",
                            approve=None, branch="", verify_lines=["echo x"])


def test_emit_operator_handoff_writes_the_sidecar_byte_identical_to_the_block(tmp_path):
    """The copy-whole block the agent relays and the sidecar the Stop hook checks are ONE string."""
    (tmp_path / ".git" / "pr-flow").mkdir(parents=True)
    path = tmp_path / ".git" / "pr-flow" / "next.sh"
    lines = []
    relay = dh.emit_operator_handoff(str(tmp_path), "tag", str(path),
                                     suffix="   # release-v1 step:tag -> v1",
                                     has_assertion=False, out=lines.append)
    out = "\n".join(lines)
    assert "START COPY" in out and "END COPY" in out
    assert relay in out
    assert relay == f"bash {path}   # release-v1 step:tag -> v1"
    sidecar = dh.relay_line_path(str(tmp_path)).read_text().strip()
    assert sidecar == relay, "the sidecar must equal the relayed block line byte-for-byte"


def test_plan_history_suffix_takes_an_explicit_target(tmp_path):
    """ship-release has no pull request; it names the version as the target instead of `new PR`."""
    assert dh.plan_history_suffix("tag", target="v0.1.55") == "   # change step:tag -> v0.1.55"
    # and the PR path still works when no target is given
    assert dh.plan_history_suffix("merge", pr_number=9) == "   # change step:merge -> PR #9"


def test_write_emission_record_roundtrips(tmp_path):
    import json
    dh.write_emission_record(str(tmp_path), "tag", "git -C /r push origin refs/tags/v1", "main")
    rec = json.loads(dh.emission_record_path(str(tmp_path)).read_text())
    assert rec["command"] == "git -C /r push origin refs/tags/v1"
    assert rec["step"] == "tag" and rec["branch"] == "main" and rec["repo"] == str(tmp_path)


def test_discard_removes_both_the_plan_and_the_record(tmp_path):
    dh.write_saved_plan(str(tmp_path), "tag", "git -C /r push", approve=None, branch="main",
                        verify_lines=["echo x"])
    dh.write_emission_record(str(tmp_path), "tag", "git -C /r push", "main")
    assert dh.saved_plan_path(str(tmp_path)).exists()
    assert dh.emission_record_path(str(tmp_path)).exists()
    assert dh.discard_saved_plan(str(tmp_path))
    assert not dh.saved_plan_path(str(tmp_path)).exists()
    assert not dh.emission_record_path(str(tmp_path)).exists()
