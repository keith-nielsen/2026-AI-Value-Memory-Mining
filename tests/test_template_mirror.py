"""Behaviour tests for tools/template-mirror.py — the template->live mirror driver.

Same posture as test_template_parity.py: build a throwaway repo layout (tools/ +
vault-template/) and a throwaway live vault, drive the real script as a subprocess the way it
runs at mirror time, and assert on its exit code, printed evidence, and — because this tool
WRITES — the resulting filesystem state. The real live vault / $VAULT_ROOT is never touched;
every fixture is a temp dir (T8, the real dogfood, is a ship-time step, not a unit test).
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
MIRROR_TOOL = REPO / "tools" / "template-mirror.py"
SHARED_LIB = REPO / "tools" / "template_sync.py"
CONTRIBUTING = REPO / "CONTRIBUTING.md"

EXIT_OK, EXIT_NEEDS_INPUT, EXIT_BLOCKED = 0, 2, 3

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
    shutil.copy(MIRROR_TOOL, repo / "tools" / "template-mirror.py")
    shutil.copy(SHARED_LIB, repo / "tools" / "template_sync.py")  # sibling import at runtime
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
        [sys.executable, str(repo / "tools" / "template-mirror.py"), str(live_arg)],
        capture_output=True, text=True,
    )


def _tree_hash(root):
    """A stable digest of every file path + bytes under root, for before/after comparison."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    return h.hexdigest()


BASE = {
    "99-Operations/scripts/a-first-script.md": "alpha\n",
    "99-Operations/schemas/some-schema-file.md": "schema\n",
}


# T1 — no-op idempotency: already at parity, nothing copied, filesystem byte-for-byte unchanged.
def test_t1_noop_idempotency(tmp_path):
    repo, live = _sandbox(tmp_path, BASE, dict(BASE))
    before = _tree_hash(live)
    r = _run(repo, live)
    assert r.returncode == EXIT_OK, r.stdout
    assert "0 drift" in r.stdout
    assert "MIRRORED:" not in r.stdout
    assert _tree_hash(live) == before  # not one byte changed


# T2 — forward mirror, file missing from live: it is copied, parity re-verified, exit 0.
def test_t2_forward_mirror_missing_file(tmp_path):
    live_files = {"99-Operations/scripts/a-first-script.md": "alpha\n"}  # schema absent in live
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_OK, r.stdout
    assert "MIRRORED: 99-Operations/schemas/some-schema-file.md (was MISSING-IN-LIVE)" in r.stdout
    assert (live / "99-Operations/schemas/some-schema-file.md").read_text() == "schema\n"
    assert "0 drift" in r.stdout


# T3 — forward mirror, differing content: live is overwritten with the repo's bytes, exit 0.
def test_t3_forward_mirror_differing_content(tmp_path):
    live_files = dict(BASE)
    live_files["99-Operations/scripts/a-first-script.md"] = "alpha\n# stray local edit\n"
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_OK, r.stdout
    assert "MIRRORED: 99-Operations/scripts/a-first-script.md (was DIFFERS)" in r.stdout
    # live now byte-identical to the repo template
    assert (live / "99-Operations/scripts/a-first-script.md").read_bytes() == b"alpha\n"
    assert "0 drift" in r.stdout


# T4 — untracked-live-file safety: a live-only lockstep file is never deleted/modified, is
# reported under its own MISSING-IN-TEMPLATE header, and the run exits 2 (not 0).
def test_t4_untracked_live_file_is_reported_not_deleted(tmp_path):
    live_files = dict(BASE)
    live_files["99-Operations/scripts/a-live-only-script.md"] = "live only\n"
    repo, live = _sandbox(tmp_path, BASE, live_files)
    before = _tree_hash(live)
    r = _run(repo, live)
    assert r.returncode == EXIT_NEEDS_INPUT, r.stdout
    assert "MISSING-IN-TEMPLATE (present only in the live vault" in r.stdout
    assert "MISSING-IN-TEMPLATE: 99-Operations/scripts/a-live-only-script.md" in r.stdout
    # untouched: the file still exists with its original bytes, whole tree unchanged
    assert (live / "99-Operations/scripts/a-live-only-script.md").read_text() == "live only\n"
    assert _tree_hash(live) == before


# T5 — excluded file is never touched and never counted, matching template-parity.py exactly.
def test_t5_excluded_file_is_never_touched(tmp_path):
    live_files = dict(BASE)
    live_files["99-Operations/schemas/naming-rules.json"] = '{"live": "generated"}\n'
    repo, live = _sandbox(tmp_path, BASE, live_files)
    r = _run(repo, live)
    assert r.returncode == EXIT_OK, r.stdout
    assert "1 excluded" in r.stdout
    assert "naming-rules.json" not in r.stdout
    # the generated live artifact is left exactly as it was (template ships no copy of it)
    assert (live / "99-Operations/schemas/naming-rules.json").read_text() == '{"live": "generated"}\n'


# blocked posture is shared with template-parity.py; assert the mirror honours it too.
def test_no_live_vault_is_blocked(tmp_path):
    repo, live = _sandbox(tmp_path, BASE, dict(BASE))
    r = _run(repo, tmp_path / "does-not-exist")
    assert r.returncode == EXIT_BLOCKED
    assert "BLOCKED" in r.stdout


# T6 — ceremony-doc structural check: the CONTRIBUTING step-5 line that closes the F26 loop is a
# single, non-wrapping, &&-free command line (this is the property whose absence caused F26).
def test_t6_contributing_step5_is_a_single_short_line():
    step5 = [
        ln for ln in CONTRIBUTING.read_text().splitlines()
        if re.match(r"^\s*5\.\s+tools/template-mirror\.py\b", ln)
    ]
    assert len(step5) == 1, f"expected exactly one step-5 mirror line, found {len(step5)}"
    line = step5[0]
    assert "&&" not in line, "step 5 must not chain commands with && (F26)"
    assert len(line) < 100, f"step 5 is {len(line)} chars — could wrap a narrow terminal (F26)"
    # no stale placeholder prose survives anywhere in the file
    assert "(operator action)" not in CONTRIBUTING.read_text()
