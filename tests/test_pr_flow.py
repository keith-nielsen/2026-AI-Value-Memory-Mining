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
import re
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


def test_the_route_header_explains_every_marker_it_renders(work):
    """A key that is not on the page is not a key. Six glyphs were shipped with no legend at all —
    the reader had to infer all of them from context."""
    commit_on(work, "feat/x")
    r = run_flow(work, "--branch", "feat/x")
    key_line = [ln for ln in r.stdout.splitlines() if ln.strip().startswith("key:")]
    assert key_line, "the route header must carry a legend"
    route_line = [ln for ln in r.stdout.splitlines() if ln.startswith("route:")][0]
    rendered = set(re.findall(r"\[(.)\]", route_line))
    explained = set(re.findall(r"\[(.)\]", key_line[0]))
    assert rendered <= explained, f"unexplained markers: {rendered - explained}"


def test_waiting_and_untested_do_not_share_a_glyph():
    """`[~]` means 'built but NOT TESTED' in task files — a deficiency needing action. The driver's
    wait state means 'the platform has not answered', which resolves itself. One glyph for both
    would let an untested item read as benignly in flight."""
    assert pr_flow.MARK["wait"][0] == "?"
    assert "~" not in {glyph for glyph, _ in pr_flow.MARK.values()}


def test_the_pass_mark_is_not_a_glyph_that_inverts_by_convention():
    """`x` means *selected* in the US/UK but 「×」(batsu) means *wrong* across much of East Asia.
    The pair was the real hazard: `[x]`=passed beside `[!]`=failed scans as two negatives under
    that reading, collapsing the route's most important distinction."""
    glyphs = {glyph for glyph, _ in pr_flow.MARK.values()}
    assert pr_flow.MARK["ok"][0] == "P" and pr_flow.MARK["fail"][0] == "F"
    assert "x" not in glyphs and "!" not in glyphs


def test_every_marker_is_ascii_so_no_font_can_render_it_as_a_box():
    for glyph, words in pr_flow.MARK.values():
        assert len(glyph) == 1 and ord(glyph) < 128, f"{glyph!r} is not single-char ASCII"
        assert words, "a marker with no definition cannot appear in the legend"


def test_a_completed_route_does_not_report_a_step_past_the_end(work):
    """Cosmetic, but it was reported as `step 15/14` on a finished lifecycle."""
    route = pr_flow.Route()
    for sid, _ in pr_flow.STEPS:
        route.mark(sid, "ok")
    assert f"step {len(pr_flow.STEPS)}/{len(pr_flow.STEPS)}" in route.header()


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


def test_signoff_is_still_read_after_the_change_is_archived(tmp_path):
    """Archiving on the feature branch BEFORE the merge is the recommended order (archiving after
    costs a second PR), which moves tasks.md one level deeper. The first cut then reported
    `no unarchived change` — so the merge gate, which refuses only on signed is False, went INERT at
    exactly the step it exists to guard. Found by walking this change's own ceremony."""
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-08-04-add-pr-flow-driver"
    d.mkdir(parents=True)
    (d / "tasks.md").write_text(GATE4 + "- [x] 4.1 **Approved** — Keith Nielsen, 2026-08-04\n")
    signed, detail = pr_flow.approval_state(str(tmp_path), "feat/add-pr-flow-driver")
    assert signed is True
    assert "archived" in detail


def test_an_unrelated_archived_signoff_never_authorizes_this_branch(tmp_path):
    """Every archived change carries a valid sign-off, so an unkeyed scan of the archive would let
    a June approval authorize today's merge — the wrong-scope error one level up."""
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-06-28-something-else"
    d.mkdir(parents=True)
    (d / "tasks.md").write_text(GATE4 + "- [x] 4.1 **Approved** — someone, 2026-06-28\n")
    signed, _ = pr_flow.approval_state(str(tmp_path), "feat/add-pr-flow-driver")
    assert signed is None, "an unrelated archived change must not satisfy this branch's gate"


def test_archived_but_unsigned_still_refuses(tmp_path):
    d = tmp_path / "openspec" / "changes" / "archive" / "2026-08-04-add-pr-flow-driver"
    d.mkdir(parents=True)
    (d / "tasks.md").write_text(GATE4 + "- [ ] 4.1 Operator records **Approved**\n")
    signed, detail = pr_flow.approval_state(str(tmp_path), "feat/add-pr-flow-driver")
    assert signed is False and "UNSIGNED" in detail


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
    """Found by dogfooding at the moment of use: the script CLAIMED to re-assert the approved state
    and contained no assertion at all — only an expiry. A safety claim with no mechanism behind it
    is the class-9 defect inside the mechanism built to prevent it."""
    path = pr_flow.write_saved_plan(str(work), "merge", "gh api -X PUT /x", "merges PR #51",
                                    "feat/x",
                                    assert_args=["pr=51", "head=abc123", "failures=0"])
    text = pathlib.Path(path).read_text()
    assert "set -euo pipefail" in text
    assert "date +%s" in text and "EXPIRED" in text
    assert "--assert-preconditions pr=51 head=abc123 failures=0" in text
    # The assertion must precede the mutation, or `set -e` cannot stop it.
    assert text.index("--assert-preconditions") < text.index("gh api -X PUT /x")


