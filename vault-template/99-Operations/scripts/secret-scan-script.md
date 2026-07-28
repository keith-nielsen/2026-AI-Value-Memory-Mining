---
type: meta-script
deploy_target: ~/bin/vault_secrets.py
runtime: manual
class: script
created: 2026-07-28
updated: 2026-07-28
---
## Rationale

Single source of truth for credential-format detection (INV-7, Tier-0). Imported and called
by the `pre-commit` commit gate, and runnable standalone over arbitrary paths or over the
whole git object database for a historical sweep.

**Why this exists.** INV-7 ("no secrets in any vault file") is Tier-0 and, until this script,
was enforced by **nothing** — no hook, no linter, no CI job. A secret pasted into a note
committed cleanly. The 2026-07-28 Tier-0 enforcement audit found it the only live invariant
with zero mechanism of any kind, alongside INV-6.

**Two tiers, and only one of them blocks.** `HIGH` patterns are anchored on published vendor
token formats (`ghp_` + 36 chars, `AKIA` + 16, and so on): a match is a credential or a
deliberate forgery, so the false-positive rate is ~0 and it is safe to block a commit on.
`ADVISORY` patterns are contextual (`password = "…"`) and have a real false-positive rate over
a corpus that legitimately *discusses* credentials — which this vault does constantly. Advisory
matches are **reported by the standalone tool and never consulted by the hook.** This split is
deliberate and is the direct application of the `github-canary-barium-lunch-investigation`
finding RC-E: *over-denial is not benign, it is camouflage.* A gate that fires on every note
about tokens teaches its operator to bypass it, and the vault's own audit notes would be its
most frequent victims.

**Redaction is a hard property, not a courtesy.** A scanner that prints what it found writes
the secret into a terminal, a log, and possibly a commit message — violating INV-7 while
checking it. Every reported match is truncated to its first 4 characters plus a length.

**Detection scope, stated honestly.** This matches *known formats*. It does not detect a
password with no distinguishing shape, a secret split across lines, or one that is encoded or
encrypted. It is a boundary gate, not an assurance that no secret exists — that claim requires
custody discipline (credentials held in the OS keyring or a manager), of which this script is
one mechanical half. Do not cite a clean run as proof of absence.

**Environment-free**, per the fleet contract (ADR-0023): no config, no `$VAULT_ROOT`, no
network (INV-6). It reads only the bytes it is given.

