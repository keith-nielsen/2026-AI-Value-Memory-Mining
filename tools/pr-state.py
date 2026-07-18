#!/usr/bin/env python3
"""PR-state reporter — prints a pull request's state PER LAYER, with the layer named on
every line.

GitHub is a stack of layers — event payload, workflow run, check aggregation, REST,
GraphQL, branch/PR state machine — that answer different questions and routinely disagree
while all being correct (the F21 record in the live vault's determinism-failure-modes
Site: a rerun replays the OLD event payload; `gh run list` and `gh pr checks` aggregate a
`continue-on-error` job differently; `gh pr edit` can fail silently on GraphQL where REST
succeeds; merging a parent with `--delete-branch` closes a stacked child irreversibly).
Ad-hoc `gh` composition collapses those layers into one oracle; this reporter keeps them
apart so two conflicting answers read as a named-layer signal, not chaos.

Read-only: every call is a read (`gh pr view`, `gh run list`, `git ls-remote`). It mutates
nothing and emits no outward command, so it sits below the INV-14 rail. It is also the
post-mutation verifier: after any gh/GraphQL mutation, re-run it and read the layer —
never trust a silent success.

Usage:  tools/pr-state.py PR_NUMBER
Exit:   0 report delivered (disagreement between layers is a finding, not a failure) ·
        3 blocked (not a repo / gh missing / PR not resolvable).
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

EXIT_OK = 0
EXIT_BLOCKED = 3

PR_FIELDS = ("number,title,url,state,isDraft,mergeable,mergeStateStatus,"
             "baseRefName,headRefName,headRefOid,statusCheckRollup")


def _die_blocked(msg):
    print(f"BLOCKED: {msg}")
    raise SystemExit(EXIT_BLOCKED)


def _run(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def remote_branch_sha(root, branch):
    r = _run(["git", "-C", str(root), "ls-remote", "origin", f"refs/heads/{branch}"])
    if r.returncode != 0:
        _die_blocked(f"ls-remote origin failed: {r.stderr.strip()}")
    return r.stdout.split("\t")[0].strip() or None


def check_rollup(rollup):
    """(name, verdict) per check — CheckRun and StatusContext shapes both occur."""
    out = []
    for c in rollup or []:
        name = c.get("name") or c.get("context") or "?"
        verdict = c.get("conclusion") or c.get("state") or c.get("status") or "?"
        out.append((name, verdict.upper()))
    return out


def main(argv):
    if len(argv) != 2 or not re.match(r"^\d+$", argv[1]):
        _die_blocked("usage: tools/pr-state.py PR_NUMBER")
    number = argv[1]
    if shutil.which("gh") is None:
        _die_blocked("gh CLI not found on PATH")
    top = _run(["git", "rev-parse", "--show-toplevel"])
    if top.returncode != 0:
        _die_blocked("not inside a git repository")
    root = pathlib.Path(top.stdout.strip())

    r = _run(["gh", "pr", "view", number, "--json", PR_FIELDS], cwd=str(root))
    if r.returncode != 0:
        _die_blocked(f"gh pr view {number} failed: {r.stderr.strip()}")
    pr = json.loads(r.stdout)
    head_oid = pr.get("headRefOid") or ""

    print(f"pr-state: #{pr['number']} {pr['title']} ({pr['url']})")

    # Layer: the PR state machine, answered over GraphQL.
    print(f"layer [pr-state-machine · GraphQL]: state={pr['state']} "
          f"draft={pr['isDraft']} mergeable={pr.get('mergeable')} "
          f"mergeStateStatus={pr.get('mergeStateStatus')}")

    # Layer: the branch state on origin — refs are truth the PR object only mirrors.
    base, head = pr["baseRefName"], pr["headRefName"]
    base_sha = remote_branch_sha(root, base)
    head_sha = remote_branch_sha(root, head)
    print(f"layer [branch]: base '{base}' "
          + (f"at {base_sha[:12]}" if base_sha else "ABSENT on origin")
          + f" · head '{head}' "
          + (f"at {head_sha[:12]}" if head_sha else "ABSENT on origin")
          + (f" (PR head oid {head_oid[:12]})" if head_oid else ""))
    if base_sha is None:
        print(f"HAZARD [branch]: base branch '{base}' is deleted — GitHub will neither "
              f"reopen nor retarget a PR once its base is gone; retarget a stacked child "
              f"BEFORE merging its parent with --delete-branch (F21).")
    if head_sha and head_oid and head_sha != head_oid:
        print(f"HAZARD [branch]: origin head {head_sha[:12]} != PR head oid "
              f"{head_oid[:12]} — one of the two layers is stale; re-read before acting.")

    # Layer: check-level aggregation (what `gh pr checks` and the merge box read).
    checks = check_rollup(pr.get("statusCheckRollup"))
    good = [c for c in checks if c[1] in ("SUCCESS", "NEUTRAL", "SKIPPED")]
    print(f"layer [check-aggregation]: {len(good)} of {len(checks)} checks successful")
    for name, verdict in checks:
        if (name, verdict) not in good:
            print(f"layer [check-aggregation]: {verdict}: {name}")

    # Layer: run-level aggregation (what `gh run list` reads) — a continue-on-error job
    # can make this layer and the check layer disagree while both are correct.
    runs = []
    if head_oid:
        r = _run(["gh", "run", "list", "--commit", head_oid,
                  "--json", "name,status,conclusion,event"], cwd=str(root))
        if r.returncode != 0:
            _die_blocked(f"gh run list failed: {r.stderr.strip()}")
        runs = json.loads(r.stdout)
    for run in runs:
        print(f"layer [workflow-run]: {run['name']} ({run['event']}): "
              f"{run.get('conclusion') or run.get('status')}")
    run_bad = [x for x in runs if x.get("conclusion") not in (None, "success", "skipped")]
    check_bad = [c for c in checks if c not in good]
    if runs and bool(run_bad) != bool(check_bad):
        print(f"LAYERS-DISAGREE: workflow-run reports "
              f"{len(run_bad)} failing of {len(runs)} runs, check-aggregation reports "
              f"{len(check_bad)} failing of {len(checks)} checks — both can be correct "
              f"(run-level vs check-level aggregation, e.g. continue-on-error). Name the "
              f"layer your gate actually reads before acting (F21).")

    # Layer: the event payload — not re-readable, and the one reruns are stuck with.
    print("layer [event-payload]: not re-readable — a workflow RERUN replays the payload "
          "snapshotted at the triggering event, so body/base edits made since are "
          "invisible to it. To make a gate see an amended PR body, push a new commit "
          "(mints a fresh event) or have the job read the body from the API (F21).")

    print("note [mutation-verify]: after any gh/GraphQL mutation (e.g. gh pr edit "
          "--base), re-run this reporter and read the layer — GraphQL can fail silently "
          "where REST succeeds; trust re-read state, never a silent success (F21).")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
