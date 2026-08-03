"""Behaviour tests for tools/pr-flow.py and tools/gh_read.py — the PR-lifecycle pair.

Same posture as test_ceremony_tools.py: a throwaway work repo cloned from a throwaway local BARE
origin, so every git layer (fetch, ls-remote, rev-list, merge-base) is exercised for real and
OFFLINE. No test here touches the network — the driver's local guards all precede its first
GitHub read, which is exactly why slug resolution is lazy.

The cases are weighted toward the ORDERING and POSTCONDITION defects recorded in F30, because
those are what the driver exists to prevent: advancing on a stale base, pushing over a divergent
remote without a lease, and treating a half-finished rebase as settled state.
"""
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
FLOW = REPO / "tools" / "pr-flow.py"

EXIT_OK, EXIT_REFUSED, EXIT_NEEDS_INPUT, EXIT_BLOCKED = 0, 1, 2, 3

sys.path.insert(0, str(REPO / "tools"))
import gh_read  # noqa: E402


def git(args, cwd):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def run_flow(work, *extra):
    return subprocess.run(
        [sys.executable, str(FLOW), *extra],
        cwd=work, capture_output=True, text=True,
    )


@pytest.fixture()
def work(tmp_path):
    """A work repo with a real local bare origin and a `main` both sides agree on."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)],
                   check=True, capture_output=True)
    w = tmp_path / "work"
    subprocess.run(["git", "clone", str(origin), str(w)], check=True, capture_output=True)
    git(["config", "user.email", "t@example.com"], w)
    git(["config", "user.name", "T"], w)
    (w / "README.md").write_text("base\n")
    git(["add", "-A"], w)
    git(["commit", "-m", "base commit"], w)
    git(["push", "-u", "origin", "main"], w)
    return w


def commit_on(work, branch, text="feature\n"):
    git(["switch", "-c", branch], work)
    (work / f"{branch.replace('/', '-')}.md").write_text(text)
    git(["add", "-A"], work)
    git(["commit", "-m", f"work on {branch}"], work)


# --- local guards -----------------------------------------------------------------------------

def test_refuses_when_branch_equals_base(work):
    r = run_flow(work, "--branch", "main", "--base", "main")
    assert r.returncode == EXIT_REFUSED
    assert "both" in r.stdout


def test_refuses_dirty_worktree(work):
    commit_on(work, "feat/x")
    (work / "dirty.md").write_text("uncommitted\n")
    r = run_flow(work, "--branch", "feat/x")
    assert r.returncode == EXIT_REFUSED
    assert "not clean" in r.stdout


def test_refuses_while_a_rebase_is_still_in_progress(work):
    """F30 item 6: a rebase reported complete while .git/rebase-merge was still active is what
    silently blocked a later branch deletion. The driver must not advance over that state."""
    commit_on(work, "feat/x")
    (work / ".git" / "rebase-merge").mkdir()
    r = run_flow(work, "--branch", "feat/x")
    assert r.returncode == EXIT_REFUSED
    assert "rebase-merge" in r.stdout
    assert "rebase --quit" in r.stdout


def test_refuses_branch_with_no_commits_over_base(work):
    git(["switch", "-c", "feat/empty"], work)
    r = run_flow(work, "--branch", "feat/empty")
    assert r.returncode == EXIT_REFUSED
    assert "no commits" in r.stdout


# --- ordering: the F30 defect the driver exists to prevent ------------------------------------

def test_emits_rebase_when_branch_does_not_contain_base_tip(work):
    """A PR opened on a stale base reports checks that are not about its own change."""
    commit_on(work, "feat/stale")
    git(["switch", "main"], work)
    (work / "moved.md").write_text("base moved\n")
    git(["add", "-A"], work)
    git(["commit", "-m", "advance main"], work)
    git(["push", "origin", "main"], work)

    r = run_flow(work, "--branch", "feat/stale")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert "rebase origin/main" in r.stdout
    assert "BEFORE pushing or merging" in r.stdout


def test_emits_plain_push_when_remote_branch_absent(work):
    commit_on(work, "feat/new")
    r = run_flow(work, "--branch", "feat/new")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert "push -u origin feat/new" in r.stdout
    assert "--force" not in r.stdout


def test_emits_force_with_lease_never_bare_force_when_remote_diverges(work):
    commit_on(work, "feat/div")
    git(["push", "-u", "origin", "feat/div"], work)
    (work / "amended.md").write_text("rewritten\n")
    git(["add", "-A"], work)
    git(["commit", "--amend", "--no-edit"], work)

    r = run_flow(work, "--branch", "feat/div")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert "--force-with-lease" in r.stdout
    assert "--force " not in r.stdout.replace("--force-with-lease", "")


def test_emitted_commands_name_an_owner(work):
    """Ownership is the class of error a driver cannot fix by ordering alone, so every emitted
    command carries it explicitly rather than leaving the caller to guess."""
    commit_on(work, "feat/owner")
    r = run_flow(work, "--branch", "feat/owner")
    assert "owner:" in r.stdout


def test_capabilities_probe_reports_without_raising(work):
    """Ownership is measured, never recalled — the probe must degrade, not explode, offline."""
    r = run_flow(work, "--capabilities")
    assert r.returncode == EXIT_OK
    assert "CAPABILITY PROBE" in r.stdout
    assert "git push" in r.stdout


# --- gh_read pure helpers ----------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://github.com/owner/repo.git", "owner/repo"),
    ("https://github.com/owner/repo", "owner/repo"),
    ("git@github.com:owner/repo.git", "owner/repo"),
    ("ssh://git@github.com/owner/Repo-With-Caps.git", "owner/Repo-With-Caps"),
])
def test_slug_parsing_uses_the_remote_not_the_folder(tmp_path, url, expected):
    d = tmp_path / "r"
    d.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "remote", "add", "origin", url], cwd=d, check=True)
    assert gh_read.slug_from_remote(str(d)) == expected


def test_slug_is_none_for_a_non_github_remote(tmp_path):
    d = tmp_path / "r"
    d.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(tmp_path / "bare.git")],
                   cwd=d, check=True)
    assert gh_read.slug_from_remote(str(d)) is None


def test_summarize_checks_counts_skipped_and_neutral_as_ok():
    """RC-E, over-denial is camouflage: scope-review legitimately reports `skipped` on one
    trigger and success on the other. A summariser that called that a failure would train its
    operator to bypass the gate."""
    payload = {"check_runs": [
        {"name": "a", "status": "completed", "conclusion": "success"},
        {"name": "b", "status": "completed", "conclusion": "skipped"},
        {"name": "c", "status": "completed", "conclusion": "neutral"},
    ]}
    total, pending, failures = gh_read.summarize_checks(payload)
    assert (total, pending, failures) == (3, [], [])


def test_summarize_checks_separates_pending_from_failing():
    payload = {"check_runs": [
        {"name": "running", "status": "in_progress", "conclusion": None},
        {"name": "broken", "status": "completed", "conclusion": "failure"},
        {"name": "timed-out", "status": "completed", "conclusion": "timed_out"},
    ]}
    total, pending, failures = gh_read.summarize_checks(payload)
    assert total == 3
    assert pending == ["running"]
    assert failures == ["broken", "timed-out"]


def test_summarize_checks_is_empty_safe():
    assert gh_read.summarize_checks({}) == (0, [], [])
