# SPDX-License-Identifier: Apache-2.0
"""The saved-plan hand-off carries a shell-history annotation.

Every saved-plan invocation is byte-identical — `bash <repo>/.git/pr-flow/next.sh` — so
`history | grep next.sh` is a wall of indistinguishable lines. The operator had been appending the
annotation by hand at the moment of a mutation, which is the worst possible time to be remembering
anything. The driver holds every field it needs.
"""
import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("pr_flow_suffix", REPO / "tools" / "pr-flow.py")
pf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pf)


def test_suffix_matches_the_operators_established_convention():
    """`# <mnemonic> step:<step> -> <target>`, read off the operator's own shell history."""
    assert pf.plan_history_suffix("merge", "/x/.git/pr-flow/body-preflight.md", 80) == \
        "   # preflight step:merge -> PR #80"


def test_pr_step_has_no_pr_number_yet():
    assert pf.plan_history_suffix("pr", "/x/body-v0.1.44.md", None) == \
        "   # v0.1.44 step:pr -> new PR"


def test_mnemonic_distinguishes_two_changes_on_the_same_topic():
    """`const-truth` and `const-diff-gate` were both constitution work. If the mnemonic collapsed
    them the history would be unnavigable exactly where it matters most."""
    a = pf.plan_history_suffix("merge", "/x/body-const-truth.md", 85)
    b = pf.plan_history_suffix("merge", "/x/body-const-diff-gate.md", 89)
    assert a != b
    assert "const-truth" in a and "const-diff-gate" in b


def test_a_non_body_prefixed_stem_is_used_verbatim():
    assert "release-v0148" in pf.plan_history_suffix("pr", "/x/release-v0148.md", None)


def test_no_body_file_still_produces_a_usable_annotation():
    """A missing mnemonic must not produce a bare `#` — the annotation exists to disambiguate."""
    s = pf.plan_history_suffix("merge", None, 91)
    assert s.strip() == "# change step:merge -> PR #91"


def test_the_suffix_is_a_shell_comment():
    """It is appended to a runnable command line: it MUST start a comment, or it becomes arguments."""
    for args in [("merge", "/x/body-a.md", 1), ("pr", None, None)]:
        assert pf.plan_history_suffix(*args).lstrip().startswith("#")
