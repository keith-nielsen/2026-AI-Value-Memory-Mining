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
import shlex
import shutil
import subprocess
import sys
import time
import uuid

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
INVOCATION = None  # set once in main(): the argv that produced THIS run

# Set once in main() from --after-mutation: the step whose mutation just ran, when this invocation
# is the verify tail of a saved plan rather than an ordinary route derivation. Two things change in
# that mode, and BOTH exist because GitHub's read view lags its own writes:
#   1. an unconfirmed step is WAITING, not REFUSED — a red verdict under a successful irreversible
#      mutation invites the one reaction that must never happen: re-running the mutation;
#   2. no outward mutation may be emitted at all — see the guard in emit().
AFTER_MUTATION = None
MUTATION_EVIDENCE = None  # path to the mutation's captured output, so its own proof can be quoted

# Bounded, budget-aware lag tolerance. Small because the anonymous REST channel allows 60 reads/hour
# and a full invocation already costs several.
#
# ⚠ THESE NUMBERS ARE NOT MEASURED. They were chosen from taste — inside a fix for a measurement
# problem — and the live record already indicts them: of the two merges where the ladder actually
# ran, #67 cleared on the LAST rung (~7s) and #68 exceeded it entirely. A ladder sitting at the
# median stalls roughly half the time. The earlier claim here that "two extra reads is enough to
# clear the lag observed on #63/#64/#66" was an assertion, not an observation, and #68 refuted it.
#
# They stay provisional until `--lag-report` holds enough real observations to size them from data.
# DO NOT retune them by feel — inventing a more pleasing constant is the defect, not the fix.
LAG_RETRY_DELAYS = (2, 5)
LAG_RETRY_MIN_BUDGET = 10  # below this many remaining reads, report once and stop spending

PROC_START = time.time()   # for the saved plan's verify tail, ~the moment the mutation finished
LAG_LOG_NAME = "lag-observations.jsonl"
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
# Glyph, and the words that define it. The legend is rendered FROM this table, so a marker cannot
# exist without an explanation — the route header is read far more often than this source file.
#
# `P`/`F`, NOT `x`/`!`. The pass mark was originally `x`, copied from the markdown checkbox habit
# rather than chosen. `x` INVERTS by convention: "an X in the box" means *selected* in the US/UK,
# while 「×」(batsu) means *wrong* across Japan and much of East Asia, against 「○」(maru) for
# correct. The isolated glyph is survivable; the PAIR was not — `[x]`=passed sat beside `[!]`=failed,
# so under the batsu reading both scan as negative and the route's single most important
# distinction collapses. A legend only rescues that if it is read, and a status line's whole value
# is being scannable WITHOUT reading prose. `P`/`F` are language-bound but never inverted, and are
# ASCII so no terminal font can render them as a box (operator's call, 2026-08-05).
#
# `?` (not `~`) for waiting, deliberately: `[~]` means "built but NOT TESTED" in task files, which
# is a deficiency requiring action, while this means "the platform has not answered yet", which
# resolves itself. One glyph for both would let an untested item read as benignly in-flight.
#
# Task files keep markdown's `[x]` for done: GitHub's renderer only recognises `[ ]` and `[x]`, so
# that split is forced by the renderer, not an oversight. Both legends state their own set.
MARK = {
    "ok":      ("P", "passed"),
    "na":      ("-", "not applicable here"),
    "current": (">", "current step"),
    "todo":    (" ", "not yet reached"),
    "wait":    ("?", "awaiting the platform"),
    "fail":    ("F", "failed"),
}


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
        cells = " ".join(f"[{MARK[self.state[sid]][0]}]{sid}" for sid, _ in STEPS)
        done = sum(1 for sid, _ in STEPS if self.state[sid] in ("ok", "na"))
        step_no = min(done + 1, len(STEPS))
        lines = ["route: " + cells, f"       step {step_no}/{len(STEPS)}"]
        if next_owner:
            lines[-1] += f" · next owner: {next_owner}"
        # Explain only the glyphs actually rendered: a legend for markers that are not on screen is
        # noise, and this header prints on every invocation.
        used = {self.state[sid] for sid, _ in STEPS}
        key = " · ".join(f"[{MARK[k][0]}] {MARK[k][1]}" for k in MARK if k in used)
        lines.append(f"       key: {key}")
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


TIMEOUT_RC = 124   # conventional shell exit code for a timed-out command
UNRUNNABLE_RC = 127  # conventional shell exit code for "command not executable"


def run(cmd, cwd=None, stdin=None, timeout=60):
    """Run a command and degrade EVERY failure into a return code. This never raises.

    F33: an unhandled `TimeoutExpired` from `git fetch` crashed the driver out of its own exit-code
    contract — a traceback, no route header, no state, on a tool whose four exit codes ARE the
    product. The guard written for "the fetch failed" checked the RETURN CODE and so could not see
    an EXCEPTION, which is the one path the failure actually took. The fix belongs here rather than
    at each call site: a guard can only act on what the runner can express, so the runner must be
    total.
    """
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout, input=stdin,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            cmd, TIMEOUT_RC, "", f"timed out after {timeout}s (no response from the remote)")
    except (OSError, ValueError) as exc:  # missing binary, bad cwd, bad argv
        return subprocess.CompletedProcess(
            cmd, UNRUNNABLE_RC, "", f"could not execute {cmd[0]!r}: {exc}")


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

def confirm_mutation(step):
    """The mutation under verification has been OBSERVED to land — leave post-mutation mode.

    Item 22, measured in production on PR #67's own merge. Suppression was scoped to *"this run was
    invoked with the flag"*, so it kept firing after the merge was confirmed: the driver printed
    `merged: PR #67 at 2026-08-14T10:13:11Z` and then suppressed the branch delete with
    `WAITING remote-gone: the read view does not yet show the merge mutation` — a claim the line
    directly above it had already disproven — blocking a step that genuinely needed doing.

    The correct scope is *"the verified mutation is still unconfirmed"*. Once confirmed, every later
    step is NEW work, not a re-emission, and must proceed normally. Over-denial is its own failure
    mode, never a safe default: a guard that blocks correct work teaches its reader to ignore it,
    costing exactly the protection it was added for.

    Keyed to the SPECIFIC step, because `post_merge()` pre-marks pr/body/checks/... as `ok` before it
    has verified anything — a hook keyed to "any step went ok" would clear on that loop and reopen
    the duplicate-emit hazard.
    """
    global AFTER_MUTATION
    if AFTER_MUTATION == step:
        AFTER_MUTATION = None