def test_saved_plan_never_claims_an_assertion_it_does_not_make(work):
    """When there is no pull request to assert against, the script must say so rather than inherit
    the reassuring header. Saying only what it does is the whole corrective."""
    path = pr_flow.write_saved_plan(str(work), "pr", "gh pr create --title x", "opens a PR",
                                    "feat/x")
    text = pathlib.Path(path).read_text()
    assert "--assert-preconditions" not in text
    assert "no live-state assertion is made here" in text
    assert "Consent was given for the state asserted below" not in text


def test_saved_plan_pins_its_verification_target(work):
    """The mutation is literal text fixed at WRITE time; the verification must be too.

    It used to end `--branch "${PR_FLOW_BRANCH:-$(git branch --show-current)}"`, resolved at RUN
    time. Switch branches in between and the plan MUTATES ONE PULL REQUEST THEN VERIFIES ANOTHER —
    measured 2026-08-12, when a plan re-merged #64 and then reported `REFUSED: no open PR` about a
    different branch, directly beneath `"merged": true`.
    """
    pr_flow.INVOCATION = ["--branch", "feat/pinned", "--base", "main"]
    path = pr_flow.write_saved_plan(str(work), "merge", "gh api -X PUT /x", "merges PR #51",
                                    "feat/pinned")
    tail = pathlib.Path(path).read_text().split("# VERIFY")[1]
    assert "$(git branch --show-current)" not in tail
    assert "feat/pinned" in tail


def test_saved_plan_tail_carries_the_after_mutation_flags(work):
    """Item 19: the tail must KNOW it is verifying a mutation, pinned at write time like the branch.

    Derived at run time it would be guesswork; pinned, it is the fact that licenses lag tolerance
    and forbids emitting another mutation.
    """
    pr_flow.INVOCATION = ["--branch", "feat/lag", "--base", "main"]
    path = pr_flow.write_saved_plan(str(work), "merge", "gh api -X PUT /x", "merges PR #51",
                                    "feat/lag")
    text = pathlib.Path(path).read_text()
    tail = text.split("# VERIFY")[1]
    assert "--after-mutation merge" in tail
    assert "--mutation-evidence" in tail
    assert '"$_ev"' in tail, "the evidence path must expand in bash, not arrive quoted"
    assert 'tee "$_ev"' in text, "the mutation's own response must be captured as it is shown"


def test_after_mutation_reports_waiting_not_refused_when_the_merge_is_not_visible(work, monkeypatch):
    """Item 19, the original symptom: REFUSED, exit 1, directly beneath `"merged": true`.

    Nothing was wrong — GitHub's read view had not caught up with its own write. The operator's
    natural reaction to red-after-irreversible is to re-run the merge, which is the one thing that
    must never happen here.
    """
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    monkeypatch.setattr(pr_flow, "LAG_RETRY_DELAYS", (0, 0))  # same code path, no wall-clock cost
    monkeypatch.setattr(pr_flow.gh_read, "pull_request",
                        lambda slug, n: ({"number": n, "state": "open", "merged_at": None},
                                         "anon-rest"))
    route = pr_flow.Route()
    rc = pr_flow.post_merge(str(work), "o/r", "feat/lag", 64, False, route)
    assert rc == EXIT_NEEDS_INPUT, "waiting is exit 2, not the exit 1 of a refusal"


def test_without_after_mutation_an_unmerged_pr_is_still_a_refusal(work, monkeypatch):
    """The adversarial half: lag tolerance must not soften an ordinary run into a false pass.

    Outside a post-mutation verify there is no successful mutation to contradict, so an unmerged PR
    at this point is a genuine refusal and keeps its old verdict.
    """
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", None)
    monkeypatch.setattr(pr_flow.gh_read, "pull_request",
                        lambda slug, n: ({"number": n, "state": "open", "merged_at": None},
                                         "anon-rest"))
    route = pr_flow.Route()
    rc = pr_flow.post_merge(str(work), "o/r", "feat/lag", 64, False, route)
    assert rc == EXIT_REFUSED


def test_after_mutation_never_emits_an_outward_mutation(work, monkeypatch, capsys):
    """Item 19's SHARPER instance (PR #66) — the one that is not survivable.

    Seconds after `gh pr create` succeeded, the verify tail read 0 PRs and re-emitted
    `gh pr create`. Following that instruction opens a DUPLICATE pull request; the merge case was
    survivable only because GitHub answered idempotently. The suppression is structural — the emit
    cannot happen — rather than a caveat in the output prose.
    """
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "pr")
    route = pr_flow.Route()
    rc = pr_flow.emit(route, "pr", "cd /x && gh pr create --base main --head feat/lag "
                                   '--title "T" --body-file b.md',
                      pr_flow.OPERATOR, pr_flow.OPERATOR, pr_flow.CONSENT_ACT, "why",
                      root=str(work), branch="feat/lag")
    printed = capsys.readouterr().out
    assert rc == EXIT_NEEDS_INPUT
    assert "SUPPRESSED" in printed
    assert "NEXT COMMAND (run exactly this" not in printed, \
        "the command must never be presented as an instruction to run"
    assert "duplicate" in printed.lower()
    assert not pr_flow.saved_plan_path(str(work)).exists(), \
        "a suppressed step must not leave a runnable plan behind"


