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

# The continuous-integration jobs whose work is NOT a stdlib heredoc, and so is invisible to
# `ci_steps()`. These are the four commands that were being run by hand before every push — the
# whole point of this tool is that there is ONE command, not five remembered ones.
#
# Each entry is (job name in ci.yml, argv). A job that cannot run here is reported SKIP with its
# reason, never PASS: a check that did not run has not passed, which is the defect class this repo
# keeps finding in itself (`md-lint`'s `|| true`, the `/tmp` hardcodes).
LOCAL_JOBS = [
    ("openspec-validate", ["node_modules/.bin/openspec", "validate", "--all", "--strict"]),
    ("inv6-offline-static", [sys.executable, "tools/inv6-offline-check.py", "--selftest"]),
    ("inv6-offline-static", [sys.executable, "tools/inv6-offline-check.py"]),
    ("validate-scripts", ["bash", ".github/scripts/validate-scripts.sh"]),
    ("fleet-pytest", [sys.executable, "-m", "pytest", "tests/", "-q"]),
    ("inv6-offline-dynamic", ["bash", ".github/scripts/inv6-offline-dynamic.sh"]),
]

# Jobs deliberately not reproduced locally, with the reason. Named here so the coverage report can
# account for every job in ci.yml — an unlisted, unrun job is the silent gap this tool exists to
# close, so the accounting must PARTITION.
NOT_LOCAL = {
    "md-lint": "markdownlint-cli is not installed locally; the CI job is also advisory (`|| true`)",
    # The hardcoded /tmp path that used to block this job is FIXED — it now runs locally in ~4s.
    # It is still not reproduced here, for a better reason found by running it: `--history` scans
    # UNREACHABLE objects on purpose (to catch a secret committed and then amended away), and
    # unreachable objects are per-clone garbage. A fresh CI checkout has none; this working clone
    # carries 103, including old copies of the scanner's OWN test fixtures, which match as
    # `private-key-block` and report 2 HIGH findings that do not exist on the remote.
    # Running it here would cry wolf on every developer machine, so it stays CI's job.
    "secret-scan": "`--history` scans unreachable objects, which are per-clone garbage — it reports "
                   "false HIGHs against any working clone and is only meaningful on a fresh checkout",
    "scope-review": "reproduced by STEP 7 below, against the real merge-base diff",
    "constitutional-diff-gate": "reproduced by STEP 7b below, against the real merge-base diff",
    "push": "not a job — a workflow trigger",
}


class _Missing:
    """A synthetic result for an executable that is not installed here.

    Found by running the tool in a scratch repository with no `node_modules`: `subprocess.run`
    RAISES `FileNotFoundError` rather than returning non-zero, so an absent tool crashed the whole
    pre-flight — killing the coverage report, which is the one thing that must always print. A tool
    that dies when a check is unavailable teaches its caller to stop running it.

    The unit tests did not catch this because they monkeypatch `LOCAL_JOBS` to `[]` and so never
    reach the loop. *Which real invocation reaches this line?* — answered by running, not reading.
    """

    returncode = 127

    def __init__(self, exe):
        self.stdout = ""
        self.stderr = f"{exe}: command not found"


