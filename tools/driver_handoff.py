#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Shared operator-handoff machinery for the two lifecycle drivers (item 41).

`pr-flow.py` and `ship-release.py` both reach a point where the next command is IRREVERSIBLE OUTBOUND
(a branch/tag push, a PR merge, a `gh api` mutation, a release create) and therefore OPERATOR-ONLY —
the INV-14 outbound guard hard-denies those on the agent's channel (item 37). Both must hand that
command to the operator the same way: write a short, self-guarding `next.sh`, and print the item-39
copy-whole relay block the agent copies verbatim (byte-checked by the item-40 Stop hook).

That machinery lived in `pr-flow.py`. Duplicating ~50 lines of it into `ship-release.py` would fork
the format the outbound guard and the relay-conformance hook compare against — the class-9 defect
(a second copy with no merge). So it is extracted here and IMPORTED by both drivers, the same way
`gh_read.py` is the one shared read layer.

What is generic (here) vs. what each driver supplies:

* Generic: the saved-plan skeleton (shebang, expiry guard, branch guard, `cd`, evidence capture,
  the mutation line), the emission record the guard reads, the history-suffix comment, and the
  copy-whole relay block + `relay-line.txt` sidecar.
* Per-driver: the VERIFY tail (pr-flow re-invokes `pr-flow.py --after-mutation`; ship-release
  re-invokes `ship-release.py`, which re-derives release state), and any pre-mutation assertion
  lines (pr-flow's `--assert-preconditions`; ship-release has none). Both are passed in as ready
  shell lines, so this module never names a driver.

Stdlib-only, offline, deterministic (it writes files and formats strings; it spawns nothing).
"""
import json
import pathlib
import shlex
import time

PLAN_TTL_SECONDS = 24 * 60 * 60  # industry practice: approvals expire so stale plans cannot apply


def saved_plan_path(root):
    """The saved plan. One place names it, so writer and cleaner cannot drift apart."""
    return pathlib.Path(root) / ".git" / "pr-flow" / "next.sh"


def emission_record_path(root):
    """The emission record the outbound guard reads. One place names it, as above."""
    return pathlib.Path(root) / ".git" / "pr-flow" / "emitted.json"


def relay_line_path(root):
    """The canonical relay-line sidecar the item-40 Stop hook byte-checks against."""
    return pathlib.Path(root) / ".git" / "pr-flow" / "relay-line.txt"


def plan_history_suffix(step, body_file=None, pr_number=None, target=None):
    """A trailing comment that makes the operator's shell history navigable.

    Every saved-plan invocation is BYTE-IDENTICAL — `bash <repo>/.git/pr-flow/next.sh` — so
    `history | grep next.sh` returns a wall of indistinguishable lines and the operator must
    reconstruct which step each one was. They had been appending this by hand:

        bash .../next.sh   # preflight step:merge -> PR #80
        bash .../next.sh   # v0.1.44 step:pr -> new PR

    The driver holds every field that annotation needs, so it emits it. Reconstructing it by memory
    at the moment of a mutation is exactly the wrong time to be remembering anything.

    The mnemonic comes from the body-file stem (`body-preflight.md` -> `preflight`), which is what
    the operator's own convention used and keeps two changes on the same topic distinguishable —
    `const-truth` and `const-diff-gate` were both constitution work and must not read alike. When a
    caller has no body-file (ship-release keys off the version), it passes `target` directly.
    """
    mnemonic = ""
    if body_file:
        stem = pathlib.Path(body_file).stem
        mnemonic = stem[5:] if stem.startswith("body-") else stem
    if target is None:
        target = f"PR #{pr_number}" if pr_number else "new PR"
    return f"   # {mnemonic or 'change'} step:{step} -> {target}"


def write_emission_record(root, step, command, branch):
    """Record the command a driver emitted, verbatim, for the outbound guard to recognise.

    Vault failure class 10, stage 1: the driver prints the exact command and the agent retypes it
    wrong. On 2026-08-16 `git -C <literal> push` was retyped as `R=…; cd "$R"; git -C "$R" push …`;
    the guard resolves effective targets from RAW TEXT, could not resolve `"$R"`, fell back to the
    reported cwd — the vault — and denied. Correctly, on what it could see. A day of wrong
    conclusions followed from one mangled retype.

    `write_saved_plan` already solves this for the OPERATOR (F14, F26: the paste channel corrupting
    a hand-off). It was gated to operator-owned steps on the assumption that an agent transfers
    commands losslessly. This records EVERY step, which is the asymmetry being corrected.

    The record is what the guard compares against; a mismatch DOWNGRADES nothing and simply leaves
    the existing confirmation in place. It can never produce a refusal — see the guard note.

    `repo` is recorded so the record identifies its own subject: a repository is "governed" exactly
    when a driver has emitted for it, which keeps the guard free of any environment dependency.
    """
    try:
        (pathlib.Path(root) / ".git" / "pr-flow").mkdir(parents=True, exist_ok=True)
        path = emission_record_path(root)
        path.write_text(json.dumps({
            "command": command,
            "step": step,
            "branch": branch or "",
            "repo": str(root),
            "expires": int(time.time()) + PLAN_TTL_SECONDS,
        }, indent=2) + "\n", encoding="utf-8")
        return path
    except OSError:
        # Never fatal. A driver that dies because it could not write an advisory record would
        # trade a downgrade for an outage, and the guard fails safe to ASK without it.
        return None


def discard_saved_plan(root):
    """Delete a spent plan. A plan that outlives its step is a loaded command left on the desk.

    `write_saved_plan` fires only on OPERATOR-owned steps, so the file survives untouched across
    every intervening AGENT-owned step (push, branch delete) while still holding the LAST operator
    mutation. Deleting it once the lifecycle completes is the other half of the branch guard.
    """
    # The emission record is discarded with it, and for the same reason: a record that outlives its
    # step is an authorisation left lying where a later, different command can match it.
    try:
        rec = emission_record_path(root)
        if rec.exists():
            rec.unlink()
    except OSError:
        pass
    try:
        p = saved_plan_path(root)
        if p.exists():
            p.unlink()
            return p
    except OSError:
        pass
    return None


def write_saved_plan(root, step, command, approve, branch, *, assert_lines=None, verify_lines=None,
                     foreign=False):
    """Write an operator command to disk so a SHORT line is what gets pasted.

    F14 and F26: the interactive paste channel corrupted two hand-offs and clobbered a repo file.
    The full text is printed for review; only a short invocation is typed. The file also carries
    the precondition assertion (when the caller supplies one), which is what closes the TOCTOU
    window on an operator step.

    It further records the BRANCH it was written for. The expiry and the precondition assertion both
    guard against the STATE moving; neither guards against the caller standing at a different step
    than the plan was written for. That is a distinct failure, and it is the one that fired.

    `assert_lines` (pre-mutation) and `verify_lines` (post-mutation) are supplied by the driver as
    ready shell lines: this module builds the driver-agnostic skeleton and never re-implements a
    driver's own verify contract. pr-flow passes its `--after-mutation` re-invocation; ship-release
    passes its own re-run, which re-derives release state.

    `foreign` (item 42): a branch the driver does not own has, by the driver's own definition, no
    local copy — so the checkout can never equal it, and the step guard would refuse every operator
    step on every Dependabot pull request. For such a branch the guard is the OBJECT, not the
    checkout: the caller's precondition assertion pins the pull request and its head SHA, which
    identifies the step's target exactly. A foreign plan therefore requires `assert_lines`; without
    them it would carry no guard at all, and is refused.
    """
    try:
        d = pathlib.Path(root) / ".git" / "pr-flow"
        d.mkdir(parents=True, exist_ok=True)
        path = saved_plan_path(root)
        expiry = int(time.time()) + PLAN_TTL_SECONDS
        header = (
            ["# Consent was given for the state asserted below. If GitHub has moved, this aborts",
             "# WITHOUT mutating: approval does not transfer to a different state."]
            if assert_lines else
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
            '  echo "saved plan EXPIRED — re-run the driver to derive a current one" >&2',
            "  exit 1",
            "fi",
        ]
        if not branch:
            # Never write an UNGUARDED plan. A guard that is silently absent is worse than none:
            # the file still reads as safe while the protection is gone. `branch` is positional-
            # required above so a call site cannot omit it by accident; this catches an empty value.
            raise ValueError("write_saved_plan requires the branch the plan is written for")
        if foreign:
            if not assert_lines:
                raise ValueError("a foreign-branch plan requires a precondition assertion — it "
                                 "is the only guard such a plan carries")
            body += [f"# Branch '{branch}' is FOREIGN (no local copy), so no checkout comparison "
                     "is made — it could never pass.",
                     "# The precondition assertion below pins the pull request and its head SHA; "
                     "that is this plan's step guard."]
        else:
            # The step guard. Consent was given for ONE step of ONE branch's lifecycle; running
            # this file from somewhere else is not that step, however unchanged GitHub's state may be.
            body += [
                f"_want={shlex.quote(branch)}",
                f'_have="$(git -C {shlex.quote(str(root))} branch --show-current)"',
                'if [ "$_have" != "$_want" ]; then',
                '  echo "saved plan was written for branch \'$_want\' (step '
                f"{step}) but you are on '$_have'.\" >&2",
                '  echo "Re-run the driver to derive a plan for where you actually are." >&2',
                "  exit 1",
                "fi",
            ]
        body.append(f"cd {root}")
        if approve:
            body.append(f"# authorizing: {approve}")
        if assert_lines:
            # The assertion runs BEFORE the mutation and `set -e` aborts on its non-zero exit, so
            # a state that moved between emission and execution never reaches the command.
            body += list(assert_lines)
        body += [
            # Capture the mutation's own response alongside showing it. When the read view lags,
            # the platform's own "merged": true is what settles the operator's question — an
            # inference from `set -e` is correct but far less convincing at the moment it matters.
            '_ev="$(mktemp -t pr-flow-evidence.XXXXXX)"',
            'trap \'rm -f "$_ev"\' EXIT',
            "",
            "# MUTATION — the step you authorized:",
            f'{command} 2>&1 | tee "$_ev"',
        ]
        body += list(verify_lines or [])
        path.write_text("\n".join(body) + "\n")
        path.chmod(0o755)
        return path
    except OSError:
        return None


def emit_operator_handoff(root, step, path, *, suffix, has_assertion, out=print):
    """Print the copy-whole relay block for a saved operator plan, and write its sidecar.

    Item 39: the operator handoff is a COPY-WHOLE BLOCK, not a `To run it:` one-liner the caller
    then retypes. F43: the caller reconstructs the line from the formatting rules and drops the tag /
    swaps the path form / reformats it — >=4 times in one session on a standing rule. Emitting the
    finished block makes copying it lazier than rebuilding it, so the caller's shortcutting pull
    produces correctness. The copyable line is FLUSH-LEFT because an indented paste is mangled
    (operator-command-formatting), and it is byte-identical to the saved-plan invariant form — the
    contract item 40 byte-checks a relayed line against.

    Returns the relay line so a caller can assert on it in tests.
    """
    relay_line = f"bash {path}{suffix}"
    # item 40: the canonical relay line, written to a sidecar so the relay-conformance Stop hook can
    # byte-check what the agent relayed against what the driver emitted. Best-effort — a failed write
    # must never break emission.
    try:
        relay_line_path(root).write_text(relay_line + "\n", encoding="utf-8")
    except OSError:
        pass
    out("")
    out(f"  Saved plan: {path}")
    out("  Relay this block to the operator VERBATIM — copy it whole, do not reformat:")
    out("START COPY")
    out("```bash")
    out(relay_line)
    out("```")
    out("END COPY")
    if has_assertion:
        out("  It re-asserts the state you were shown and aborts WITHOUT mutating if "
            "GitHub has moved; it expires in 24h.")
    else:
        # Say only what the script does. Claiming an assertion this step cannot make is the same
        # false-assurance defect the drivers exist to prevent (class 9).
        out("  It carries a 24h expiry. No live-state assertion is made at this step.")
    return relay_line

