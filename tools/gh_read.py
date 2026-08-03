#!/usr/bin/env python3
"""Shared GitHub READ layer — anonymous REST first, `gh` only as a fallback.

Why this exists (F30, class 8, live vault `determinism-failure-modes-claude`): the standing rule
"run tools/pr-state.py first on any confusing PR state" was **unrunnable by a sandboxed agent**,
because every read in that reporter went through `gh`, and a sandboxed `gh` cannot reach the OS
keyring — it falls back to a stale token and reports a misleading `HTTP 401 / token is invalid`.
Measured 2026-08-03: `gh auth status` fails in-sandbox while `api.github.com` answers **200
anonymously**, and plain `git` (ls-remote/fetch/push) works. A tool whose reads are unavailable
exactly when an agent needs them is a tool that gets replaced by hand-rolled `curl` at the moment
of confusion — which is what happened, and is how the six F30 declarations went unobserved.

So: every read here tries the **anonymous REST API** first (no token, no keyring, works sandboxed)
and falls back to `gh api` only when anonymity is insufficient (private repo, or rate-limited).
The channel that answered is returned with the data and is meant to be PRINTED, never stripped —
class 7 in the same record: a fact whose channel is removed is indistinguishable from a fact that
was verified.

Reads only. This module performs no mutation and emits no outward command, so it sits below the
INV-14 rail exactly as `pr-state.py` does. It is NOT a deterministic fleet script (it is a
maintainer/ceremony tool that legitimately talks to the network), so INV-6 is not engaged.
"""
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request

API = "https://api.github.com"
TIMEOUT = 30

CH_ANON = "anon-rest"
CH_GH = "gh-api"


class ReadError(RuntimeError):
    """A read failed on every available channel."""


def _run(cmd, timeout=TIMEOUT):
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def slug_from_remote(cwd=None):
    """Resolve owner/repo from the git remote. Returns None when not derivable.

    Deliberately reads the REMOTE, not the directory name: the folder here is
    `value-memory-mining` while the repo is `2026-AI-Value-Memory-Mining`, and guessing from the
    folder is a documented way to address the wrong repository.
    """
    r = _run(["git"] + (["-C", cwd] if cwd else []) + ["remote", "get-url", "origin"])
    if r.returncode != 0:
        return None
    url = r.stdout.strip()
    m = re.search(r"github\.com[:/]+([^/]+)/(.+?)(?:\.git)?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _anon(path):
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "vmm-gh-read"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _gh(path):
    if not shutil.which("gh"):
        raise ReadError("gh not installed")
    r = _run(["gh", "api", path])
    if r.returncode != 0:
        raise ReadError(f"gh api failed: {r.stderr.strip()[:200]}")
    return json.loads(r.stdout)


def get(path):
    """GET a REST path. Returns (payload, channel). Anonymous first, `gh` as fallback.

    The channel is returned so callers can print it. A caller that discards it turns a
    provenance-carrying read into a bare assertion.
    """
    try:
        return _anon(path), CH_ANON
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        anon_err = exc
    try:
        return _gh(path), CH_GH
    except ReadError as exc:
        raise ReadError(
            f"both channels failed for {path} — anonymous: {anon_err}; gh: {exc}"
        ) from exc


def pull_request(slug, number):
    return get(f"/repos/{slug}/pulls/{number}")


def check_runs(slug, sha):
    return get(f"/repos/{slug}/commits/{sha}/check-runs?per_page=100")


def branches(slug):
    return get(f"/repos/{slug}/branches?per_page=100")


def pulls_for_branch(slug, branch, base=None, state="open"):
    """PRs whose head is `branch`. `head` needs the owner prefix in the REST filter.

    `state="all"` matters: a CLOSED-unmerged PR is invisible to an open-only query, so a driver
    that only asks for open PRs concludes "no PR" and proposes creating a duplicate. This repo has
    two such PRs in its history (#18 auto-closed by Dependabot, #29 closed irrecoverably when its
    stacked parent merged with --delete-branch).
    """
    owner = slug.split("/")[0]
    q = f"/repos/{slug}/pulls?state={state}&head={owner}:{branch}&per_page=100"
    if base:
        q += f"&base={base}"
    return get(q)


def open_children(slug, branch):
    """Open PRs whose BASE is `branch` — i.e. PRs stacked on top of it.

    F21: merging a parent with `--delete-branch` auto-closes every stacked child IRRECOVERABLY —
    GitHub then refuses both to reopen it (base gone) and to retarget it (closed). PR #29 in this
    repo died exactly that way and had to be recreated. Children must be retargeted BEFORE the
    parent merges, so they have to be visible before the merge is emitted.
    """
    return get(f"/repos/{slug}/pulls?state=open&base={branch}&per_page=100")


def summarize_checks(payload):
    """Reduce a check-runs payload to (total, pending, failures[]).

    `skipped` and `neutral` count as OK — a `continue-on-error` burn-in job (scope-review)
    legitimately reports `skipped` on one trigger and success on the other, and treating that as
    failure is the over-denial pattern (RC-E) that gets a gate disabled rather than obeyed.
    """
    runs = payload.get("check_runs", [])
    pending = [r["name"] for r in runs if r.get("status") != "completed"]
    failures = sorted({
        r["name"] for r in runs
        if r.get("status") == "completed"
        and r.get("conclusion") not in ("success", "neutral", "skipped")
    })
    return len(runs), pending, failures
