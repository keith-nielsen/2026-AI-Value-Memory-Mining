# SPDX-License-Identifier: Apache-2.0
"""`vault-render.py` must resolve its notes and its targets from the SAME root.

Found 2026-09-08 while validating a scratch harness *before* trusting it for a change to a
restricted area -- not by reading the code. The harness reported `reconcile 15/15 ok, exit 0`
while comparing the LIVE vault's notes against a CLONE's deployed files.

The mechanism: notes come from `_vault_root()`, which is env-FIRST (`VAULT_ROOT` wins), while
`deploy_target` is written relative in every note and a bare `Path()` resolved it against the
process CWD. When those two disagree the tool silently cross-compares trees -- and in `render`
mode it would WRITE one vault's code blocks into another tree's paths.

Measured against the pre-fix note: **2 of the 3 tests fail**, and the third is labelled as
non-discriminating rather than counted as coverage. That distinction was itself earned --
the first cut of the cross-tree test passed against the defect, because the broken code
read the wrong tree, found a difference, and reported DRIFT for the wrong reason. An
assertion that cannot separate a correct verdict from a coincidental one is not a guard.
"""
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template/99-Operations/scripts/render-reconcile-script.md"
CODE = re.compile(r"^```(?:python|bash)\n(.*?)^```", re.S | re.M)


def _render_source():
    """The implementation block of the render note -- the thing that actually ships."""
    body = NOTE.read_text().split("---", 2)[2]
    blocks = CODE.findall(body)
    assert len(blocks) == 1, f"expected exactly one code fence, found {len(blocks)}"
    return blocks[0]


def _build_vault(root, marker_in_note=False):
    """A minimal but STRUCTURALLY REAL vault: config marker, one note, its rendered target."""
    (root / "99-Operations").mkdir(parents=True, exist_ok=True)
    (root / "99-Operations/config.env").write_text("# marker\n")
    (root / "99-Operations/scripts").mkdir(parents=True, exist_ok=True)
    (root / "99-Operations/bin").mkdir(parents=True, exist_ok=True)
    payload = "print('x')\n" + ("# PERTURBED\n" if marker_in_note else "")
    (root / "99-Operations/scripts/demo-thing-script.md").write_text(
        "---\ntype: meta-script\ndeploy_target: 99-Operations/bin/demo-thing.py\n"
        "runtime: manual\nclass: script\n---\n## Rationale\ndemo\n\n```python\n"
        + payload + "```\n")
    (root / "99-Operations/bin/demo-thing.py").write_text("print('x')\n")


def _run_reconcile(tmp_path, vault_root, cwd):
    """Run the SHIPPED render source, with VAULT_ROOT and cwd deliberately controllable."""
    script = tmp_path / "vault-render.py"
    script.write_text(_render_source())
    r = subprocess.run([sys.executable, str(script), "reconcile"],
                       cwd=str(cwd), env={"VAULT_ROOT": str(vault_root), "PATH": "/usr/bin:/bin",
                                          "HOME": str(tmp_path)},
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_note_side_drift_is_detected(tmp_path):
    """Baseline behaviour: a note that no longer matches its target IS drift.

    ⚠ This test does NOT discriminate the fix -- with cwd == vault both the fixed and the
    broken code resolve to the same tree, so it passes either way. It is retained as a plain
    regression on the tool's core purpose, and is deliberately NOT counted as coverage of the
    root-resolution defect. The discriminating test is the next one.
    """
    v = tmp_path / "vault"
    _build_vault(v, marker_in_note=True)
    rc, out = _run_reconcile(tmp_path, vault_root=v, cwd=v)
    assert rc == 1, f"expected drift exit 1, got {rc}\n{out}"
    assert "DRIFT" in out and "demo-thing.py" in out, out


def test_target_is_resolved_against_the_notes_root_not_the_cwd(tmp_path):
    """THE REGRESSION, and it had to be built to DISCRIMINATE.

    A first cut of this test perturbed tree A and asserted DRIFT. It passed against the
    defect too: the broken code read B's target, found it differed from A's note, and
    reported DRIFT for entirely the wrong reason. The assertion could not tell a correct
    verdict from a coincidental one -- vacuous coverage that reads as a guard.

    So the trees are built the other way round. Tree A is INTERNALLY CONSISTENT, so the
    only correct verdict is `ok`. Tree B's target is deliberately different. Now:

        fixed   -> resolves A's target, finds it consistent  -> ok,    exit 0
        broken  -> resolves B's target against the CWD       -> DRIFT, exit 1

    A spurious DRIFT about a tree nobody asked about is the signature of the defect.
    """
    a, b = tmp_path / "a", tmp_path / "b"
    _build_vault(a, marker_in_note=False)    # notes AND target agree -- nothing to report
    _build_vault(b, marker_in_note=False)
    # Make B's deployed file differ, so a CWD-resolved read cannot help but notice it.
    (b / "99-Operations/bin/demo-thing.py").write_text("print('DIFFERENT TREE')\n")

    rc, out = _run_reconcile(tmp_path, vault_root=a, cwd=b)
    assert rc == 0, (
        "reconcile reported drift while VAULT_ROOT names an internally consistent tree — "
        f"it resolved the target against the CWD instead of the notes' root\n{out}")
    assert "DRIFT" not in out, out


def test_render_source_never_resolves_a_bare_relative_deploy_target(tmp_path):
    """Structural guard: the fix must not regress to a CWD-relative Path().

    A behavioural test can be satisfied by a coincidence of directories; this one reads the
    shipped source and requires the target to be joined to the resolved root.
    """
    src = _render_source()
    assert 'target = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))' not in src, (
        "deploy_target is resolved bare — it must be joined to the root the notes came from")
    assert "vault / _dt" in src or "vault /" in src, (
        "no join between the resolved vault root and the deploy target")
