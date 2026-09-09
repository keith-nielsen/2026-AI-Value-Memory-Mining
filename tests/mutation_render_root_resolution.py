#!/usr/bin/env python3
"""Mutation matrix for the render root-resolution fix.

A passing test proves nothing unless you know what would make it fail. This breaks the
shipped implementation in specific, plausible ways and requires each break to be KILLED by
at least one named test. A mutant that SURVIVES is a measured coverage hole.

Every mutation is a thing a competent author could actually write -- not noise.
"""
import pathlib
import re
import subprocess
import sys

R = pathlib.Path("/home/administrator/Documents/repo/value-memory-mining")
NOTE = R / "vault-template/99-Operations/scripts/render-reconcile-script.md"
TESTS = "tests/test_render_root_resolution.py"

FIXED = (
    '    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))\n'
    '    target = _dt if _dt.is_absolute() else (vault / _dt)'
)

MUTANTS = {
    "M1 no join at all (the original defect)":
        '    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))\n'
        '    target = _dt',
    "M2 join to the CWD instead of the root (same defect, different spelling)":
        '    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))\n'
        '    target = _dt if _dt.is_absolute() else (pathlib.Path.cwd() / _dt)',
    # EQUIVALENT MUTANT -- retained deliberately so a future run re-derives the finding
    # rather than rediscovering it as a scare. pathlib's `/` discards the left operand when
    # the right is absolute, so this cannot be killed by any test. Measured 2026-09-09.
    "M3 join unconditionally, ignoring is_absolute [EQUIVALENT]":
        '    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))\n'
        '    target = vault / _dt',
    "M4 inverted condition":
        '    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))\n'
        '    target = (vault / _dt) if _dt.is_absolute() else _dt',
    "M5 joined to the wrong root (parent of the vault)":
        '    _dt = pathlib.Path(os.path.expanduser(str(post["deploy_target"])))\n'
        '    target = _dt if _dt.is_absolute() else (vault.parent / _dt)',
}

original = NOTE.read_text()
assert FIXED in original, "the fixed form is not present — refusing to mutate an unknown state"

results = []
try:
    for label, mutant in MUTANTS.items():
        NOTE.write_text(original.replace(FIXED, mutant, 1))
        r = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "--no-header", "-x",
                            "--tb=no"], cwd=str(R), capture_output=True, text=True)
        killed = r.returncode != 0
        killers = sorted({m.split("::")[-1].split()[0]
                          for m in re.findall(r"FAILED \S+::(\S+)", r.stdout)})
        if not killers:
            killers = sorted({m for m in re.findall(r"^FAILED (\S+)", r.stdout, re.M)})
        results.append((label, killed, killers))
finally:
    NOTE.write_text(original)

print("=" * 92)
print("MUTATION MATRIX — every mutant must be KILLED by a named test")
print("=" * 92)
survivors = 0
for label, killed, killers in results:
    mark = "KILLED " if killed else "SURVIVED"
    if not killed:
        survivors += 1
    print(f"  [{mark}] {label}")
    if killed:
        print(f"             by: {', '.join(killers) or '(test name not captured)'}")
    else:
        print("             ** NO TEST DETECTED THIS BREAK — coverage hole **")
print("-" * 92)
print(f"mutants: {len(results)}   killed: {len(results)-survivors}   SURVIVED: {survivors}")
print("note restored:", FIXED in NOTE.read_text())
expected_equivalent = sum(1 for l, k, _ in results if "[EQUIVALENT]" in l and not k)
unexpected = survivors - expected_equivalent
print(f"expected-equivalent survivors: {expected_equivalent} | UNEXPECTED survivors: {unexpected}")
sys.exit(1 if unexpected else 0)