def is_outward_mutation(command):
    """Would running this command change state on GitHub? Classified by shape, not by step name.

    Keyed to the verbs the driver itself emits. A step-name allowlist would have to be revisited
    every time a step is added, and the failure mode of forgetting is that a mutation escapes the
    guard silently — the wrong direction to be wrong in.
    """
    c = " ".join(command.split())
    # Matched with the verb SEPARATED from its program, because that is how the driver emits every
    # one of them: `git -C <root> push …`, `cd <root> && gh api -X PUT …`. A literal "git push"
    # substring test misses ALL FOUR push sites — measured end-to-end 2026-08-13, where the guard
    # waved through the very push the driver had just emitted one line below it. The unit test that
    # passed had used a hand-written `git push -u origin br`, a shape this tool never produces.
    return any(re.search(p, c) for p in (
        r"\bgit\b[^|;&]*\bpush\b",
        r"\bgh\b[^|;&]*\bpr\s+(create|merge|edit|close|reopen|ready)\b",
        r"\bgh\b[^|;&]*\bapi\b[^|;&]*(-X|--method)\s+(PUT|POST|PATCH|DELETE)\b",
        r"\bgh\b[^|;&]*\brelease\s+(create|edit|delete|upload)\b",
    ))


def emit(route, step, command, runs, authority, consent, why, approve=None, plan=False, root=None,
         assert_args=None, branch=None):
    if plan:
        raise PlanStop("emit", step, command, runs, authority, consent, why)

    # THE guard for item 19's sharper instance. On #66 the verify tail read 0 PRs seconds after
    # `gh pr create` succeeded, and re-emitted `gh pr create` — an instruction that, followed,
    # opens a DUPLICATE pull request. The merge case was survivable only because GitHub answered
    # idempotently; this one is not. A post-mutation verify exists to observe, so it may not
    # instruct a mutation. Structural, not a caveat in the output prose: the emit cannot happen.
    if AFTER_MUTATION and is_outward_mutation(command):
        route.mark(step, "wait")
        print("")
        print(route.header())
        print("")
        print(f"WAITING {step}: the read view does not yet show the {AFTER_MUTATION} mutation, so "
              "this step still looks unstarted.")
        print(f"  evidence:  {mutation_proof()}")
        print("  diagnosis: read-after-write lag. The route below would otherwise have told you to "
              "run:")
        print(f"    {command}")
        print("  SUPPRESSED — running that after a successful mutation would duplicate it.")
        print("  next:      re-run this driver WITHOUT --after-mutation once the read view "
              "settles;")
        print("             it will either advance or tell you what is genuinely missing.")
        return EXIT_NEEDS_INPUT
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
        path = write_saved_plan(root, step, command, approve, branch, assert_args)
        if path:
            print("")
            print(f"  Saved plan: {path}")
            print(f"  To run it:  bash {path}")
            if assert_args:
                print("  It re-asserts the state you were shown and aborts WITHOUT mutating if "
                      "GitHub has moved; it expires in 24h.")
            else:
                # Say only what the script does. Claiming an assertion this step cannot make is the
                # same false-assurance defect the driver exists to prevent (class 9).
                print("  It carries a 24h expiry. NO live-state assertion is possible at this step "
                      "— there is no pull request yet to assert against.")
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


def mutation_proof():
    """The mutation's own evidence, for quoting back when the read view contradicts it.

    Under `set -euo pipefail` the verify tail only runs at all if the mutation exited 0 — that fact
    alone is proof, and it holds even when no evidence file was captured. Where the file exists, the
    platform's own response is far more persuasive to a worried operator than an inference.
    """
    exited_ok = "the mutation command exited 0 (set -e would have aborted this script otherwise)"
    if not MUTATION_EVIDENCE:
        return exited_ok
    try:
        text = pathlib.Path(MUTATION_EVIDENCE).read_text(errors="replace")
    except OSError:
        return exited_ok
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict):
        # Quote the fields that actually settle the question, not the whole payload.
        facts = [f"{k}={data[k]}" for k in ("merged", "sha", "number", "state", "html_url")
                 if k in data]
        if facts:
            return "the mutation reported " + ", ".join(facts)
    snippet = " ".join(text.split())[:160]
    return f"the mutation reported: {snippet}" if snippet else exited_ok


def lag_log_path(root):
    """One place names the observation log, so writer and reporter cannot drift apart."""
    return pathlib.Path(root) / ".git" / "pr-flow" / LAG_LOG_NAME


def log_lag_observation(root, record):
    """Append ONE raw observation. Raw only — never a summary, never a recommendation.

    Why this exists (operator, 2026-08-14): *"I just want to be sure that we're capturing the
    information that we're failing with so that subsequent fixes are grounded in observations and not
    creating random aesthetically pleasing ladders."* The retry ladder above was invented. Nothing in
    this repo recorded what GitHub's read view actually does, so every future adjustment would have
    been another guess wearing a number.

    Writes into `.git/` deliberately: it is per-clone operational telemetry, not source. It must
    never fail the driver — a logger that can abort a merge verification is worse than no logger.
    """
    try:
        p = lag_log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    except (OSError, TypeError, ValueError):
        pass  # telemetry is never load-bearing


