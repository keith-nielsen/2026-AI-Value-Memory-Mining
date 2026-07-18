"""Behaviour tests for tools/ship-release.py and tools/pr-state.py — the GitHub ceremony pair.

Each test builds a throwaway work repo cloned from a throwaway local BARE origin, so every
git layer (fetch, ls-remote, tags, push) is exercised for real and offline. Only `gh` is
faked: a stub executable prepended to PATH that answers reads from fixture files in
$GH_STUB_DIR — the tools never execute `gh` mutations, so the stub only ever serves reads.
The tools are driven as subprocesses and asserted on exit codes and printed evidence, the
same posture as the template-parity tests.
"""
import json
import os
import pathlib
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SHIP = REPO / "tools" / "ship-release.py"
PRSTATE = REPO / "tools" / "pr-state.py"

EXIT_OK, EXIT_REFUSED, EXIT_NEEDS_INPUT, EXIT_BLOCKED = 0, 1, 2, 3

CHANGELOG = """# Changelog

## [Unreleased]

## [0.1.31] - 2026-07-18

### Added
- Ceremony pair under test.

## [0.1.30] - 2026-07-17

### Changed
- Prior entry.
"""

GH_STUB = """#!/usr/bin/env python3
import os, pathlib, sys
d = pathlib.Path(os.environ["GH_STUB_DIR"])
args = sys.argv[1:]

def serve(path, default=None):
    if path.is_file():
        sys.stdout.write(path.read_text())
        raise SystemExit(0)
    if default is not None:
        sys.stdout.write(default)
        raise SystemExit(0)
    raise SystemExit(1)

if args[:2] == ["release", "view"]:
    # live gh exposes isLatest on `release list` only; `view --json` rejects it —
    # the stub mirrors that so the field split stays covered (caught on the first
    # real ship, which the original permissive stub had waved through)
    if "--json" in args and "isLatest" in args[args.index("--json") + 1]:
        sys.stderr.write('Unknown JSON field: "isLatest"\\n')
        raise SystemExit(1)
    p = d / ("release-" + args[2] + ".json")
    if p.is_file():
        serve(p)
    sys.stderr.write("release not found\\n")
    raise SystemExit(1)
if args[:2] == ["release", "list"]:
    serve(d / "releases.json", "[]")
if args[:2] == ["pr", "view"]:
    p = d / ("pr-" + args[2] + ".json")
    if p.is_file():
        serve(p)
    sys.stderr.write("no pull requests found\\n")
    raise SystemExit(1)
if args[:2] == ["run", "list"]:
    serve(d / "runs.json", "[]")
sys.stderr.write("gh-stub: unhandled: %r\\n" % (args,))
raise SystemExit(1)
"""


class Ceremony:
    """A work clone + bare origin + gh stub; the handle every test drives."""

    def __init__(self, tmp_path):
        self.origin = tmp_path / "origin.git"
        self.work = tmp_path / "work"
        self.stub_dir = tmp_path / "gh-stub"
        self.stub_dir.mkdir()
        bindir = tmp_path / "bin"
        bindir.mkdir()
        gh = bindir / "gh"
        gh.write_text(GH_STUB)
        gh.chmod(0o755)
        self.env = dict(os.environ)
        self.env["PATH"] = f"{bindir}{os.pathsep}{self.env['PATH']}"
        self.env["GH_STUB_DIR"] = str(self.stub_dir)

        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)],
                       check=True, capture_output=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.work)],
                       check=True, capture_output=True, text=True)
        self.git("checkout", "-q", "-B", "main")
        self.git("config", "user.name", "ci")
        self.git("config", "user.email", "ci@ci")
        (self.work / "CHANGELOG.md").write_text(CHANGELOG)
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.git("push", "-q", "-u", "origin", "main")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.work), *args],
                              check=True, capture_output=True, text=True)

    def head(self):
        return self.git("rev-parse", "HEAD").stdout.strip()

    def commit_change(self, msg="more"):
        (self.work / "file.txt").write_text(msg)
        self.git("add", "-A")
        self.git("commit", "-qm", msg)
        return self.head()

    def stub(self, name, payload):
        (self.stub_dir / name).write_text(json.dumps(payload))

    def run_tool(self, tool, *args):
        return subprocess.run([sys.executable, str(tool), *[str(a) for a in args]],
                              cwd=str(self.work), env=self.env,
                              capture_output=True, text=True)