## Implementation
```python
#!/usr/bin/env python3
"""Credential-format detection for INV-7. Two tiers; only HIGH is gate-worthy.

Usage:
  vault_secrets.py --staged            scan git-staged content (the commit gate's mode)
  vault_secrets.py PATH [PATH ...]     scan files/directories
  vault_secrets.py --history [REPO]    scan every blob in the object DB, incl. unreachable
  vault_secrets.py --selftest          prove the patterns fire (control); exit 0 if healthy

Exit: 0 clean · 1 HIGH match found · 2 bad usage · 3 selftest failed (instrument INVALID).
"""
import re
import subprocess
import sys
import pathlib

EXIT_OK, EXIT_FOUND, EXIT_USAGE, EXIT_SELFTEST = 0, 1, 2, 3

# --- HIGH: anchored vendor formats. A match is a credential. Safe to block on. ---
HIGH = [
    ("github-pat-classic", re.compile(rb"\bghp_[A-Za-z0-9]{36}\b")),
    ("github-oauth",       re.compile(rb"\bgho_[A-Za-z0-9]{36}\b")),
    ("github-user-server", re.compile(rb"\bgh[usr]_[A-Za-z0-9]{36}\b")),
    ("github-pat-fine",    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{22,}")),
    ("pypi-token",         re.compile(rb"\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{20,}")),
    ("npm-token",          re.compile(rb"\bnpm_[A-Za-z0-9]{36}\b")),
    ("anthropic-key",      re.compile(rb"\bsk-ant-[A-Za-z0-9\-_]{24,}")),
    ("openai-key",         re.compile(rb"\bsk-proj-[A-Za-z0-9\-_]{20,}|\bsk-[A-Za-z0-9]{48}\b")),
    ("aws-access-key",     re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("google-api-key",     re.compile(rb"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("slack-token",        re.compile(rb"\bxox[baprs]-[0-9A-Za-z\-]{10,}")),
    ("stripe-live-key",    re.compile(rb"\b[sr]k_live_[0-9a-zA-Z]{24,}")),
    ("private-key-block",  re.compile(rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?: BLOCK)?-----")),
    ("gh-oauth-yaml",      re.compile(rb"^\s*oauth_token:\s*\S+", re.M)),
]

# --- ADVISORY: contextual. Real false-positive rate. NEVER consulted by the gate. ---
ADVISORY = [
    ("assignment-secretish", re.compile(
        rb"""(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)\b"""
        rb"""\s*[:=]\s*(?P<q>["'])(?P<val>(?!\s*$)[^"'\n]{8,})(?P=q)""")),
    ("jwt-like", re.compile(rb"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".mypy_cache", ".pytest_cache"}
MAX_BYTES = 2_000_000


def redact(raw):
    """Never emit a secret. First 4 chars + length is enough to locate and triage it."""
    s = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    return f"{s[:4]}... (len={len(s)})"


def scan_bytes(data, patterns):
    hits = []
    for name, rx in patterns:
        for m in rx.finditer(data):
            line = data.count(b"\n", 0, m.start()) + 1
            val = (m.groupdict() or {}).get("val")
            hits.append((name, line, redact(val if val else m.group(0))))
    return hits


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, check=False)


def scan_staged(repo="."):
    """Added/copied/modified staged blobs. Content, not names — the naming gate does names."""
    out = _git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACM").stdout
    hits = []
    for name in out.decode("utf-8", "replace").splitlines():
        if not name.strip():
            continue
        blob = _git(repo, "show", f":{name}").stdout
        if len(blob) > MAX_BYTES:
            continue
        for pat, line, red in scan_bytes(blob, HIGH):
            hits.append((name, line, pat, red))
    return hits


def iter_files(paths):
    for raw in paths:
        p = pathlib.Path(raw)
        if p.is_file():
            yield p
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and not f.is_symlink() and not (SKIP_DIRS & set(f.parts)):
                    yield f


def scan_paths(paths, patterns):
    hits = []
    for f in iter_files(paths):
        try:
            if f.stat().st_size > MAX_BYTES:
                continue
            data = f.read_bytes()
        except OSError:
            continue
        for pat, line, red in scan_bytes(data, patterns):
            hits.append((str(f), line, pat, red))
    return hits


def scan_history(repo="."):
    """Every blob in the object DB — including UNREACHABLE ones (discarded commits,
    dropped rebases, amended-away content). `rev-list` cannot see those, and they are
    exactly where an accidentally-committed-then-'removed' secret survives."""
    paths = {}
    for line in _git(repo, "rev-list", "--all", "--objects").stdout.decode(
            "utf-8", "replace").splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            paths.setdefault(parts[0], parts[1])

    listing = _git(repo, "cat-file", "--batch-all-objects",
                   "--batch-check=%(objectname) %(objecttype) %(objectsize)").stdout
    hits = []
    for row in listing.decode("utf-8", "replace").splitlines():
        parts = row.split()
        if len(parts) != 3 or parts[1] != "blob" or int(parts[2]) > MAX_BYTES:
            continue
        sha = parts[0]
        data = _git(repo, "cat-file", "blob", sha).stdout
        where = paths.get(sha, f"<unreachable blob {sha[:12]}>")
        for pat, line, red in scan_bytes(data, HIGH):
            hits.append((where, line, pat, red))
    return hits


def selftest():
    """Control: the patterns must fire on synthetic inputs, and ADVISORY-only input must
    NOT reach HIGH. A scanner that cannot be shown to detect anything reports 'clean' for
    both a clean corpus and a broken regex — the failure mode this whole gate exists to avoid."""
    # Every fixture is BUILT, never written as a literal: this file is itself scanned by the
    # CI job and by its own commit gate, so a literal fixture would make the scanner report a
    # finding against its own source forever. Concatenation keeps the pattern out of the bytes
    # on disk while producing it exactly at runtime. (Caught by running the CI job: the
    # private-key header was the one fixture left literal and it flagged this file plus the
    # test module.) The alternative — excluding the scanner's own paths from the scan — would
    # carve a blind spot precisely where a real secret would be most quietly hidden.
    cases = [
        (b'tok = "ghp_' + b"A" * 36 + b'"', "github-pat-classic"),
        (b"AWS=AKIA" + b"ABCDEFGHIJKLMNOP", "aws-access-key"),
        (b"npm_" + b"B" * 36, "npm-token"),
        (b"-----BEGIN " + b"OPENSSH " + b"PRIVATE KEY" + b"-----", "private-key-block"),
    ]
    problems = []
    for data, expected in cases:
        names = {n for n, _, _ in scan_bytes(data, HIGH)}
        if expected not in names:
            problems.append(f"HIGH pattern {expected!r} did not fire")
    advisory_only = b'password = "hunter2000"'
    if scan_bytes(advisory_only, HIGH):
        problems.append("advisory-tier input leaked into the HIGH tier")
    if not scan_bytes(advisory_only, ADVISORY):
        problems.append("ADVISORY pattern did not fire")
    if scan_bytes(b"a perfectly ordinary sentence about tokens and passwords", HIGH):
        problems.append("HIGH tier fired on benign prose")
    for p in problems:
        print(f"SELFTEST FAIL: {p}", file=sys.stderr)
    return problems


def _print(hits, label):
    print(f"{label}: {len(hits)} match(es)")
    for where, line, pat, red in hits:
        print(f"  [{pat}] {where}:{line}  {red}")


def main(argv):
    if not argv:
        print(__doc__, file=sys.stderr)
        return EXIT_USAGE

    if argv[0] == "--selftest":
        problems = selftest()
        print("selftest: patterns fire, tiers are disjoint" if not problems
              else f"selftest: {len(problems)} problem(s)")
        return EXIT_SELFTEST if problems else EXIT_OK

    # The gate refuses to run on an uncontrolled instrument.
    if selftest():
        print("BLOCKED: vault_secrets.py selftest failed - the scanner is not trustworthy.",
              file=sys.stderr)
        return EXIT_SELFTEST

    if argv[0] == "--staged":
        hits = scan_staged()
        if hits:
            print("", file=sys.stderr)
            print("  BLOCKED: staged content matches a credential format (INV-7)", file=sys.stderr)
            for where, line, pat, red in hits:
                print(f"     {where}:{line}  [{pat}]  {red}", file=sys.stderr)
            print("", file=sys.stderr)
            print("  INV-7 is Tier-0: no secrets in any vault file. Remove the credential,", file=sys.stderr)
            print("  then ROTATE it - a secret that reached the working tree is compromised.", file=sys.stderr)
            print("", file=sys.stderr)
            return EXIT_FOUND
        return EXIT_OK

    if argv[0] == "--history":
        repo = argv[1] if len(argv) > 1 else "."
        hits = scan_history(repo)
        _print(hits, "HIGH (object database, incl. unreachable)")
        return EXIT_FOUND if hits else EXIT_OK

    high = scan_paths(argv, HIGH)
    adv = scan_paths(argv, ADVISORY)
    _print(high, "HIGH")
    _print(adv, "ADVISORY (report-only, never gates)")
    return EXIT_FOUND if high else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```
