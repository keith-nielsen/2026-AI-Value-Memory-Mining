"""Behaviour tests for tools/preflight.py — the local route pre-flight (ADR-0041).

The tool exists to reduce error INCIDENCE by moving checks from continuous integration to the
keyboard. Its own failure mode is therefore the one that matters most: printing `CLEAR` while
silently not having run half of CI. Coverage accounting is tested before anything else.

Synthetic repositories rather than a copy of this one: the states worth testing (a job the tool
does not know about, a check that cannot run) are states this repository is not in, and waiting for
it to enter them is not a test.
"""
import importlib.util
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("preflight", REPO / "tools" / "preflight.py")
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


CI_TEMPLATE = """\
name: ci
on:
  push:
jobs:
{jobs}
"""

HEREDOC_JOB = """\
  spec-lint:
    runs-on: ubuntu-latest
    steps:
      - name: Check something with stdlib
        run: |
          python3 - << 'EOF'
          print("ok")
          EOF
"""


def make_repo(tmp_path, jobs):
    root = tmp_path / "repo"
    (root / ".github/workflows").mkdir(parents=True)
    (root / ".github/workflows/ci.yml").write_text(CI_TEMPLATE.format(jobs=jobs))
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    return root


# --- coverage: the tool's own worst failure mode -------------------------------------------------

def test_a_ci_job_the_tool_does_not_know_about_is_reported_as_a_silent_gap(tmp_path, capsys,
                                                                           monkeypatch):
    """The anti-vacuity property, and the reason this file leads with it.

    A pre-flight that prints CLEAR while quietly skipping jobs is worse than no pre-flight, because
    it is believed. This repository's own record is full of that shape — `md-lint`'s `|| true`, two
    hardcoded `/tmp` paths, and a poll loop that reported READY over 22 pending checks.

    The specific decay this guards: someone adds a job to `ci.yml` tomorrow. Without accounting, the
    fraction the tool covers shrinks silently while the verdict keeps saying CLEAR.
    """
    root = make_repo(tmp_path, HEREDOC_JOB + "  brand-new-job:\n    runs-on: ubuntu-latest\n")
    monkeypatch.setattr(preflight, "LOCAL_JOBS", [])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    rc = preflight.main()
    out = capsys.readouterr().out

    assert "UNACCOUNTED" in out, "a job the tool neither runs nor explains must be named"
    assert "brand-new-job" in out
    assert rc == 1, "an unaccounted job must FAIL the run, not merely be mentioned"
    assert "CLEAR" not in out, "the verdict must not read clear while coverage is incomplete"


def test_coverage_partitions_every_declared_job(tmp_path, monkeypatch, capsys):
    """Reproduced / unrunnable / not-reproduced must cover every job — item 25's lesson.

    A tally that covers some of its categories is how a footer comes to contradict its own table.
    """
    root = make_repo(tmp_path, HEREDOC_JOB + "  md-lint:\n    runs-on: ubuntu-latest\n")
    monkeypatch.setattr(preflight, "LOCAL_JOBS", [])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    preflight.main()
    out = capsys.readouterr().out
    assert "UNACCOUNTED" not in out, "md-lint is declared in NOT_LOCAL, so it is accounted for"
    assert "md-lint" in out, "a job that is not reproduced must still be NAMED, with its reason"


def test_ci_jobs_is_derived_from_the_file_never_hardcoded(tmp_path):
    """A hardcoded job list is correct only on the day it is written — item 10's `range(1, 9)`."""
    root = make_repo(tmp_path, HEREDOC_JOB + "  another:\n    runs-on: ubuntu-latest\n")
    assert set(preflight.ci_jobs(root)) == {"push", "spec-lint", "another"}


# --- SKIP is not PASS ----------------------------------------------------------------------------

@pytest.mark.parametrize("stderr,expected", [
    ("OSError: [Errno 30] Read-only file system: '/tmp/x.py'", "SKIP"),
    ("bash: markdownlint: command not found", "SKIP"),
    ("unshare: Operation not permitted", "SKIP"),
    ("AssertionError: the corpus is wrong", "FAIL"),
])
def test_a_check_that_could_not_run_is_skip_not_fail_and_not_pass(stderr, expected):
    """An environment limitation is not a finding — and it is not a pass either.

    Both errors are live in this repository: the `secret-scan` job writes its scanner to a hardcoded
    `/tmp` path, and `validate-scripts.sh` redirects to bare `/tmp` (queue item 10, two instances).
    Under a write-scoped sandbox those produce 12 false FAILs for checks that never ran. Calling
    them PASS would be the opposite and worse error.
    """
    class R:
        returncode = 1
    R.stderr, R.stdout = stderr, ""
    verdict, why = preflight.verdict_for(R)
    assert verdict == expected
    if expected == "SKIP":
        assert why, "a skip must carry its reason, or it is indistinguishable from a pass"