def test_after_mutation_clears_once_its_verified_step_is_confirmed(work, monkeypatch, capsys):
    """Item 22 — measured in PRODUCTION on PR #67's own merge, one command after the fix landed.

    The merge confirmed (`merged: PR #67 at 2026-08-14T10:13:11Z`) and the VERY NEXT step printed
    `WAITING remote-gone: the read view does not yet show the merge mutation` — a claim the line
    directly above it had already disproven — and suppressed a branch delete that genuinely needed
    doing. Suppression was scoped to *"this run carried the flag"*; it must be scoped to *"the
    verified mutation is still unconfirmed"*.

    Over-denial is its own failure: `github-command-inventory-classification.md` §6 —
    *"never regress into the corrosion of over-denial"*. A guard that blocks correct work trains its
    reader to ignore it, costing exactly the protection it was added for.
    """
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    branch = "feat/confirmed"
    commit_on(work, branch)
    git(["push", "-u", "origin", branch], work)          # the remote branch really exists
    monkeypatch.setattr(pr_flow.gh_read, "pull_request",
                        lambda slug, n: ({"number": n, "state": "closed",
                                          "merged_at": "2026-08-14T10:13:11Z",
                                          "base": {"ref": "main"}}, "anon-rest"))
    route = pr_flow.Route()
    rc = pr_flow.post_merge(str(work), "o/r", branch, 67, False, route)
    printed = capsys.readouterr().out

    assert "SUPPRESSED" not in printed, "the merge is confirmed — later steps are new work"
    assert "push origin --delete" in printed, "remote-gone must emit its delete"
    assert "does not yet show" not in printed, "a diagnosis contradicted on screen is worse than none"
    assert pr_flow.AFTER_MUTATION is None, "post-mutation mode ends when its step is confirmed"
    assert rc == EXIT_NEEDS_INPUT


def _drive_args(**over):
    import argparse
    base = dict(branch="feat/x", base="main", body_file=None, title=None, plan=False,
                capabilities=False, lag_report=False, ready=None, sha=None, pr=None,
                assert_preconditions=None, after_mutation=None, mutation_evidence=None)
    base.update(over)
    return argparse.Namespace(**base)


def test_lag_retry_is_REACHED_through_the_real_entry_point(work, monkeypatch):
    """Item 23 — REACHABILITY, asserted at `drive()`, never against `lag_tolerant` directly.

    The helper's own unit tests all passed while the retry was DEAD CODE on every real invocation:
    `prefetched` is a 2-tuple `(list, channel)`, so `if prefetched:` is truthy even when the list is
    EMPTY — and empty is precisely the lag symptom. Measured on PR #68's own creation: the guard
    suppressed the duplicate correctly, but `pulls_for_branch` was called exactly ONCE.

    This is the class a unit test structurally cannot catch, because the unit test supplies the input
    that production computes. The only question that catches it is *which real invocation reaches
    this line?* — and the only way to answer it is to drive the real entry point.
    """
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    calls = []

    def fake_pulls(slug, branch, base, state="all"):
        calls.append(branch)
        return ([], "anon-rest")          # the mutation landed; the read view has not caught up

    monkeypatch.setattr(pr_flow.gh_read, "pulls_for_branch", fake_pulls)
    monkeypatch.setattr(pr_flow.gh_read, "slug_from_remote", lambda root: "o/r")
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "pr")
    monkeypatch.setattr(pr_flow, "LAG_RETRY_DELAYS", (0, 0))
    monkeypatch.setitem(pr_flow.gh_read.BUDGET, "remaining", 60)

    pr_flow.drive(_drive_args(after_mutation="pr"), str(work), pr_flow.Route())

    # The prefetch IS the first attempt, so the ladder costs exactly one read per rung on top of it
    # — the prefetch read is not wasted.
    assert len(calls) == 1 + len(pr_flow.LAG_RETRY_DELAYS), (
        f"prefetch + every rung must reach the read; got {len(calls)} call(s) — "
        "an empty prefetch was consumed as an answer")


def test_the_NO_LAG_case_is_observed_too(work, monkeypatch):
    """The bias guard, asserted where it actually failed: at the call site, not in the helper.

    Measured on PR #69's own creation. `lag_tolerant` logs every attempt — but the `pr` step
    short-circuited to the prefetch and never called it, so a run where the read view KEPT UP
    recorded nothing at all. A log holding only the lagging cases makes the ladder look more
    necessary than it is, and is the exact bias the log was built to avoid.

    The helper being correct is not the property that matters. What matters is that every real
    invocation reaches it — which is a question about the call site, and answerable only from here.
    """
    import json as _json
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    monkeypatch.setattr(pr_flow.gh_read, "pulls_for_branch",
                        lambda slug, branch, base, state="all": (
                            [{"number": 7, "state": "open", "draft": False, "title": "t",
                              "head": {"sha": "x"}, "base": {"ref": "main"}}], "anon-rest"))
    monkeypatch.setattr(pr_flow.gh_read, "slug_from_remote", lambda root: "o/r")
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "pr")

    pr_flow.drive(_drive_args(after_mutation="pr"), str(work), pr_flow.Route())

    path = pr_flow.lag_log_path(str(work))
    assert path.exists(), "a run with NO lag must still be recorded, or the log is biased"
    recs = [_json.loads(x) for x in path.read_text().splitlines()]
    assert recs[-1]["visible"] is True
    assert recs[-1]["outcome"] == "visible"
    assert recs[-1]["attempt"] == 0, "the prefetch is attempt 0, not a skipped observation"


