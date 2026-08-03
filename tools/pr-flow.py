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

    git(["fetch", "--quiet", "origin", base], cwd=root)
    base_ref = f"origin/{base}"

    # --- Locality: is this OUR branch, or one that lives only on the remote? -------------------
    # `git rev-parse <name>` resolves a remote-tracking ref by DWIM when no local branch exists,
    # so a bare rev-parse cannot tell the two apart — it silently reported a dependabot branch as
    # local. Ask refs/heads explicitly.
    local_sha = git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
                    cwd=root).stdout.strip() or None
    r = git(["ls-remote", "origin", f"refs/heads/{branch}"], cwd=root)
    remote_sha = r.stdout.split()[0] if r.stdout.strip() else None
    # A branch absent from BOTH sides is the normal end state of a completed lifecycle, not an
    # error — the driver must stay re-entrant after the last step, so the verdict is deferred to
    # the PR lookup rather than refused here.
    absent = not local_sha and not remote_sha
    if absent:
        out("locality", f"{branch} is absent locally and on origin — "
                        "checking whether its lifecycle already completed")

    foreign = local_sha is None
    if foreign and not absent:
        # Remote-only: dependabot and any other bot/collaborator branch. We do not own it, so we
        # never rebase or push it — dependabot rebases its own branches, and a force-push from
        # here detaches it from that automation. Everything before the PR is skipped; the
        # lifecycle for a foreign branch is read-checks-then-merge.
        kind = "dependabot" if branch.startswith("dependabot/") else "remote-only"
        out("locality", f"{kind} branch at {remote_sha[:7]} — NOT local; "
                        "rebase/push steps are skipped (we do not own this branch)")
    elif not absent:
        out("locality", f"local branch at {local_sha[:7]}")

        problem = check_clean_worktree(root)
        if problem:
            return refuse(*problem)
        out("worktree", "clean, no operation in progress")

        # Local mutations act on the CHECKED-OUT branch. Emitting `git rebase` while a different
        # branch is checked out would rebase the wrong one, so the switch is emitted first.
        current = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()

        base_sha = git(["rev-parse", base_ref], cwd=root).stdout.strip()
        if base_sha and git(["merge-base", "--is-ancestor", base_sha, local_sha],
                            cwd=root).returncode != 0:
            if current != branch:
                return emit(
                    f"git -C {root} switch {branch}",
                    OWNER_GIT,
                    f"{branch} needs a rebase onto {base_ref}, but {current!r} is checked out — "
                    "a bare `git rebase` would rebase the WRONG branch.",
                )
            return emit(
                f"git -C {root} rebase {base_ref}",
                OWNER_GIT,
                f"{branch} does not contain {base_ref}. Rebase BEFORE pushing or merging — "
                "a PR opened on a stale base reports checks that are not about its own change "
                "(F30: #50 was pushed before #49 merged).",
            )
        out("base-current", f"{branch} contains {base_ref}")

        ahead = git(["rev-list", "--count", f"{base_ref}..{branch}"], cwd=root).stdout.strip()
        if ahead == "0":
            return refuse(f"{branch} has no commits over {base_ref}", "nothing to open a PR for")
        out("commits", f"{ahead} over {base_ref}")

        if remote_sha != local_sha:
            if remote_sha is None:
                cmd = f"git -C {root} push -u origin {branch}"
                why = "remote branch does not exist yet"
            else:
                cmd = f"git -C {root} push --force-with-lease origin {branch}"
                why = ("remote branch differs from local (rebased). --force-with-lease, never "
                       "--force: it refuses rather than overwrites if anything else pushed "
                       "meanwhile")
            return emit(cmd, OWNER_GIT, why)
        out("pushed", f"origin/{branch} == local ({local_sha[:7]})")

    head_local_sha = local_sha or remote_sha

    # --- Guard 4: a PR must exist --------------------------------------------------------------
    slug = gh_read.slug_from_remote(root)
    if not slug:
        print("BLOCKED: cannot resolve owner/repo from the origin remote — local guards passed, "
              "but PR state cannot be read", file=sys.stderr)
        return EXIT_BLOCKED
    out("repo", slug)
    try:
        prs, ch = gh_read.pulls_for_branch(slug, branch, base, state="all")
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot read PRs — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    open_prs = [p for p in prs if p["state"] == "open"]
    merged = [p for p in prs if p.get("merged_at")]
    dead = [p for p in prs if p["state"] == "closed" and not p.get("merged_at")]
    out("pr-lookup", f"{len(prs)} PR(s) for {branch} -> {base} "
                     f"({len(open_prs)} open, {len(merged)} merged, {len(dead)} closed-unmerged)"
                     f"  [via {ch}]")

    if not open_prs and merged:
        return post_merge(root, slug, branch, merged[-1]["number"], foreign)

    if not open_prs:
        if absent and not merged:
            return refuse(
                f"branch {branch!r} exists neither locally nor on origin, and has no merged PR",
                "nothing to drive — check the branch name",
            )
        if dead:
            print(f"NOTE: PR #{dead[-1]['number']} for this branch is CLOSED and unmerged. "
                  "GitHub will not reopen a PR whose base branch is gone, nor retarget a closed "
                  "one (F21) — a fresh PR is the only route, and that is deliberate, not a "
                  "workaround.")
        if foreign:
            return refuse(
                f"{branch} is a remote-only branch with no open PR",
                "we do not own this branch; nothing here creates a PR for it",
            )
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

    if len(open_prs) > 1:
        return refuse(
            f"{len(open_prs)} open PRs share head {branch!r}: "
            + ", ".join(f"#{p['number']}" for p in open_prs),
            "resolve the ambiguity by hand — silently picking one is how the wrong PR gets merged",
        )

    pr = open_prs[0]
    number = pr["number"]
    head_sha = pr["head"]["sha"]
    out("pr", f"#{number} — {pr['title'][:70]}")

    if pr.get("draft"):
        return refuse(f"PR #{number} is a DRAFT",
                      "mark it ready for review before the lifecycle can advance")

    if head_local_sha and head_sha != head_local_sha:
        return refuse(
            f"PR #{number} head ({head_sha[:7]}) is not the branch tip "
            f"({head_local_sha[:7]})",
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

    # --- Guard 6: no stacked child may be orphaned by this merge (F21) -------------------------
    try:
        children, ch = gh_read.open_children(slug, branch)
    except gh_read.ReadError:
        children = []
    if children:
        return refuse(
            f"PR #{number} has {len(children)} open PR(s) stacked on it: "
            + ", ".join(f"#{c['number']} ({c['head']['ref']})" for c in children),
            "RETARGET each child onto this PR's base BEFORE merging this one — "
            "`gh pr edit <child> --base " + base + "`. Merging a parent with --delete-branch "
            "auto-closes stacked children IRRECOVERABLY: GitHub then refuses to reopen (base gone) "
            "AND to retarget (closed). PR #29 in this repo died exactly that way (F21).",
        )
    if base != "main":
        print(f"NOTE [stacked]: base is {base!r}, not main — this PR is itself a stacked child. "
              "If its parent merges first, this PR is auto-closed and unrecoverable. Retarget it "
              "onto main as soon as the parent is ready to merge.")

    # --- Guard 7: merge ------------------------------------------------------------------------
    if not pr.get("merged_at"):
        delete_flag = "" if foreign else " --delete-branch"
        return emit(
            f"cd {root} && gh pr merge {number} --merge{delete_flag}",
            OWNER_GH,
            f"all {total} checks green."
            + (" Foreign branch: --delete-branch is omitted, since deleting a bot's branch can "
               "make it recreate the PR." if foreign else
               " NOTE --delete-branch is NOT atomic: if the local delete fails (e.g. the worktree "
               "is on that branch) gh aborts BEFORE deleting the remote and still prints "
               "✓ Merged. This driver verifies the deletion afterwards — do not trust the tick."),
        )

    return post_merge(root, slug, branch, number, foreign)


def post_merge(root, slug, branch, number, foreign=False):
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
        if foreign:
            out("remote-branch", f"{branch} still on origin — left alone (foreign branch; its "
                                 "owner reclaims or deletes it)")
        else:
            return emit(
                f"git -C {root} push origin --delete {branch}",
                OWNER_GIT,
                "the remote branch SURVIVED the merge — this is the non-atomic --delete-branch "
                "failure, and it is invisible to every file-side check this repo owns (F30).",
            )
    else:
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
    out("local-branch", "absent" if foreign else "deleted")

    print("")
    print(f"LIFECYCLE COMPLETE: PR #{number} merged, remote and local branches cleaned.")
    print("  Next, if this change ships a version: tools/ship-release.py vX.Y.Z")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