def test_a_zero_exit_is_pass_regardless_of_output():
    class R:
        returncode = 0
        stderr = "warning: Read-only file system somewhere harmless"
        stdout = "fine"
    assert preflight.verdict_for(R)[0] == "PASS", \
        "the SKIP heuristic reads stderr, so it must never override a genuine success"


# --- the archive simulation ----------------------------------------------------------------------

def test_the_archive_simulation_catches_a_citation_that_only_dangles_once_archived(tmp_path,
                                                                                   monkeypatch,
                                                                                   capsys):
    """The measured motivation for this whole tool — PR #79, 2026-08-15.

    A forward ADR citation is LEGAL inside a live change directory and ILLEGAL inside the archive,
    because an archived change is a record and a record must resolve. So the act of archiving is
    what converts a legitimate reference into a dangling one, without the text changing. It turned
    a pull request red after a push, a PR and a red check-run — and it is decidable locally by
    copying the change to an archive path and re-running the shipped checker.
    """
    root = make_repo(tmp_path, HEREDOC_JOB)
    (root / "openspec/adr").mkdir(parents=True)
    (root / "openspec/adr/0001-first.md").write_text("# ADR-0001\n")
    live = root / "openspec/changes/some-change"
    live.mkdir(parents=True)
    (root / "openspec/changes/archive").mkdir()
    # The citation token is BUILT, never spelled: this file is a record for the very checker
    # under test, so spelling the token literally here would dangle in the real corpus and
    # fail CI. Caught twice by running the pre-flight: once for the fixture data, and again
    # for the COMMENT that explained the first fix and spelled the token while doing so.
    fake = "ADR-" + "0099"
    (live / "tasks.md").write_text(f"- [ ] 1.1 blocked until {fake} is written\n")

    # NOT textwrap.dedent: `ci_steps()` matches `^      - name:` with SIX spaces and requires the
    # heredoc two lines below. Dedent strips exactly the indentation the extractor keys on, so a
    # dedented fixture silently produces a ci.yml with no extractable steps — the check would then
    # "pass" by never running. Found by running this test.
    checker = (
        "      - name: Check every cited ADR resolves\n"
        "        run: |\n"
        "          python3 - << 'EOF'\n"
        "          import pathlib, re, sys\n"
        '          have = {int(p.name[:4]) for p in pathlib.Path("openspec/adr").glob("[0-9]*-*.md")}\n'
        "          bad = []\n"
        '          for path in pathlib.Path(".").rglob("*.md"):\n'
        "              parts = path.parts\n"
        '              if len(parts) > 2 and parts[0] == "openspec" and parts[1] == "changes" and parts[2] != "archive":\n'
        "                  continue\n"
        '              for m in re.finditer(r"ADR-([0-9]{4})", path.read_text()):\n'
        "                  if int(m.group(1)) not in have:\n"
        '                      bad.append(f"{path}: ADR-{m.group(1)}")\n'
        '          print("\\n".join(bad), file=sys.stderr)\n'
        "          sys.exit(1 if bad else 0)\n"
        "          EOF\n"
    )
    ci = (root / ".github/workflows/ci.yml")
    ci.write_text(ci.read_text().replace(
        "  spec-lint:\n    runs-on: ubuntu-latest\n    steps:\n",
        "  spec-lint:\n    runs-on: ubuntu-latest\n    steps:\n" + checker))

    monkeypatch.setattr(preflight, "LOCAL_JOBS", [])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    rc = preflight.main()
    out = capsys.readouterr().out

    assert "MUST DEFER" in out, \
        "the change cites an ADR that does not exist; archiving it would dangle the citation"
    assert "some-change" in out
    assert rc == 1

    # And the adversarial half: writing the record clears it. A guard that never passes is not a
    # guard, it is an obstacle — and this exact flip was observed on the real branch.
    (root / "openspec/adr/0099-now-written.md").write_text(f"# {fake}\n")
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    rc2 = preflight.main()
    out2 = capsys.readouterr().out
    assert "CAN ARCHIVE" in out2, "once the cited record exists the change may archive"
    assert rc2 == 0


