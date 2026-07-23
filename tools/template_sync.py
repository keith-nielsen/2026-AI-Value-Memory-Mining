#!/usr/bin/env python3
"""Shared tree-walk + comparison logic for the template<->live mirror tools.

Both `template-parity.py` (detect drift) and `template-mirror.py` (fix drift) operate on
the same concept — the LOCKSTEP scaffold declared in `template-sync-manifest.json` — and must
agree, byte-for-byte, on what "in sync" means. That agreement lives here, in one module both
import, so the detector and the fixer can never silently diverge about which files are governed
scaffold, how they are compared, or how the closing tally is phrased.

Stdlib-only, offline, no LLM (the INV-6 determinism posture at the mirror-time maintenance
layer). Not a fleet script and not deployed anywhere: a repo-side maintainer library that sits
alongside its two callers in `tools/`.
"""
import json
import os
import pathlib

EXIT_OK = 0
EXIT_BLOCKED = 3

# Drift reasons, single source of truth so both tools print identical wording.
MISSING_IN_LIVE = "MISSING-IN-LIVE"
MISSING_IN_TEMPLATE = "MISSING-IN-TEMPLATE"
DIFFERS = "DIFFERS"


def die_blocked(msg):
    """Print the BLOCKED evidence line and exit 3 — the fleet's blocked contract."""
    print(f"BLOCKED: {msg}")
    raise SystemExit(EXIT_BLOCKED)


def load_manifest(tools_dir: pathlib.Path):
    """Return (lockstep_prefixes, exclude_set) from template-sync-manifest.json, or die."""
    manifest = json.loads((tools_dir / "template-sync-manifest.json").read_text())
    prefixes = manifest.get("lockstep", [])
    if not prefixes:
        die_blocked("manifest declares no lockstep prefixes")
    exclude = set(manifest.get("exclude", []))
    return prefixes, exclude


def resolve_trees(tools_dir: pathlib.Path, live_arg):
    """Resolve (template_dir, live_dir, prefixes, exclude) or die BLOCKED.

    `template_dir` is `<repo>/vault-template` (tools/ lives at the repo root); `live_arg` is a
    path string (from argv or $VAULT_ROOT). Same resolution and blocked conditions both tools use.
    """
    template = tools_dir.parent / "vault-template"
    if not template.is_dir():
        die_blocked(f"no vault-template/ found at {template}")
    if not live_arg:
        die_blocked("no live vault — pass its path or export VAULT_ROOT")
    live = pathlib.Path(live_arg).expanduser().resolve()
    if not (live / "99-Operations").is_dir():
        die_blocked(f"{live} does not look like a vault (no 99-Operations/)")
    prefixes, exclude = load_manifest(tools_dir)
    return template, live, prefixes, exclude


def live_arg_from(argv):
    """The live-vault path: positional argv[1] if given, else $VAULT_ROOT (may be None)."""
    return argv[1] if len(argv) > 1 else os.environ.get("VAULT_ROOT")


def files_under(root: pathlib.Path, prefix: str):
    """Repo-relative file paths under root/prefix (empty set if the dir is absent)."""
    base = root / prefix
    if not base.exists():
        return set()
    return {str(p.relative_to(root)) for p in base.rglob("*") if p.is_file()}


def compare(template: pathlib.Path, live: pathlib.Path, prefixes, exclude):
    """Walk both trees and classify every non-excluded lockstep file.

    Returns (checked, excluded, drift) where drift is a list of (rel, reason) with reason one of
    MISSING_IN_LIVE / MISSING_IN_TEMPLATE / DIFFERS. Directory-prefix scope: the union of files
    under each prefix in EITHER tree is compared, so a newly-shipped file cannot go unchecked.
    """
    checked = 0
    excluded = 0
    drift = []
    for prefix in prefixes:
        for rel in sorted(files_under(template, prefix) | files_under(live, prefix)):
            if rel in exclude:
                excluded += 1
                continue
            checked += 1
            t, l = template / rel, live / rel
            if not l.exists():
                drift.append((rel, MISSING_IN_LIVE))
            elif not t.exists():
                drift.append((rel, MISSING_IN_TEMPLATE))
            elif t.read_bytes() != l.read_bytes():
                drift.append((rel, DIFFERS))
    return checked, excluded, drift


def tally_line(checked, prefixes, excluded, drift_count):
    """The closing evidence line, denominator first — never a bare 'clean' (F20).

    Byte-identical wording for both tools so the 'evidence with a denominator' rule cannot
    erode one tool at a time.
    """
    return (f"parity: {checked} lockstep files checked across {len(prefixes)} "
            f"prefixes ({excluded} excluded) — {drift_count} drift")