def test_ordinary_runs_still_reuse_the_prefetch_and_spend_no_extra_read(work, monkeypatch):
    """The narrowing must not undo the F34 budget saving on a 60-reads/hour channel."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    calls = []

    def fake_pulls(slug, branch, base, state="all"):
        calls.append(branch)
        return ([], "anon-rest")

    monkeypatch.setattr(pr_flow.gh_read, "pulls_for_branch", fake_pulls)
    monkeypatch.setattr(pr_flow.gh_read, "slug_from_remote", lambda root: "o/r")
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", None)      # ordinary run, not a verify
    pr_flow.drive(_drive_args(), str(work), pr_flow.Route())
    assert len(calls) == 1, "an empty prefetch is still a usable answer outside a verify"


def test_every_lag_attempt_is_logged_including_the_censored_one(work, monkeypatch):
    """Operator, 2026-08-14: capture what we are failing with, so the next ladder is not invented.

    Two properties matter more than the count. EVERY attempt is recorded — logging only the lagging
    cases would bias the record toward lag. And a ladder that runs out is marked CENSORED, because a
    lower bound silently treated as a measurement is how a too-short ladder justifies itself with its
    own data.
    """
    import json as _json
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    monkeypatch.setattr(pr_flow, "LAG_RETRY_DELAYS", (0, 0))
    monkeypatch.setitem(pr_flow.gh_read.BUDGET, "remaining", 60)

    pr_flow.lag_tolerant(lambda: ({}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="pr=99")
    recs = [_json.loads(x) for x in pr_flow.lag_log_path(str(work)).read_text().splitlines()]

    assert len(recs) == 1 + len(pr_flow.LAG_RETRY_DELAYS), "every attempt is an observation"
    assert recs[-1]["outcome"] == "censored-ladder-exhausted"
    assert all(r["visible"] is False for r in recs)
    assert len({r["series"] for r in recs}) == 1, "one mutation, one series"
    assert recs[0]["subject"] == "pr=99"

    # And the immediately-visible case is logged too, or the record over-represents lag.
    pr_flow.lag_tolerant(lambda: ({"merged_at": "now"}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="pr=100")
    recs = [_json.loads(x) for x in pr_flow.lag_log_path(str(work)).read_text().splitlines()]
    assert recs[-1]["outcome"] == "visible" and recs[-1]["attempt"] == 0


def test_lag_report_refuses_to_recommend_a_ladder(work, monkeypatch, capsys):
    """The report stops at the evidence. Handing back a number is how the next guess gets adopted."""
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    monkeypatch.setattr(pr_flow, "LAG_RETRY_DELAYS", (0,))
    monkeypatch.setitem(pr_flow.gh_read.BUDGET, "remaining", 60)
    pr_flow.lag_tolerant(lambda: ({}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="pr=99")
    capsys.readouterr()

    pr_flow.lag_report(str(work))
    out = capsys.readouterr().out
    assert "CENSORED" in out, "censoring must be visible in the summary, not buried"
    assert "LOWER BOUND" in out
    assert "not a distribution" in out
    assert not re.search(r"(recommend|suggest|try|set)\w*\s+\(?\d+\s*s", out, re.I), \
        "the report must not propose a delay"


def test_confirm_mutation_only_clears_the_step_it_was_verifying(monkeypatch):
    """Confirming some OTHER step must not end post-mutation mode early.

    `post_merge()` pre-marks pr/body/checks/... `ok` before verifying anything, so a hook keyed to
    'any step went ok' would clear on that loop and reopen the duplicate-emit hazard.
    """
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    pr_flow.confirm_mutation("pr")
    assert pr_flow.AFTER_MUTATION == "merge", "another step's confirmation proves nothing"
    pr_flow.confirm_mutation("merge")
    assert pr_flow.AFTER_MUTATION is None


def test_suppression_still_holds_while_the_verified_step_is_unconfirmed(work, monkeypatch, capsys):
    """The narrowing must not reopen item 19's sharper instance (the duplicate-PR hazard)."""
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "pr")
    route = pr_flow.Route()
    rc = pr_flow.emit(route, "pr", "cd /x && gh pr create --base main --head f "
                                   '--title "T" --body-file b.md',
                      pr_flow.OPERATOR, pr_flow.OPERATOR, pr_flow.CONSENT_ACT, "why",
                      root=str(work), branch="f")
    printed = capsys.readouterr().out
    assert "SUPPRESSED" in printed
    assert rc == EXIT_NEEDS_INPUT


@pytest.mark.parametrize("command,mutating", [
    # THE SHAPES THE DRIVER ACTUALLY EMITS — lifted from its own f-strings, not hand-written.
    # An earlier version of this test used `git push -u origin feat/lag`, which this tool never
    # produces; all four real push sites interpose `-C <root>` and slipped straight through the
    # guard. Caught end-to-end, not here. Copy from the emit site; do not compose from memory.
    ("git -C /r push -u origin feat/lag", True),
    ("git -C /r push origin feat/lag", True),
    ("git -C /r push --force-with-lease origin feat/lag", True),
    ("git -C /r push origin --delete feat/lag", True),
    ("cd /r && gh pr create --base main --head feat/lag --title \"T\" --body-file b.md", True),
    ("cd /r && gh api -X PATCH /repos/o/r/pulls/64 -f body=@b.md", True),
    ("cd /r && gh api -X PUT /repos/o/r/pulls/64/merge -f sha=abc", True),
    # Reads and local-only work must stay emittable — over-denial is its own failure.
    ("python3 /r/tools/pr-flow.py --ready merged --pr 64", False),
    ("git -C /r rebase origin/main", False),
    ("git -C /r branch -D feat/lag", False),
    ("cd /r && gh pr view 64", False),
    ("cd /r && gh api /repos/o/r/pulls/64", False),
])
def test_outward_mutation_is_classified_by_shape_not_by_step_name(command, mutating):
    """A step-name allowlist fails silently when a step is added; shape does not.

    Note `git -C /r branch -D` is NOT outward: deleting a LOCAL branch changes nothing on GitHub,
    and suppressing it would strand the lifecycle's last step.
    """
    assert pr_flow.is_outward_mutation(command) is mutating


