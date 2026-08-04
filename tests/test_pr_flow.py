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
    git(["switch", "feat/stale"], work)  # the branch under test IS checked out

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


# --- shapes the repo's own PR history proves are allowed ---------------------------------------

def test_switches_before_rebasing_so_the_wrong_branch_is_never_rebased(work):
    """A bare `git rebase` acts on HEAD. Emitting it while another branch is checked out rebases
    the wrong branch — caught during the flow review, before it could be run."""
    commit_on(work, "feat/stale")
    git(["switch", "main"], work)
    (work / "moved.md").write_text("base moved\n")
    git(["add", "-A"], work)
    git(["commit", "-m", "advance main"], work)
    git(["push", "origin", "main"], work)
    git(["switch", "-c", "feat/other"], work)  # a DIFFERENT branch is checked out

    r = run_flow(work, "--branch", "feat/stale")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert "switch feat/stale" in r.stdout
    assert "WRONG branch" in r.stdout
    assert "rebase origin/main" not in r.stdout.split("NEXT COMMAND")[1]


def test_remote_only_branch_is_never_rebased_or_pushed(work):
    """Dependabot branches (3 open on the live repo today) are not ours. `git rev-parse <name>`
    resolves a remote-tracking ref by DWIM, so the driver once treated one as local and proposed
    rebasing it — which would detach it from Dependabot's own automation."""
    commit_on(work, "dependabot/npm_and_yarn/thing-1.7.0")
    git(["push", "-u", "origin", "dependabot/npm_and_yarn/thing-1.7.0"], work)
    git(["switch", "main"], work)
    git(["branch", "-D", "dependabot/npm_and_yarn/thing-1.7.0"], work)

    r = run_flow(work, "--branch", "dependabot/npm_and_yarn/thing-1.7.0")
    assert "dependabot branch" in r.stdout
    assert "NOT local" in r.stdout
    # No rebase or push is ever EMITTED for a branch we do not own. (The locality line mentions
    # the words while explaining that those steps are skipped, so assert on the emitted command.)
    emitted = r.stdout.split("NEXT COMMAND")[1] if "NEXT COMMAND" in r.stdout else ""
    assert "rebase" not in emitted
    assert "push" not in emitted


def test_absent_branch_defers_the_verdict_instead_of_refusing_outright(work):
    """A branch gone from both sides is the normal END STATE of a completed lifecycle. Refusing
    there would break the driver's re-entrancy contract."""
    r = run_flow(work, "--branch", "feat/gone")
    assert "absent locally and on origin" in r.stdout
    assert "checking whether its lifecycle already completed" in r.stdout


def test_pr_lookup_asks_for_all_states_not_just_open(monkeypatch):
    """A CLOSED-unmerged PR is invisible to an open-only query, so the driver would propose
    creating a duplicate. This repo has two such PRs: #18 and #29."""
    seen = {}

    def fake_get(path):
        seen["path"] = path
        return [], "stub"

    monkeypatch.setattr(gh_read, "get", fake_get)
    gh_read.pulls_for_branch("o/r", "feat/x", "main", state="all")
    assert "state=all" in seen["path"]
    assert "head=o:feat/x" in seen["path"]


def test_open_children_queries_by_base_for_the_f21_hazard(monkeypatch):
    """Stacked children must be visible BEFORE the parent merges — merging with --delete-branch
    closes them irrecoverably (PR #29 died this way)."""
    seen = {}

    def fake_get(path):
        seen["path"] = path
        return [], "stub"

    monkeypatch.setattr(gh_read, "get", fake_get)
    gh_read.open_children("o/r", "parent-branch")
    assert "base=parent-branch" in seen["path"]
    assert "state=open" in seen["path"]