def lag_tolerant(read, satisfied, root=None, subject=None, first=None):
    """Re-read a lagging condition a bounded number of times before believing the negative.

    Item 19: on #64 the merge returned `{"merged": true}` and the very next read said
    `state=open`; on #66 the `pr` step read 0 PRs seconds after `gh pr create` succeeded. Nothing
    was wrong either time — GitHub's read view had not caught up with its own write. A single read
    cannot distinguish that from a mutation that genuinely did not land; only elapsed time can.

    Returns (value, channel, attempts). Spends nothing when not verifying a mutation, and stops
    early when the read budget is too low to justify the spend — a probe that exhausts the channel
    to polish a message has made things worse.
    """
    series = uuid.uuid4().hex[:8]  # ties one mutation's attempts together in the log
    t0 = time.time()

    # EVERY attempt is recorded, including an immediately-visible one: logging only the lagging
    # cases would bias the record toward lag and make the ladder look more necessary than it is.
    # Attempts are held until the series ends so that exactly ONE record — the last — carries the
    # outcome. Writing a separate terminal record would double-count the final read as two
    # observations, which is the same over-counting defect as reporting attempts never made.
    attempts = []

    def note_attempt(attempt, seen, chan):
        attempts.append({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "series": series,
            # TWO INDEPENDENT FACTS, TWO FIELDS (item 25). They were collapsed: `step` carried the
            # sentinel "(not-a-verify)" and `outcome` could itself BE "not-a-verify", entangling
            # *was this a verify?* with *was the value visible?*. Measured on the real log — 26
            # series, only 6 of them verifies, all reported together as "22 became visible". Sizing
            # the ladder from that would average in twenty runs that were never waiting for anything.
            "step": AFTER_MUTATION,          # None when this is not a post-mutation verify
            "is_verify": bool(AFTER_MUTATION),
            "subject": subject,
            "attempt": attempt,
            "since_read_s": round(time.time() - t0, 2),
            # For the saved plan's verify tail the process starts right after the mutation, so this
            # is the closer proxy for true time-since-write. It over-reads on an ordinary manual run.
            "since_proc_start_s": round(time.time() - PROC_START, 2),
            "visible": bool(seen),
            "channel": chan,
            "budget_remaining": gh_read.BUDGET.get("remaining"),
        })

    def flush(outcome):
        if attempts:
            attempts[-1]["outcome"] = outcome
        for rec in attempts:
            log_lag_observation(root, rec)

    # `first` is an answer the caller already paid for (the terminal-state prefetch). Passing it in
    # rather than special-casing it at the call site buys two things that a branch there did not:
    # the no-lag case is OBSERVED like any other, and the prefetch read is no longer wasted when the
    # ladder does run. The first version of this change branched at the call site, so the fast path
    # skipped `lag_tolerant` entirely and logged NOTHING — leaving a record containing only lagging
    # cases, which is precisely the bias this log was built to avoid. Measured on PR #69's own
    # creation: the read view kept up, and the observation file came back empty.
    value, ch = first if first is not None else read()
    ok = satisfied(value)
    note_attempt(0, ok, ch)
    if ok or not AFTER_MUTATION:
        # `not-visible` is a plain fact about a non-verify run, NOT a censored observation: nothing
        # was being waited for, so it is not a lower bound on anything and must never reach a
        # lag summary. That distinction is the whole reason these outcomes now partition.
        flush("visible" if ok else "not-visible")
        return value, ch, 0

    tries = 0  # re-reads ACTUALLY made. Reporting the ladder length here would overstate the
    for i, delay in enumerate(LAG_RETRY_DELAYS, start=1):  # effort on every budget-break path,
        remaining = gh_read.BUDGET.get("remaining")        # which is the tools-that-report-a-
        if remaining is not None and remaining < LAG_RETRY_MIN_BUDGET:  # non-result-as-a-result
            note(f"lag re-read skipped — only {remaining} reads remain on this channel")  # class.
            flush("abandoned-low-budget")
            return value, ch, tries
        print(f"VERIFY  {AFTER_MUTATION}: not visible yet — re-reading "
              f"({i}/{len(LAG_RETRY_DELAYS)}, +{delay}s)")
        time.sleep(delay)
        value, ch = read()
        tries = i
        ok = satisfied(value)
        note_attempt(i, ok, ch)
        if ok:
            flush("visible")
            return value, ch, tries
    # CENSORED: the ladder ran out before the read view caught up. This series is a LOWER BOUND on
    # the true lag, not a measurement of it. Any summary that treats it as an observed value — or
    # drops it because it has no end time — underestimates the distribution, which is exactly how a
    # too-short ladder gets justified by the data its own shortness produced.
    flush("censored-ladder-exhausted")
    return value, ch, tries


OUTCOMES = ("visible", "not-visible", "censored-ladder-exhausted", "abandoned-low-budget")


def normalize_observation(rec):
    """Upgrade a pre-partition record ON READ. The log is evidence and is never rewritten.

    Item 25's migration question, which is why a schema change to existing on-disk state deserves
    the same design pass as introducing it. Records written before the split carry
    `step: "(not-a-verify)"` and can carry `outcome: "not-a-verify"`; both encode *is_verify* in a
    field that is supposed to mean something else. Translating on read keeps every observation
    already collected usable — and rewriting the file to "clean" it would destroy the only real
    measurements this operation has of GitHub's read-after-write behaviour.
    """
    r = dict(rec)
    if "is_verify" not in r:
        r["is_verify"] = r.get("step") not in (None, "(not-a-verify)")
    if r.get("step") == "(not-a-verify)":
        r["step"] = None
    if r.get("outcome") == "not-a-verify":
        r["outcome"] = "not-visible"
    return r


