#!/usr/bin/env python3
"""INV-6 static half — prove no fleet script CALLS the network, without flagging ones that NAME it.

INV-6: "`[script]` operations make no network calls and no LLM calls." The Requirement at
`maintenance/spec.md` has always carried a correct behavioural scenario; until 2026-07-28 nothing
ran it. This is the static half of the mechanism; the dynamic half runs the fleet suite inside a
network namespace (CI job `inv6-offline-dynamic`).

**The design problem this tool exists to solve.** A grep-based checker flags exactly the two scripts
it must not: `outbound-publish-guard` and `push-guard` are the INV-14 rail, and their whole job is to
*name* outward verbs (`git push`, `gh repo create`, `npm publish`) inside regex literals. Naming is
not calling. So Python is analysed by **AST** — an `import socket` is an Import node and a
`"git push"` in a pattern is a Constant, and the two are never confused. (The identical
self-reference trap bit the INV-7 scanner on the day it shipped: its own private-key fixture matched
its own pattern table. Same lesson, second application.)

**Honest bounds, stated because a checker that overstates itself is worse than none:**
  - Static analysis is complete over *text* and blind to *semantics*: `__import__(name)` with a
    computed name, `eval`, or a network call inside a C extension is undecidable here. Dynamic
    indirection through `__import__`/`importlib` is therefore reported as **UNRESOLVED**, not clean.
  - Bash has no AST here. The bash half is a conservative command-position scan and is explicitly
    the weaker half — the same unbounded-language problem that leaves the INV-14 guard's regex with
    known holes. It is not claimed to be complete.
  - Passing this tool does NOT prove a script is offline. It proves no *statically visible* network
    call exists. The netns run is what proves behaviour, and it is bounded by test coverage.

Scope: the Layer-0 fleet only — `vault-template/99-Operations/scripts/*.md`. Repo-side maintainer
tools (`ship-release.py`, `template-mirror.py`, …) are NOT fleet scripts; several legitimately use
the network and the maintenance spec says so. Repo-only, stdlib-only, offline, no LLM.

Usage:  tools/inv6-offline-check.py [--selftest]
Exit:   0 clean · 1 violation found · 3 selftest failed (instrument INVALID).
"""
import argparse
import ast
import pathlib
import re
import sys

EXIT_OK, EXIT_VIOLATION, EXIT_SELFTEST = 0, 1, 3

# Unambiguously network-bearing modules. Deliberately tight: a dual-use module (asyncio) is NOT
# listed, because an over-flagging checker gets bypassed (RC-E — over-denial is camouflage).
NET_MODULES = {
    "socket", "ssl", "urllib", "http", "ftplib", "smtplib", "poplib", "imaplib",
    "telnetlib", "xmlrpc", "requests", "urllib3", "httpx", "aiohttp", "paramiko",
    "boto3", "botocore",
}

# Binaries that are network operations by nature, in COMMAND position.
NET_BINARIES = {
    "curl", "wget", "nc", "ncat", "netcat", "telnet", "ssh", "scp", "sftp", "rsync",
    "gh", "pip", "pip3", "npm", "npx", "yarn", "pnpm", "cargo", "gem", "twine", "docker",
}

# `git` is overwhelmingly local in this fleet (diff, log, add, commit, rev-parse). Only these
# subcommands touch a remote.
GIT_NET_SUBCMDS = {"push", "fetch", "pull", "clone", "ls-remote", "remote", "submodule"}

SUBPROCESS_FUNCS = {"run", "call", "check_call", "check_output", "Popen"}
OS_EXEC_FUNCS = {"system", "popen"}


def _argv_from(node):
    """Best-effort literal argv from a subprocess/os call's first argument."""
    if not node.args:
        return None
    a = node.args[0]
    if isinstance(a, ast.Constant) and isinstance(a.value, str):
        return a.value.split()
    if isinstance(a, (ast.List, ast.Tuple)):
        out = []
        for e in a.elts:
            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                out.append(e.value)
            else:
                out.append(None)          # non-literal element
        return out
    return None                            # computed argv — reported as UNRESOLVED below


def _flag_argv(argv, lineno, findings, why):
    if not argv or argv[0] is None:
        findings.append((lineno, "UNRESOLVED", f"{why}: argv is not a literal; cannot decide statically"))
        return
    exe = pathlib.PurePosixPath(argv[0]).name
    if exe in NET_BINARIES:
        findings.append((lineno, "VIOLATION", f"{why}: invokes network binary '{exe}'"))
    elif exe == "git":
        sub = next((a for a in argv[1:] if a and not a.startswith("-")), None)
        if sub in GIT_NET_SUBCMDS:
            findings.append((lineno, "VIOLATION", f"{why}: invokes 'git {sub}' (contacts a remote)"))


def check_python(src):
    """AST walk. A string literal naming a verb is a Constant and is never reported."""
    findings = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [(getattr(e, "lineno", 0), "UNRESOLVED", f"does not parse: {e.msg}")]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split(".")[0] in NET_MODULES:
                    findings.append((node.lineno, "VIOLATION", f"imports network module '{n.name}'"))
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in NET_MODULES:
                findings.append((node.lineno, "VIOLATION", f"imports from network module '{node.module}'"))
        elif isinstance(node, ast.Call):
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            owner = ""
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                owner = f.value.id

            if owner == "subprocess" and name in SUBPROCESS_FUNCS:
                _flag_argv(_argv_from(node), node.lineno, findings, f"subprocess.{name}")
            elif owner == "os" and name in OS_EXEC_FUNCS:
                _flag_argv(_argv_from(node), node.lineno, findings, f"os.{name}")
            elif name in ("__import__", "import_module"):
                arg = node.args[0] if node.args else None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.split(".")[0] in NET_MODULES:
                        findings.append((node.lineno, "VIOLATION",
                                         f"dynamic import of network module '{arg.value}'"))
                else:
                    findings.append((node.lineno, "UNRESOLVED",
                                     "dynamic import with a computed name; cannot decide statically"))
    return findings


