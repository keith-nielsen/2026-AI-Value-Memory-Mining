"""Tests for the INV-6 static checker.

Weighted deliberately toward the FALSE-POSITIVE direction. A checker that fires on real network
calls is easy; one that stays silent on the INV-14 guards — whose entire purpose is to *name*
`git push`, `gh repo create` and `npm publish` inside regex literals — is the hard and necessary
property. Get that wrong and the two most security-relevant scripts in the fleet fail CI forever,
which ends with the check being disabled rather than the fleet being fixed (RC-E: over-denial is
camouflage).
"""
import importlib.util
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location("inv6", REPO / "tools" / "inv6-offline-check.py")
inv6 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inv6)


def viols(findings):
    return [f for f in findings if f[1] == "VIOLATION"]


def test_selftest_is_healthy():
    # The control for every other test here.
    assert inv6.selftest() == []


@pytest.mark.parametrize("src,why", [
    ("import socket", "network module"),
    ("import urllib.request", "dotted network module"),
    ("from http.client import HTTPSConnection", "from-import of a network module"),
    ("import subprocess\nsubprocess.run(['curl', 'https://x'])", "subprocess curl"),
    ("import subprocess\nsubprocess.check_output(['gh', 'api', '/x'])", "subprocess gh"),
    ("import subprocess\nsubprocess.run(['git', 'push', 'origin', 'main'])", "git push"),
    ("import subprocess\nsubprocess.run(['git', 'ls-remote', 'origin'])", "git ls-remote"),
    ("import os\nos.system('wget https://x')", "os.system wget"),
    ("__import__('socket')", "dynamic import of a network module"),
])
def test_python_violations_are_detected(src, why):
    assert viols(inv6.check_python(src)), why


@pytest.mark.parametrize("src,why", [
    ('import re\nOUTWARD = re.compile(r"\\bgit\\s+push\\b|\\bgh\\s+repo\\s+create\\b")',
     "outward verbs as regex literals — the INV-14 guard case"),
    ('PUBLISH = "npm publish|twine upload|docker push"', "verbs in a plain string"),
    ("import subprocess\nsubprocess.run(['git', 'diff', '--cached', '--name-only'])", "local git"),
    ("import subprocess\nsubprocess.run(['git', 'commit', '-F', 'msg.txt'])", "local git commit"),
    ("import pathlib, json, re, sys", "ordinary stdlib imports"),
    ('print("do not run git push from here")', "verb inside a print"),
])
def test_python_names_are_not_flagged(src, why):
    assert not viols(inv6.check_python(src)), f"false positive on {why}"


@pytest.mark.parametrize("src,why", [
    ("curl -s https://example.com", "bash curl"),
    ("git push origin main", "bash git push"),
    ("cd /tmp && wget https://x", "network binary after &&"),
])
def test_bash_violations_are_detected(src, why):
    assert viols(inv6.check_bash(src)), why


@pytest.mark.parametrize("src,why", [
    ('echo "never run git push here"', "verb inside a quoted string"),
    ("# git push is what this hook blocks", "verb inside a comment"),
    ("git diff --cached --name-only --diff-filter=AR", "local git"),
    ("git rev-parse HEAD", "local git rev-parse"),
])
def test_bash_names_are_not_flagged(src, why):
    assert not viols(inv6.check_bash(src)), f"false positive on {why}"


def test_unresolvable_indirection_is_reported_not_ignored():
    # Static analysis cannot decide this. Reporting it as UNRESOLVED rather than clean is the
    # honest behaviour: silence here would be a claim the tool cannot support.
    f = inv6.check_python("import importlib\nimportlib.import_module(name)")
    assert any(k == "UNRESOLVED" for _, k, _ in f)


def test_computed_argv_is_reported_not_ignored():
    f = inv6.check_python("import subprocess\nsubprocess.run(cmd)")
    assert any(k == "UNRESOLVED" for _, k, _ in f)


def test_the_real_fleet_is_clean():
    """The end-to-end assertion: every shipped fleet note passes, guards included."""
    notes = sorted((REPO / "vault-template" / "99-Operations" / "scripts").glob("*.md"))
    assert len(notes) >= 14, f"expected the full fleet, found {len(notes)}"
    problems = {n.name: inv6.check_note(n) for n in notes if inv6.check_note(n)}
    assert problems == {}, f"fleet is not statically clean: {problems}"


@pytest.mark.parametrize("guard", ["outbound-publish-guard-script", "push-guard-script"])
def test_inv14_guards_name_outward_verbs_and_still_pass(guard):
    """The discrimination, asserted on the real files rather than on fixtures.

    These two notes genuinely contain `git push` / `gh repo create` / `npm publish`. A naive
    grep flags them; the AST/command-position analysis must not.
    """
    note = REPO / "vault-template" / "99-Operations" / "scripts" / f"{guard}.md"
    text = note.read_text()
    assert "push" in text, "precondition: this guard should name outward verbs"
    assert not viols(inv6.check_note(note)), f"{guard} was flagged for NAMING a verb it blocks"