def lag_report(root):
    """Print the RAW read-after-write observations. Reports; never recommends.

    The ladder in this file was invented, and the only defence against inventing the next one is a
    record of what GitHub actually did. So this deliberately stops at the evidence: it shows every
    series, marks the censored ones, and does NOT compute a suggested delay. A tool that hands you a
    number is a tool you will adopt the number from, and a number derived from 4 observations with 2
    censored is the same guess wearing a decimal point.
    """
    path = lag_log_path(root)
    if not path.exists():
        print(f"no observations yet — {path}")
        print("  The log fills as post-mutation verifies run (saved plans with --after-mutation).")
        return EXIT_OK

    series = {}
    for line in path.read_text(errors="replace").splitlines():
        try:
            rec = normalize_observation(json.loads(line))
        except ValueError:
            continue
        series.setdefault(rec.get("series"), []).append(rec)

    # Only VERIFY series can inform the ladder. An ordinary run was not waiting for anything, so its
    # timing says nothing about read-after-write lag; folding the two together is how 20 unrelated
    # runs came to sit inside a "22 became visible" tally.
    verifies, ordinary = [], []
    for sid, recs in sorted(series.items(), key=lambda kv: kv[1][0].get("ts", "")):
        recs.sort(key=lambda r: r.get("attempt", 0))
        (verifies if recs[-1].get("is_verify") else ordinary).append(recs)

    print(f"READ-AFTER-WRITE OBSERVATIONS  ({path})")
    print("  raw record only — this report deliberately recommends NO ladder")
    print("")
    if not verifies:
        print("  no post-mutation verifies recorded yet — nothing here bears on the ladder")
    else:
        print(f"  {'step':<9} {'subject':<28} {'attempts':>8}  {'visible at':>11}  outcome")
    tally = {k: 0 for k in OUTCOMES}
    unknown = 0
    for recs in verifies:
        last = recs[-1]
        outcome = last.get("outcome", "(incomplete)")
        if outcome in tally:
            tally[outcome] += 1
        else:
            unknown += 1
        print(f"  {str(last.get('step') or '?'):<9} {str(last.get('subject') or ''):<28} "
              f"{len(recs):>8}  {str(last.get('since_proc_start_s', '?')) + 's':>11}  {outcome}")

    # The tally MUST partition the rows above it. A footer that disagrees with its own table is the
    # defect this section was rewritten to remove — it previously printed "22 series" over 26 rows.
    counted = sum(tally.values()) + unknown
    print("")
    print(f"  {len(verifies)} verify series — "
          + ", ".join(f"{tally[k]} {k}" for k in OUTCOMES if tally[k])
          + (f", {unknown} unrecognised" if unknown else ""))
    if counted != len(verifies):
        print(f"  ⚠ TALLY DOES NOT PARTITION: {counted} counted against {len(verifies)} rows — "
              "treat this report as unreliable and fix the categories before using the data.")
    print(f"  ({len(ordinary)} ordinary runs also recorded — excluded: they were not waiting "
          "for a mutation)")

    censored = tally["censored-ladder-exhausted"] + tally["abandoned-low-budget"]
    if censored:
        # Kept SHOUTING deliberately. This rewrite first listed outcomes in lowercase only, and a
        # standing test caught the loss of prominence: censoring is the one fact a reader must not
        # skim, because treating a lower bound as a measurement is how a short ladder self-justifies.
        print(f"  ⚠ {censored} CENSORED")
        print("    A censored series is a LOWER BOUND on the lag, not a measurement of it.")
        print("    Averaging only the visible ones understates the distribution — which is exactly")
        print("    how a too-short ladder gets justified by the data it produced.")
    if len(verifies) < 20:
        print(f"  ⚠ {len(verifies)} verify series is not a distribution. Do not resize the ladder "
              "from this yet.")
    print("  Timing caveat: `since_proc_start_s` approximates time-since-write only for a saved")
    print("  plan's verify tail, where the process starts moments after the mutation.")
    return EXIT_OK


def waiting(route, step, what, probe, plan=False):
    """The mutation succeeded; the read view has not caught up. NOT a refusal, and never red.

    Item 19, measured twice. `refuse()` prints REFUSED and exits 1 directly beneath a successful
    irreversible mutation, and the natural operator reaction to that is to run the mutation again.
    The driver already owned the right vocabulary — `not_ready` and exit 2 mean "the platform has
    not answered yet" everywhere else in this file; this path simply never used it.
    """
    if plan:
        raise PlanStop("wait", step, why=what)
    route.mark(step, "wait")
    print("")
    print(route.header())
    print("")
    print(f"WAITING {step}: {what}")
    print(f"  evidence:  {mutation_proof()}")
    print("  diagnosis: read-after-write lag on GitHub's own read view, not a failed mutation.")
    print(f"  poll:      {probe}")
    print(f"  DO NOT re-run the {step} mutation — it reported success. Poll the read view instead.")
    budget = gh_read.budget_report()
    if budget:
        print(f"  budget:    {budget} (poll no faster than 60s)")
    return EXIT_NEEDS_INPUT


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


def saved_plan_path(root):
    """The saved plan. One place names it, so writer and cleaner cannot drift apart."""
    return pathlib.Path(root) / ".git" / "pr-flow" / "next.sh"


def verify_invocation(root, step=None):
    """The driver invocation that produced this plan, PINNED at write time.

    The tail used to be `--branch "${PR_FLOW_BRANCH:-$(git branch --show-current)}"`, which resolves
    when the script RUNS while the mutation above it is literal text fixed when the script was
    WRITTEN. Switch branches in between and the plan MUTATES ONE PULL REQUEST THEN VERIFIES ANOTHER.
    Measured 2026-08-12: it re-merged #64 and then printed `REFUSED: no open PR` about
    `release/v0.1.39` — a true statement about an object it had never touched, directly beneath
    `"merged": true`. The reassuring line and the alarming line described different pull requests.

    Reconstructing the caller's own argv pins the branch and carries `--base`, `--body-file` and
    `--title` along with it, so the tail can actually reach the step it verifies instead of refusing
    for want of arguments it was never handed.
    """
    argv = INVOCATION if INVOCATION is not None else [a for a in sys.argv[1:] if a != "--plan"]
    argv = [a for a in argv if a not in ("--after-mutation", "--mutation-evidence")]
    if step:
        # Pinned at write time, exactly like the branch: the tail must know it is verifying a
        # mutation it just ran, because that is what licenses lag tolerance and forbids emitting
        # another mutation. Derived at run time it would be guesswork.
        argv += ["--after-mutation", step, "--mutation-evidence", "$_ev"]
    quoted = " ".join(shlex.quote(a) for a in [sys.executable, f"{root}/tools/pr-flow.py", *argv])
    # $_ev must reach bash unquoted to expand; everything else stays quoted.
    return quoted.replace("'$_ev'", '"$_ev"')


