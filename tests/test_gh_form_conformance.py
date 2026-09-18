# SPDX-License-Identifier: Apache-2.0
"""Every `gh` invocation this repository SHIPS must pass the guard that will receive it.

WRITTEN RED-FIRST. At the time of writing, seven call sites are refused by the guard — the two
emitted commands, two executed reads, and the canary workflow's three calls. A detector written
after the conversions could not demonstrate that it would have caught them.

WHY THIS EXISTS. The lifecycle driver emitted `gh pr create` at its pull-request step while the
invocation-form allowlist refused that exact form, and the same driver used `gh api` with an explicit
REST path at three other steps. The rule existed, was applied three times, and was missed once.
Nothing compared the emissions against the guard, so the gap persisted rather than being caught on
the next run. This module is that comparison.

THE GUARD IS THE ORACLE. No pattern list is authored here. The refusal rule is *imported* by running
the shipped guard — restating it would be the estate's class-9 defect, and a restated copy would
drift from the original exactly when it mattered. The guard is extracted from its meta-script note
(INV-3 source of truth) and run as a real subprocess, the way the harness runs it, rather than
imported: that way the hook's own fail-open path is observable instead of being a caught exception.

TWO BLIND SPOTS ARE DESIGNED OUT, because a detector that merely mirrors the guard reproduces them:

  1. COMMAND SUBSTITUTION. Measured 2026-09-18: the guard PERMITS `open=$(gh issue list …)` because
     `open=$(gh` parses as an environment assignment, so the command word becomes `issue`. The
     canary's dedupe read is exactly that shape. This module therefore UNWRAPS substitution and
     submits the inner command, so the finding does not depend on the guard being able to see it.
  2. UNLEXABLE INPUT. `shlex` raises on a trailing backslash or an unbalanced quote, and the guard's
     `main()` does `except Exception: return` — fail open, silently. A form the guard cannot lex is
     reported here as a finding in its own right, never skipped.

SCOPE, stated so this suite is not credited with more than it covers: it checks FORM, not CHANNEL.
Whether a given subcommand reaches GraphQL or REST is a property of the `gh` binary, is documented
nowhere authoritative, and changes between releases. Form is stable, checkable offline, and does not
rot — which is the whole argument for an allowlist over an audit.
"""
import ast
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
NOTE = REPO / "vault-template/99-Operations/scripts/gh-invocation-guard-script.md"

# Command sinks: a string reaching one of these BECOMES a command. Enumerating sinks rather than
# message functions is deliberate — new message functions appear constantly, new sinks are rare and
# architectural, so coverage of a new emission needs nobody to remember anything.
SINK_CALLS = {"emit", "_emit_next", "run", "check_output", "check_call", "Popen", "system"}
SINK_NAMES = {"cmd", "command", "next_cmd"}

PY_DIRS = ("tools", ".claude/hooks", ".github/scripts")
GH_WORD = re.compile(r"(?:^|[;&|(]\s*|\$\(\s*|`\s*)gh\s+[a-z]")


@pytest.fixture(scope="module")
def guard(tmp_path_factory):
    """The shipped guard body, extracted from its note — the same block `render` deploys."""
    assert NOTE.exists(), f"{NOTE.relative_to(REPO)} is missing; the guard has no source of truth"
    m = re.search(r"^## Implementation\s*\n```python\n(.*?)^```",
                  NOTE.read_text(encoding="utf-8"), re.S | re.M)
    assert m, "no python implementation block in the gh invocation guard note"
    p = tmp_path_factory.mktemp("ghguard") / "gh-invocation-guard.py"
    p.write_text(m.group(1), encoding="utf-8")
    return p


def decide(guard, cmd):
    """-> (decision, reason). 'defer' = exit 0 with no output: the hook stands aside."""
    r = subprocess.run(
        [sys.executable, str(guard)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}),
        capture_output=True, text=True, env=dict(os.environ))
    assert r.returncode == 0, f"guard exited {r.returncode}: {r.stderr[:300]}"
    if not r.stdout.strip():
        return "defer", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


