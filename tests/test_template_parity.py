"""Behaviour tests for tools/template-parity.py — the template<->live mirror check.

Each test builds a throwaway repo layout (tools/ + vault-template/) and a throwaway live
vault, then drives the real script as a subprocess — the way it actually runs at mirror
time — and asserts on its exit code and printed evidence. No fleet fixture is needed: the
parity tool is a standalone stdlib comparator, not a rendered fleet script.
"""
import json
import shutil
import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
REAL_TOOL = REPO / "tools" / "template-parity.py"

EXIT_OK, EXIT_DRIFT, EXIT_BLOCKED = 0, 1, 3

MANIFEST = {
    "lockstep": ["99-Operations/scripts/", "99-Operations/schemas/"],
    "exclude": ["99-Operations/schemas/naming-rules.json"],
}


def _write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _sandbox(tmp_path, template_files, live_files):
    """Lay out tmp/repo/{tools,vault-template} + tmp/live; return (repo, live)."""
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    shutil.copy(REAL_TOOL, repo / "tools" / "template-parity.py")
    (repo / "tools" / "template-sync-manifest.json").write_text(json.dumps(MANIFEST))
    template = repo / "vault-template"
    live = tmp_path / "live"
    for root, files in ((template, template_files), (live, live_files)):
        # every vault needs a 99-Operations/ dir to be recognised as a vault
        (root / "99-Operations").mkdir(parents=True, exist_ok=True)
        for rel, text in files.items():
            _write(root, rel, text)
    return repo, live


def _run(repo, live_arg):
    return subprocess.run(
        [sys.executable, str(repo / "tools" / "template-parity.py"), str(live_arg)],
        capture_output=True, text=True,
    )


BASE = {
    "99-Operations/scripts/a-first-script.md": "alpha\n",
    "99-Operations/schemas/some-schema-file.md": "schema\n",
}


def test_clean_mirror_is_zero_drift(tmp_path):
    repo, live = _sandbox(tmp_path, BASE, dict(BASE))
    r = _run(repo, live)
    assert r.returncode == EXIT_OK, r.stdout
    assert "2 lockstep files checked" in r.stdout
    assert "0 drift" in r.stdout


def test_hand_edited_live_file_is_differs_drift(tmp_path):
    live_files = dict(BASE)
    live_files["99-Operations/scripts/a-first-script.md"] = "alpha\n# stray local edit\n"
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_DRIFT
    assert "DIFFERS: 99-Operations/scripts/a-first-script.md" in r.stdout
    assert "1 drift" in r.stdout


def test_file_missing_from_live_is_flagged(tmp_path):
    live_files = {"99-Operations/scripts/a-first-script.md": "alpha\n"}  # schema dropped
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_DRIFT
    assert "MISSING-IN-LIVE: 99-Operations/schemas/some-schema-file.md" in r.stdout


def test_new_shipped_file_missing_from_template_is_flagged(tmp_path):
    live_files = dict(BASE)
    live_files["99-Operations/scripts/a-newer-script.md"] = "newer\n"  # in live, not template
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_DRIFT
    assert "MISSING-IN-TEMPLATE: 99-Operations/scripts/a-newer-script.md" in r.stdout


def test_generated_artifact_is_excluded_not_flagged(tmp_path):
    # naming-rules.json exists only in live (generated) — must NOT be drift
    live_files = dict(BASE)
    live_files["99-Operations/schemas/naming-rules.json"] = '{"generated": true}\n'
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_OK, r.stdout
    assert "1 excluded" in r.stdout
    assert "naming-rules.json" not in r.stdout


def test_no_live_vault_is_blocked(tmp_path):
    repo, live = _sandbox(tmp_path, BASE, dict(BASE))
    r = _run(repo, tmp_path / "does-not-exist")
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in r.stdout