def discard_saved_plan(root):
    """Delete a spent plan. A plan that outlives its step is a loaded command left on the desk.

    `write_saved_plan` fires only on OPERATOR-owned steps, so the file survives untouched across
    every intervening AGENT-owned step (push, branch delete) while still holding the LAST operator
    mutation. Deleting it once the lifecycle completes is the other half of the branch guard.
    """
    try:
        p = saved_plan_path(root)
        if p.exists():
            p.unlink()
            return p
    except OSError:
        pass
    return None


def write_saved_plan(root, step, command, approve, branch, assert_args=None):
    """Write the operator's command to disk so a SHORT line is what gets pasted.

    F14 and F26: the interactive paste channel corrupted two hand-offs and clobbered a repo file.
    The full text is printed for review; only a short invocation is typed. The file also carries
    the precondition assertion, which is what closes the TOCTOU window on an operator step.

    It further records the BRANCH it was written for. The expiry and the precondition assertion both
    guard against the STATE moving; neither guards against the caller standing at a different step
    than the plan was written for. That is a distinct failure, and it is the one that fired.
    """
    try:
        d = pathlib.Path(root) / ".git" / "pr-flow"
        d.mkdir(parents=True, exist_ok=True)
        path = saved_plan_path(root)
        expiry = int(time.time()) + PLAN_TTL_SECONDS
        header = (
            ["# Consent was given for the state asserted below. If GitHub has moved, this aborts",
             "# WITHOUT mutating: approval does not transfer to a different state."]
            if assert_args else
            ["# NOTE: no live-state assertion is made here — this step has no pull request to",
             "# assert against. The expiry and the branch guard below are the staleness guards."]
        )
        body = [
            "#!/usr/bin/env bash",
            f"# generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} by pr-flow.py"
            f" — step '{step}'" + (f", branch '{branch}'" if branch else ""),
            *header,
            "set -euo pipefail",
            f'if [ "$(date +%s)" -gt {expiry} ]; then',
            '  echo "saved plan EXPIRED — re-run tools/pr-flow.py to derive a current one" >&2',
            "  exit 1",
            "fi",
        ]
        if not branch:
            # Never write an UNGUARDED plan. A guard that is silently absent is worse than none:
            # the file still reads as safe while the protection is gone. `branch` is positional-
            # required above so a call site cannot omit it by accident; this catches an empty value.
            raise ValueError("write_saved_plan requires the branch the plan is written for")
        if branch:
            # The step guard. Consent was given for ONE step of ONE branch's lifecycle; running this
            # file from somewhere else is not that step, however unchanged GitHub's state may be.
            body += [
                f"_want={shlex.quote(branch)}",
                f'_have="$(git -C {shlex.quote(str(root))} branch --show-current)"',
                'if [ "$_have" != "$_want" ]; then',
                '  echo "saved plan was written for branch \'$_want\' (step '
                f"{step}) but you are on '$_have'.\" >&2",
                '  echo "Re-run tools/pr-flow.py to derive a plan for where you actually are." >&2',
                "  exit 1",
                "fi",
            ]
        body.append(f"cd {root}")
        if approve:
            body.append(f"# authorizing: {approve}")
        if assert_args:
            # The assertion runs BEFORE the mutation and `set -e` aborts on its non-zero exit, so
            # a state that moved between emission and execution never reaches the command.
            body.append(f"python3 {root}/tools/pr-flow.py --assert-preconditions "
                        + " ".join(assert_args))
        body += [
            # Capture the mutation's own response alongside showing it. When the read view lags,
            # the platform's own "merged": true is what settles the operator's question — an
            # inference from `set -e` is correct but far less convincing at the moment it matters.
            '_ev="$(mktemp -t pr-flow-evidence.XXXXXX)"',
            'trap \'rm -f "$_ev"\' EXIT',
            "",
            "# MUTATION — the step you authorized:",
            f"{command} 2>&1 | tee \"$_ev\"",
            "",
            "# VERIFY — did it land? (invocation pinned at write time, see verify_invocation.)",
            "# --after-mutation makes an unconfirmed read WAITING rather than REFUSED, and forbids",
            "# this tail from emitting another mutation.",
            f'echo "MUTATION {step}: command exited 0"',
            verify_invocation(root, step),
        ]
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

    # EXACT comparison, except `head` where a short SHA prefix is a convenience. A prefix match on a
    # count would let an approved `failures=1` silently satisfy an actual 12.
    moved = [(k, v, actual.get(k)) for k, v in want.items()
             if k != "pr" and k in actual
             and (not actual[k].startswith(v) if k == "head" else actual[k] != v)]
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


GATE4_HEADING = re.compile(r"^#{2,}\s.*\bGate 4\b", re.I)
ANY_HEADING = re.compile(r"^#{2,}\s")
# A sign-off is a RECORD, not a word: ticked box, the word, AND an ISO date. The date is what makes
# it unforgeable by the template, whose unticked task necessarily contains the word "Approved"
# while describing what signing would mean.
SIGNOFF_LINE = re.compile(r"^\s*- \[[xX]\]\s.*\bApproved\b.*\b\d{4}-\d{2}-\d{2}\b")

SIGNOFF_SHAPE = ("a ticked item inside the '## 4. Gate 4' section carrying the word Approved and "
                 "an ISO date, e.g. `- [x] 4.1 ... **Approved** — <operator>, 2026-08-04`")


