#!/usr/bin/env python3
"""Template<->live parity check — is a deployed vault's LOCKSTEP scaffold in sync
with what this repo's `vault-template/` ships?

Orthogonal to render/reconcile. `reconcile` compares a script note to its deployed
`~/bin` target (note -> host). This compares the framework repo's shipped scaffold
(`vault-template/<prefix>`) against a deployed live vault (`<VAULT_ROOT>/<prefix>`) for
every LOCKSTEP prefix declared in `template-sync-manifest.json`. It answers the question
`reconcile` cannot: after a post-merge mirror, does every governed scaffold file the repo
shipped actually match what is deployed? Detection-only — it never writes; a human re-runs
the mirror to resolve drift (same posture as reconcile / INV-3).

Repo-only tool. The deployed vault is standalone (F15) and never references the repo, so
parity is a maintainer/mirror-time concern — not a vault fleet script, not a CI gate (CI
has no live vault to compare against). Stdlib-only, offline, no LLM (the INV-6 determinism
posture at the mirror-time layer).

Usage:  tools/template-parity.py [LIVE_VAULT]     # LIVE_VAULT defaults to $VAULT_ROOT
Exit:   0 in parity · 1 drift found · 3 blocked (no resolvable live vault / bad manifest).
"""
import json
import os
import pathlib
import sys

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_BLOCKED = 3


def _die_blocked(msg):
    print(f"BLOCKED: {msg}")
    raise SystemExit(EXIT_BLOCKED)


def _files_under(root: pathlib.Path, prefix: str):
    """Repo-relative file paths under root/prefix (empty set if the dir is absent)."""
    base = root / prefix
    if not base.exists():
        return set()
    return {str(p.relative_to(root)) for p in base.rglob("*") if p.is_file()}


def main(argv):
    here = pathlib.Path(__file__).resolve().parent          # tools/
    template = here.parent / "vault-template"                # repo-root/vault-template
    if not template.is_dir():
        _die_blocked(f"no vault-template/ found at {template}")

    live_arg = argv[1] if len(argv) > 1 else os.environ.get("VAULT_ROOT")
    if not live_arg:
        _die_blocked("no live vault — pass its path or export VAULT_ROOT")
    live = pathlib.Path(live_arg).expanduser().resolve()
    if not (live / "99-Operations").is_dir():
        _die_blocked(f"{live} does not look like a vault (no 99-Operations/)")

    manifest = json.loads((here / "template-sync-manifest.json").read_text())
    prefixes = manifest.get("lockstep", [])
    if not prefixes:
        _die_blocked("manifest declares no lockstep prefixes")
    exclude = set(manifest.get("exclude", []))

    checked = 0
    excluded = 0
    drift = []                                                # (rel, reason)
    for prefix in prefixes:
        for rel in sorted(_files_under(template, prefix) | _files_under(live, prefix)):
            if rel in exclude:
                excluded += 1
                continue
            checked += 1
            t, l = template / rel, live / rel
            if not l.exists():
                drift.append((rel, "MISSING-IN-LIVE"))
            elif not t.exists():
                drift.append((rel, "MISSING-IN-TEMPLATE"))
            elif t.read_bytes() != l.read_bytes():
                drift.append((rel, "DIFFERS"))

    for rel, reason in drift:
        print(f"{reason}: {rel}")
    # Print the denominator, never a bare "clean": an empty drift list is only trustworthy
    # next to the count of files actually compared (F20 — evidence, not an unearned "ok").
    print(f"parity: {checked} lockstep files checked across {len(prefixes)} "
          f"prefixes ({excluded} excluded) — {len(drift)} drift")
    return EXIT_DRIFT if drift else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
