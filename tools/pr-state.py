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

Read-only: every call is a read — REST via `gh_read` (anonymous first, `gh api` second, and the
channel that answered is printed) plus `git ls-remote`. It mutates nothing and emits no outward
command, so it sits below the INV-14 rail. It is also the post-mutation verifier: after any
mutation, re-run it and read the layer — never trust a silent success.

⚠ NO GraphQL CHANNEL REMAINS (2026-09-19, `prefer-rest-over-graphql-forms`). `mergeStateStatus`
comes from REST `mergeable_state`, the run layer from `/actions/runs`, and the check layer from
check-runs. The layer NAMES are unchanged and still mean what they meant: they describe different
aggregations that can legitimately disagree, not different transports.

Usage:  tools/pr-state.py PR_NUMBER
Exit:   0 report delivered (disagreement between layers is a finding, not a failure) ·
        3 blocked (not a repo / PR not resolvable / owner-repo unreadable from origin).
"""
import pathlib
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gh_read  # noqa: E402

EXIT_OK = 0
EXIT_BLOCKED = 3


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
    top = _run(["git", "rev-parse", "--show-toplevel"])
    if top.returncode != 0:
        _die_blocked("not inside a git repository")
    root = pathlib.Path(top.stdout.strip())

    # A SANDBOXED gh cannot reach the OS keyring and fails with a bogus 401, which used to make
    # this reporter unusable exactly when an agent needed it (F30). Degraded layers are reported
    # as UNAVAILABLE, never synthesised: inventing a layer would defeat the whole point of a
    # per-layer reporter.
    # EVERY LAYER IS NOW REST. GraphQL returned success for operations that did not take effect
    # (a body edit reported success and did not apply, F21/F21-3), so the estate reads the
    # observable channel only. `gh_read.get()` tries anonymous REST first and `gh api` second, so
    # both channels are covered by one call and each read reports which one answered.
    pr, channel = None, None
    gh_present = shutil.which("gh") is not None
    slug = gh_read.slug_from_remote(str(root))

    if slug:
        try:
            rest, channel = gh_read.pull_request(slug, int(number))
        except gh_read.ReadError:
            rest = None
        if rest is not None:
            pr = {
                "number": rest["number"],
                "title": rest["title"],
                "url": rest["html_url"],
                "state": "MERGED" if rest.get("merged_at") else rest["state"].upper(),
                "isDraft": rest.get("draft"),
                "mergeable": rest.get("mergeable"),
                # REST answers this after all (§5.2). `mergeable_state` carries the same enum as
                # GraphQL's mergeStateStatus, lowercased, so the field is no longer GraphQL-only.
                # ⚠ `mergeable` is computed ASYNCHRONOUSLY: `None` on a cold read is a real state,
                # not an error, and `--ready mergeable` already polls for it.
                "mergeStateStatus": (rest.get("mergeable_state") or "").upper() or None,
                "baseRefName": rest["base"]["ref"],
                "headRefName": rest["head"]["ref"],
                "headRefOid": rest["head"]["sha"],
                "statusCheckRollup": None,
            }

    # THE `gh pr view` FALLBACK IS GONE (§4.1), and removing it lost nothing that was being used.
    # Measured 2026-09-19 by reading what it actually added:
    #   * the CHANNEL was already covered — `gh_read.get()` tries anonymous REST and then
    #     `gh api` itself, so the fallback duplicated the second half of the path above;
    #   * its unique value was the two GraphQL-only fields. `mergeStateStatus` now comes from
    #     REST `mergeable_state` (§5.2), and the rollup already had a REST substitute below,
    #     labelled as the different layer it is.
    # What genuinely goes: the case where `slug_from_remote` cannot parse `origin` (an SSH alias
    # host, say) but `gh` could resolve the repo from git context itself. That degrades to BLOCKED
    # with the reason named, rather than being synthesised — the rule this reporter already
    # follows for every other degraded layer.

    if pr is None:
        _die_blocked(f"PR #{number} unreadable on every channel "
                     f"(REST {'attempted' if slug else 'unavailable: no owner/repo from origin'}; "
                     f"gh {'attempted' if gh_present else 'not on PATH'})")

    head_oid = pr.get("headRefOid") or ""
    print(f"pr-state: read via {channel}")

    print(f"pr-state: #{pr['number']} {pr['title']} ({pr['url']})")

    # Layer: the PR state machine. Name the channel that actually answered — labelling a
    # REST-sourced line "GraphQL" is the channel-stripping defect this reporter exists to prevent.
    # `mergeStateStatus` is no longer a GraphQL-only field; `None` still prints as UNKNOWN because
    # GitHub computes mergeability asynchronously and has genuinely not answered yet.
    print(f"layer [pr-state-machine · REST]: state={pr['state']} "
          f"draft={pr['isDraft']} mergeable={pr.get('mergeable')} "
          f"mergeStateStatus={pr.get('mergeStateStatus') or 'UNKNOWN (not yet computed)'}")

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
    # Degraded path: GraphQL's rollup is unavailable, so read check-runs over REST instead. This
    # is a DIFFERENT layer with the same subject — labelled as such, not passed off as the rollup.
    if head_oid and slug:
        try:
            payload, ck_ch = gh_read.check_runs(slug, head_oid)
            pr["statusCheckRollup"] = [
                {"name": c["name"], "conclusion": c.get("conclusion"), "status": c.get("status")}
                for c in payload.get("check_runs", [])
            ]
            print(f"layer [check-aggregation]: REST check-runs [via {ck_ch}] — this is the "
                  f"check-run layer, NOT GraphQL's rollup; same subject, different aggregation")
        except gh_read.ReadError as exc:
            print(f"layer [check-aggregation]: UNAVAILABLE ({exc})")
    checks = check_rollup(pr.get("statusCheckRollup"))
    good = [c for c in checks if c[1] in ("SUCCESS", "NEUTRAL", "SKIPPED")]
    pending = [c for c in checks if c[1] in
               ("IN_PROGRESS", "QUEUED", "PENDING", "EXPECTED", "WAITING")]
    check_bad = [c for c in checks if c not in good and c not in pending]
    print(f"layer [check-aggregation]: {len(good)} of {len(checks)} checks successful"
          + (f", {len(pending)} pending" if pending else ""))
    for name, verdict in checks:
        if (name, verdict) not in good:
            print(f"layer [check-aggregation]: {verdict}: {name}")

    # Layer: run-level aggregation (what `gh run list` reads) — a continue-on-error job
    # can make this layer and the check layer disagree while both are correct.
    # §4.2: `gh run list --commit` became `/repos/{slug}/actions/runs?head_sha=`. The four fields
    # this layer consumes were MEASURED present in that response, `name` included — the plan's
    # pre-registered "a single call drops workflow names" trap does not apply (see
    # gh_read.workflow_runs). The layer also stopped depending on `gh` being installed: it now
    # reads anonymously first, so a channel that used to print UNAVAILABLE answers.
    runs = []
    if head_oid and slug:
        try:
            payload, run_ch = gh_read.workflow_runs(slug, head_oid)
            runs = payload.get("workflow_runs", [])
            print(f"layer [workflow-run]: read via {run_ch}")
        except gh_read.ReadError as exc:
            print(f"layer [workflow-run]: UNAVAILABLE ({exc}) — the LAYERS-DISAGREE comparison "
                  f"below is SKIPPED rather than guessed.")
    elif head_oid:
        print("layer [workflow-run]: UNAVAILABLE — no owner/repo could be read from origin, so "
              "the LAYERS-DISAGREE comparison below is SKIPPED rather than guessed.")
    for run in runs:
        print(f"layer [workflow-run]: {run['name']} ({run['event']}): "
              f"{run.get('conclusion') or run.get('status')}")
    run_bad = [x for x in runs if x.get("conclusion") not in (None, "success", "skipped")]
    # While checks are still pending the layers are EXPECTED to be out of sync — a
    # disagreement is a signal only between two settled aggregations.
    if runs and not pending and bool(run_bad) != bool(check_bad):
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

    print("note [mutation-verify]: after any mutation (e.g. a base retarget), re-run this "
          "reporter and read the layer — a mutation that reports success can leave the state "
          "unchanged, which is why the estate re-reads rather than trusting an exit code. The "
          "recorded instances were GraphQL (F21, F21-3); the discipline is not channel-specific.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