def approval_state(root, branch=None):
    """Step 0: Gate-4 sign-off is the one pure-authority step, measured structurally.

    THREE defects were found here by audit, all of the same family — a check loose enough to be
    satisfied by prose that merely mentions the thing it is meant to verify:

      1. The first cut matched the word "Approved" ANYWHERE, so the unticked task DESCRIBING the
         sign-off read as the sign-off. Dogfooding caught it reporting Gate 4 signed while unsigned.
      2. The second cut required a ticked box but still scanned the WHOLE file, so any ticked item
         mentioning the word would pass.
      3. Its `return` sat inside the per-file loop, so only the FIRST change directory was ever
         examined and a second unarchived change was never checked at all.

    So the match is now scoped to the Gate-4 SECTION, requires a ticked box, and requires an ISO
    date — a record with a shape, not a keyword. Every unarchived change is evaluated, and one
    unsigned change is enough to withhold authorization.
    """
    results = []
    for t in sorted(pathlib.Path(root).glob("openspec/changes/*/tasks.md")):
        if "archive" in t.parts:
            continue
        results.append((_gate4_signed(t), t.relative_to(root)))
    if results:
        unsigned = [str(p) for ok, p in results if not ok]
        if unsigned:
            return False, f"Gate 4 UNSIGNED in {', '.join(unsigned)} — expected {SIGNOFF_SHAPE}"
        return True, f"recorded in {', '.join(str(p) for _, p in results)}"

    # No UNARCHIVED change — but archiving on the feature branch before the merge is the
    # RECOMMENDED order (archiving after costs a second pull request), so by merge time the
    # sign-off for the change this branch carries has moved into the archive. Reading it there is
    # what keeps the gate live at the one moment it matters.
    #
    # Looked up BY NAME, never by scanning the archive: any historical change would carry a valid
    # sign-off, so an unkeyed scan would let some 2026-06 approval authorize today's merge — the
    # same wrong-scope error that made the first cut of this function match any ticked line.
    stem = (branch or "").split("/")[-1]
    if stem:
        for d in sorted(pathlib.Path(root).glob("openspec/changes/archive/*")):
            t = d / "tasks.md"
            if d.is_dir() and d.name.endswith(stem) and t.exists():
                if _gate4_signed(t):
                    return True, f"recorded in {t.relative_to(root)} (archived)"
                return False, (f"Gate 4 UNSIGNED in archived {d.name} — expected {SIGNOFF_SHAPE}")
    return None, "no openspec change on this branch matches it"


def _gate4_signed(path):
    """True only for a ticked, dated sign-off inside the Gate-4 section of this file."""
    in_gate4 = False
    for line in path.read_text(errors="replace").splitlines():
        if ANY_HEADING.match(line):
            in_gate4 = bool(GATE4_HEADING.match(line))
            continue
        if in_gate4 and SIGNOFF_LINE.match(line):
            return True
    return False


def unarchived_change(root):
    for d in sorted(pathlib.Path(root).glob("openspec/changes/*")):
        if d.is_dir() and d.name != "archive":
            return d.name
    return None