def test_every_command_the_driver_emits_is_classified(work):
    """Guard against the classifier drifting from the emit sites it is supposed to cover.

    The end-to-end miss happened because the test's idea of an emitted command and the driver's
    actual f-string had diverged. This reads the source and fails if a push/gh-mutation emit site
    appears that the classifier does not match.
    """
    src = (REPO / "tools" / "pr-flow.py").read_text()
    emitted = re.findall(r'cmd = \(?f?"([^"]*(?:push|gh api -X|gh pr create)[^"]*)"', src)
    assert emitted, "no emit sites found — the scrape pattern has gone stale, not the code"
    for template in emitted:
        concrete = (template.replace("{root}", "/r").replace("{branch}", "feat/lag")
                            .replace("{base}", "main").replace("{slug}", "o/r")
                            .replace("{number}", "64").replace("{args.title}", "T")
                            .replace("{args.body_file}", "b.md"))
        assert pr_flow.is_outward_mutation(concrete), \
            f"driver emits this but the guard does not classify it as a mutation: {concrete}"


def test_every_ladder_rung_can_actually_succeed(monkeypatch):
    """Item 24: no rung may land inside a window where nothing has ever been observed to arrive.

    The old `(2, 5)` ladder spent its first two reads at ~3.3s and ~5.8s on the `merge` step, where
    arrival is 11.0-11.3s: a 0-for-13 hit rate across the whole record. Those probes could not
    succeed, cost a read each against a 60/hour channel, and printed a 'not visible yet' line that
    reads like a fault. This pins the property that convicted them, not the specific numbers.
    """
    cumulative, total = [], 0
    for d in pr_flow.LAG_RETRY_DELAYS:
        total += d
        cumulative.append(total + pr_flow.MEASURED_FIRST_READ_S)

    assert cumulative[0] > pr_flow.MEASURED_ARRIVAL_S["pr"], (
        "the FIRST retry must be able to answer the fast step; a rung that lands before the `pr` "
        "band closes is spending a read on a question that cannot yet have an answer")
    assert any(t > pr_flow.MEASURED_ARRIVAL_S["merge"] for t in cumulative[:-1]), (
        "a rung BEFORE the last must clear the `merge` band — a ladder whose final rung sits on the "
        "arrival point is a coin flip, which is exactly how #75 came to be censored")
    assert cumulative[-1] > 2 * pr_flow.MEASURED_ARRIVAL_S["merge"], (
        "the last rung is the tail probe: past it the right conclusion is 'something is wrong', so "
        "it must sit well clear of ordinary lag rather than just past it")


def test_lag_ladder_rungs_are_monotonic(monkeypatch):
    """Adversarial half: the property above is satisfiable by a ladder that is nonsense in shape.

    `(30, 1, 1)` passes every assertion in the test above while probing three times in two seconds
    after a half-minute of silence. Growth is what makes a rung's failure informative — each one
    must buy meaningfully more time than the last, or the extra reads tell you nothing new.
    """
    delays = pr_flow.LAG_RETRY_DELAYS
    assert len(delays) >= 2, "one rung cannot distinguish slow from stuck"
    assert all(b > a for a, b in zip(delays, delays[1:])), \
        f"rungs must grow: {delays} probes again before the platform has had more time to answer"


def test_lag_tolerant_stops_spending_when_the_read_budget_is_low(monkeypatch):
    """A probe that exhausts a 60/hour channel to polish a message has made things worse."""
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    monkeypatch.setitem(pr_flow.gh_read.BUDGET, "remaining", 3)
    calls = []

    def read():
        calls.append(1)
        return ({}, "anon-rest")

    value, ch, tries = pr_flow.lag_tolerant(read, lambda v: False)
    assert len(calls) == 1, "one read, then it stopped: the budget was below the floor"
    assert tries == 0


def test_lag_tolerant_returns_as_soon_as_the_read_view_catches_up(monkeypatch):
    """The point is to stop paying the moment the answer arrives, not to burn the whole ladder."""
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    monkeypatch.setattr(pr_flow, "LAG_RETRY_DELAYS", (0, 0))
    monkeypatch.setitem(pr_flow.gh_read.BUDGET, "remaining", 60)
    seq = [{"merged_at": None}, {"merged_at": "2026-08-13T00:00:00Z"}, {"merged_at": None}]
    value, ch, tries = pr_flow.lag_tolerant(lambda: (seq.pop(0), "anon-rest"),
                                            lambda v: bool(v.get("merged_at")))
    assert value["merged_at"] and tries == 1
    assert len(seq) == 1, "it stopped at the first satisfying read"


def test_lag_tolerant_spends_nothing_outside_a_post_mutation_verify(monkeypatch):
    """Ordinary runs must cost exactly what they cost today — this is a 60-reads/hour channel."""
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", None)
    calls = []
    pr_flow.lag_tolerant(lambda: (calls.append(1), ({}, "anon-rest"))[1], lambda v: False)
    assert len(calls) == 1


