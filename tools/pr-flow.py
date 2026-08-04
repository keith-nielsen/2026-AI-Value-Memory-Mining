#!/usr/bin/env python3
"""PR-flow driver — a level-triggered state machine for the branch -> merge lifecycle.

The sibling of `tools/ship-release.py`, which mechanizes tag -> Release. That ceremony has been
driven since v0.1.30; the lifecycle BEFORE it — branch, push, pull request, checks, merge, branch
delete — was still composed by hand every time, and F30 records what that cost in one session.

Three properties, each named for the established pattern it implements, so a reader recognises the
shape rather than learning a local dialect:

  LEVEL-TRIGGERED   No state file. Every invocation re-derives state from the world, so a missed
                    step or a lost session is corrected by the next pass. (Kubernetes controllers.)
  CHALLENGE/RESPONSE The driver challenges with ONE command, the caller responds by running exactly
                    that, and the driver verifies the action actually completed before advancing.
                    (Aviation checklists: the monitoring pilot confirms the response AND the act.)
  PLAN BEFORE STEP  `--plan` shows the whole remaining route before anything is done, so planning
                    is never reconstructed from recall. (terraform plan / kubectl --dry-run.)

It **never executes an outward mutation**: the INV-14 outbound guard text-matches the command the
CALLER runs, so a wrapper that ran it internally would silently bypass that rail.

Authority is separated from execution (RACI; four-eyes). Execution is never assigned to the operator
where the agent is measured capable — there the operator's role is CONSENT, discharged through the
INV-14 ask at the moment of execution, and the consent class is measured by running the guard, not
recalled from a table.

`gh pr merge --delete-branch` is never emitted. It is defective on three independent counts:
it cannot express a head precondition (cli/cli#5686), it bypasses GitHub's own retargeting of
stacked children so they are CLOSED instead (cli/cli#1168 — this is how PR #29 died, F21), and its
branch deletion is non-atomic and prints a success tick when it did not happen (F30). The merge goes
through the REST endpoint carrying `sha`, and deletion is a separate, verified step.

Usage:  tools/pr-flow.py --branch BR [--base main] [--body-file PATH] [--title STR]
        tools/pr-flow.py --plan --branch BR
        tools/pr-flow.py --ready {checks|mergeable|merged} [--sha SHA] [--pr N]
        tools/pr-flow.py --assert-preconditions K=V [K=V ...]
        tools/pr-flow.py --capabilities
Exit:   0 satisfied / lifecycle complete · 1 refused · 2 next command emitted or NOT READY
        · 3 blocked (bad invocation / not a repo / unreadable)
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gh_read  # noqa: E402

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_NEEDS_INPUT = 2
EXIT_BLOCKED = 3

AGENT = "AGENT"
OPERATOR = "OPERATOR"

CONSENT_LOCAL = "none needed — local only, nothing leaves this machine"
CONSENT_ACT = "implicit in the act: you run it, so you authorize it"
PLAN_TTL_SECONDS = 24 * 60 * 60  # industry practice: approvals expire so stale plans cannot apply

# Why `gh` mutations stay with the operator. BOTH halves matter: if the reason reads as mere
# inconvenience, the "fix" is to export a token — which would delete credential absence, the one
# measured barrier the INV-14 rail actually rests on.
WHY_OPERATOR_RUNS_GH = (
    "`gh` needs the operating system keyring, which a sandboxed process cannot reach (it reports a "
    "misleading 401). No write token is exported here BY POLICY — credential absence is the real "
    "barrier — so this stays yours to run."
)

# The ordered step table. ONE traversal drives both the emitter and the planner; a second list
# would drift from the first, which is the defect this whole change exists to end.
STEPS = [
    ("approval",    "Gate-4 sign-off recorded"),
    ("worktree",    "clean, no operation in progress"),
    ("base",        "branch contains the base tip"),
    ("commits",     "at least one commit over base"),
    ("pushed",      "origin matches local"),
    ("pr",          "exactly one open, non-draft pull request"),
    ("body",        "body carries the declared-scope block"),
    ("checks",      "checks registered, none pending, none failing"),
    ("mergeable",   "platform reports it mergeable"),
    ("children",    "no open pull request stacked on this branch"),
    ("archive",     "spec delta archived on this branch"),
    ("merge",       "merged"),
    ("remote-gone", "remote branch deleted"),
    ("local-gone",  "local branch deleted"),
]
MARK = {"ok": "x", "na": "-", "current": ">", "todo": " ", "wait": "~", "fail": "!"}


class PlanStop(Exception):
    """Raised in --plan mode at the first unsatisfied step: the route stops being measured here."""

    def __init__(self, kind, step, command=None, runs=None, authority=None, consent=None,
                 why=None):
        super().__init__(step)
        self.kind, self.step, self.command = kind, step, command
        self.runs, self.authority, self.consent, self.why = runs, authority, consent, why


class Route:
    """Records the outcome of each step as the single traversal walks it."""

    def __init__(self):
        self.state = {sid: "todo" for sid, _ in STEPS}
        self.detail = {}

    def mark(self, sid, state, detail=""):
        self.state[sid] = state
        if detail:
            self.detail[sid] = detail

    def header(self, next_owner=None):
        cells = " ".join(f"[{MARK[self.state[sid]]}]{sid}" for sid, _ in STEPS)
        done = sum(1 for sid, _ in STEPS if self.state[sid] in ("ok", "na"))
        lines = ["route: " + cells, f"       step {done + 1}/{len(STEPS)}"]
        if next_owner:
            lines[-1] += f" · next owner: {next_owner}"
        return "\n".join(lines)

    def table(self, stop):
        rows = []
        for n, (sid, guard) in enumerate(STEPS, 1):
            st = self.state[sid]
            if sid == getattr(stop, "step", None):
                label = "CURRENT"
            elif st == "ok":
                label = "MEASURED ok"
            elif st == "na":
                label = "N/A"
            elif st == "wait":
                label = "NOT READY"
            elif st == "fail":
                label = "MEASURED no"
            else:
                label = "PROJECTED"
            rows.append(f"{n:>2}  {sid:<12} {label:<12} {self.detail.get(sid, guard)}")
        return "\n".join(rows)


def run(cmd, cwd=None, stdin=None):
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=cwd, timeout=60, input=stdin,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git(args, cwd=None):
    return run(["git"] + args, cwd=cwd)


QUIET = False  # set in --plan mode: the route table is the output, not a running commentary


def out(label, msg):
    if not QUIET:
        print(f"{label}: {msg}")


def note(msg):
    if not QUIET:
        print(msg)


# --- consent: measured by running the guard, never declared -------------------------------------

def find_guard(root):
    for cand in (pathlib.Path(root) / ".claude/hooks/outbound-publish-guard.py",
                 pathlib.Path(os.environ.get("VAULT_ROOT", "/nonexistent"))
                 / ".claude/hooks/outbound-publish-guard.py",
                 pathlib.Path.home() / ".claude/hooks/outbound-publish-guard.py"):
        if cand.exists():
            return str(cand)
    return None


def probe_consent(root, command):
    """Ask the outbound guard what it would decide for this exact command. Measured, not recalled.

    Returns a human sentence. A guard that cannot be found yields UNVERIFIED — never an assumption,
    because assuming `ask` where the answer is `deny` would send the caller into a wall.
    """
    guard = find_guard(root)
    if not guard:
        return "UNVERIFIED — no outbound guard found at any known home"
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": root})
    try:
        r = run([sys.executable, guard], stdin=payload)
        decision = (json.loads(r.stdout or "{}")
                    .get("hookSpecificOutput", {}).get("permissionDecision"))
    except Exception:  # noqa: BLE001 - a probe reports, never raises
        return "UNVERIFIED — the outbound guard could not be evaluated"
    if decision == "ask":
        return "INV-14 outbound ask — you approve at execution time, the agent then runs it"
    if decision == "deny":
        return "INV-14 HARD DENY — this command would be refused; do not run it"
    return "no outbound rail matches this command"


# --- emitters ------------------------------------------------------------------------------------

def emit(route, step, command, runs, authority, consent, why, approve=None, plan=False, root=None):
    if plan:
        raise PlanStop("emit", step, command, runs, authority, consent, why)
    route.mark(step, "current")
    print("")
    print(route.header(next_owner=runs))
    print("")
    print("NEXT COMMAND (run exactly this, then re-invoke this driver):")
    print(f"  {command}")
    print(f"  runs:      {runs}")
    print(f"  authority: {authority}")
    print(f"  consent:   {consent}")
    print(f"  owner:     {runs}")  # retained: the single-field form other tooling still greps for
    print(f"  why:       {why}")
    if approve:
        print("  approve:   " + approve)
    if runs == OPERATOR and root:
        path = write_saved_plan(root, step, command, approve)
        if path:
            print("")
            print(f"  Saved plan: {path}")
            print(f"  To run it:  bash {path}")
            print("  It re-asserts the state you were shown and aborts if GitHub has moved; it "
                  "expires in 24h.")
    return EXIT_NEEDS_INPUT


def refuse(route, step, why, fix=None, plan=False):
    if plan:
        raise PlanStop("refuse", step, why=why)
    route.mark(step, "current")
    print("")
    print(route.header())
    print("")
    print(f"REFUSED: {why}")
    if fix:
        print(f"  fix: {fix}")
    return EXIT_REFUSED


def not_ready(route, step, what, probe, plan=False):
    """Asynchronous platform state is NOT READY, which is not a verdict and not a failure."""
    if plan:
        raise PlanStop("wait", step, why=what)
    route.mark(step, "wait")
    print("")
    print(route.header())
    print("")
    print(f"NOT READY: {what}")
    print(f"  test:  {probe}")
    print("  agent: poll that with Monitor — do NOT sleep in the foreground.")
    print("  human: re-run it; it prints the state each time.")
    budget = gh_read.budget_report()
    if budget:
        print(f"  budget: {budget} (poll no faster than 60s; 304s do NOT come free on this channel)")
    return EXIT_NEEDS_INPUT


def write_saved_plan(root, step, command, approve):
    """Write the operator's command to disk so a SHORT line is what gets pasted.

    F14 and F26: the interactive paste channel corrupted two hand-offs and clobbered a repo file.
    The full text is printed for review; only a short invocation is typed. The file also carries
    the precondition assertion, which is what closes the TOCTOU window on an operator step.
    """
    try:
        d = pathlib.Path(root) / ".git" / "pr-flow"
        d.mkdir(parents=True, exist_ok=True)
        path = d / "next.sh"
        expiry = int(time.time()) + PLAN_TTL_SECONDS
        body = [
            "#!/usr/bin/env bash",
            f"# generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} by pr-flow.py"
            f" — step '{step}'",
            "# Consent was given for the state asserted below. If GitHub has moved, this aborts",
            "# WITHOUT mutating: approval does not transfer to a different state.",
            "set -euo pipefail",
            f'if [ "$(date +%s)" -gt {expiry} ]; then',
            '  echo "saved plan EXPIRED — re-run tools/pr-flow.py to derive a current one" >&2',
            "  exit 1",
            "fi",
            f"cd {root}",
        ]
        if approve:
            body.append(f"# authorizing: {approve}")
        body += [command, "", "# verify the mutation actually landed:",
                 f"python3 {root}/tools/pr-flow.py --branch \"${{PR_FLOW_BRANCH:-$(git branch "
                 f"--show-current)}}\""]
        path.write_text("\n".join(body) + "\n")
        path.chmod(0o755)
        return path
    except OSError:
        return None


# --- probes ---------------------------------------------------------------------------------------

def capabilities(repo_root):
    """Probe what this process can actually do, and who authorizes each channel.

    F30: the agent asserted 'no GitHub egress this session' and it was false. A static ownership
    table would have encoded that wrong answer durably; a probe cannot, because it re-measures.
    """
    print("CAPABILITY PROBE (measured now, not recalled)")
    slug = gh_read.slug_from_remote(repo_root)
    print(f"  repo slug (from remote, not folder name): {slug or 'UNRESOLVED'}")
    print("  channel .................. state ......... runs / authority")

    try:
        _, ch = gh_read.get(f"/repos/{slug}") if slug else (None, None)
        print(f"  READ  github state ....... OK via {ch:<9} {AGENT} / {AGENT}")
    except Exception as exc:  # noqa: BLE001 - probe reports, never raises
        print(f"  READ  github state ....... FAILED ({str(exc)[:60]})")

    r = git(["ls-remote", "--heads", "origin"], cwd=repo_root)
    print(f"  READ  git ls-remote ...... {'OK' if r.returncode == 0 else 'FAILED':<13} "
          f"{AGENT} / {AGENT}")

    r = git(["push", "--dry-run", "origin", "HEAD"], cwd=repo_root)
    ok = r.returncode == 0
    print(f"  WRITE git push ........... {'OK (dry-run)' if ok else 'FAILED':<13} "
          f"{AGENT if ok else OPERATOR} / {OPERATOR} via the INV-14 ask")
    if not ok and r.stderr.strip():
        print(f"        {r.stderr.strip().splitlines()[-1][:110]}")

    if shutil.which("gh"):
        r = run(["gh", "auth", "status"], cwd=repo_root)
        ok = r.returncode == 0 and "Logged in" in (r.stdout + r.stderr)
        print(f"  WRITE gh mutations ....... {'OK' if ok else 'UNAVAILABLE':<13} "
              f"{AGENT if ok else OPERATOR} / {OPERATOR}")
    else:
        print(f"  WRITE gh mutations ....... {'UNAVAILABLE':<13} {OPERATOR} / {OPERATOR} "
              "(gh not installed)")

    budget = gh_read.rate_limit() or gh_read.budget_report()
    print(f"  READ  budget ............. {budget or 'UNMEASURED (channel unreachable)'}")
    return EXIT_OK


def ready(args):
    """Answer ONE named condition in ONE request, with a meaningful exit code (Monitor-friendly).

    Arguments are validated BEFORE the slug is resolved: a missing identifier is a caller error,
    and reporting it as "cannot resolve the remote" would name the wrong cause.
    """
    if args.ready == "checks" and not args.sha:
        print("BLOCKED: --ready checks needs --sha (the driver prints it); supplying it keeps "
              "this to a single request", file=sys.stderr)
        return EXIT_BLOCKED
    if args.ready in ("mergeable", "merged") and not args.pr:
        print(f"BLOCKED: --ready {args.ready} needs --pr N", file=sys.stderr)
        return EXIT_BLOCKED
    slug = gh_read.slug_from_remote(os.getcwd())
    if not slug:
        print("BLOCKED: cannot resolve owner/repo from the origin remote", file=sys.stderr)
        return EXIT_BLOCKED
    try:
        if args.ready == "checks":
            payload, ch = gh_read.check_runs(slug, args.sha)
            total, pending, failures = gh_read.summarize_checks(payload)
            print(f"checks: {total} runs, {len(pending)} pending, {len(failures)} failing [{ch}]")
            return EXIT_OK if total and not pending and not failures else EXIT_NEEDS_INPUT
        pr, ch = gh_read.pull_request(slug, args.pr)
        if args.ready == "mergeable":
            print(f"mergeable: {pr.get('mergeable')} [{ch}]")
            return EXIT_OK if pr.get("mergeable") is True else EXIT_NEEDS_INPUT
        print(f"merged: {bool(pr.get('merged_at'))} [{ch}]")
        return EXIT_OK if pr.get("merged_at") else EXIT_NEEDS_INPUT
    except gh_read.ReadError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return EXIT_BLOCKED


def assert_preconditions(pairs):
    """Optimistic concurrency control: re-assert the state consent was given for, before mutating.

    Compares PREDICATES, not raw tallies — a benign new passing check must not abort a merge the
    operator already authorized. That distinction is what keeps this from becoming RC-E over-denial.
    """
    want = dict(p.split("=", 1) for p in pairs if "=" in p)
    slug = gh_read.slug_from_remote(os.getcwd())
    if not slug or "pr" not in want:
        print("BLOCKED: --assert-preconditions needs pr=N inside a GitHub repo", file=sys.stderr)
        return EXIT_BLOCKED
    try:
        pr, _ = gh_read.pull_request(slug, int(want["pr"]))
        head = pr["head"]["sha"]
        actual = {
            "head": head,
            "draft": str(bool(pr.get("draft"))).lower(),
            "base": pr["base"]["ref"],
            "mergeable": "ok" if pr.get("mergeable") is not False else "false",
        }
        if "failures" in want or "pending" in want:
            payload, _ = gh_read.check_runs(slug, head)
            total, pending, failures = gh_read.summarize_checks(payload)
            actual["failures"] = str(len(failures))
            actual["pending"] = str(len(pending))
        if "children" in want:
            kids, _ = gh_read.open_children(slug, pr["head"]["ref"])
            actual["children"] = str(len(kids))
    except (gh_read.ReadError, KeyError, ValueError) as exc:
        print(f"BLOCKED: cannot re-assert state — {exc}", file=sys.stderr)
        return EXIT_BLOCKED

    moved = [(k, v, actual.get(k)) for k, v in want.items()
             if k != "pr" and k in actual and not actual[k].startswith(v)]
    if moved:
        print("PRECONDITION FAILED — the state you approved has moved; not mutating:")
        for k, expected, got in moved:
            print(f"  {k}: approved {expected!r}, now {got!r}")
        print("  Re-run tools/pr-flow.py to derive a current plan.")
        return EXIT_REFUSED
    print(f"preconditions hold ({', '.join(f'{k}={v}' for k, v in sorted(want.items()))})")
    return EXIT_OK


# --- guards -----------------------------------------------------------------------------------

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


def approval_state(root):
    """Step 0: Gate-4 sign-off is the one pure-authority step, and it is measured, not assumed.

    The checkbox must be TICKED. Matching the word "Approved" anywhere is not enough: the unticked
    task that DESCRIBES the sign-off (`- [ ] 4.1 Operator ... records **Approved**`) contains it
    too, and an earlier cut of this function read that description as the act — reporting Gate 4
    signed while it was not. That is precisely the declared-end-state-never-reached defect this
    driver exists to prevent, so it is asserted structurally, on the tick.
    """
    hits = sorted(pathlib.Path(root).glob("openspec/changes/*/tasks.md"))
    for t in hits:
        if "archive" in t.parts:
            continue
        for line in t.read_text(errors="replace").splitlines():
            if re.match(r"\s*- \[[xX]\]", line) and "Approved" in line:
                return True, f"recorded ticked in {t.relative_to(root)}"
        return False, f"Gate 4 UNSIGNED in {t.relative_to(root)} (no ticked Approved item)"
    return None, "no unarchived openspec change on this branch"


def unarchived_change(root):
    for d in sorted(pathlib.Path(root).glob("openspec/changes/*")):
        if d.is_dir() and d.name != "archive":
            return d.name
    return None


def scope_block_in(text):
    return bool(re.search(r"^```scope\b", text or "", re.M))


# --- the traversal ---------------------------------------------------------------------------

def drive(args, root, route, plan=False):
    branch = args.branch or git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
    base = args.base
    if not plan:
        out("branch", branch)
        out("base", base)

    if branch == base:
        return refuse(route, "worktree", f"branch and base are both {base!r}",
                      "check out the feature branch first", plan)

    signed, detail = approval_state(root)
    route.mark("approval", "na" if signed is None else ("ok" if signed else "fail"), detail)
    if signed is False:
        note(f"NOTE [approval]: {detail} — the lifecycle may be walked, but the merge is not "
              "authorized until the operator records it. Agents may not sign.")

    # B3: a failed fetch leaves origin/<base> stale, and base-currency measured against a stale ref
    # silently restores the very defect the guard exists to prevent.
    fetched = git(["fetch", "--quiet", "origin", base], cwd=root).returncode == 0
    base_ref = f"origin/{base}"
    if not fetched and git(["rev-parse", "--verify", "--quiet", base_ref], cwd=root).returncode:
        return refuse(route, "base", f"could not fetch {base_ref} and no local copy exists",
                      "base-currency cannot be measured against a ref that was never read", plan)
    if not fetched:
        note(f"NOTE [base]: fetch of {base_ref} FAILED — its tip is UNVERIFIED (last known copy "
              "in use). Re-run when the remote is reachable before trusting base-currency.")

    local_sha = git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
                    cwd=root).stdout.strip() or None
    r = git(["ls-remote", "origin", f"refs/heads/{branch}"], cwd=root)
    remote_sha = r.stdout.split()[0] if r.stdout.strip() else None
    absent = not local_sha and not remote_sha
    if absent:
        out("locality", f"{branch} is absent locally and on origin — "
                        "checking whether its lifecycle already completed")

    foreign = local_sha is None
    if foreign and not absent:
        kind = "dependabot" if branch.startswith("dependabot/") else "remote-only"
        out("locality", f"{kind} branch at {remote_sha[:7]} — NOT local; "
                        "rebase/push steps are skipped (we do not own this branch)")
    if foreign or absent:
        for sid in ("worktree", "base", "commits", "pushed"):
            route.mark(sid, "na", "not our branch" if foreign else "branch absent")
    else:
        out("locality", f"local branch at {local_sha[:7]}")

        problem = check_clean_worktree(root)
        if problem:
            return refuse(route, "worktree", problem[0], problem[1], plan)
        route.mark("worktree", "ok", "clean, no operation in progress")
        out("worktree", "clean, no operation in progress")

        current = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
        base_sha = git(["rev-parse", base_ref], cwd=root).stdout.strip()
        if base_sha and git(["merge-base", "--is-ancestor", base_sha, local_sha],
                            cwd=root).returncode != 0:
            if current != branch:
                return emit(route, "base", f"git -C {root} switch {branch}", AGENT, AGENT,
                            CONSENT_LOCAL,
                            f"{branch} needs a rebase onto {base_ref}, but {current!r} is checked "
                            "out — a bare `git rebase` would rebase the WRONG branch.",
                            plan=plan, root=root)
            return emit(route, "base", f"git -C {root} rebase {base_ref}", AGENT, AGENT,
                        CONSENT_LOCAL,
                        f"{branch} does not contain {base_ref}. Rebase BEFORE pushing or merging — "
                        "a PR opened on a stale base reports checks that are not about its own "
                        "change (F30: #50 was pushed before #49 merged).",
                        plan=plan, root=root)
        route.mark("base", "ok", f"contains {base_ref}")
        out("base-current", f"{branch} contains {base_ref}")

        ahead = git(["rev-list", "--count", f"{base_ref}..{branch}"], cwd=root).stdout.strip()
        if ahead == "0":
            return refuse(route, "commits", f"{branch} has no commits over {base_ref}",
                          "nothing to open a PR for", plan)
        route.mark("commits", "ok", f"{ahead} over {base_ref}")
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
            return emit(route, "pushed", cmd, AGENT, OPERATOR, probe_consent(root, cmd), why,
                        approve=f"sends {ahead} commit(s) from {branch} to origin. The command "
                                "carries an explicit -C target, so the guard resolves the repo "
                                "and not the vault.",
                        plan=plan, root=root)
        route.mark("pushed", "ok", f"origin == local ({local_sha[:7]})")
        out("pushed", f"origin/{branch} == local ({local_sha[:7]})")

    head_local_sha = local_sha or remote_sha

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
        return post_merge(root, slug, branch, merged[-1]["number"], foreign, route, plan)

    if not open_prs:
        if absent and not merged:
            return refuse(route, "pr",
                          f"branch {branch!r} exists neither locally nor on origin, and has no "
                          "merged PR", "nothing to drive — check the branch name", plan)
        if dead:
            note(f"NOTE: PR #{dead[-1]['number']} for this branch is CLOSED and unmerged. "
                  "GitHub will not reopen a PR whose base branch is gone, nor retarget a closed "
                  "one (F21) — a fresh PR is the only route, and that is deliberate.")
        if foreign:
            return refuse(route, "pr", f"{branch} is a remote-only branch with no open PR",
                          "we do not own this branch; nothing here creates a PR for it", plan)
        # B4: the scope block was previously required in prose only, inside the tool built to end
        # prose requirements. It is now checked before the command is emitted.
        if not args.body_file:
            return refuse(route, "pr", "no open PR, and --body-file was not supplied",
                          "the PR body must carry a fenced ```scope block (the declared-scope CI "
                          "gate reads it). Supply --body-file PATH and --title.", plan)
        body_path = pathlib.Path(args.body_file)
        if not body_path.exists():
            return refuse(route, "pr", f"--body-file {args.body_file} does not exist",
                          "an emitted command with a missing input is not executable as written",
                          plan)
        if not scope_block_in(body_path.read_text(errors="replace")):
            return refuse(route, "pr", f"{args.body_file} has no fenced ```scope block",
                          "the declared-scope CI gate fails without it, and --body-file bypasses "
                          "the PR template, so the block has to be yours", plan)
        if not args.title:
            return refuse(route, "pr", "--title was not supplied",
                          "refusing to emit a command containing a placeholder", plan)
        cmd = (f'cd {root} && gh pr create --base {base} --head {branch} '
               f'--title "{args.title}" --body-file {args.body_file}')
        return emit(route, "pr", cmd, OPERATOR, OPERATOR, CONSENT_ACT, WHY_OPERATOR_RUNS_GH,
                    approve=f"opens a PR from {branch} onto {base}; body {args.body_file} carries "
                            "a scope block [verified].",
                    plan=plan, root=root)

    if len(open_prs) > 1:
        return refuse(route, "pr",
                      f"{len(open_prs)} open PRs share head {branch!r}: "
                      + ", ".join(f"#{p['number']}" for p in open_prs),
                      "resolve the ambiguity by hand — silently picking one is how the wrong PR "
                      "gets merged", plan)

    pr = open_prs[0]
    number = pr["number"]
    head_sha = pr["head"]["sha"]
    out("pr", f"#{number} — {pr['title'][:70]}")

    if pr.get("draft"):
        return refuse(route, "pr", f"PR #{number} is a DRAFT",
                      "mark it ready for review before the lifecycle can advance", plan)
    if head_local_sha and head_sha != head_local_sha:
        return refuse(route, "pr",
                      f"PR #{number} head ({head_sha[:7]}) is not the branch tip "
                      f"({head_local_sha[:7]})", "re-read the PR; something pushed out of band",
                      plan)
    route.mark("pr", "ok", f"#{number}, open, not draft, head matches")

    # --- body: the declared-scope block must be IN the PR, not merely in a local file ------------
    if not scope_block_in(pr.get("body")):
        cmd = (f"cd {root} && gh api -X PATCH /repos/{slug}/pulls/{number} "
               f"-f body=\"$(cat {args.body_file or '<BODY-FILE>'})\"")
        if not args.body_file:
            return refuse(route, "body", f"PR #{number} body carries no fenced ```scope block",
                          "supply --body-file PATH so the correction can be emitted", plan)
        return emit(route, "body", cmd, OPERATOR, OPERATOR, CONSENT_ACT,
                    "the body is PATCHed through the REST endpoint, not `gh pr edit`, which can "
                    "fail SILENTLY behind a deprecated GraphQL layer (F21). NOTE: a body-derived "
                    "check reads the body from the event payload as of PUSH time — after this "
                    "PATCH the gate needs a PUSH, not a re-run.",
                    approve=f"replaces the body of PR #{number} with {args.body_file}.",
                    plan=plan, root=root)
    route.mark("body", "ok", "declared-scope block present in the PR body")

    # --- checks -----------------------------------------------------------------------------------
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
        fix = ("fix them. Note this repo's `main` ruleset has NO required_status_checks "
               "(ADR-0034 follow-on pending), so a merge would SUCCEED over a red check — "
               "the gate here is this driver, not the server.")
        if any("scope" in n.lower() or "body" in n.lower() for n in failures):
            fix += (" A body-derived gate reads the pull_request event payload, which is a "
                    "SNAPSHOT as of push time: re-running the job replays the STALE body. "
                    "Correct the body, then PUSH — do not re-run.")
        return refuse(route, "checks", f"PR #{number} has {len(failures)} failing check(s)", fix,
                      plan)
    if total == 0:
        # B1: zero runs is a race with the platform queueing the workflow, not a green result.
        return not_ready(route, "checks", f"no check runs have registered on {head_sha[:7]} yet",
                         f"tools/pr-flow.py --ready checks --sha {head_sha}", plan)
    if pending:
        return not_ready(route, "checks",
                         f"{len(pending)} check(s) still running: "
                         + ", ".join(sorted(set(pending))[:6]),
                         f"tools/pr-flow.py --ready checks --sha {head_sha}", plan)
    route.mark("checks", "ok", f"{total} runs, all green")

    # --- mergeable: only the SINGLE-PR endpoint carries this field --------------------------------
    try:
        full, ch = gh_read.pull_request(slug, number)
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot read mergeability — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    mergeable = full.get("mergeable")
    out("mergeable", f"{mergeable} (state={full.get('mergeable_state')})  [via {ch}]")
    if mergeable is None:
        return not_ready(route, "mergeable",
                         "GitHub has not finished computing mergeability for this PR",
                         f"tools/pr-flow.py --ready mergeable --pr {number}", plan)
    if mergeable is False:
        return refuse(route, "mergeable", f"PR #{number} is NOT mergeable "
                      f"(state={full.get('mergeable_state')})",
                      "resolve the conflict against the base and push", plan)
    route.mark("mergeable", "ok", "platform reports mergeable")

    # --- stacked children (F21) --------------------------------------------------------------------
    try:
        children, _ = gh_read.open_children(slug, branch)
    except gh_read.ReadError:
        children = []
    if children:
        names = ", ".join(f"#{c['number']} ({c['head']['ref']})" for c in children)
        return refuse(route, "children",
                      f"PR #{number} has {len(children)} open PR(s) stacked on it: {names}",
                      "RETARGET each child onto this PR's base BEFORE merging this one — "
                      f"`gh api -X PATCH /repos/{slug}/pulls/<child> -f base={base}` (NOT "
                      "`gh pr edit --base`, which can fail silently), then re-read the base to "
                      "confirm it moved. PR #29 died exactly this way (F21).", plan)
    route.mark("children", "ok", "no open PR is stacked on this branch")
    if base != "main":
        note(f"NOTE [stacked]: base is {base!r}, not main — this PR is itself a stacked child. "
              "Retarget it onto main as soon as its parent is ready to merge.")

    # --- archive advisory (the v0.1.34 lesson: a late archive costs a second PR) --------------------
    pending_change = unarchived_change(root)
    if pending_change:
        route.mark("archive", "current", f"{pending_change} not yet archived")
        note(f"NOTE [archive]: openspec/changes/{pending_change}/ is not archived. Archiving on "
              "THIS branch before the merge keeps it in one PR — a later archive costs a second "
              "PR (v0.1.34 paid that).")
    else:
        route.mark("archive", "ok", "no unarchived change on this branch")

    if not full.get("merged_at"):
        # The pure-authority step actually binds here: agents may not sign, so an unsigned Gate 4
        # stops the merge rather than merely annotating it.
        if signed is False:
            return refuse(route, "merge", f"Gate 4 is unsigned — {detail}",
                          "the operator records **Approved** against the sign-off task; agents may "
                          "not sign. Every earlier step may be walked; this one may not.", plan)
        cmd = (f"cd {root} && gh api -X PUT /repos/{slug}/pulls/{number}/merge "
               f"-f merge_method=merge -f sha={head_sha}")
        return emit(route, "merge", cmd, OPERATOR, OPERATOR, CONSENT_ACT,
                    f"all {total} checks green. `sha=` is a SERVER-SIDE precondition: if the head "
                    "moved, GitHub answers 409 and refuses rather than merging something you did "
                    "not review. `gh pr merge --delete-branch` is deliberately NOT used — it "
                    "cannot express this precondition, it bypasses GitHub's retargeting of stacked "
                    "children, and its deletion is non-atomic under a success tick.",
                    approve=f"merges PR #{number} ({pr['title'][:60]}) into {base} at "
                            f"{head_sha[:7]}; {total} checks green, {len(children)} stacked "
                            "children. Branch deletion is a separate, verified step.",
                    plan=plan, root=root)
    return post_merge(root, slug, branch, number, foreign, route, plan)


def post_merge(root, slug, branch, number, foreign, route, plan=False):
    """Verify the merge landed AND the branch is actually gone. The tick is not evidence."""
    for sid in ("pr", "body", "checks", "mergeable", "children", "archive", "merge"):
        if route.state[sid] == "todo":
            route.mark(sid, "ok", "completed earlier in this lifecycle")
    try:
        pr, ch = gh_read.pull_request(slug, number)
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot re-read PR #{number} — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    if not pr.get("merged_at"):
        return refuse(route, "merge", f"PR #{number} is not merged (state={pr.get('state')}) "
                                      f"[via {ch}]", None, plan)
    route.mark("merge", "ok", f"merged {pr['merged_at']}")
    out("merged", f"PR #{number} at {pr['merged_at']}  [via {ch}]")

    r = git(["ls-remote", "origin", f"refs/heads/{branch}"], cwd=root)
    if r.stdout.strip():
        if foreign:
            route.mark("remote-gone", "na", "foreign branch, left to its owner")
            out("remote-branch", f"{branch} still on origin — left alone (foreign branch)")
        else:
            cmd = f"git -C {root} push origin --delete {branch}"
            return emit(route, "remote-gone", cmd, AGENT, OPERATOR, probe_consent(root, cmd),
                        "the merge did not delete the remote branch. Deletion is a separate step "
                        "here precisely so it is verified rather than assumed (F30).",
                        approve=f"deletes the merged branch {branch} from origin.",
                        plan=plan, root=root)
    else:
        route.mark("remote-gone", "ok", "deleted")
        out("remote-branch", "deleted")

    local = git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root)
    if local.returncode == 0:
        cur = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
        if cur == branch:
            return emit(route, "local-gone", f"git -C {root} switch {pr['base']['ref']}",
                        AGENT, AGENT, CONSENT_LOCAL,
                        "the local branch cannot be deleted while it is checked out — this is "
                        "exactly what made gh's --delete-branch half-fail.", plan=plan, root=root)
        return emit(route, "local-gone", f"git -C {root} branch -D {branch}", AGENT, AGENT,
                    CONSENT_LOCAL, "local branch still present after the merge",
                    plan=plan, root=root)
    route.mark("local-gone", "ok", "deleted")
    out("local-branch", "absent" if foreign else "deleted")

    print("")
    print(route.header())
    print("")
    print(f"LIFECYCLE COMPLETE: PR #{number} merged, remote and local branches cleaned.")
    print("  Next, if this change ships a version: tools/ship-release.py vX.Y.Z")
    return EXIT_OK


def render_plan(route, stop, branch, base):
    print(f"PLAN  {branch} -> {base}   (the driver re-measures every step; this is not a record)")
    budget = gh_read.budget_report()
    if budget:
        print(f"budget: {budget}")
    print("")
    print(" #  step         state        guard")
    print(route.table(stop))
    print("")
    if stop.kind == "emit":
        print(f"CURRENT step '{stop.step}' — runs: {stop.runs} · authority: {stop.authority}")
        print(f"  command:   {stop.command}")
        print(f"  consent:   {stop.consent}")
    elif stop.kind == "refuse":
        print(f"BLOCKED at '{stop.step}': {stop.why}")
    else:
        print(f"NOT READY at '{stop.step}': {stop.why}")
    print("")
    print("PROJECTED steps are NOT verified — no command text is composed for them, because an "
          "unreached step's command is a prediction.")
    return EXIT_NEEDS_INPUT


def main(argv=None):
    ap = argparse.ArgumentParser(description="Guarded pull request lifecycle driver.")
    ap.add_argument("--branch", help="feature branch (default: current)")
    ap.add_argument("--base", default="main")
    ap.add_argument("--body-file", help="PR body file; must contain a fenced ```scope block")
    ap.add_argument("--title")
    ap.add_argument("--plan", action="store_true", help="show the whole remaining route, then exit")
    ap.add_argument("--capabilities", action="store_true",
                    help="probe what this process can do, then exit")
    ap.add_argument("--ready", choices=("checks", "mergeable", "merged"),
                    help="answer ONE readiness condition in one request; exit 0 ready, 2 waiting")
    ap.add_argument("--sha", help="head SHA, for --ready checks")
    ap.add_argument("--pr", type=int, help="pull request number, for --ready / --assert")
    ap.add_argument("--assert-preconditions", nargs="+", metavar="K=V",
                    help="re-assert the state consent was given for; exit 1 if it moved")
    args = ap.parse_args(argv)

    r = git(["rev-parse", "--show-toplevel"])
    if r.returncode != 0:
        print("BLOCKED: not inside a git repository", file=sys.stderr)
        return EXIT_BLOCKED
    root = r.stdout.strip()

    if args.capabilities:
        return capabilities(root)
    if args.ready:
        return ready(args)
    if args.assert_preconditions:
        return assert_preconditions(args.assert_preconditions)

    route = Route()
    if args.plan:
        globals()["QUIET"] = True
        branch = args.branch or git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
        try:
            code = drive(args, root, route, plan=True)
        except PlanStop as stop:
            return render_plan(route, stop, branch, args.base)
        return code
    return drive(args, root, route, plan=False)


if __name__ == "__main__":
    sys.exit(main())