@pytest.fixture
def ceremony(tmp_path):
    return Ceremony(tmp_path)


# ---------------------------------------------------------------- ship-release


def test_ship_blocked_on_malformed_version(ceremony):
    r = ceremony.run_tool(SHIP, "0.1.31")
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in r.stdout


def test_ship_refuses_unmerged_target(ceremony):
    unmerged = ceremony.commit_change("not pushed")  # local only — not on origin/main
    r = ceremony.run_tool(SHIP, "v0.1.31", "--commit", unmerged)
    assert r.returncode == EXIT_REFUSED
    assert "NOT an ancestor" in r.stdout
    # F10: no tag may exist after a refused merge proof
    tags = ceremony.git("tag", "--list").stdout.strip()
    assert tags == ""


def test_ship_refuses_missing_changelog_entry(ceremony):
    r = ceremony.run_tool(SHIP, "v9.9.9")
    assert r.returncode == EXIT_REFUSED
    assert "no '## [9.9.9]'" in r.stdout


def test_ship_full_ceremony_walk(ceremony):
    target = ceremony.head()

    # Step 1: guards pass, local tag is created and verified, push command is emitted.
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert "guard [branch]:" in r.stdout
    assert "guard [changelog]:" in r.stdout
    assert "mutated [local-tag]: created annotated v0.1.31" in r.stdout
    next_cmd = [ln for ln in r.stdout.splitlines() if ln.startswith("NEXT: ")][-1][6:]
    assert next_cmd == "git push origin refs/tags/v0.1.31"

    # The caller runs the emitted command through the gated channel.
    subprocess.run(next_cmd.split(), cwd=str(ceremony.work), env=ceremony.env,
                   check=True, capture_output=True)

    # Step 2: remote tag verified as landed on the target; release command is emitted.
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert f"layer [remote-tag]: v0.1.31 at {target[:12]}" in r.stdout
    next_cmd = [ln for ln in r.stdout.splitlines() if ln.startswith("NEXT: ")][-1][6:]
    assert next_cmd.startswith("gh release create v0.1.31 --verify-tag --latest")
    assert "--notes-file" in next_cmd

    # The caller creates the release; the stub now knows it.
    ceremony.stub("release-v0.1.31.json", {"tagName": "v0.1.31", "isDraft": False})
    ceremony.stub("releases.json", [{"tagName": "v0.1.31", "isLatest": True}])

    # Step 3: release verified, parity tally closes the ship.
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_OK
    assert ("parity: 1 version tags on origin / 1 releases — "
            "0 tags without a release, 0 releases without a tag") in r.stdout


def test_ship_refuses_stale_local_tag(ceremony):
    old = ceremony.head()
    ceremony.git("tag", "-a", "v0.1.31", "-m", "stale", old)
    new = ceremony.commit_change("newer")
    ceremony.git("push", "-q", "origin", "main")
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_REFUSED
    assert "stale local tag" in r.stdout
    # The true cause is named with both commits — never mis-reported as "not merged" (F10)
    assert old[:12] in r.stdout and new[:12] in r.stdout
    assert "NOT an ancestor" not in r.stdout


def test_ship_refuses_remote_tag_on_wrong_commit(ceremony):
    old = ceremony.head()
    ceremony.git("tag", "-a", "v0.1.31", "-m", "wrong", old)
    ceremony.git("push", "-q", "origin", "refs/tags/v0.1.31")
    ceremony.git("tag", "-d", "v0.1.31")
    ceremony.commit_change("newer")
    ceremony.git("push", "-q", "origin", "main")
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_REFUSED
    assert "wrong commit" in r.stdout


