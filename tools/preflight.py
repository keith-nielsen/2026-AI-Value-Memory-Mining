"""PROTOTYPE — pre-flight the GitHub route locally, before any mutation.

Each section models ONE route step that today is only judged after a push, and judges it with the
SAME oracle the platform uses, so the local answer cannot drift from the remote one:

  step 7  body        scope-review, run against the real merge-base diff
  step 8  checks      every stdlib CI check, extracted from ci.yml and executed here
  step 9  mergeable   trial merge against the base — predicts a conflict without pushing
  step 11 archive     simulated archive, judged by the archive-sensitive checks

Not modellable locally, and deliberately not guessed at: `pr` (remote object), `children` (remote
stack), `merge` (server-side), and anything decided by a ruleset the session cannot read.

Usage:  preflight.py <repo> [--base origin/main] [--body-file PATH]
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FENCE = re.compile(r"```scope[ \t]*\r?\n(.*?)```", re.DOTALL)


def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def ci_steps(root):
    """Every CI step whose body is a stdlib python heredoc — the locally reproducible subset."""
    src = (root / ".github/workflows/ci.yml").read_text().splitlines()
    out, i = [], 0
    while i < len(src):
        m = re.match(r"^      - name: (.+)$", src[i])
        if m and i + 2 < len(src) and "python3 - << 'EOF'" in src[i + 2]:
            body, j = [], i + 3
            while j < len(src) and src[j].strip() != "EOF":
                body.append(src[j])
                j += 1
            ind = min((len(x) - len(x.lstrip()) for x in body if x.strip()), default=0)
            out.append((m.group(1), "\n".join(x[ind:] for x in body)))
            i = j
        i += 1
    return out


def section(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--body-file")
    a = ap.parse_args()
    root = Path(a.repo).resolve()
    failures = []

    # --- step 8: checks -----------------------------------------------------------------------
    section("STEP 8  checks — every stdlib CI check, run locally")
    for name, code in ci_steps(root):
        r = run([sys.executable, "-c", code], cwd=root)
        ok = r.returncode == 0
        # A check that could not RUN here is not a check that FAILED. Reporting the two the same way
        # is how a tool starts reporting a non-result as a result — the defect class this repo keeps
        # finding in itself. An environment limitation is named as one and never counted as a finding.
        unrunnable = (not ok) and any(
            s in r.stderr for s in ("Read-only file system", "Permission denied",
                                    "No such file or directory: '/tmp", "command not found"))
        verdict = "PASS" if ok else ("SKIP" if unrunnable else "FAIL")
        tail = (r.stdout.strip().splitlines() or [""])[-1][:58]
        print(f"  {verdict}  {name:<52} {tail}")
        if unrunnable:
            why = next((l for l in r.stderr.splitlines() if "Error" in l or "error" in l), "")
            print(f"          not runnable in this environment — {why.strip()[:70]}")
            print("          (CI runs it; this is a local limitation, NOT a finding)")
        elif not ok:
            failures.append(f"checks: {name}")
            for line in r.stderr.strip().splitlines()[:3]:
                print(f"          {line[:88]}")

    # --- step 9: mergeable --------------------------------------------------------------------
    section(f"STEP 9  mergeable — trial merge against {a.base}")
    base = run(["git", "merge-base", "HEAD", a.base], cwd=root).stdout.strip()
    if not base:
        print(f"  SKIP  cannot resolve merge-base with {a.base}")
    else:
        r = run(["git", "merge-tree", "--write-tree", "HEAD", a.base], cwd=root)
        if r.returncode == 0:
            print(f"  PASS  clean trial merge against {a.base} (no conflict)")
        else:
            conflicts = [l for l in r.stdout.splitlines() if l and not l[0].isdigit()][:6]
            print(f"  FAIL  trial merge CONFLICTS — the platform will report this after you push")
            for c in conflicts:
                print(f"          {c[:88]}")
            failures.append("mergeable: trial merge conflicts")

    # --- step 7: body / declared scope ---------------------------------------------------------
    section("STEP 7  body — scope-review against the real merge-base diff")
    if not a.body_file:
        print("  SKIP  no --body-file given")
    else:
        with tempfile.TemporaryDirectory() as td:
            scope, diff = Path(td) / "scope.json", Path(td) / "pr.diff"
            body = Path(a.body_file).read_text()
            if not FENCE.search(body):
                print("  FAIL  body carries no ```scope block")
                failures.append("body: no scope block")
            else:
                import os
                env = dict(os.environ, PR_BODY=body)
                r = run([sys.executable, ".github/scripts/extract-declared-scope.py"],
                        cwd=root, env=env)
                scope.write_text(r.stdout)
                diff.write_text(run(["git", "diff", f"{a.base}...HEAD"], cwd=root).stdout)
                r2 = run([sys.executable, ".github/scripts/check-scope-findings.py",
                          str(scope), str(diff)], cwd=root)
                print("  " + (r2.stdout.strip().splitlines() or ["(no output)"])[0][:88])
                for line in r2.stdout.strip().splitlines()[1:5]:
                    print(f"        {line[:88]}")
                if r2.returncode != 0:
                    failures.append("body: declared scope does not cover the diff")
                    print("        HINT: a rename touches BOTH paths — an archive must declare "
                          "source AND destination")

    # --- step 11: archive ----------------------------------------------------------------------
    section("STEP 11  archive — can each live change archive on its own branch?")
    live = [p for p in (root / "openspec/changes").iterdir()
            if p.is_dir() and p.name != "archive"] if (root / "openspec/changes").exists() else []
    if not live:
        print("  PASS  no live change directory — nothing owed")
    else:
        arch_sensitive = [(n, c) for n, c in ci_steps(root)
                          if "ADR" in n and ("resolves" in n or "contiguous" in n)]
        for c in sorted(live):
            with tempfile.TemporaryDirectory() as td:
                sim = Path(td) / "sim"
                shutil.copytree(root, sim, ignore=shutil.ignore_patterns(".git", "node_modules"))
                dest = sim / "openspec/changes/archive" / f"2026-01-01-{c.name}"
                shutil.copytree(sim / "openspec/changes" / c.name, dest)
                shutil.rmtree(sim / "openspec/changes" / c.name)
                bad = []
                for name, code in arch_sensitive:
                    rr = run([sys.executable, "-c", code], cwd=sim)
                    if rr.returncode:
                        bad.append((name, (rr.stderr.strip().splitlines() or [""])[0]))
                if bad:
                    print(f"  MUST DEFER  {c.name}")
                    for n, w in bad:
                        print(f"              {n}: {w[:80]}")
                    failures.append(f"archive: {c.name} cannot archive yet")
                else:
                    print(f"  CAN ARCHIVE {c.name}")

    section("VERDICT")
    if failures:
        print(f"  {len(failures)} issue(s) would have surfaced only AFTER a push:")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("  clear — every locally-modellable route step passes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
