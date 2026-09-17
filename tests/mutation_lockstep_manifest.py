#!/usr/bin/env python3
"""Mutation matrix for the lockstep manifest guard.

PR #115's manifest change shipped with no test. These mutations are the ways that change could
silently regress -- each must be KILLED, or the guard is decorative.
"""
import json
import pathlib
import re
import subprocess
import sys

R = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = R / "tools/template-sync-manifest.json"
TESTS = "tests/test_lockstep_manifest_contents.py"


ORIGINAL_TEXT = MANIFEST.read_text()


def mutate(fn):
    """Each mutant starts from the ORIGINAL, never from the previous mutant.

    The first cut of this matrix re-read the file inside the loop, so M2 was applied on top of
    M1 and so on. Every mutant after the first was compound, and the killer lists grew
    monotonically -- which reads like thorough coverage and is actually a broken harness. A
    matrix that cannot isolate one change cannot attribute a kill to it.
    """
    m = json.loads(ORIGINAL_TEXT)
    fn(m)
    return json.dumps(m, indent=2) + "\n"


MUTANTS = {
    "M1 drop 96-Runbooks/ (the item-34 regression)":
        lambda m: m["lockstep"].remove("96-Runbooks/"),
    "M2 drop .claude/commands/ (the prime goes unguarded)":
        lambda m: m["lockstep"].remove(".claude/commands/"),
    "M3 revert to the original two prefixes":
        lambda m: m.__setitem__("lockstep", ["99-Operations/scripts/", "99-Operations/schemas/"]),
    "M4 declare .claude/ wholesale (breaks per-instance settings ownership)":
        lambda m: m["lockstep"].append(".claude/"),
    "M5 declare render output lockstep (permanently red)":
        lambda m: m["lockstep"].append("99-Operations/bin/"),
    "M6 strip the reasoning comments":
        lambda m: [m.pop(k) for k in [k for k in m if k.startswith("_")]],
}

original = ORIGINAL_TEXT
results = []
try:
    for label, fn in MUTANTS.items():
        MANIFEST.write_text(mutate(fn))
        r = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "--no-header",
                            "--tb=no"], cwd=str(R), capture_output=True, text=True)
        killers = sorted(set(re.findall(r"FAILED \S+::(\S+)", r.stdout)))
        results.append((label, r.returncode != 0, killers))
finally:
    MANIFEST.write_text(original)

print("=" * 92)
print("MUTATION MATRIX — lockstep manifest")
print("=" * 92)
survivors = 0
for label, killed, killers in results:
    print(f"  [{'KILLED ' if killed else 'SURVIVED'}] {label}")
    if killed:
        print(f"             by: {', '.join(killers) or '(name not captured)'}")
    else:
        survivors += 1
        print("             ** NO TEST DETECTED THIS — coverage hole **")
print("-" * 92)
print(f"mutants: {len(results)}   killed: {len(results)-survivors}   SURVIVED: {survivors}")
print("manifest restored:", MANIFEST.read_text() == original)
sys.exit(1 if survivors else 0)