# --- enumeration, by mechanism rather than by pattern -------------------------------------------

def _unwrap(text):
    """Yield `text` plus every command nested inside substitution, backticks or a subshell.

    The guard cannot see these; this module must. Without unwrapping, the canary's
    `open=$(gh issue list …)` would be reported as conforming — the precise false negative
    measured in the 2026-09-18 dry run.
    """
    yield text
    for pat in (r"\$\(([^()]*)\)", r"`([^`]*)`", r"\(\s*([^()]*)\)"):
        for inner in re.findall(pat, text):
            if inner.strip():
                yield inner.strip()


def _docstrings(tree):
    out = set()
    for n in ast.walk(tree):
        body = getattr(n, "body", None)
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and body:
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
               and isinstance(first.value.value, str):
                out.add(id(first.value))
    return out


def _python_sites(path):
    """Executed argv lists, and strings that reach a command SINK. Prose is not a command."""
    return _sites_from_tree(ast.parse(path.read_text(errors="replace")))


def _sites_from_tree(tree):
    """One implementation, shared by `.py` files and by the notes' python fences.

    Two enumerators over the same language would drift, and the one used less often would drift
    first — which is the failure mode this whole module exists to catch.
    """
    skip = _docstrings(tree)
    for n in ast.walk(tree):
        # (a) executed: a list/tuple literal whose first element is "gh"
        if isinstance(n, (ast.List, ast.Tuple)) and n.elts:
            head = n.elts[0]
            if isinstance(head, ast.Constant) and head.value == "gh":
                parts = [e.value if isinstance(e, ast.Constant) else "X" for e in n.elts]
                yield n.lineno, " ".join(str(p) for p in parts)
        # (b) emitted: a string reaching a sink call, or assigned to a command-shaped name
        sunk = []
        if isinstance(n, ast.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in SINK_CALLS and n.args:
                # ONLY the first positional argument. `emit(route, "pr", cmd, why=…, approve=…)`
                # carries prose in its keyword arguments that mentions refused forms on purpose —
                # walking the whole call reported the driver's own explanation of why it avoids
                # `gh pr merge` as if it were an emission. A string that MENTIONS a command is not
                # a command; the sink's command argument is.
                sunk = list(ast.walk(n.args[0]))
        elif isinstance(n, ast.Assign) and n.targets:
            if getattr(n.targets[0], "id", None) in SINK_NAMES:
                sunk = list(ast.walk(n.value))
        for sub in sunk:
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and id(sub) not in skip:
                if GH_WORD.search(sub.value):
                    yield sub.lineno, sub.value
            elif isinstance(sub, ast.JoinedStr):
                flat = "".join(v.value if isinstance(v, ast.Constant) else "X"
                               for v in sub.values)
                if GH_WORD.search(flat):
                    yield sub.lineno, flat


def collect():
    """-> (sites, denominator). A count with no denominator is how a silent miss hides."""
    sites, files, failures = [], 0, []

    for d in PY_DIRS:
        for f in sorted((REPO / d).rglob("*.py")) if (REPO / d).is_dir() else []:
            files += 1
            try:
                for lineno, text in _python_sites(f):
                    sites.append((f, lineno, text))
            except SyntaxError as exc:
                failures.append((f, exc))

    for f in sorted((REPO / ".github/workflows").glob("*.y*ml")):
        files += 1
        # Join `\`-continued lines FIRST. A command split across lines is one command; lexing the
        # first fragment alone reported a trailing backslash as "unlexable" when the real file is
        # perfectly well formed. The continuation is a property of the file, not of the command.
        raw, joined, start = f.read_text(errors="replace").splitlines(), [], None
        buf = ""
        for i, line in enumerate(raw, 1):
            s = line.strip()
            if start is None:
                start = i
            if s.endswith("\\"):
                buf += s[:-1] + " "
                continue
            joined.append((start, buf + s))
            buf, start = "", None
        for i, text in joined:
            if GH_WORD.search(text):
                sites.append((f, i, text))

    # Literate meta-script notes: a python fence IS code and is parsed as code. Scanning its lines
    # as text reported the guard note's own comments and refusal messages — the file whose job is
    # to name refused forms — as if it emitted them.
    for f in sorted((REPO / "vault-template/99-Operations/scripts").glob("*.md")):
        files += 1
        for m in re.finditer(r"^```python\n(.*?)^```", f.read_text(errors="replace"), re.S | re.M):
            offset = f.read_text(errors="replace")[:m.start()].count("\n") + 1
            block = m.group(1)
            try:
                tree = ast.parse(block)
            except SyntaxError as exc:
                failures.append((f, exc))
                continue
            for lineno, text in _sites_from_tree(tree):
                sites.append((f, offset + lineno, text))

    return sites, (files, failures)


# --- the checks ---------------------------------------------------------------------------------

def test_the_enumeration_has_a_denominator():
    """A finding count means nothing without the size of the set it was drawn from."""
    _, (files, failures) = collect()
    assert not failures, f"files that would not parse are UNCHECKED, not clean: {failures}"
    assert files >= 15, f"only {files} files scanned — the enumeration is not reaching the tree"


def test_no_shipped_gh_form_is_refused_by_the_guard(guard):
    """THE CHECK. Every `gh` invocation the repo ships must pass the guard that receives it."""
    refused, seen = [], set()
    for path, lineno, text in collect()[0]:
        if (path, lineno) in seen:
            continue  # one site, one finding: an f-string yields both its flattened and inner forms
        for candidate in _unwrap(text):
            if not GH_WORD.search(candidate):
                continue
            decision, reason = decide(guard, candidate)
            if decision == "deny":
                seen.add((path, lineno))
                refused.append(
                    f"{path.relative_to(REPO)}:{lineno}\n"
                    f"      form:  {candidate.strip()[:90]}\n"
                    f"      guard: {reason.splitlines()[0][:110]}")
                break
    assert not refused, (
        f"{len(refused)} shipped `gh` form(s) are refused by the estate's own guard:\n\n"
        + "\n".join(refused)
        + "\n\nEach must become `gh api <REST path>`; the guard's message carries the mapping.")


def test_an_unlexable_form_is_a_finding_not_a_skip():
    """The guard fails OPEN on input it cannot lex; this suite must not inherit that.

    Vendor documentation is explicit that a hook which does not return a deny lets the call
    proceed, so a form `shlex` chokes on is silently permitted in production. Reporting it as
    'no findings' would be the same class of wrong answer this module exists to prevent.
    """
    unlexable = []
    for path, lineno, text in collect()[0]:
        for candidate in _unwrap(text):
            if not GH_WORD.search(candidate):
                continue
            try:
                shlex.split(candidate)
            except ValueError as exc:
                unlexable.append(f"{path.relative_to(REPO)}:{lineno} ({exc}): {candidate[:70]}")
    assert not unlexable, (
        "these forms cannot be lexed, so the guard fails OPEN on them and permits them "
        "silently:\n  " + "\n  ".join(unlexable))


def test_coverage_does_not_depend_on_registration(guard, tmp_path):
    """A NEW emission must be caught without anyone adding it to a list.

    The spec requires coverage that does not depend on the author remembering. This proves the
    property on a fixture rather than asserting it: a freshly-written non-conforming emission,
    in a shape the guard itself cannot see, is still detected.
    """
    fixture = tmp_path / "newly_added_tool.py"
    fixture.write_text(
        "def build():\n"
        "    cmd = 'cd /tmp && open=$(gh issue list --state open)'\n"
        "    return cmd\n", encoding="utf-8")
    found = [t for _, t in _python_sites(fixture)]
    assert found, "a new emission assigned to `cmd` was not enumerated at all"
    verdicts = [decide(guard, c)[0] for t in found for c in _unwrap(t) if GH_WORD.search(c)]
    assert "deny" in verdicts, (
        "the substituted form was not refused — the detector has inherited the guard's "
        "blind spot instead of designing it out")