def test_mutation_proof_quotes_the_platforms_own_response(tmp_path, monkeypatch):
    """`"merged": true` from GitHub settles the question far better than an inference."""
    ev = tmp_path / "ev.json"
    ev.write_text('{"merged": true, "sha": "96e5d91", "message": "Pull Request merged"}')
    monkeypatch.setattr(pr_flow, "MUTATION_EVIDENCE", str(ev))
    proof = pr_flow.mutation_proof()
    assert "merged=True" in proof and "96e5d91" in proof


def test_mutation_proof_falls_back_to_the_set_e_inference(monkeypatch):
    """No evidence file is not no evidence: under `set -e` the tail only runs if the mutation did."""
    monkeypatch.setattr(pr_flow, "MUTATION_EVIDENCE", None)
    assert "exited 0" in pr_flow.mutation_proof()


def test_saved_plan_refuses_to_run_from_a_different_branch(work):
    """Consent was given for ONE step of ONE branch. The expiry and the precondition assertion both
    guard the STATE moving; neither guards the caller standing somewhere else."""
    path = pr_flow.write_saved_plan(str(work), "merge", "echo MUTATION-RAN", "merges PR #51",
                                    "feat/written-for")
    git(["switch", "-q", "-c", "some/other-branch"], cwd=work)
    r = subprocess.run(["bash", str(path)], capture_output=True, text=True)
    assert r.returncode != 0
    assert "MUTATION-RAN" not in r.stdout          # the mutation must not have run
    assert "feat/written-for" in r.stderr          # names what it was written for
    assert "some/other-branch" in r.stderr         # names where you actually are


def test_saved_plan_is_never_written_without_a_guard(work):
    """A guard that is silently absent is worse than none: the file still reads as safe."""
    with pytest.raises(ValueError):
        pr_flow.write_saved_plan(str(work), "merge", "gh api -X PUT /x", "merges PR #51", "")


def test_every_operator_step_supplies_the_branch_to_its_saved_plan():
    """`body` and `merge` were missed when the guard was first wired — `merge` being the
    irreversible step. A per-call-site audit is the only thing that catches an omission here."""
    src = pathlib.Path(pr_flow.__file__).read_text()
    missing = []
    for m in re.finditer(r'emit\(route, "([a-z-]+)"', src):
        s = m.start()
        depth, i = 0, s
        while i < len(src):
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if "branch=" not in src[s:i + 1]:
            missing.append(m.group(1))
    assert not missing, f"emit() call sites missing branch=: {missing}"


def test_discard_saved_plan_removes_a_spent_plan(work):
    """A plan that outlives its step stays runnable. That is how a stale plan re-issued a merge."""
    path = pr_flow.write_saved_plan(str(work), "merge", "gh api -X PUT /x", "merges PR #51",
                                    "feat/x")
    assert pathlib.Path(path).exists()
    assert pr_flow.discard_saved_plan(str(work))
    assert not pathlib.Path(path).exists()
    assert pr_flow.discard_saved_plan(str(work)) is None


def test_assert_preconditions_compares_counts_exactly_not_by_prefix(work, monkeypatch, capsys):
    """A prefix comparison would let an approved `failures=1` be satisfied by an actual 12."""
    monkeypatch.setattr(pr_flow.gh_read, "slug_from_remote", lambda *a, **k: "o/r")
    monkeypatch.setattr(pr_flow.gh_read, "pull_request",
                        lambda *a, **k: (open_pr("abc123"), "stub"))
    monkeypatch.setattr(pr_flow.gh_read, "check_runs", lambda *a, **k: (
        {"check_runs": [{"name": f"c{i}", "status": "completed", "conclusion": "failure"}
                        for i in range(12)]}, "stub"))
    monkeypatch.chdir(work)
    code = pr_flow.assert_preconditions(["pr=51", "failures=1"])
    assert code == EXIT_REFUSED
    assert "failures" in capsys.readouterr().out


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


def test_run_degrades_a_timeout_into_a_return_code_and_never_raises():
    """F33: an unhandled TimeoutExpired from `git fetch` crashed the driver out of its own exit-code
    contract. A guard that inspects a return code cannot see an exception, so the runner must be
    total — otherwise the guard written for 'the operation failed' misses the way it actually did."""
    r = pr_flow.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)
    assert r.returncode == pr_flow.TIMEOUT_RC
    assert "timed out" in r.stderr


def test_run_degrades_a_missing_binary_instead_of_raising():
    r = pr_flow.run(["definitely-not-a-real-binary-xyz"])
    assert r.returncode == pr_flow.UNRUNNABLE_RC
    assert "could not execute" in r.stderr


