#!/usr/bin/env python3
"""PR-flow driver — a guarded, re-entrant state machine for the branch -> merge lifecycle.

The sibling of `tools/ship-release.py`, which mechanizes tag -> Release. That ceremony has been
driven since v0.1.30; the lifecycle BEFORE it — branch, push, PR, checks, merge, branch delete —
was still composed by hand every time, and F30 (live vault `determinism-failure-modes-claude`)
records what that cost in one session: a child PR pushed before its parent merged, a body PATCH
named as required and then dropped from the instruction list, a merge whose `--delete-branch`
half-failed and left a remote branch alive under a `✓` tick, a rebase reported complete while
`.git/rebase-merge` was still active, and three emitted commands that were not executable as
written (`git rev-parse --short` with three revisions among them).

Every one of those is an ORDERING or POSTCONDITION defect, which is what a state machine is for.
The failures that a driver does NOT fix are ownership errors — "the operator must run this" when
the agent could — so ownership is **probed, not remembered**: see `--capabilities`.

Same load-bearing contract as `ship-release.py`, for the same reason: it **never executes an
outward mutation**. `git push` and every `gh` mutation are ASK-gated by the INV-14 outbound guard,
which text-matches the command the CALLER runs; a wrapper that ran them internally would silently
bypass that rail. So the driver proves each guard, EMITS the next single command verbatim with its
owner named, and exits 2. The caller runs exactly that, re-invokes, and the driver verifies the
mutation actually landed before advancing — silent successes are never trusted (the `--delete-branch`
that reported ✓ and did not delete is precisely this).

Re-entrant: no state file. Every invocation re-derives state from the world, so it is safe to
re-run at any point, including after a failure or a context loss.

Reads go through `tools/gh_read.py` (anonymous REST first, `gh` fallback), so the driver keeps
working in a sandboxed session where `gh` cannot reach the keyring.

Usage:  tools/pr-flow.py --branch BR [--base main] [--body-file PATH] [--title STR]
        tools/pr-flow.py --capabilities
Exit:   0 lifecycle complete (merged, branch cleaned) · 1 guard refused · 2 next command emitted
        (or checks still running) · 3 blocked (bad invocation / not a repo / unreadable)
"""
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gh_read  # noqa: E402

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_NEEDS_INPUT = 2
EXIT_BLOCKED = 3

OWNER_GH = "OPERATOR (gh needs the OS keyring; a sandboxed gh reports a bogus 401)"
OWNER_GIT = "AGENT or OPERATOR (plain git works sandboxed with GIT_TERMINAL_PROMPT=0)"


def run(cmd, cwd=None):
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd, timeout=60,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git(args, cwd=None):
    return run(["git"] + args, cwd=cwd)


def out(label, msg):
    print(f"{label}: {msg}")


def emit(command, owner, why):
    """Print the ONE next command, its owner, and why it is next. Never run it."""
    print("")
    print("NEXT COMMAND (run exactly this, then re-invoke this driver):")
    print(f"  {command}")
    print(f"  owner: {owner}")
    print(f"  why:   {why}")
    return EXIT_NEEDS_INPUT


def refuse(why, fix=None):
    print("")
    print(f"REFUSED: {why}")
    if fix:
        print(f"  fix: {fix}")
    return EXIT_REFUSED


def capabilities(repo_root):
    """Probe what this process can actually do. Ownership is measured, never recalled.

    F30: the agent asserted 'no GitHub egress this session' and it was false — git and the
    anonymous API both worked. A static ownership table would have encoded that wrong answer
    durably; a probe cannot, because it re-measures.
    """
    print("CAPABILITY PROBE (measured now, not recalled)")
    slug = gh_read.slug_from_remote(repo_root)
    print(f"  repo slug (from remote, not folder name): {slug or 'UNRESOLVED'}")

    try:
        payload, ch = gh_read.get(f"/repos/{slug}") if slug else (None, None)
        print(f"  READ  github state ....... OK via {ch}  -> agent can verify state itself")
    except Exception as exc:  # noqa: BLE001 - probe reports, never raises
        print(f"  READ  github state ....... FAILED ({exc})")

    r = git(["ls-remote", "--heads", "origin"], cwd=repo_root)
    print(f"  READ  git ls-remote ...... {'OK' if r.returncode == 0 else 'FAILED'}")

    r = git(["push", "--dry-run", "origin", "HEAD"], cwd=repo_root)
    ok = r.returncode == 0
    print(f"  WRITE git push ........... {'OK (dry-run)' if ok else 'FAILED'}  -> {OWNER_GIT if ok else 'operator only'}")
    if not ok:
        print(f"        {r.stderr.strip().splitlines()[-1][:120] if r.stderr.strip() else ''}")

    if shutil.which("gh"):
        r = run(["gh", "auth", "status"], cwd=repo_root)
        ok = r.returncode == 0 and "Logged in" in (r.stdout + r.stderr)
        print(f"  WRITE gh mutations ....... {'OK' if ok else 'UNAVAILABLE'}  -> {OWNER_GH if not ok else 'agent may run gh'}")
    else:
        print("  WRITE gh mutations ....... UNAVAILABLE (gh not installed)")
    return EXIT_OK