def _ci_scope_rule(root):
    """Load the declared-scope CI gate's OWN fence rule, so the two cannot disagree.

    Read-only import of `.github/scripts/extract-declared-scope.py` (it guards its `__main__`, so
    importing executes nothing). Returns None if unavailable.
    """
    try:
        import importlib.util
        p = pathlib.Path(root) / ".github/scripts/extract-declared-scope.py"
        spec = importlib.util.spec_from_file_location("_declared_scope", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.FENCE_RE
    except Exception:  # noqa: BLE001 - absence is handled by the caller's stricter fallback
        return None


def scope_block_in(text, root=None):
    """True only if the body carries a scope block THE CI GATE WOULD ACCEPT.

    An earlier cut of this tested `^```scope` alone. That is looser than the gate it claims to
    pre-verify: a fence opened at line start and NEVER CLOSED passed here and is rejected there.
    A check that green-lights what the real gate will fail is worse than no check, because it is
    relied upon. The gate's own regex is therefore imported rather than restated, and the block
    must additionally carry at least one path entry — the gate fails an empty one.
    """
    body = text or ""
    rule = _ci_scope_rule(root) if root else None
    if rule is None:
        # Conservative fallback: line-anchored open AND a closing fence, matching the gate's shape.
        rule = re.compile(r"^```scope[ \t]*\r?\n(.*?)```", re.DOTALL | re.M)
    m = rule.search(body)
    return bool(m) and any(ln.strip() for ln in m.group(1).splitlines())


# --- the traversal ---------------------------------------------------------------------------

def drive(args, root, route, plan=False):
    prefetched = None  # the terminal-state lookup, reused so the fix costs no extra read budget
    branch = args.branch or git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
    base = args.base
    if not plan:
        out("branch", branch)
        out("base", base)

    if branch == base:
        return refuse(route, "worktree", f"branch and base are both {base!r}",
                      "check out the feature branch first", plan)

    signed, detail = approval_state(root, branch)
    route.mark("approval", "na" if signed is None else ("ok" if signed else "fail"), detail)
    if signed is False:
        note(f"NOTE [approval]: {detail} — the lifecycle may be walked, but the merge is not "
              "authorized until the operator records it. Agents may not sign.")

    # B3: a failed fetch leaves origin/<base> stale, and base-currency measured against a stale ref
    # silently restores the very defect the guard exists to prevent.
    # A TIMEOUT is a failure this guard must see. Before F33 it could not: the runner raised, so the
    # return code it inspects was never produced. `run()` is now total, and the reason is reported.
    fetch = git(["fetch", "--quiet", "origin", base], cwd=root)
    fetched = fetch.returncode == 0
    why_not = ((fetch.stderr or "").strip().splitlines() or [f"exit {fetch.returncode}"])[-1][:120]
    base_ref = f"origin/{base}"
    if not fetched and git(["rev-parse", "--verify", "--quiet", base_ref], cwd=root).returncode:
        return refuse(route, "base",
                      f"could not fetch {base_ref} and no local copy exists — {why_not}",
                      "base-currency cannot be measured against a ref that was never read", plan)
    if not fetched:
        note(f"NOTE [base]: fetch of {base_ref} FAILED ({why_not}) — its tip is UNVERIFIED (last "
             "known copy in use). Re-run when the remote is reachable before trusting "
             "base-currency.")

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

        # F34 — TERMINAL STATE IS RESOLVED BEFORE PRE-TERMINAL GUARDS.
        # A merge advances origin/<base> PAST this branch, so the base-current guard below would
        # emit a rebase for a branch whose pull request merged seconds earlier, and the traversal
        # would never reach the lookup that says so. The pre-merge guards are only meaningful while
        # the change is UNMERGED. This state — merged, not yet cleaned up — is one the driver's own
        # saved plan schedules on every lifecycle, and it had no test: the coverage enumerated the
        # states the WORLD presents and not the states this MECHANISM creates.
        # The lookup is skipped when the slug is unresolvable, preserving the offline local path.
        early_slug = gh_read.slug_from_remote(root)
        if early_slug:
            try:
                prefetched = gh_read.pulls_for_branch(early_slug, branch, base, state="all")
            except gh_read.ReadError:
                prefetched = None
            if prefetched:
                seen = prefetched[0]
                done = [p for p in seen if p.get("merged_at")]
                still_open = [p for p in seen if p["state"] == "open"]
                if done and not still_open:
                    for sid in ("base", "commits", "pushed"):
                        route.mark(sid, "na", "pull request already merged — pre-merge guard moot")
                    out("lifecycle", f"PR #{done[-1]['number']} is already merged — pre-merge "
                                     "guards skipped; verifying the merge and cleanup instead")
                    return post_merge(root, early_slug, branch, done[-1]["number"], foreign,
                                      route, plan)

        current = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
        base_sha = git(["rev-parse", base_ref], cwd=root).stdout.strip()
        if base_sha and git(["merge-base", "--is-ancestor", base_sha, local_sha],
                            cwd=root).returncode != 0:
            if current != branch:
                return emit(route, "base", f"git -C {root} switch {branch}", AGENT, AGENT,
                            CONSENT_LOCAL,
                            f"{branch} needs a rebase onto {base_ref}, but {current!r} is checked "
                            "out — a bare `git rebase` would rebase the WRONG branch.",
                            plan=plan, root=root, branch=branch)
            return emit(route, "base", f"git -C {root} rebase {base_ref}", AGENT, AGENT,
                        CONSENT_LOCAL,
                        f"{branch} does not contain {base_ref}. Rebase BEFORE pushing or merging — "
                        "a PR opened on a stale base reports checks that are not about its own "
                        "change (F30: #50 was pushed before #49 merged).",
                        plan=plan, root=root, branch=branch)
        route.mark("base", "ok", f"contains {base_ref}")
        out("base-current", f"{branch} contains {base_ref}")

        ahead = git(["rev-list", "--count", f"{base_ref}..{branch}"], cwd=root).stdout.strip()
        if ahead == "0":
            return refuse(route, "commits", f"{branch} has no commits over {base_ref}",
                          "nothing to open a PR for", plan)
        route.mark("commits", "ok", f"{ahead} over {base_ref}")
        out("commits", f"{ahead} over {base_ref}")

        if remote_sha != local_sha:
            fast_forward = remote_sha is not None and git(
                ["merge-base", "--is-ancestor", remote_sha, local_sha], cwd=root).returncode == 0
            if remote_sha is None:
                cmd = f"git -C {root} push -u origin {branch}"
                why = "remote branch does not exist yet"
            elif fast_forward:
                # Local merely ADDS commits: this is a fast-forward and a plain push is correct.
                # Emitting --force-with-lease here would work, but it would normalise a force push
                # for a case that never needed one, and a reader seeing the flag would reasonably
                # infer that history had been rewritten. Caught by dogfooding.
                cmd = f"git -C {root} push origin {branch}"
                why = ("local is ahead of origin by new commits (a fast-forward). No force flag: "
                       "nothing is being rewritten, and a force push emitted where none is needed "
                       "teaches the reader to skip past the flag that does matter")
            else:
                cmd = f"git -C {root} push --force-with-lease origin {branch}"
                why = ("remote branch differs from local (rebased). --force-with-lease, never "
                       "--force: it refuses rather than overwrites if anything else pushed "
                       "meanwhile")
            return emit(route, "pushed", cmd, AGENT, OPERATOR, probe_consent(root, cmd), why,
                        approve=f"sends {ahead} commit(s) from {branch} to origin. The command "
                                "carries an explicit -C target, so the guard resolves the repo "
                                "and not the vault.",
                        plan=plan, root=root, branch=branch)
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
        # The `pr` step is where item 19's sharper instance fired: seconds after a successful
        # `gh pr create`, this read returned 0 PRs. Give the read view a bounded chance to catch
        # up before the route concludes the pull request does not exist.
        #
        # ITEM 23: `prefetched` is a 2-TUPLE `(list, channel)`, so a bare `if prefetched:` is truthy
        # even when the list is EMPTY — and an empty list is precisely the lag symptom. The retry
        # below was therefore unreachable on every real invocation where the slug resolves, i.e.
        # always. Measured on PR #68's own creation: the guard suppressed the duplicate correctly,
        # but `pulls_for_branch` was called exactly once and no re-read ever happened.
        #
        # The prefetch is handed to `lag_tolerant` as its FIRST attempt rather than consumed by a
        # branch here. One path, so every outcome is observed and the prefetch read is never wasted:
        # when it already answers, `lag_tolerant` returns immediately having spent nothing extra;
        # when it came back empty during a verify, the ladder continues from it.
        prs, ch, _ = lag_tolerant(
            lambda: gh_read.pulls_for_branch(slug, branch, base, state="all"),
            lambda found: bool(found), root=root, subject=f"branch={branch}",
            first=prefetched)
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
        if not scope_block_in(body_path.read_text(errors="replace"), root):
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
                    plan=plan, root=root, branch=branch)

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
    confirm_mutation("pr")  # item 22: the create is visible — stop suppressing later steps

    # --- body: the declared-scope block must be IN the PR, not merely in a local file ------------
    if not scope_block_in(pr.get("body"), root):
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
                    plan=plan, root=root, branch=branch,
                    assert_args=[f"pr={number}", f"head={head_sha}", "draft=false", f"base={base}"])
    route.mark("body", "ok", "declared-scope block present in the PR body")
    confirm_mutation("body")  # item 22: the PATCH is visible — stop suppressing later steps

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
                    plan=plan, root=root, branch=branch,
                    assert_args=[f"pr={number}", f"head={head_sha}", "draft=false", f"base={base}",
                                 "failures=0", "pending=0", "children=0", "mergeable=ok"])
    return post_merge(root, slug, branch, number, foreign, route, plan)