def test_an_escaping_exception_still_prints_the_route_and_exits_blocked(work, monkeypatch, capsys):
    """A state machine that dies without printing where it got is not carrying state. The four exit
    codes are the contract; a traceback is outside it."""
    commit_on(work, "feat/x")
    monkeypatch.chdir(work)
    monkeypatch.setattr(pr_flow, "drive",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    code = pr_flow.main(["--branch", "feat/x"])
    o = capsys.readouterr()
    assert code == EXIT_BLOCKED
    assert "route: " in o.out
    assert "state actually reached" in o.out
    assert "RuntimeError: boom" in o.err
    assert "Traceback" not in o.err


def test_a_failed_fetch_names_why_it_failed(work, monkeypatch, capsys):
    """The guard used to say only 'FAILED'. A timeout and a missing remote need different fixes, so
    the reason has to reach the caller."""
    commit_on(work, "feat/x")
    real = pr_flow.git

    def fake_git(args, cwd=None):
        if args[:2] == ["fetch", "--quiet"]:
            return subprocess.CompletedProcess(
                args, pr_flow.TIMEOUT_RC, "", "timed out after 60s (no response from the remote)")
        return real(args, cwd=cwd)

    monkeypatch.setattr(pr_flow, "git", fake_git)
    pr_flow.drive(args_for("feat/x"), str(work), pr_flow.Route())
    assert "timed out after 60s" in capsys.readouterr().out


# =================================================================================================
# THE CREDIBLE STATE SPACE, ENUMERATED FORWARD.
#
# The original regression replayed HISTORY — 49 past pull requests and 22 recorded failures — and
# was presented as coverage. It is not: a replay validates against the old failure surface, not the
# new one the mechanism itself creates. F34 was exactly that gap. "PR merged, branch not yet
# cleaned up" is a state this driver's OWN saved plan schedules on every single lifecycle, and it
# had no test, because it had never appeared in history — there was no driver before.
#
# So: enumerate the states the lifecycle can credibly ENTER, forward, and assert the verdict for
# each. Not the full cross-product (that is the ocean); the states a real ceremony passes through
# or lands in when something is off.
# =================================================================================================

def pr_at(sha, **kw):
    return open_pr(sha, **kw)


GREEN = {"check_runs": [{"name": "ci", "status": "completed", "conclusion": "success"}]}
PENDING = {"check_runs": [{"name": "ci", "status": "in_progress", "conclusion": None}]}
RED = {"check_runs": [{"name": "ci", "status": "completed", "conclusion": "failure"}]}
NO_RUNS = {"check_runs": []}

# id, prs-for-branch, check payload, full-PR override, children, expected exit, expected marker
LIFECYCLE_STATES = [
    ("S7  pushed, no pull request",        [],            NO_RUNS, None, (), EXIT_NEEDS_INPUT, "gh pr create"),
    ("S8  body lacks the scope block",     ["body-less"], NO_RUNS, None, (), EXIT_NEEDS_INPUT, "gh api -X PATCH"),
    ("S9  no check runs registered",       ["open"],      NO_RUNS, None, (), EXIT_NEEDS_INPUT, "NOT READY"),
    ("S10 checks still pending",           ["open"],      PENDING, None, (), EXIT_NEEDS_INPUT, "NOT READY"),
    ("S11 a check is failing",             ["open"],      RED,     None, (), EXIT_REFUSED,     "failing check"),
    ("S12 mergeable not yet computed",     ["open"],      GREEN, {"mergeable": None}, (), EXIT_NEEDS_INPUT, "NOT READY"),
    ("S13 not mergeable (conflict)",       ["open"],      GREEN, {"mergeable": False}, (), EXIT_REFUSED, "NOT mergeable"),
    ("S14 an open child is stacked on it", ["open"],      GREEN, None, ({"number": 29, "head": {"ref": "kid"}},), EXIT_REFUSED, "stacked on it"),
    ("S15 all clear -> merge",             ["open"],      GREEN, None, (), EXIT_NEEDS_INPUT, "gh api -X PUT"),
    # S16 ("merged, branch not yet cleaned up") is deliberately NOT a row here. Verified by removing
    # the fix: this harness leaves the branch containing origin/main, so a row for S16 passes
    # VACUOUSLY — the traversal never reaches the guard that breaks, and the row proves nothing
    # while reading as coverage. S16 requires the base-ahead geometry a real merge creates, so it
    # has its own test below, and that test was confirmed to FAIL without the fix.
    ("S21 pull request is a draft",        ["draft"],     GREEN, None, (), EXIT_REFUSED,     "DRAFT"),
    ("S22 two open pull requests, one head", ["open", "open2"], GREEN, None, (), EXIT_REFUSED, "open PRs share head"),
    ("S23 closed-unmerged, none open",     ["dead"],      NO_RUNS, None, (), EXIT_NEEDS_INPUT, "CLOSED and unmerged"),
]


@pytest.mark.parametrize("state", LIFECYCLE_STATES, ids=[s[0] for s in LIFECYCLE_STATES])
def test_every_credible_lifecycle_state_has_a_defined_verdict(work, monkeypatch, capsys, state):
    label, kinds, checks, full_override, children, want_code, want_text = state
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)

    made = []
    for k in kinds:
        if k == "open":
            made.append(pr_at(sha))
        elif k == "open2":
            made.append(pr_at(sha, number=52))
        elif k == "draft":
            made.append(pr_at(sha, draft=True))
        elif k == "dead":
            made.append(pr_at(sha, state="closed", merged_at=None))
        elif k == "merged":
            made.append(pr_at(sha, state="closed", merged_at="2026-08-04T00:00:00Z"))
        elif k == "body-less":
            made.append(pr_at(sha, body="no scope block here"))
    full = pr_at(sha, **(full_override or {}))
    if "merged" in kinds:
        full = pr_at(sha, state="closed", merged_at="2026-08-04T00:00:00Z")
    stub_reads(monkeypatch, prs=made, checks=checks, full=full, children=children)

    body = work.parent / "body.md"
    body.write_text("t\n```scope\ntools/pr-flow.py\n```\n")
    code, _ = drive(work, args_for("feat/x", body_file=str(body), title="t"))
    o = capsys.readouterr().out
    assert code == want_code, f"{label}: expected exit {want_code}, got {code}\n{o}"
    assert want_text in o, f"{label}: expected {want_text!r} in output\n{o}"