def check_clean_worktree(root):
    for marker in (".git/rebase-merge", ".git/rebase-apply", ".git/MERGE_HEAD",
                   ".git/CHERRY_PICK_HEAD"):
        if (pathlib.Path(root) / marker).exists():
            return (f"an in-progress operation is still active ({marker})",
                    "finish it, or `git rebase --quit` / `git merge --abort` — "
                    "a half-finished rebase silently blocks branch deletion later")
    r = git(["status", "--porcelain"], cwd=root)
    if r.stdout.strip():
        return ("working tree is not clean", "commit or stash before advancing the lifecycle")
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guarded PR lifecycle driver.")
    ap.add_argument("--branch", help="feature branch (default: current)")
    ap.add_argument("--base", default="main")
    ap.add_argument("--body-file", help="PR body file (must contain a ```scope block)")
    ap.add_argument("--title")
    ap.add_argument("--capabilities", action="store_true",
                    help="probe what this process can do, then exit")
    args = ap.parse_args(argv)

    r = git(["rev-parse", "--show-toplevel"])
    if r.returncode != 0:
        print("BLOCKED: not inside a git repository", file=sys.stderr)
        return EXIT_BLOCKED
    root = r.stdout.strip()

    if args.capabilities:
        return capabilities(root)

    # The slug is resolved LAZILY, at the first read that needs GitHub. Every guard up to the
    # push is purely local, and blocking on an unresolvable remote would refuse to answer
    # questions that do not depend on it.
    branch = args.branch or git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
    base = args.base
    out("branch", branch)
    out("base", base)

    if branch == base:
        return refuse(f"branch and base are both {base!r}", "check out the feature branch first")

    # --- Guard 1: local state must be settled before anything outward ------------------------
    problem = check_clean_worktree(root)
    if problem:
        return refuse(*problem)
    out("worktree", "clean, no operation in progress")

    local_sha = git(["rev-parse", branch], cwd=root).stdout.strip()
    if not local_sha:
        return refuse(f"branch {branch!r} does not exist locally")

    # --- Guard 2: the branch must contain the base tip (ordering) -----------------------------
    base_ref = f"origin/{base}"
    git(["fetch", "--quiet", "origin", base], cwd=root)
    base_sha = git(["rev-parse", base_ref], cwd=root).stdout.strip()
    if base_sha:
        merged = git(["merge-base", "--is-ancestor", base_sha, local_sha], cwd=root).returncode == 0
        if not merged:
            return emit(
                f"git -C {root} rebase {base_ref}",
                OWNER_GIT,
                f"{branch} does not contain {base_ref}. Rebase BEFORE pushing or merging — "
                "a PR opened on a stale base reports checks that are not about its own change "
                "(F30 item: #50 was pushed before #49 merged).",
            )
    out("base-current", f"{branch} contains {base_ref}")

    ahead = git(["rev-list", "--count", f"{base_ref}..{branch}"], cwd=root).stdout.strip()
    if ahead == "0":
        return refuse(f"{branch} has no commits over {base_ref}", "nothing to open a PR for")
    out("commits", f"{ahead} over {base_ref}")

    # --- Guard 3: remote branch must match local ----------------------------------------------
    r = git(["ls-remote", "origin", f"refs/heads/{branch}"], cwd=root)
    remote_sha = r.stdout.split()[0] if r.stdout.strip() else None
    if remote_sha != local_sha:
        if remote_sha is None:
            cmd = f"git -C {root} push -u origin {branch}"
            why = "remote branch does not exist yet"
        else:
            cmd = f"git -C {root} push --force-with-lease origin {branch}"
            why = ("remote branch differs from local (rebased). --force-with-lease, never --force: "
                   "it refuses rather than overwrites if anything else pushed meanwhile")
        return emit(cmd, OWNER_GIT, why)
    out("pushed", f"origin/{branch} == local ({local_sha[:7]})")

    # --- Guard 4: a PR must exist --------------------------------------------------------------
    slug = gh_read.slug_from_remote(root)
    if not slug:
        print("BLOCKED: cannot resolve owner/repo from the origin remote — local guards passed, "
              "but PR state cannot be read", file=sys.stderr)
        return EXIT_BLOCKED
    out("repo", slug)
    try:
        prs, ch = gh_read.pulls_for_branch(slug, branch, base)
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot read PRs — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    out("pr-lookup", f"{len(prs)} open PR(s) for {branch} -> {base}  [via {ch}]")

    if not prs:
        body = args.body_file or "<PATH-TO-BODY-FILE>"
        title = args.title or "<TITLE>"
        return emit(
            f'cd {root} && gh pr create --base {base} --head {branch} '
            f'--title "{title}" --body-file {body}',
            OWNER_GH,
            "no open PR. The body file MUST contain a ```scope block (declared-scope gate). "
            "Use --body-file, not --body: the PR template is bypassed either way, and the scope "
            "block has to be yours.",
        )

    pr = prs[0]
    number = pr["number"]
    head_sha = pr["head"]["sha"]
    out("pr", f"#{number} — {pr['title'][:70]}")

    if head_sha != local_sha:
        return refuse(
            f"PR #{number} head ({head_sha[:7]}) is not the local branch tip ({local_sha[:7]})",
            "re-read the PR; something pushed out of band",
        )

    # --- Guard 5: checks must be complete and green -------------------------------------------
    try:
        payload, ch = gh_read.check_runs(slug, head_sha)
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot read checks — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    total, pending, failures = gh_read.summarize_checks(payload)
    out("checks", f"{total} runs, {len(pending)} pending, {len(failures)} failing  [via {ch}]")

    if failures:
        for name in failures:
            print(f"  FAILING: {name}")
        return refuse(
            f"PR #{number} has {len(failures)} failing check(s)",
            "fix them. Note this repo's `main` ruleset has NO required_status_checks "
            "(ADR-0034 follow-on pending), so a merge would SUCCEED over a red check — "
            "the gate here is this driver, not the server.",
        )
    if pending:
        print("")
        print(f"CHECKS STILL RUNNING ({len(pending)}): {', '.join(sorted(set(pending))[:6])}")
        print("  Re-invoke this driver to re-read. Nothing to run in the meantime.")
        return EXIT_NEEDS_INPUT

    # --- Guard 6: merge ------------------------------------------------------------------------
    if not pr.get("merged_at"):
        return emit(
            f"cd {root} && gh pr merge {number} --merge --delete-branch",
            OWNER_GH,
            f"all {total} checks green. NOTE --delete-branch is NOT atomic: if the local delete "
            "fails (e.g. the worktree is on that branch) gh aborts BEFORE deleting the remote and "
            "still prints ✓ Merged. This driver verifies the deletion afterwards — do not trust "
            "the tick.",
        )

    return post_merge(root, slug, branch, number)


