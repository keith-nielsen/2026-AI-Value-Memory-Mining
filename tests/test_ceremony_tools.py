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

if args[:1] == ["api"]:
    # The shared read layer's fallback channel (item 21). Paths are the ones ship-release asks
    # for; anything else is an unhandled case and must fail loudly rather than answer emptily.
    path = args[1]
    if "/releases/latest" in path:
        serve(d / "latest.json")            # absent file => exit 1, i.e. no Latest release
    if "/releases" in path:
        if "page=2" in path:          # the fixtures never exceed one page
            sys.stdout.write("[]")
            raise SystemExit(0)
        serve(d / "releases.json", "[]")
    sys.stderr.write("gh-stub: unhandled api path: %r\\n" % (path,))
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
        # The bare origin lives at a PATH that parses as a GitHub URL, so `slug_from_remote` — which
        # reads `git remote get-url origin` and matches `github.com/<owner>/<repo>` — resolves a real
        # slug while every git operation stays local and offline. Note `insteadOf` does NOT work for
        # this: `git remote get-url` applies the rewrite and reports the local path, defeating the
        # split it appears to give.
        self.slug = "vmm-test/ceremony"
        self.origin = tmp_path / "github.com" / "vmm-test" / "ceremony.git"
        self.origin.parent.mkdir(parents=True)
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
        # STILL OFFLINE after ship-release moved to the shared read layer (item 21). `gh_read.get()`
        # tries the anonymous REST channel first and falls back to `gh api`; pointing the proxy at a
        # closed port makes the anonymous attempt fail immediately with URLError, so the faked `gh`
        # serves — deterministically, with no packet leaving the machine. These tests therefore
        # exercise the FALLBACK channel; the anonymous path is covered by running the real tool
        # against the real repository, which is where it has to work anyway.
        self.env["https_proxy"] = self.env["HTTPS_PROXY"] = "http://127.0.0.1:1"

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
    # `-C <root>`, not a bare `git push`. This assertion previously encoded the DEFECT: the emitted
    # command depended on the caller's cwd, so it could not be run verbatim from anywhere else — and
    # a command that cannot be run as emitted can never match its own emission record (ADR-0043).
    # Measured shipping v0.1.48 on 2026-08-17.
    assert next_cmd == f"git -C {ceremony.work} push origin refs/tags/v0.1.31"

    # The caller runs the emitted command through the gated channel — now from an UNRELATED cwd
    # (the origin's parent, not the work tree), which is the property `-C` exists to give and the
    # old form did not have. An agent's shell resets its cwd between calls; this is that geometry.
    subprocess.run(next_cmd.split(), cwd=str(ceremony.origin.parent), env=ceremony.env,
                   check=True, capture_output=True)

    # Step 2: remote tag verified as landed on the target; release command is emitted.
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert r.returncode == EXIT_NEEDS_INPUT
    assert f"layer [remote-tag]: v0.1.31 at {target[:12]}" in r.stdout
    next_cmd = [ln for ln in r.stdout.splitlines() if ln.startswith("NEXT: ")][-1][6:]
    # `-R <slug>` for the same reason as `-C` above: the emitted command names its subject rather
    # than inheriting it from wherever the caller happens to be standing.
    assert next_cmd.startswith(f"gh release create v0.1.31 -R {ceremony.slug} --verify-tag --latest")
    assert "--notes-file" in next_cmd

    # The caller creates the release; the stub now knows it.
    # Fixtures are REST-shaped, because that is what the read layer actually receives.
    ceremony.stub("releases.json", [{"tag_name": "v0.1.31", "draft": False}])
    ceremony.stub("latest.json", {"tag_name": "v0.1.31"})

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
    ceremony.stub("releases.json", [{"tag_name": "v0.1.31", "draft": False}])
    ceremony.stub("latest.json", {"tag_name": "v0.1.31"})
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


def test_ship_reads_do_not_require_gh_at_all(ceremony):
    """Item 21 — THE defect. Measured twice mid-ceremony on this repo's own v0.1.40 ship.

    `gh release view` / `gh release list` need the operating-system keyring; a confined session gets
    a misleading 401 and the driver exited `3 BLOCKED` on a READ, after both real guards had passed.
    That violates the shipped `maintenance` requirement *GitHub Reads Degrade To An Unauthenticated
    Channel* and made the whole release ceremony operator-only by defect.

    The strongest available statement of "reads no longer need `gh`" is to remove `gh` from PATH
    entirely and require the driver to still answer. The anonymous channel is unreachable here (the
    proxy points at a closed port), so with no `gh` either, BOTH channels are gone — the driver must
    then BLOCK on a named read failure rather than on `gh` being absent, and must never claim a
    release state it could not observe.
    """
    env = dict(ceremony.env)
    env["PATH"] = "/usr/bin:/bin"          # the stub is gone; real gh is not on this PATH either
    r = subprocess.run([sys.executable, str(SHIP), "v0.1.31"],
                       cwd=str(ceremony.work), env=env, capture_output=True, text=True)
    assert r.returncode == EXIT_BLOCKED
    assert "cannot read releases" in r.stdout, \
        "a failed read must be named as a read failure, not as a missing binary"
    assert "gh release view" not in r.stdout, "the tool must no longer shell out to gh for reads"


def test_ship_names_the_channel_that_answered(ceremony):
    """The same requirement's second half: report the channel alongside the data.

    A read that does not say which channel answered is a bare assertion — the caller cannot tell a
    measured state from a defaulted one.
    """
    ceremony.stub("releases.json", [{"tag_name": "v0.1.31", "draft": False}])
    ceremony.stub("latest.json", {"tag_name": "v0.1.31"})
    ceremony.git("tag", "-a", "v0.1.31", "-m", "t", ceremony.head())
    ceremony.git("push", "-q", "origin", "refs/tags/v0.1.31")
    r = ceremony.run_tool(SHIP, "v0.1.31")
    assert "layer [release-object]:" in r.stdout
    assert "[via " in r.stdout, "the release-object layer must name its channel"


def test_absent_vs_draft_is_stated_on_anon_and_silent_on_gh():
    """Exhaustiveness, tested at the seam because the channel decides the answer.

    GitHub hides DRAFT releases from unauthenticated callers, so on `anon-rest` a missing release
    means *absent OR draft* and the driver must say so — emitting `gh release create` against an
    existing draft is the failure. On `gh-api` the caller is authenticated, drafts ARE visible, and
    the caveat must stay SILENT: printing it anyway is over-denial, which teaches readers to skip
    warnings. Found by the design pass rather than by a failure, which is the point of doing one.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("ship_under_test", SHIP)
    ship = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ship)

    anon = ship.draft_caveat(None, ship.gh_read.CH_ANON, "v0.1.31")
    assert anon and "absent OR draft" in anon

    assert ship.draft_caveat(None, ship.gh_read.CH_GH, "v0.1.31") is None, \
        "authenticated reads see drafts — no caveat is owed"
    assert ship.draft_caveat({"tagName": "v0.1.31", "isDraft": False},
                             ship.gh_read.CH_ANON, "v0.1.31") is None, \
        "a release that WAS found carries no ambiguity"