def run(cmd, cwd=None, env=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return _Missing(cmd[0] if cmd else "?")


def ci_jobs(root):
    """Every job declared in ci.yml, derived — never a hardcoded list that drifts from the file."""
    src = (root / ".github/workflows/ci.yml").read_text().splitlines()
    return [m.group(1) for m in (re.match(r"^  ([a-z0-9-]+):$", l) for l in src) if m]


UNRUNNABLE = ("Read-only file system", "Permission denied", "No such file or directory",
              "command not found", "not found", "unshare", "Operation not permitted")


def verdict_for(r):
    """PASS / SKIP / FAIL. An environment limitation is SKIP and is never counted as a finding."""
    if r.returncode == 0:
        return "PASS", ""
    blob = (r.stderr or "") + (r.stdout or "")
    for s in UNRUNNABLE:
        if s in blob:
            why = next((l for l in blob.splitlines() if s in l), s)
            return "SKIP", why.strip()[:76]
    return "FAIL", ""


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
    ran_jobs, skipped_jobs = set(), {}

    # --- the rest of CI: the jobs that are not stdlib heredocs ----------------------------------
    # These were five separately-remembered commands before this section existed. Remembering is a
    # weak control; one command that prints its own coverage is a strong one.
    section("CI JOBS  the non-heredoc jobs, run locally")
    for job, argv in LOCAL_JOBS:
        r = run(argv, cwd=root)
        v, why = verdict_for(r)
        tail = (r.stdout.strip().splitlines() or [""])[-1][:56]
        print(f"  {v}  {job:<52} {tail}")
        if v == "SKIP":
            skipped_jobs[job] = why or "did not run here"
            print(f"          not runnable here — {why}")
            print("          (CI runs it; a check that did not run has NOT passed)")
        else:
            ran_jobs.add(job)
            if v == "FAIL":
                failures.append(f"{job}: failed")
                for line in ((r.stderr or r.stdout).strip().splitlines() or [""])[-3:]:
                    print(f"          {line[:88]}")

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

    # --- step 7b: constitutional impact --------------------------------------------------------
    # Needs no --body-file: the declaration is read from the TREE, which is the whole point of
    # putting it there rather than in a PR body. So this step always runs.
    section("STEP 7b  constitutional diff gate — against the real merge-base diff")
    with tempfile.TemporaryDirectory() as td:
        cdiff = Path(td) / "pr.diff"
        cdiff.write_text(run(["git", "diff", f"{a.base}...HEAD"], cwd=root).stdout)
        r3 = run([sys.executable, ".github/scripts/check-constitutional-impact.py", str(cdiff)],
                 cwd=root)
        for line in (r3.stdout.strip().splitlines() or ["(no output)"])[:5]:
            print(f"  {line[:88]}")
        if r3.returncode != 0:
            for line in r3.stderr.strip().splitlines()[:6]:
                print(f"        {line[:88]}")
            # Report-only in CI during burn-in (ADR-0042), so report-only here too — a local gate
            # stricter than the one that actually runs would train its reader to skip pre-flight.
            print("        NOTE: Phase A is report-only in CI; not counted as a pre-flight failure")

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

    # --- coverage -------------------------------------------------------------------------------
    # A clean verdict is worthless if the tool silently did not run half of CI. The accounting must
    # PARTITION every job declared in ci.yml into reproduced / skipped-with-reason / not-local, and
    # SHOUT if any job falls through — an unaccounted job is precisely the silent gap this tool
    # exists to close, and a new CI job added tomorrow must show up here rather than be missed.
    section("COVERAGE  what this run can and cannot tell you")
    jobs = [j for j in ci_jobs(root) if j not in ("push",)]
    heredoc_backed = {"constitution-lint", "vocabulary-lint", "spec-lint", "runbook-lint",
                      "naming-validator", "link-check", "standalone-vault-lint"}
    reproduced = sorted((ran_jobs | heredoc_backed) & set(jobs))
    skipped = sorted(set(skipped_jobs) & set(jobs))
    declared_not_local = sorted(set(NOT_LOCAL) & set(jobs))
    unaccounted = sorted(set(jobs) - set(reproduced) - set(skipped) - set(declared_not_local))

    print(f"  reproduced locally .... {len(reproduced):>2} — {', '.join(reproduced)}")
    if skipped:
        print(f"  could not run here .... {len(skipped):>2} — {', '.join(skipped)}")
        for j in skipped:
            print(f"      {j}: {skipped_jobs[j]}")
    if declared_not_local:
        print(f"  not reproduced ........ {len(declared_not_local):>2}")
        for j in declared_not_local:
            print(f"      {j}: {NOT_LOCAL[j]}")
    if unaccounted:
        print(f"  ⚠ UNACCOUNTED ......... {len(unaccounted):>2} — {', '.join(unaccounted)}")
        print("    A job in ci.yml that this tool neither runs nor explains is a SILENT GAP.")
        print("    Add it to LOCAL_JOBS or to NOT_LOCAL with a reason before trusting a clear run.")
        failures.append(f"coverage: {len(unaccounted)} CI job(s) unaccounted for")

    section("VERDICT")
    print(f"  {len(reproduced)}/{len(jobs)} CI jobs reproduced · {len(skipped)} unrunnable here · "
          f"{len(declared_not_local)} not reproduced by design")
    if failures:
        print(f"  {len(failures)} issue(s) that would otherwise surface only AFTER a push:")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("  CLEAR — every locally-modellable route step and CI job passes.")
    print("  This is not a promise the remote will be green: the jobs listed above as unrunnable or")
    print("  not reproduced were NOT checked, and the platform decides `pr`, `children` and `merge`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