# Command position: start of line, or after ; && || | ( { or a pipe. Comments stripped first.
_CMD_POS = re.compile(r"(?:^|[;&|(){}]|\b(?:then|do|else)\b)\s*([A-Za-z_][\w./-]*)")


def check_bash(src):
    """Conservative command-position scan. The weaker half, and documented as such."""
    findings = []
    for i, raw in enumerate(src.split("\n"), 1):
        line = re.sub(r"(?<!\\)#.*$", "", raw)          # strip comments
        line = re.sub(r"'[^']*'|\"[^\"]*\"", " ", line)  # blank quoted strings: naming != calling
        for m in _CMD_POS.finditer(line):
            exe = m.group(1)
            if exe in NET_BINARIES:
                findings.append((i, "VIOLATION", f"invokes network binary '{exe}' in command position"))
            elif exe == "git":
                rest = line[m.end():].split()
                sub = next((t for t in rest if not t.startswith("-")), None)
                if sub in GIT_NET_SUBCMDS:
                    findings.append((i, "VIOLATION", f"invokes 'git {sub}' (contacts a remote)"))
    return findings


FENCE = re.compile(r"^```(python|bash)\n(.*?)^```", re.S | re.M)


def check_note(path):
    body = path.read_text(encoding="utf-8")
    blocks = FENCE.findall(body)
    if len(blocks) != 1:
        return [(0, "UNRESOLVED", f"expected exactly 1 python|bash fence, found {len(blocks)}")]
    lang, src = blocks[0]
    return check_python(src) if lang == "python" else check_bash(src)


def selftest():
    """Controls in BOTH directions: the checker must fire on real calls AND stay silent on names.

    The second half is the one that matters here — the INV-14 guards are fleet scripts whose
    source is dense with outward verbs as regex literals. A checker that cannot tell a Constant
    from an Import would flag the two most security-relevant scripts in the fleet and be switched
    off within a week.
    """
    must_fire = [
        ("import socket", "python", "import of a network module"),
        ("import urllib.request", "python", "dotted network import"),
        ("import subprocess\nsubprocess.run(['curl', 'https://x'])", "python", "subprocess curl"),
        ("import subprocess\nsubprocess.run(['git', 'push', 'origin'])", "python", "subprocess git push"),
        ("import os\nos.system('wget https://x')", "python", "os.system wget"),
        ("curl https://example.com", "bash", "bash curl"),
        ("git push origin main", "bash", "bash git push"),
    ]
    must_stay_silent = [
        ('import re\nOUTWARD = re.compile(r"\\bgit\\s+push\\b|\\bgh\\s+repo\\s+create\\b")',
         "python", "outward verbs as REGEX LITERALS (the INV-14 guard case)"),
        ("import subprocess\nsubprocess.run(['git', 'diff', '--cached'])", "python", "local git"),
        ("import subprocess\nsubprocess.run(['git', 'log', '-1'])", "python", "local git log"),
        ('echo "do not run git push here"', "bash", "verb inside a quoted string"),
        ("git diff --name-only", "bash", "local git in bash"),
        ("import pathlib, json, re", "python", "ordinary stdlib"),
    ]
    problems = []
    for src, lang, why in must_fire:
        f = check_python(src) if lang == "python" else check_bash(src)
        if not any(k == "VIOLATION" for _, k, _ in f):
            problems.append(f"did NOT fire on {why!r}")
    for src, lang, why in must_stay_silent:
        f = check_python(src) if lang == "python" else check_bash(src)
        if any(k == "VIOLATION" for _, k, _ in f):
            problems.append(f"FALSE POSITIVE on {why!r}: {f}")
    for p in problems:
        print(f"SELFTEST FAIL: {p}", file=sys.stderr)
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scripts-dir", default="vault-template/99-Operations/scripts")
    args = ap.parse_args()

    if args.selftest:
        problems = selftest()
        print("selftest: fires on calls, silent on names" if not problems
              else f"selftest: {len(problems)} problem(s)")
        return EXIT_SELFTEST if problems else EXIT_OK

    # The gate refuses to run on an unvalidated instrument (the exit-3 pattern, third use).
    if selftest():
        print("BLOCKED: inv6-offline-check selftest failed - the checker is not trustworthy.",
              file=sys.stderr)
        return EXIT_SELFTEST

    notes = sorted(pathlib.Path(args.scripts_dir).glob("*.md"))
    if not notes:
        print(f"BLOCKED: no fleet notes found under {args.scripts_dir}", file=sys.stderr)
        return EXIT_VIOLATION

    violations = unresolved = 0
    for note in notes:
        for lineno, kind, msg in check_note(note):
            print(f"  [{kind}] {note.name}:{lineno}  {msg}")
            if kind == "VIOLATION":
                violations += 1
            else:
                unresolved += 1

    print(f"inv6-offline-check: {len(notes)} fleet notes analysed - "
          f"{violations} violation(s), {unresolved} unresolved")
    print("NOTE: a clean static result does not prove offline behaviour; "
          "the netns run (inv6-offline-dynamic) is the behavioural half.")
    return EXIT_VIOLATION if (violations or unresolved) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