def post_merge(root, slug, branch, number):
    """Verify the merge landed AND the branch is actually gone. The tick is not evidence."""
    try:
        pr, ch = gh_read.pull_request(slug, number)
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot re-read PR #{number} — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    if not pr.get("merged_at"):
        return refuse(f"PR #{number} is not merged (state={pr.get('state')})  [via {ch}]")
    out("merged", f"PR #{number} at {pr['merged_at']}  [via {ch}]")

    r = git(["ls-remote", "origin", f"refs/heads/{branch}"], cwd=root)
    if r.stdout.strip():
        return emit(
            f"git -C {root} push origin --delete {branch}",
            OWNER_GIT,
            "the remote branch SURVIVED the merge — this is the non-atomic --delete-branch "
            "failure, and it is invisible to every file-side check this repo owns (F30).",
        )
    out("remote-branch", "deleted")

    local = git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root)
    if local.returncode == 0:
        cur = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
        if cur == branch:
            return emit(
                f"git -C {root} switch {pr['base']['ref']}",
                OWNER_GIT,
                "the local branch cannot be deleted while it is checked out — this is exactly "
                "what made gh's --delete-branch half-fail.",
            )
        return emit(
            f"git -C {root} branch -D {branch}",
            OWNER_GIT,
            "local branch still present after the merge",
        )
    out("local-branch", "deleted")

    print("")
    print(f"LIFECYCLE COMPLETE: PR #{number} merged, remote and local branches cleaned.")
    print("  Next, if this change ships a version: tools/ship-release.py vX.Y.Z")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