# =================================================================================================
# Second pass: route/plan, authority, correct verbs, readiness and the TOCTOU window.
#
# The GitHub-side steps cannot be reached from the subprocess tests above, because the work repo's
# origin is a local bare path with no resolvable slug. These load the driver IN-PROCESS and stub the
# read layer, so every branch after the PR lookup is exercised OFFLINE.
# =================================================================================================

import importlib.util  # noqa: E402
import types  # noqa: E402

_spec = importlib.util.spec_from_file_location("pr_flow", FLOW)
pr_flow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_flow)


def args_for(branch, **kw):
    a = types.SimpleNamespace(branch=branch, base="main", body_file=None, title=None)
    for k, v in kw.items():
        setattr(a, k, v)
    return a


def stub_reads(monkeypatch, *, prs, checks=None, full=None, children=()):
    monkeypatch.setattr(pr_flow.gh_read, "slug_from_remote", lambda *_a, **_k: "o/r")
    monkeypatch.setattr(pr_flow.gh_read, "pulls_for_branch",
                        lambda *a, **k: (prs, "stub"))
    monkeypatch.setattr(pr_flow.gh_read, "check_runs",
                        lambda *a, **k: (checks or {"check_runs": []}, "stub"))
    monkeypatch.setattr(pr_flow.gh_read, "pull_request",
                        lambda *a, **k: (full if full is not None else prs[0], "stub"))
    monkeypatch.setattr(pr_flow.gh_read, "open_children", lambda *a, **k: (list(children), "stub"))


def open_pr(head_sha, **kw):
    pr = {"number": 51, "state": "open", "title": "t", "draft": False,
          "head": {"sha": head_sha, "ref": "feat/x"}, "base": {"ref": "main"},
          "body": "text\n```scope\ntools/pr-flow.py\n```\n", "mergeable": True,
          "mergeable_state": "clean", "merged_at": None}
    pr.update(kw)
    return pr


def head_of(work, branch="feat/x"):
    return git(["rev-parse", f"refs/heads/{branch}"], work).stdout.strip()


def drive(work, a, plan=False):
    route = pr_flow.Route()
    code = pr_flow.drive(a, str(work), route, plan=plan)
    return code, route


# --- A: the route is visible before the step ---------------------------------------------------

def test_plan_lists_every_step_and_composes_no_command_for_projected_ones(work):
    commit_on(work, "feat/x")
    r = run_flow(work, "--plan", "--branch", "feat/x")
    for sid, _ in pr_flow.STEPS:
        assert sid in r.stdout
    assert "PROJECTED" in r.stdout
    # The current step may carry a command; a projected one must never do so.
    projected = [ln for ln in r.stdout.splitlines() if "PROJECTED" in ln]
    assert projected and not any("git " in ln or "gh " in ln for ln in projected)


def test_every_emission_carries_the_route_header(work):
    commit_on(work, "feat/x")
    r = run_flow(work, "--branch", "feat/x")
    assert "route: " in r.stdout
    assert "step " in r.stdout


# --- C: authority is distinguished from execution ----------------------------------------------

def test_push_runs_as_agent_under_operator_authority(work):
    """The correction F30 names in its own framing: do not hand the operator a command the agent
    can run. Authority stays theirs; the keystrokes do not."""
    commit_on(work, "feat/x")
    r = run_flow(work, "--branch", "feat/x")
    assert "runs:      AGENT" in r.stdout
    assert "authority: OPERATOR" in r.stdout
    assert "consent:" in r.stdout


def test_purely_local_command_needs_no_consent(work):
    commit_on(work, "feat/stale")
    git(["switch", "main"], work)
    (work / "moved.md").write_text("moved\n")
    git(["add", "-A"], work)
    git(["commit", "-m", "advance"], work)
    git(["push", "origin", "main"], work)
    git(["switch", "feat/stale"], work)
    r = run_flow(work, "--branch", "feat/stale")
    assert "runs:      AGENT" in r.stdout
    assert "authority: AGENT" in r.stdout
    assert "nothing leaves this machine" in r.stdout