def test_ship_parity_tally_flags_release_gap(ceremony):
    target = ceremony.head()
    for tag in ("v0.1.30", "v0.1.31"):
        ceremony.git("tag", "-a", tag, "-m", tag, target)
        ceremony.git("push", "-q", "origin", f"refs/tags/{tag}")
    ceremony.stub("release-v0.1.31.json", {"tagName": "v0.1.31", "isDraft": False})
    ceremony.stub("releases.json", [{"tagName": "v0.1.31", "isLatest": True}])
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_REFUSED
    assert "parity-miss [release-object]: tag v0.1.30 has no Release" in r.stdout
    assert "2 version tags on origin / 1 releases — 1 tags without a release" in r.stdout


# ------------------------------------------------------------------- pr-state


PR_BASE = {
    "number": 7, "title": "test pr", "url": "https://example.invalid/pr/7",
    "state": "OPEN", "isDraft": False, "mergeable": "MERGEABLE",
    "mergeStateStatus": "CLEAN", "baseRefName": "main", "headRefName": "main",
    "headRefOid": "", "statusCheckRollup": [],
}


def test_pr_state_blocked_when_pr_not_found(ceremony):
    r = ceremony.run_tool(PRSTATE, "99")
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in r.stdout


def test_pr_state_reports_every_layer_by_name(ceremony):
    pr = dict(PR_BASE)
    pr["headRefOid"] = ceremony.head()
    pr["statusCheckRollup"] = [
        {"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}]
    ceremony.stub("pr-7.json", pr)
    ceremony.stub("runs.json", [
        {"name": "CI", "status": "completed", "conclusion": "success",
         "event": "pull_request"}])
    r = ceremony.run_tool(PRSTATE, "7")
    assert r.returncode == EXIT_OK
    for token in ("layer [pr-state-machine · GraphQL]:", "layer [branch]:",
                  "layer [check-aggregation]: 1 of 1 checks successful",
                  "layer [workflow-run]: CI (pull_request): success",
                  "layer [event-payload]:", "note [mutation-verify]:"):
        assert token in r.stdout, token
    assert "LAYERS-DISAGREE" not in r.stdout
    assert "HAZARD" not in r.stdout


def test_pr_state_flags_deleted_base_branch(ceremony):
    pr = dict(PR_BASE)
    pr["baseRefName"] = "gone-parent-branch"
    pr["headRefOid"] = ceremony.head()
    ceremony.stub("pr-7.json", pr)
    r = ceremony.run_tool(PRSTATE, "7")
    assert r.returncode == EXIT_OK
    assert "HAZARD [branch]: base branch 'gone-parent-branch' is deleted" in r.stdout


def test_pr_state_pending_checks_are_not_failures(ceremony):
    pr = dict(PR_BASE)
    pr["headRefOid"] = ceremony.head()
    pr["statusCheckRollup"] = [
        {"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"},
        {"name": "fleet", "status": "IN_PROGRESS", "conclusion": None}]
    ceremony.stub("pr-7.json", pr)
    ceremony.stub("runs.json", [
        {"name": "CI", "status": "completed", "conclusion": "success",
         "event": "pull_request"}])
    r = ceremony.run_tool(PRSTATE, "7")
    assert r.returncode == EXIT_OK
    assert "layer [check-aggregation]: 1 of 2 checks successful, 1 pending" in r.stdout
    assert "IN_PROGRESS: fleet" in r.stdout
    # settled-vs-pending is expected skew, not a layer disagreement
    assert "LAYERS-DISAGREE" not in r.stdout


def test_pr_state_names_disagreeing_layers(ceremony):
    pr = dict(PR_BASE)
    pr["headRefOid"] = ceremony.head()
    pr["statusCheckRollup"] = [
        {"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"},
        {"name": "scope-review", "status": "COMPLETED", "conclusion": "FAILURE"}]
    ceremony.stub("pr-7.json", pr)
    ceremony.stub("runs.json", [
        {"name": "CI", "status": "completed", "conclusion": "success",
         "event": "pull_request"}])
    r = ceremony.run_tool(PRSTATE, "7")
    assert r.returncode == EXIT_OK
    assert "LAYERS-DISAGREE:" in r.stdout
    assert "FAILURE: scope-review" in r.stdout