def test_two_live_changes_on_one_capability_spec_are_both_named(tmp_path, monkeypatch, capsys):
    """Task 6.2 — the concurrency case, and ADR-0040's deferred follow-on made decidable.

    ADR-0040 left open whether the exception could be decided from repository state. It can, and the
    report must name BOTH changes: a report saying only "defer" leaves the reader to work out which
    change defers to which, and the merge ORDER is the whole content of the exception.

    Measured relevance: on 2026-08-15 this question was answered by hand for item 26, and the
    hand-answer was initially WRONG — a task note claimed no concurrent maintenance delta existed
    when two branches carried one.
    """
    root = make_repo(tmp_path, HEREDOC_JOB)
    (root / "openspec/changes/archive").mkdir(parents=True)
    for name in ("change-alpha", "change-beta"):
        d = root / "openspec/changes" / name
        (d / "specs/maintenance").mkdir(parents=True)
        (d / "specs/maintenance/spec.md").write_text("## ADDED Requirements\n")
        (d / "tasks.md").write_text("- [x] 1.1 done\n")

    monkeypatch.setattr(preflight, "LOCAL_JOBS", [])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    preflight.main()
    out = capsys.readouterr().out
    assert "change-alpha" in out and "change-beta" in out, \
        "both sides of a concurrency decision must be named, or the reader cannot order them"


def test_the_trial_merge_predicts_a_conflict_before_any_push(tmp_path, monkeypatch, capsys):
    """Task 6.4 — `mergeable` is judged by the platform only after a push; predict it locally.

    Two branches appending to the same spec file is the exact shape produced by two changes with a
    delta on one capability, which is the normal state of this repository.
    """
    root = make_repo(tmp_path, HEREDOC_JOB)
    spec_file = root / "spec.md"
    run = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)
    run("config", "user.email", "t@example.com")
    run("config", "user.name", "T")
    spec_file.write_text("base\n")
    run("add", "-A"); run("commit", "-qm", "base")
    run("branch", "other")
    spec_file.write_text("base\nHEAD's line\n")
    run("add", "-A"); run("commit", "-qm", "head")
    run("checkout", "-q", "other")
    spec_file.write_text("base\nother's conflicting line\n")
    run("add", "-A"); run("commit", "-qm", "other")
    run("checkout", "-q", "main")

    monkeypatch.setattr(preflight, "LOCAL_JOBS", [])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root), "--base", "other"])
    rc = preflight.main()
    out = capsys.readouterr().out
    assert "CONFLICTS" in out, "a conflict the platform would report after a push must surface here"
    assert rc == 1


def test_a_missing_executable_skips_instead_of_crashing_the_run(tmp_path, monkeypatch, capsys):
    """Found by RUNNING the tool in a scratch repo, not by any test above it.

    `subprocess.run` RAISES `FileNotFoundError` for an absent executable rather than returning
    non-zero, so a machine without `node_modules` crashed the entire pre-flight — taking the coverage
    report with it, which is the one thing that must always print.

    ⚠ Every other test in this file monkeypatches `LOCAL_JOBS` to `[]` and therefore never reaches
    the loop where this lives. That is the reachability failure the repository keeps recording:
    *which real invocation reaches this line?* — answered by running, not by reading. This test
    deliberately exercises the real path with a job whose command does not exist.
    """
    root = make_repo(tmp_path, HEREDOC_JOB)
    monkeypatch.setattr(preflight, "LOCAL_JOBS",
                        [("openspec-validate", ["definitely-not-a-real-binary-xyz", "--check"])])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    rc = preflight.main()
    out = capsys.readouterr().out

    assert "SKIP" in out, "an absent tool is a local limitation, not a finding and not a pass"
    assert "COVERAGE" in out, "the coverage report must survive an unavailable check"
    assert "openspec-validate" in out
    assert rc == 0, "a skipped check must not be counted as a failure"


def test_no_live_change_directory_is_not_an_error(tmp_path, monkeypatch, capsys):
    """Most branches carry no change dir at all (defect fixes ship bare). That is not a finding."""
    root = make_repo(tmp_path, HEREDOC_JOB)
    monkeypatch.setattr(preflight, "LOCAL_JOBS", [])
    monkeypatch.setattr(sys, "argv", ["preflight.py", str(root)])
    rc = preflight.main()
    out = capsys.readouterr().out
    assert "nothing owed" in out
    assert rc == 0, "a clean synthetic repo must pass, or the tool cries wolf on every branch"