def test_a_push_is_never_emitted_without_an_explicit_target_redirect(work):
    """A bare `git push` from a session whose cwd is the vault resolves its effective target TO the
    vault and is HARD DENIED. The redirect is what keeps the emitted command runnable."""
    commit_on(work, "feat/x")
    r = run_flow(work, "--branch", "feat/x")
    line = [ln for ln in r.stdout.splitlines() if "push" in ln and ln.strip().startswith("git")]
    assert line and all("-C " in ln for ln in line)


GATE4 = "## 4. Gate 4 — HUMAN SIGN-OFF\n"


def write_tasks(tmp_path, name, body):
    d = tmp_path / "openspec" / "changes" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "tasks.md").write_text(body)
    return d


def test_gate4_signoff_is_a_record_with_a_shape_not_a_keyword(tmp_path):
    """Three defects were found in this check by audit, all the same family: loose enough to be
    satisfied by prose that merely MENTIONS the thing it verifies. Each is locked down here."""
    # 1. The unticked task DESCRIBING the sign-off necessarily contains the word.
    write_tasks(tmp_path, "c", GATE4 + "- [ ] 4.1 Operator records **Approved**\n")
    signed, detail = pr_flow.approval_state(str(tmp_path))
    assert signed is False and "UNSIGNED" in detail

    # 2. A ticked item mentioning it OUTSIDE the Gate-4 section must not count.
    write_tasks(tmp_path, "c",
                "## 3. Regression\n- [x] 3.9 Checked whether the operator Approved 2026-08-04\n")
    assert pr_flow.approval_state(str(tmp_path))[0] is False

    # 3. Ticked and in-section but with no date is not a record.
    write_tasks(tmp_path, "c", GATE4 + "- [x] 4.1 Operator records **Approved**\n")
    assert pr_flow.approval_state(str(tmp_path))[0] is False

    # The real shape: ticked, in section, with an ISO date.
    write_tasks(tmp_path, "c", GATE4 + "- [x] 4.1 **Approved** — Keith Nielsen, 2026-08-04\n")
    assert pr_flow.approval_state(str(tmp_path))[0] is True


def test_every_unarchived_change_is_evaluated_not_just_the_first(tmp_path):
    """The earlier cut returned from inside the per-file loop, so a SECOND unarchived change was
    never examined — one signed change would have authorized an unsigned one."""
    write_tasks(tmp_path, "a", GATE4 + "- [x] 4.1 **Approved** — op, 2026-08-04\n")
    write_tasks(tmp_path, "b", GATE4 + "- [ ] 4.1 Operator records **Approved**\n")
    signed, detail = pr_flow.approval_state(str(tmp_path))
    assert signed is False
    assert "b/tasks.md" in detail


# --- B/D: correct verbs and the guards that were missing ----------------------------------------

def test_merge_uses_the_server_side_sha_precondition_and_never_delete_branch(work, monkeypatch,
                                                                            capsys):
    """`gh pr merge --delete-branch` is wrong on three counts: no head precondition, it bypasses
    GitHub's retargeting of stacked children (how #29 died), and its deletion fails open."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    stub_reads(monkeypatch, prs=[open_pr(sha)],
               checks={"check_runs": [{"name": "ci", "status": "completed",
                                       "conclusion": "success"}]})
    code, _ = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert code == EXIT_NEEDS_INPUT
    command = o.split("NEXT COMMAND")[1].splitlines()[1]
    assert "gh api -X PUT /repos/o/r/pulls/51/merge" in command
    assert f"sha={sha}" in command
    # The prose names the flag in order to warn against it; the COMMAND must never carry it.
    assert "--delete-branch" not in command
    assert "--delete-branch` is deliberately NOT used" in o


def test_zero_check_runs_is_not_ready_and_never_green(work, monkeypatch, capsys):
    """A push races the platform queueing its workflow. Zero runs is 'not yet', not 'all green'."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    stub_reads(monkeypatch, prs=[open_pr(head_of(work))], checks={"check_runs": []})
    code, _ = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert code == EXIT_NEEDS_INPUT
    assert "NOT READY" in o and "no check runs" in o
    assert "--ready checks --sha" in o
    assert "merge" not in o.split("NOT READY")[1]