def post_merge(root, slug, branch, number, foreign, route, plan=False):
    """Verify the merge landed AND the branch is actually gone. The tick is not evidence."""
    for sid in ("pr", "body", "checks", "mergeable", "children", "archive", "merge"):
        if route.state[sid] == "todo":
            route.mark(sid, "ok", "completed earlier in this lifecycle")
    try:
        pr, ch, tries = lag_tolerant(lambda: gh_read.pull_request(slug, number),
                                     lambda p: bool(p.get("merged_at")),
                                     root=root, subject=f"pr={number}")
    except gh_read.ReadError as exc:
        print(f"BLOCKED: cannot re-read PR #{number} — {exc}", file=sys.stderr)
        return EXIT_BLOCKED
    if not pr.get("merged_at"):
        # The merge is the irreversible step, so this is the worst possible place for a false
        # alarm. When we are verifying our own mutation, an unconfirmed read is WAITING; when we
        # are not, an unmerged PR at this point is a genuine refusal and keeps its old verdict.
        if AFTER_MUTATION:
            return waiting(route, "merge",
                           f"PR #{number} is not merged in the read view yet "
                           f"(state={pr.get('state')}) [via {ch}, {tries} re-read(s)]",
                           f"python3 {root}/tools/pr-flow.py --ready merged --pr {number}", plan)
        return refuse(route, "merge", f"PR #{number} is not merged (state={pr.get('state')}) "
                                      f"[via {ch}]", None, plan)
    route.mark("merge", "ok", f"merged {pr['merged_at']}")
    confirm_mutation("merge")  # item 22: observed to land — later steps are new work, not re-emits
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
                        plan=plan, root=root, branch=branch)
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
                        "exactly what made gh's --delete-branch half-fail.",
                        plan=plan, root=root, branch=branch)
        return emit(route, "local-gone", f"git -C {root} branch -D {branch}", AGENT, AGENT,
                    CONSENT_LOCAL, "local branch still present after the merge",
                    plan=plan, root=root, branch=branch)
    route.mark("local-gone", "ok", "deleted")
    out("local-branch", "absent" if foreign else "deleted")

    print("")
    print(route.header())
    print("")
    print(f"LIFECYCLE COMPLETE: PR #{number} merged, remote and local branches cleaned.")
    # The last operator step's plan is spent. Left on disk it outlives its step and stays runnable,
    # which is how a stale plan re-issued a merge for an ALREADY-MERGED pull request (2026-08-12).
    if root and discard_saved_plan(root):
        print("  Saved plan discarded — its step is complete and it must not be re-run.")
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
    ap.add_argument("--after-mutation", metavar="STEP",
                    help="this run verifies STEP's mutation, which just succeeded: tolerate "
                         "read-after-write lag, report WAITING not REFUSED, emit no mutation")
    ap.add_argument("--lag-report", action="store_true",
                    help="print the raw read-after-write observations, then exit")
    ap.add_argument("--mutation-evidence", metavar="PATH",
                    help="file holding the mutation's own response, quoted back when the read "
                         "view contradicts it")
    args = ap.parse_args(argv)
    # Pin the invocation that produced this run, so a saved plan verifies THIS lifecycle rather than
    # whatever branch the caller happens to stand on when they run the file.
    global INVOCATION, AFTER_MUTATION, MUTATION_EVIDENCE
    INVOCATION = [a for a in (argv if argv is not None else sys.argv[1:]) if a != "--plan"]
    AFTER_MUTATION = args.after_mutation
    MUTATION_EVIDENCE = args.mutation_evidence

    r = git(["rev-parse", "--show-toplevel"])
    if r.returncode != 0:
        print("BLOCKED: not inside a git repository", file=sys.stderr)
        return EXIT_BLOCKED
    root = r.stdout.strip()

    if args.capabilities:
        return capabilities(root)
    if args.lag_report:
        return lag_report(root)
    if args.ready:
        return ready(args)
    if args.assert_preconditions:
        return assert_preconditions(args.assert_preconditions)

    route = Route()
    # F33: a state machine that dies without printing where it got is not carrying state. ANY
    # escaping exception still emits the route reached and exits inside the declared vocabulary —
    # a traceback is not one of the four exit codes, and those codes are the whole contract.
    try:
        if args.plan:
            globals()["QUIET"] = True
            branch = args.branch or git(["rev-parse", "--abbrev-ref", "HEAD"],
                                        cwd=root).stdout.strip()
            try:
                code = drive(args, root, route, plan=True)
            except PlanStop as stop:
                return render_plan(route, stop, branch, args.base)
            return code
        return drive(args, root, route, plan=False)
    except Exception as exc:  # noqa: BLE001 - the contract is four exit codes, never a traceback
        globals()["QUIET"] = False
        print("")
        print(route.header())
        print("")
        print(f"BLOCKED: the driver could not complete — {type(exc).__name__}: {exc}",
              file=sys.stderr)
        print("  The route above is the state actually reached. Nothing was mutated; re-invoke to "
              "resume from there.")
        return EXIT_BLOCKED


if __name__ == "__main__":
    sys.exit(main())