def test_s16_the_state_the_driver_itself_creates_never_prescribes_a_rebase(work, monkeypatch,
                                                                          capsys):
    """F34, pinned separately because it is the one that shipped broken. After a merge, origin/base
    has advanced PAST the branch, so the base-current guard WILL fire unless terminal state is
    resolved first. Reproduce that exact geometry: base ahead, branch merged."""
    commit_on(work, "feat/x")
    git(["push", "-u", "origin", "feat/x"], work)
    sha = head_of(work)
    git(["switch", "main"], work)
    (work / "after-merge.md").write_text("main moved on past the branch\n")
    git(["add", "-A"], work)
    git(["commit", "-m", "merge landed"], work)
    git(["push", "origin", "main"], work)
    git(["switch", "feat/x"], work)

    merged = pr_at(sha, state="closed", merged_at="2026-08-04T00:00:00Z")
    stub_reads(monkeypatch, prs=[merged], checks=GREEN, full=merged)
    code, route = drive(work, args_for("feat/x"))
    o = capsys.readouterr().out
    assert "rebase" not in o, "a merged branch must never be told to rebase"
    assert "already merged" in o
    assert route.state["base"] == "na"
    assert code == EXIT_NEEDS_INPUT and "push origin --delete feat/x" in o


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


# --- item 25: the observation record must PARTITION -------------------------------------------

def test_verify_and_visibility_are_separate_fields(work, monkeypatch):
    """Item 25. `is_verify` and `outcome` are independent facts and need independent fields.

    They were collapsed: `step` carried the sentinel "(not-a-verify)" and `outcome` could itself BE
    "not-a-verify". Measured on the real log — 26 series, only 6 of them verifies, all summarised
    together as "22 became visible". Anyone sizing the ladder from that would have averaged in twenty
    runs that were never waiting for anything.
    """
    import json as _json
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", None)          # an ORDINARY run
    pr_flow.lag_tolerant(lambda: ({}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="branch=feat/x")
    rec = _json.loads(pr_flow.lag_log_path(str(work)).read_text().splitlines()[-1])
    assert rec["is_verify"] is False
    assert rec["step"] is None, "the sentinel string is gone; absence is None"
    assert rec["outcome"] == "not-visible", "a non-verify is not a censored observation"


def test_outcomes_partition_and_the_footer_matches_its_own_table(work, monkeypatch, capsys):
    """The footer must count exactly the rows it printed.

    It previously reported '22 series' above 26 printed rows, because the tally recognised only
    `visible` plus the censored family and silently dropped everything else. A summary that
    disagrees with the table directly above it is the item-22 defect in another costume.
    """
    monkeypatch.setattr(pr_flow, "LAG_RETRY_DELAYS", (0,))
    monkeypatch.setitem(pr_flow.gh_read.BUDGET, "remaining", 60)
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "merge")
    pr_flow.lag_tolerant(lambda: ({}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="pr=1")          # censored verify
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", "pr")
    pr_flow.lag_tolerant(lambda: ({"x": 1}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="pr=2")          # visible verify
    monkeypatch.setattr(pr_flow, "AFTER_MUTATION", None)
    pr_flow.lag_tolerant(lambda: ({}, "anon-rest"), lambda v: bool(v),
                         root=str(work), subject="branch=x")      # ordinary, must be EXCLUDED
    capsys.readouterr()

    pr_flow.lag_report(str(work))
    out = capsys.readouterr().out
    assert "2 verify series" in out, "the ordinary run must not be counted as a verify"
    assert "1 ordinary runs also recorded" in out
    assert "TALLY DOES NOT PARTITION" not in out
    # A DATA row, matched by its shape: step, subject, attempt count, elapsed, outcome. Matching on
    # the word "visible" instead swept in the header and a caveat sentence — the filter must
    # discriminate rows from prose, or it cannot check what it claims to check.
    rows = [ln for ln in out.splitlines()
            if re.match(r"^  \S+\s+\S+\s+\d+\s+[\d.]+s\s+\S+$", ln)]
    assert len(rows) == 2, f"table must print exactly the 2 verify series, got {len(rows)}"


def test_pre_partition_records_are_upgraded_on_read_not_rewritten(work):
    """Migration. The log is EVIDENCE — the only real measurements of GitHub's read lag we have.

    Old records encode `is_verify` inside fields meant for other things. They are translated on
    READ; rewriting the file to 'clean' it would destroy the observations item 24 is waiting for.
    """
    old_verify = {"series": "a", "step": "merge", "outcome": "visible", "attempt": 0}
    old_ordinary = {"series": "b", "step": "(not-a-verify)", "outcome": "not-a-verify", "attempt": 0}

    up = pr_flow.normalize_observation(old_verify)
    assert up["is_verify"] is True and up["step"] == "merge"

    down = pr_flow.normalize_observation(old_ordinary)
    assert down["is_verify"] is False
    assert down["step"] is None
    assert down["outcome"] == "not-visible", "the old outcome sentinel maps to the real outcome"

    # and the originals are untouched — normalisation returns a copy
    assert old_ordinary["step"] == "(not-a-verify)"