def test_uncomputed_mergeability_waits_rather_than_assuming_mergeable(work, monkeypatch, capsys):
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    stub_reads(monkeypatch, prs=[open_pr(sha)],
               checks={"check_runs": [{"name": "ci", "status": "completed",
                                       "conclusion": "success"}]},
               full=open_pr(sha, mergeable=None, mergeable_state="unknown"))
    code, _ = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert code == EXIT_NEEDS_INPUT
    assert "NOT READY" in o and "mergeability" in o


def test_unmergeable_pull_request_is_refused(work, monkeypatch, capsys):
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    stub_reads(monkeypatch, prs=[open_pr(sha)],
               checks={"check_runs": [{"name": "ci", "status": "completed",
                                       "conclusion": "success"}]},
               full=open_pr(sha, mergeable=False, mergeable_state="dirty"))
    code, _ = drive(work, args_for("feat/x"))
    assert code == EXIT_REFUSED
    assert "NOT mergeable" in capsys.readouterr().out


def test_stacked_children_refusal_prescribes_the_rest_patch_not_gh_pr_edit(work, monkeypatch,
                                                                          capsys):
    """F21 stumble 3: `gh pr edit --base` failed SILENTLY behind a GraphQL deprecation. Emitting it
    at the exact moment #29 died would hand over a no-op."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    stub_reads(monkeypatch, prs=[open_pr(sha)],
               checks={"check_runs": [{"name": "ci", "status": "completed",
                                       "conclusion": "success"}]},
               children=[{"number": 29, "head": {"ref": "child"}}])
    code, _ = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert code == EXIT_REFUSED
    assert "#29" in o
    assert "gh api -X PATCH" in o
    assert "gh pr edit" in o and "NOT" in o  # named only to warn against it


def test_body_derived_check_failure_prescribes_a_push_not_a_rerun(work, monkeypatch, capsys):
    """The gate reads the body from the pull_request event payload, a SNAPSHOT as of push time; a
    re-run replays the stale one. F21 stumble 1 was re-running the job."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    stub_reads(monkeypatch, prs=[open_pr(head_of(work))],
               checks={"check_runs": [{"name": "scope-review", "status": "completed",
                                       "conclusion": "failure"}]})
    code, _ = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert code == EXIT_REFUSED
    assert "SNAPSHOT" in o and "do not re-run" in o


def test_missing_scope_block_in_the_pr_body_is_caught_before_the_merge(work, monkeypatch, capsys):
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    stub_reads(monkeypatch, prs=[open_pr(sha, body="no block here")])
    body = work.parent / "body.md"
    body.write_text("text\n```scope\ntools/pr-flow.py\n```\n")
    code, _ = drive(work, args_for("feat/x", body_file=str(body)))
    o = capsys.readouterr().out
    assert code == EXIT_NEEDS_INPUT
    assert "gh api -X PATCH /repos/o/r/pulls/51" in o
    assert "PUSH, not a re-run" in o


