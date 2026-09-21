# SPDX-License-Identifier: Apache-2.0
"""Two defects found by running the v0.1.48 release ceremony, not by reading it.

1. `verify_invocation` stripped option NAMES but not their VALUES, so a saved plan written by a
   post-mutation verify tail carried orphaned positionals. The merge succeeded and the verification
   died with `unrecognized arguments`.
2. `ship-release.py` emitted cwd-dependent commands, so "run exactly this" was unrunnable from any
   directory but the repo — and a command that cannot be run as emitted can never match its own
   emission record (ADR-0043).
"""
import importlib.util
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("pr_flow_argv", REPO / "tools" / "pr-flow.py")
pr_flow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_flow)


# --------------------------------------------------------------------------
# 1. argv stripping must remove the option AND its value
# --------------------------------------------------------------------------

def test_strip_removes_the_option_value_not_just_the_name():
    """The exact PR #92 argv. Before the fix this returned [... 'pr', '/tmp/ev'] — two orphaned
    positionals that argparse rejected, AFTER the merge had already landed."""
    argv = ["--branch", "release/v0.1.48", "--base", "main", "--body-file", "/x/body.md",
            "--title", "release(v0.1.48)", "--after-mutation", "pr",
            "--mutation-evidence", "/tmp/pr-flow-evidence.MhF7Ba"]
    out = pr_flow._strip_opts_with_values(argv, ("--after-mutation", "--mutation-evidence"))
    assert out == ["--branch", "release/v0.1.48", "--base", "main", "--body-file", "/x/body.md",
                   "--title", "release(v0.1.48)"]
    assert "pr" not in out
    assert not any(a.startswith("/tmp/pr-flow-evidence") for a in out)


def test_strip_handles_the_equals_form():
    argv = ["--branch", "b", "--after-mutation=merge", "--mutation-evidence=/tmp/ev"]
    out = pr_flow._strip_opts_with_values(argv, ("--after-mutation", "--mutation-evidence"))
    assert out == ["--branch", "b"]


def test_strip_leaves_unrelated_arguments_alone():
    argv = ["--branch", "b", "--base", "main", "--title", "after-mutation is in this title"]
    out = pr_flow._strip_opts_with_values(argv, ("--after-mutation", "--mutation-evidence"))
    assert out == argv


def test_a_written_plan_tail_carries_no_orphaned_values(tmp_path, monkeypatch):
    """End-to-end on the real writer: the tail must be argparse-clean."""
    work = tmp_path / "repo"
    (work / ".git").mkdir(parents=True)
    monkeypatch.setattr(pr_flow, "INVOCATION", [
        "--branch", "release/v0.1.48", "--base", "main",
        "--after-mutation", "pr", "--mutation-evidence", "/tmp/pr-flow-evidence.XXXX"])
    tail = pr_flow.verify_invocation(str(work), step="merge")
    assert "--after-mutation merge" in tail
    assert "'pr'" not in tail and " pr " not in tail
    assert "pr-flow-evidence.XXXX" not in tail


# --------------------------------------------------------------------------
# 2. emitted commands must name their subject explicitly
# --------------------------------------------------------------------------

SHIP = (REPO / "tools" / "ship-release.py").read_text(encoding="utf-8")


def test_emitted_tag_push_carries_an_explicit_repo_target():
    """`git push origin refs/tags/X` depends on cwd; `git -C <root> push …` does not.

    An agent's shell resets its cwd between calls, so the cwd-dependent form could not be run
    verbatim — and modifying an emitted command is precisely what the outbound guard resolves
    differently. `pr-flow.py` has always emitted the `-C` form.
    """
    m = re.search(r'_emit_next\(f"git ([^"]*?)push origin refs/tags/', SHIP)
    assert m, "the tag-push emission is not in the expected form"
    assert "-C {root}" in m.group(1), f"tag push is still cwd-dependent: git {m.group(1)}push …"


PRFLOW = (REPO / "tools" / "pr-flow.py").read_text(encoding="utf-8")

# An emitted `gh` command names its repository one of two ways, and BOTH count as explicit:
#   * `-R <slug>` — the subcommand selector, still correct for any surviving subcommand form;
#   * `repos/<slug>/…` — a REST path, which carries the slug INLINE and so cannot fall back to cwd.
# The premise changed on 2026-09-19 when §4.3/§4.4 converted both emissions to `gh api`: `-R` is not
# a REST flag, so asserting it would now require the driver to emit a command GitHub rejects. The
# PROPERTY being defended is unchanged — an emitted command must be runnable verbatim from any
# directory — only the spelling that satisfies it has moved.
GH_NAMES_ITS_REPO = ("-R ", "{repo_arg}", "repos/{slug}/", "repos/{emit_slug}/")


def test_emitted_release_create_names_its_repo_inline():
    """The release emission is REST and carries the slug in the path."""
    assert "gh api -X POST repos/{emit_slug}/releases" in SHIP, \
        "the release emission is not the sanctioned REST form"
    assert "-R {emit_slug}" not in SHIP, "a `-R` selector survived the REST conversion"


def test_the_release_emission_verifies_the_tag_before_creating_it():
    """§4.4's replacement for `--verify-tag`, which has no REST equivalent.

    Without the chained read the POST is NOT inert on a typo'd version: `target_commitish`
    defaults to the default branch and GitHub creates the tag there. Asserted on the emitted
    string because that is what a human pastes — the driver's own precondition is a separate
    control and neither substitutes for the other.
    """
    assert "gh api repos/{emit_slug}/git/ref/tags/{version} > /dev/null && " in SHIP, \
        "the tag precondition is missing from the emitted release command"
    # Scoped to what is EMITTED, not to the file: the comment explaining what replaced the flag
    # names it on purpose, and an assertion over the whole file would delete that explanation.
    emitted = " ".join(m.group(1) for m in re.finditer(r"_emit_next\(f?['\"]([^'\"]+)", SHIP))
    assert "--verify-tag" not in emitted, "the flag survived inside an emitted command"


def test_no_emitted_command_is_bare_git_or_gh():
    """Guard against a future emission regressing to the cwd-dependent shape.

    WIDENED 2026-09-19 (§5.1). This read only `ship-release.py`'s `_emit_next(…)` and never saw
    `pr-flow.py`'s `emit(…)` sites — which is the second reason `gh pr create` stood unnoticed
    there for as long as it did. Both drivers are now covered by one rule.
    """
    emissions = [(m.group(1), "ship-release.py")
                 for m in re.finditer(r"_emit_next\(f?['\"]([^'\"]+)", SHIP)]
    emissions += [(m.group(1), "pr-flow.py")
                  for m in re.finditer(r"cmd = \(?f?['\"]([^'\"]+)", PRFLOW)]
    assert len(emissions) >= 4, f"only {len(emissions)} emissions found — the scan is not reaching"

    for cmd, where in emissions:
        body = cmd.split("&&", 1)[1] if cmd.startswith("cd ") and "&&" in cmd else cmd
        body = body.strip()
        if body.startswith("git "):
            assert "-C " in body, f"{where}: emitted git command lacks -C: {cmd}"
        if body.startswith("gh "):
            assert any(tok in body for tok in GH_NAMES_ITS_REPO), \
                f"{where}: emitted gh command names no repo: {cmd}"