def test_body_file_lacking_a_scope_block_is_refused_before_any_command(work, monkeypatch, capsys):
    """The scope-block rule used to live in a prose string inside the tool built to end prose."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    stub_reads(monkeypatch, prs=[])
    body = work.parent / "body.md"
    body.write_text("no fenced block at all\n")
    code, _ = drive(work, args_for("feat/x", body_file=str(body), title="t"))
    o = capsys.readouterr().out
    assert code == EXIT_REFUSED
    assert "no fenced" in o
    assert "gh pr create" not in o


def test_missing_title_refuses_rather_than_emitting_a_placeholder(work, monkeypatch, capsys):
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    stub_reads(monkeypatch, prs=[])
    body = work.parent / "body.md"
    body.write_text("t\n```scope\nx\n```\n")
    code, _ = drive(work, args_for("feat/x", body_file=str(body)))
    o = capsys.readouterr().out
    assert code == EXIT_REFUSED
    assert "placeholder" in o
    assert "<TITLE>" not in o


def test_surviving_remote_branch_after_merge_is_emitted_as_its_own_step(work, monkeypatch, capsys):
    """F30 item 3: the deletion did not happen and the tool printed a success tick anyway."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    stub_reads(monkeypatch, prs=[open_pr(sha, state="closed", merged_at="2026-08-04T00:00:00Z")],
               full=open_pr(sha, state="closed", merged_at="2026-08-04T00:00:00Z"))
    code, _ = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert code == EXIT_NEEDS_INPUT
    assert "push origin --delete feat/x" in o
    assert "verified rather than assumed" in o


# --- E: the saved plan closes the TOCTOU window on an operator step ------------------------------

def test_saved_plan_asserts_preconditions_and_expires(work):
    path = pr_flow.write_saved_plan(str(work), "merge", "gh api -X PUT /x", "merges PR #51")
    text = pathlib.Path(path).read_text()
    assert "set -euo pipefail" in text
    assert "date +%s" in text and "EXPIRED" in text
    assert "gh api -X PUT /x" in text
    assert text.index("date +%s") < text.index("gh api -X PUT /x")  # the check precedes the act


def test_fast_forward_push_carries_no_force_flag(work):
    """Local merely AHEAD of origin is a fast-forward. Emitting --force-with-lease there would
    succeed, but it normalises a force push for a case that never needed one — and a reader seeing
    the flag would reasonably infer history had been rewritten. Found by dogfooding."""
    commit_on(work, "feat/ff")
    git(["push", "-u", "origin", "feat/ff"], work)
    (work / "more.md").write_text("another commit\n")
    git(["add", "-A"], work)
    git(["commit", "-m", "add more"], work)

    r = run_flow(work, "--branch", "feat/ff")
    assert r.returncode == EXIT_NEEDS_INPUT
    command = r.stdout.split("NEXT COMMAND")[1].splitlines()[1]
    assert "push origin feat/ff" in command
    assert "--force" not in command
    assert "fast-forward" in r.stdout


def test_scope_block_detection_requires_a_fenced_block():
    assert pr_flow.scope_block_in("a\n```scope\nfile.py\n```\n")
    assert not pr_flow.scope_block_in("the word scope appears but no fence")
    assert not pr_flow.scope_block_in("```python\nscope\n```")


def test_scope_check_never_passes_what_the_ci_gate_would_reject():
    """This check exists to pre-verify the declared-scope gate. An earlier cut tested only that a
    fence was OPENED, so a body whose fence is never closed passed here and is rejected there — a
    check that green-lights what the real gate fails is worse than none, because it is relied on."""
    assert not pr_flow.scope_block_in("```scope\ntools/x.py")      # never closed
    assert not pr_flow.scope_block_in("```scope\n```")             # closed but empty
    assert pr_flow.scope_block_in("```scope\ntools/x.py\n```")


def test_scope_rule_is_the_ci_gates_own_rule_not_a_restatement():
    """Anti-drift: the tool imports the gate's regex rather than paraphrasing it, so the two
    cannot diverge as either changes."""
    rule = pr_flow._ci_scope_rule(str(REPO))
    assert rule is not None, "the CI extractor should be importable for its fence rule"
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_ds", REPO / ".github/scripts/extract-declared-scope.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert rule.pattern == mod.FENCE_RE.pattern


def test_ready_requires_its_identifier_so_it_stays_one_request(work):
    r = run_flow(work, "--ready", "checks")
    assert r.returncode == EXIT_BLOCKED
    assert "--sha" in r.stderr
